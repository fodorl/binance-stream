#!/usr/bin/env python3
"""
BBO message processor for the Binance BBO stream web server.
"""
import logging
import json
import time
import traceback
import random
from utils import current_time_ms

logger = logging.getLogger(__name__)

class BBOProcessor:
    """
    Processes BBO updates from Binance WebSocket.
    Formats and prepares them for client delivery.
    """
    def __init__(self, message_queue_processor, cache_manager=None):
        """
        Initialize the BBO processor
        
        Args:
            message_queue_processor (MessageQueueProcessor): The message queue processor for broadcasting
            cache_manager (CacheManager, optional): The cache manager for storing historical data
        """
        self.message_queue_processor = message_queue_processor
        self.cache_manager = cache_manager
        self.latest_data = {}
        
    def process_bbo_update(self, message):
        """
        Process BBO update from Binance WebSocket.
        
        Args:
            message (str): JSON message from Binance WebSocket
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            # Only log 1% of messages to avoid excessive logging
            log_this_message = random.random() < 0.01
            
            # Parse the message
            message_data = json.loads(message)
            
            # Extract data
            stream = message_data.get('stream', '')
            data = message_data.get('data', {})
            
            # Filter out heartbeats and non-BBO messages
            if not stream or not data or 'B' not in data or 'A' not in data:
                return False
            
            symbol = stream.split('@')[0].upper()
            timestamp = data.get('E', 0)
            bid_price = data.get('b', '0')
            bid_qty = data.get('B', '0')
            ask_price = data.get('a', '0')
            ask_qty = data.get('A', '0')
            
            # Calculate latency
            exchange_time = timestamp
            received_time = current_time_ms()
            backend_latency = received_time - exchange_time
            
            # Only process if latency is reasonable (less than 10 seconds)
            if backend_latency > 10000:
                if log_this_message:
                    logger.warning(f"Skipping stale update with high latency: {backend_latency}ms")
                return False
                
            # Format the data
            update_data = {
                'symbol': symbol,
                'timestamp': timestamp,
                'bidPrice': bid_price,
                'bidQty': bid_qty,
                'askPrice': ask_price,
                'askQty': ask_qty,
                'latency': {
                    'backend': backend_latency,
                    'exchangeTime': exchange_time,
                    'receivedTime': received_time
                },
                'backendLatency': backend_latency,  # Add directly to root for easier access in cache
                # Also add snake_case versions for compatibility with other parts of the system
                'bid_price': bid_price,
                'bid_qty': bid_qty,
                'ask_price': ask_price,
                'ask_qty': ask_qty,
                'exchange_time': exchange_time,
                'received_timestamp': received_time
            }
            
            # Store the latest data
            self.latest_data = update_data
            
            # Put the update in the message queue
            self.message_queue_processor.broadcast_message(('bbo_update', update_data))
            
            # Add to cache if cache_manager is available
            if self.cache_manager:
                try:
                    # Log at DEBUG level instead of INFO to reduce log spam
                    logger.debug(f"Sending {symbol} update to cache with timestamp {timestamp}")
                    self.cache_manager.process_bbo_update(update_data)
                except Exception as e:
                    logger.error(f"Error adding update to cache: {str(e)}")
                    logger.error(f"Update data that failed: {update_data}")
            else:
                logger.warning("No cache_manager available, update not cached")
            
            # Log backend latency (only 1% of messages)
            if log_this_message:
                logger.debug(f"Backend latency: {backend_latency}ms | exchange_time: {exchange_time}, received_time: {received_time}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing BBO update: {e}")
            traceback.print_exc()
            return False
            
    def get_latest_data(self):
        """Get the latest BBO data"""
        return self.latest_data
