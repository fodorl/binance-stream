#!/usr/bin/env python3
"""
Socket.IO event handlers for the Binance BBO stream web server.
"""
import logging
import time
import json

logger = logging.getLogger(__name__)

class SocketHandler:
    """
    Handles Socket.IO events and communication with clients.
    """
    def __init__(self, socketio, client_manager, message_queue_processor):
        """
        Initialize the socket handler
        
        Args:
            socketio (SocketIO): The Flask-SocketIO instance
            client_manager (ClientManager): The client manager instance
            message_queue_processor (MessageQueueProcessor): The message queue processor instance
        """
        self.socketio = socketio
        self.client_manager = client_manager
        self.message_processor = message_queue_processor
        self._configure_events()
        
    def _configure_events(self):
        """Configure all Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            client_id = self._get_client_id()
            logger.info(f"Client connected: {client_id}")
            self.client_manager.add_client(client_id)
            self.on_connect()
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = self._get_client_id()
            logger.info(f"Client disconnected: {client_id}")
            self.client_manager.remove_client(client_id)
            
        @self.socketio.on('ready')
        def handle_ready():
            client_id = self._get_client_id()
            logger.info(f"Client sent ready event: {client_id}")
            self.on_connect()  # Treat ready the same as connect
            
        @self.socketio.on('request_initial_data')
        def handle_request_initial_data():
            self.on_request_initial_data()
    
    def _get_client_id(self):
        """
        Get current client ID if available
        
        Returns:
            str: The client ID or "unknown"
        """
        try:
            from flask_socketio import request
            if hasattr(request, 'sid'):
                return request.sid
        except (ImportError, RuntimeError):
            pass
        return "unknown"
    
    def on_connect(self):
        """
        Handle client connection
        Send welcome message and initial data
        """
        client_id = self._get_client_id()
        logger.info(f"Processing connection for client: {client_id}")
        
        # Send welcome message to confirm connection
        try:
            self.socketio.emit('welcome', {'message': 'Welcome to Binance BBO Stream'}, room=client_id)
            logger.info(f"Welcome message sent to client: {client_id}")
            
            # Poke the connection with another message to ensure stability
            self.socketio.emit('connection_status', {'status': 'connected', 'timestamp': int(time.time() * 1000)}, room=client_id)
        
            # Send the latest data if available
            latest_data = self.message_processor.get_latest_data()
            if latest_data:
                logger.debug(f"Sending latest data to newly connected client: {client_id}")
                self.socketio.emit('bbo_update', latest_data, room=client_id)
                
        except Exception as e:
            logger.error(f"Error in on_connect: {e}")
    
    def on_request_initial_data(self):
        """
        Handle client request for initial data
        Send latest data if available
        """
        client_id = self._get_client_id()
        logger.debug(f"Client {client_id} requested initial data")
        
        try:
            # Send the latest data if available
            latest_data = self.message_processor.get_latest_data()
            if latest_data:
                logger.debug(f"Sending latest data to client {client_id}")
                self.socketio.emit('bbo_update', latest_data, room=client_id)
            else:
                logger.warning(f"No data available to send to client {client_id}")
                self.socketio.emit('status', {'message': 'Waiting for data from Binance...'}, room=client_id)
        except Exception as e:
            logger.error(f"Error in on_request_initial_data: {e}")

    # For backward compatibility with direct message handler functions
    def addListener(self, event, handler):
        """
        Add a listener for an event (alias for 'on' method)
        
        Args:
            event (str): The event name
            handler (function): The handler function
        """
        self.socketio.on(event)(handler)
        
    def on(self, event, handler):
        """
        Add a listener for an event
        
        Args:
            event (str): The event name
            handler (function): The handler function
        """
        self.socketio.on(event)(handler)
