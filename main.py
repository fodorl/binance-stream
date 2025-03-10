#!/usr/bin/env python3
"""
Main entry point for the Binance BBO stream application.
"""
import os
import sys
import time
import logging
import signal
import asyncio
import threading
import eventlet
from logging.handlers import RotatingFileHandler

from config import setup_logging, DEFAULT_SYMBOL, DEFAULT_AUTO_RECONNECT, DEFAULT_MAX_RETRIES
from message_processor import MessageProcessor
from websocket_client import BinanceWebSocketClient
from web import WebServer
from cache import BBOCache, CacheManager

# Patch standard library for eventlet
eventlet.monkey_patch()

# Set up logging
logger = setup_logging()

# Global reference to objects for clean shutdown
websocket_client = None
web_server = None
message_processor = None

# Create event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
stop_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle signals for clean shutdown"""
    logger.info("Shutdown signal received, cleaning up...")
    stop_event.set()

async def shutdown():
    """Perform clean shutdown"""
    global websocket_client, web_server, message_processor
    
    # Stop the message processor if it's running
    if message_processor:
        await message_processor.stop()
    
    # Stop the WebSocket client if it's running
    if websocket_client:
        await websocket_client.disconnect()
    
    # Stop the web server if it's running
    if web_server:
        web_server.stop()
    
    logger.info("Application has been shut down")

def start_web_server(web_host, web_port, debug=False):
    """Start the web server in a separate thread"""
    global web_server
    try:
        web_server = WebServer(host=web_host, port=web_port, debug=debug)
        # Start the web server
        web_server.run()
    except Exception as e:
        logger.error(f"Error in web server thread: {e}")
        
async def main():
    """Application entry point"""
    global websocket_client, web_server, stop_event, message_processor
    
    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration from environment variables
    symbol = os.environ.get("SYMBOL", DEFAULT_SYMBOL)
    web_host = os.environ.get("WEB_HOST", "0.0.0.0")
    web_port = int(os.environ.get("WEB_PORT", "5000"))
    web_enabled = os.environ.get("WEB_ENABLED", "true").lower() == "true"
    debug = os.environ.get("DEBUG", "").lower() == "true"
    use_ssl = False  # Disable SSL for debugging
    ssl_cert_path = os.environ.get("SSL_CERT_PATH", "certs/cert.pem")
    ssl_key_path = os.environ.get("SSL_KEY_PATH", "certs/key.pem")
    
    # Get cache configuration from environment variables
    cache_dir = os.environ.get("CACHE_DIR", "cache_data")
    cache_enabled = os.environ.get("CACHE_ENABLED", "true").lower() == "true"
    cache_max_items = int(os.environ.get("CACHE_MAX_ITEMS", "1000000"))
    cache_persist = os.environ.get("CACHE_PERSIST", "true").lower() == "true"
    cache_cleanup_hours = int(os.environ.get("CACHE_CLEANUP_HOURS", "6"))
    
    try:
        # Ensure cache directory exists if caching is enabled
        if cache_enabled:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Ensured cache directory exists: {cache_dir}")
        
        # Initialize the web server
        if web_enabled:
            logger.info(f"Starting web server on http://{web_host}:{web_port}")
            web_server = WebServer(
                host=web_host,
                port=web_port,
                debug=debug,
                use_ssl=use_ssl,
                ssl_cert_path=ssl_cert_path,
                ssl_key_path=ssl_key_path
            )
            
            # Configure cache if enabled
            if not cache_enabled:
                # Disable cache if not enabled
                web_server.cache_manager = None
                logger.info("Caching system is disabled by configuration")
            else:
                # Update cache manager with environment settings
                old_cache = web_server.cache_manager.cache
                logger.info(f"Previous cache object ID: {id(old_cache)}")
                
                web_server.cache_manager.cache = BBOCache(
                    max_items_per_symbol=cache_max_items,
                    persist_to_disk=cache_persist,
                    cache_dir=cache_dir
                )
                new_cache = web_server.cache_manager.cache
                logger.info(f"New cache object ID: {id(new_cache)}")
                
                # Also update the history API's cache reference
                logger.info(f"Current history API cache object ID: {id(web_server.history_api.cache)}")
                web_server.history_api.cache = web_server.cache_manager.cache
                logger.info(f"Updated history API cache object ID: {id(web_server.history_api.cache)}")
                
                web_server.cache_manager.cleanup_interval_ms = cache_cleanup_hours * 3600 * 1000
                logger.info(f"Configured cache with max items: {cache_max_items}, persist: {cache_persist}, cleanup: {cache_cleanup_hours}h")
            
            # Start the web server in a separate thread
            web_thread = eventlet.spawn(web_server.run)
            
            # Give the web server a moment to start
            await asyncio.sleep(2)
        
        # Create components
        message_processor = MessageProcessor(
            symbol=symbol,
            web_server=web_server if web_enabled else None,
            cache_manager=web_server.cache_manager if web_enabled and cache_enabled else None
        )
        
        # Start the message processor dispatch task
        await message_processor.start()
        
        websocket_client = BinanceWebSocketClient(
            symbol=symbol,
            message_processor=message_processor,
            auto_reconnect=DEFAULT_AUTO_RECONNECT,
            max_retries=DEFAULT_MAX_RETRIES
        )
        
        # Run the WebSocket client
        logger.info(f"Starting Binance BBO stream for {symbol.upper()}")
        
        # Make initial connection attempt
        connection_attempts = 0
        max_initial_attempts = 5
        initial_success = False
        
        while connection_attempts < max_initial_attempts and not initial_success and not stop_event.is_set():
            initial_success = await websocket_client.connect()
            if not initial_success:
                connection_attempts += 1
                logger.warning(f"Initial connection failed. Attempt {connection_attempts}/{max_initial_attempts}")
                await asyncio.sleep(2)
        
        if not initial_success:
            logger.error("Failed to establish initial connection after multiple attempts")
            logger.info("Continuing anyway, will keep trying in the background")
        
        # Keep running until stop signal
        message_count = 0
        last_received_time = time.time()
        
        while not stop_event.is_set():
            message = await websocket_client.receive_message()
            if message:
                message_count += 1
                last_received_time = time.time()
                await message_processor.process_message(message)
            
            # Check for prolonged silence (no messages for 60 seconds)
            if time.time() - last_received_time > 60:
                logger.warning("No messages received for 60 seconds. Reconnecting...")
                await websocket_client.disconnect()
                await asyncio.sleep(1)
                await websocket_client.connect()
                last_received_time = time.time()  # Reset timer
                
            # Log message count periodically
            if message_count > 0 and message_count % 100 == 0:
                logger.info(f"Processed {message_count} messages so far")
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Clean shutdown
        await shutdown()

def shutdown_handler(signum, frame):
    """Handle signals for clean shutdown"""
    logger.info(f"Received signal {signum}, shutting down...")
    stop_event.set()
    loop.run_until_complete(shutdown())
    logger.info("Application terminated")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

if __name__ == "__main__":
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user. Exiting...")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        import traceback
        logger.error(traceback.format_exc())
