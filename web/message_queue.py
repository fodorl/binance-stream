#!/usr/bin/env python3
"""
Message queue processor for the Binance BBO stream web server.
Handles queuing and broadcasting messages to connected clients.
"""
import logging
import random
import json
import time
import eventlet
import eventlet.queue as queue
from utils import current_time_ms

logger = logging.getLogger(__name__)

class MessageQueueProcessor:
    """
    Processes queued messages and broadcasts them to clients via Socket.IO.
    Handles throttling and batching for efficient message delivery.
    """
    def __init__(self, socketio):
        """
        Initialize the message queue processor
        
        Args:
            socketio (SocketIO): The Flask-SocketIO instance for broadcasting
        """
        self.socketio = socketio
        self.message_queue = queue.Queue()
        self.is_running = False
        self.thread = None
        
        # Throttling control
        self.last_message_time = 0
        self.throttle_interval = 100  # 100 milliseconds between messages
        self.throttled_message = None  # Store the latest message when throttling
        
        # Latest data cache
        self.latest_data = {}
    
    def broadcast_message(self, data):
        """
        Add message to queue for broadcast to all clients
        
        Args:
            data: The message data to broadcast
        """
        try:
            # Detect growing queue issues early
            queue_size = self.message_queue.qsize()
            if queue_size > 50:  # Lower threshold for warning
                logger.warning(f"Message queue is growing rapidly: size={queue_size}")

            # Add to message queue
            self.message_queue.put(data)
            logger.debug(f"Message added to queue, current size: {queue_size}")
        except Exception as e:
            logger.error(f"Error queuing message: {e}")
    
    def get_latest_data(self):
        """
        Get the latest cached data
        
        Returns:
            dict: The latest BBO data
        """
        return self.latest_data
        
    def start(self):
        """Start the message queue processor thread"""
        if not self.is_running:
            self.is_running = True
            self.thread = eventlet.spawn(self._process_message_queue)
            logger.info("Message queue processor thread started")
            
    def stop(self):
        """Stop the message queue processor thread"""
        self.is_running = False
        if self.thread:
            self.thread.kill()
            self.thread = None
        logger.info("Message queue processor thread stopped")
            
    def _process_message_queue(self):
        """Background worker to process and emit messages"""
        logger.info("Starting message processing thread")
        batch_size = 5  # Process messages in small batches for efficiency
        
        while self.is_running:
            try:
                # Process messages in batches when available
                messages_to_process = []
                process_time = current_time_ms()
                
                # Try to get a batch of messages quickly
                try:
                    # Get at least one message (blocking with timeout)
                    message = self.message_queue.get(timeout=0.5)
                    messages_to_process.append(message)
                    
                    # Get more messages if available (non-blocking)
                    for _ in range(batch_size - 1):
                        try:
                            message = self.message_queue.get_nowait()
                            messages_to_process.append(message)
                        except queue.Empty:
                            break
                except queue.Empty:
                    # No messages available, continue loop
                    continue
                
                # Log if we're processing a batch
                if len(messages_to_process) > 1:
                    logger.debug(f"Processing batch of {len(messages_to_process)} messages")
                
                # Keep track of throttling
                current_time = current_time_ms()
                time_since_last_message = current_time - self.last_message_time
                
                # Process each message in the batch
                for message in messages_to_process:
                    # Format the data for the client
                    if isinstance(message, tuple) and len(message) == 2:
                        event_type, data = message
                        # This is likely from the process_bbo_update method
                        if event_type == 'bbo_update' and isinstance(data, dict):
                            # Already formatted, just emit it
                            formatted_data = data
                            logger.debug(f"Emitting pre-formatted bbo_update data: {formatted_data}")
                            
                            # Update latest data
                            self.latest_data = formatted_data
                            
                            # Send directly via socketio
                            logger.debug(f"Emitting event '{event_type}' to all [/]")
                            self.socketio.emit(event_type, formatted_data)
                            
                            # Mark as processed
                            for i in range(len(messages_to_process)):
                                self.message_queue.task_done()
                            
                            # Skip the rest of the loop
                            continue
                    elif isinstance(message, dict):
                        if 'bid_price' in message and 'ask_price' in message:
                            # This is from our MessageProcessor
                            backendLatency = None
                            
                            # Use the already calculated latency from MessageProcessor if available
                            if message.get('latency') is not None:
                                backendLatency = message.get('latency')
                                logger.debug(f"Using pre-calculated latency: {backendLatency}ms")
                            
                            # Otherwise calculate from exchange_time
                            elif message.get('exchange_time') is not None:
                                exchange_time = int(message.get('exchange_time'))
                                received_time = message.get('received_timestamp', process_time)
                                
                                # Prefer using the original received timestamp
                                calculated_latency = received_time - exchange_time
                                
                                # Only use reasonable latency values (less than 10 seconds)
                                if calculated_latency < 10000:  # 10 seconds max
                                    backendLatency = calculated_latency
                                    logger.debug(f"Calculated latency: {backendLatency}ms (exchange_time: {exchange_time}, received_time: {received_time})")
                                else:
                                    logger.warning(f"Latency too high: {calculated_latency}ms - ignoring")
                            
                            formatted_data = {
                                'symbol': message.get('symbol', 'UNKNOWN'),
                                'bidPrice': str(message.get('bid_price', '0.00')),
                                'bidQty': str(message.get('bid_qty', '0.0000')),
                                'askPrice': str(message.get('ask_price', '0.00')),
                                'askQty': str(message.get('ask_qty', '0.0000')),
                                'timestamp': message.get('exchange_time', process_time),
                                'serverTimestamp': process_time,
                                'backendLatency': backendLatency
                            }
                            
                            # Log detailed latency info for debugging
                            logger.debug(f"Backend latency: {backendLatency}ms | exchange_time: {message.get('exchange_time')}, " +
                                       f"received_time: {message.get('received_timestamp')}, process_time: {process_time}")
                        else:
                            # This is raw Binance format
                            backendLatency = None
                            if message.get('E') is not None:
                                exchange_time = int(message.get('E'))
                                received_time = message.get('received_timestamp', process_time)
                                
                                # Prefer using the original received timestamp
                                calculated_latency = received_time - exchange_time
                                
                                # Only use reasonable latency values (less than 10 seconds)
                                if calculated_latency < 10000:  # 10 seconds max
                                    backendLatency = calculated_latency
                                    logger.debug(f"Calculated latency: {backendLatency}ms (exchange_time: {exchange_time}, received_time: {received_time})")
                                else:
                                    logger.warning(f"Latency too high: {calculated_latency}ms - ignoring")
                            
                            formatted_data = {
                                'symbol': message.get('s', 'UNKNOWN'),  # Symbol
                                'bidPrice': message.get('b', '0.00'),   # Best bid price
                                'bidQty': message.get('B', '0.0000'),   # Best bid qty
                                'askPrice': message.get('a', '0.00'),   # Best ask price
                                'askQty': message.get('A', '0.0000'),   # Best ask qty
                                'timestamp': message.get('E', process_time),  # Event time
                                'serverTimestamp': process_time,
                                'backendLatency': backendLatency
                            }
                            
                            # Log detailed latency info for debugging
                            logger.debug(f"Backend latency: {backendLatency}ms | exchange_time: {message.get('E')}, " +
                                        f"received_time: {message.get('received_timestamp')}, process_time: {process_time}")
                    
                        # Ensure timestamp is never null
                        if formatted_data['timestamp'] is None:
                            formatted_data['timestamp'] = process_time
                        
                        # Update latest data
                        self.latest_data = formatted_data
                        
                        # Apply throttling: Only send if enough time has passed since last message
                        if time_since_last_message >= self.throttle_interval:
                            # Time to send a message - use the current one
                            # Reset the throttle timer
                            self.last_message_time = current_time
                            
                            # Send to all clients
                            logger.debug(f"Broadcasting BBO update to clients")
                            
                            # Use a separate namespace broadcast instead of individual messages
                            self.socketio.emit('bbo_update', formatted_data, namespace='/')
                            
                            # Log detailed data for debugging occasionally
                            if random.random() < 0.01:  # Only log 1% of messages to avoid spam
                                logger.debug(f"Sample bbo_update data: {json.dumps(formatted_data)}")
                            
                            # Clear any throttled message since we just sent one
                            self.throttled_message = None
                        else:
                            # Not enough time has passed, store this message as the latest throttled message
                            self.throttled_message = formatted_data
                            logger.debug(f"Throttling message, time since last: {time_since_last_message}ms")
                        
                    # Mark message as processed
                    self.message_queue.task_done()
                
                # After processing the batch, send the throttled message if it exists
                if self.throttled_message is not None:
                    current_time = current_time_ms()
                    time_since_last_message = current_time - self.last_message_time
                    
                    if time_since_last_message >= self.throttle_interval:
                        # Time to send the throttled message
                        self.last_message_time = current_time
                        
                        # Emit the throttled message
                        logger.debug("Emitting throttled message")
                        self.socketio.emit('bbo_update', self.throttled_message, namespace='/')
                        
                        # Clear the throttled message
                        self.throttled_message = None
                
            except Exception as e:
                logger.error(f"Error processing message batch: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
                # Mark all messages as processed to avoid blocking the queue
                for _ in range(len(messages_to_process)):
                    try:
                        self.message_queue.task_done()
                    except Exception:
                        pass
