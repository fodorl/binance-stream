#!/usr/bin/env python3
"""
Server implementation for Binance BBO stream web interface.
Integrates Flask, Socket.IO, and SSL support for serving a real-time BBO frontend.
"""

import os
import logging
import eventlet
from flask import Flask
from flask_socketio import SocketIO

# Import cache components
from cache import BBOCache
from cache.cache_manager import CacheManager
from cache.rest_api import BBOHistoryAPI

from .message_queue import MessageQueueProcessor
from .client_manager import ClientManager
from .routes import RouteHandler
from .socket_handlers import SocketHandler
from .ssl_utils import ensure_certs_directory, create_ssl_certs
from .message_processor import BBOProcessor

# Monkey patch standard library for eventlet if not done already
eventlet.monkey_patch()

logger = logging.getLogger(__name__)

class WebServer:
    """
    Web server for the Binance BBO stream application.
    Integrates Flask, Socket.IO, and message processing.
    """
    def __init__(self, host="0.0.0.0", port=5000, debug=False, use_ssl=True, 
                 ssl_cert_path="certs/cert.pem", ssl_key_path="certs/key.pem"):
        """
        Initialize the web server
        
        Args:
            host (str): The host to bind to
            port (int): The port to bind to
            debug (bool): Whether to run in debug mode
            use_ssl (bool): Whether to use SSL
            ssl_cert_path (str): Path to SSL certificate
            ssl_key_path (str): Path to SSL key
        """
        self.host = host
        self.port = port
        self.debug = debug
        self.use_ssl = use_ssl
        self.ssl_cert_path = ssl_cert_path
        self.ssl_key_path = ssl_key_path
        print("Setting up Server...")
        
        # Create Flask app with static and template folders relative to project root
        self.app = Flask("binance_bbo_stream", 
                          static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'), 
                          template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'))
        
        # Add CORS headers
        @self.app.after_request
        def add_cors_headers(response):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            return response
        
        # Initialize Socket.IO with correct settings
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins="*",
            logger=False,  # Disable SocketIO logging to avoid spam 
            engineio_logger=False,  # Set to False to reduce log spam
            async_mode='eventlet',
            always_connect=True,
            path='/socket.io/',
            max_http_buffer_size=1e7,
            ping_timeout=20,  # 20 second ping timeout to match client
            ping_interval=25,  # 25 second ping interval to match client
            # Ensure WebSocket transport is available but don't force it
            # Allow both websocket and polling for compatibility
            # Transport upgrade is enabled by default
        )
        
        # Initialize components
        self.client_manager = ClientManager()
        self.message_queue_processor = MessageQueueProcessor(self.socketio)
        
        # Initialize the cache manager
        self.cache_manager = CacheManager(
            max_items_per_symbol=1000000,  # 1 million items per symbol
            persist_to_disk=True,
            cache_dir="cache_data",
            cleanup_interval_hours=6
        )
        
        # Initialize BBO processor with cache manager
        self.bbo_processor = BBOProcessor(self.message_queue_processor, self.cache_manager)
        
        self.route_handler = RouteHandler(self.app)
        self.socket_handler = SocketHandler(
            self.socketio, 
            self.client_manager, 
            self.message_queue_processor
        )
        
        # Initialize BBO History API
        self.history_api = BBOHistoryAPI(self.cache_manager.get_cache())
        self.app.register_blueprint(self.history_api.blueprint)
        
        # Set running flag for thread management
        self.is_running = False
        
    def start(self):
        """Start the web server and message queue processor"""
        if not self.is_running:
            self.is_running = True
            
            # Start the message queue processor
            self.message_queue_processor.start()
            
            # Start the cache manager
            self.cache_manager.start()
            
            try:
                # Use SSL if enabled
                if self.use_ssl:
                    # Ensure certificate directories exist
                    ensure_certs_directory()
                    
                    # Check if certificates exist, create them if not
                    if not os.path.exists(self.ssl_cert_path) or not os.path.exists(self.ssl_key_path):
                        logger.info(f"Creating self-signed SSL certificates at {self.ssl_cert_path} and {self.ssl_key_path}")
                        create_ssl_certs(self.ssl_cert_path, self.ssl_key_path)
                    
                    # Start with SSL
                    logger.info(f"Starting WebSocket server with SSL on https://{self.host}:{self.port}")
                    self.socketio.run(
                        self.app,
                        host=self.host,
                        port=self.port,
                        debug=self.debug,
                        certfile=self.ssl_cert_path,
                        keyfile=self.ssl_key_path,
                        use_reloader=False
                    )
                else:
                    # Start without SSL
                    logger.info(f"Starting WebSocket server without SSL on http://{self.host}:{self.port}")
                    self.socketio.run(
                        self.app,
                        host=self.host,
                        port=self.port,
                        debug=self.debug,
                        use_reloader=False
                    )
            except Exception as e:
                logger.error(f"Error starting server: {e}")
                self.is_running = False
                self.message_queue_processor.stop()
                self.cache_manager.stop()
    
    def run(self):
        """Run the web server - compatibility with older code"""
        self.start()
    
    def stop(self):
        """Stop the web server and message queue processor"""
        self.is_running = False
        self.message_queue_processor.stop()
        self.cache_manager.stop()
        logger.info("Web server stopped")
    
    def get_host_url(self) -> str:
        """Get the host URL for this server"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"
    
    def broadcast_message(self, data):
        """
        Add message to queue for broadcast to all clients
        
        Args:
            data: The message data to broadcast
        """
        self.message_queue_processor.broadcast_message(data)
