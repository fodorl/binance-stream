#!/usr/bin/env python3
"""
Client connection manager for the Binance BBO stream web server.
Handles tracking connected clients and their status.
"""
import logging
import threading

logger = logging.getLogger(__name__)

class ClientManager:
    """
    Manages connected Socket.IO clients and their state.
    Provides thread-safe access to the client list.
    """
    def __init__(self):
        """Initialize the client manager"""
        self.connected_clients = set()  # Track connected clients
        self.client_lock = threading.Lock()  # Lock for thread safety
        
    def add_client(self, client_id):
        """
        Add a client to the connected clients set
        
        Args:
            client_id (str): The client ID to add
            
        Returns:
            int: Number of connected clients after adding
        """
        with self.client_lock:
            self.connected_clients.add(client_id)
            client_count = len(self.connected_clients)
            logger.info(f"Client connected: {client_id}, total clients: {client_count}")
            return client_count
            
    def remove_client(self, client_id):
        """
        Remove a client from the connected clients set
        
        Args:
            client_id (str): The client ID to remove
            
        Returns:
            int: Number of connected clients after removal
        """
        with self.client_lock:
            if client_id in self.connected_clients:
                self.connected_clients.remove(client_id)
            client_count = len(self.connected_clients)
            logger.info(f"Client disconnected: {client_id}, remaining clients: {client_count}")
            return client_count
            
    def get_client_list(self):
        """
        Get a copy of the current client list
        
        Returns:
            list: List of connected client IDs
        """
        with self.client_lock:
            return list(self.connected_clients)
            
    def get_client_count(self):
        """
        Get the current number of connected clients
        
        Returns:
            int: Number of connected clients
        """
        with self.client_lock:
            return len(self.connected_clients)
            
    def is_client_connected(self, client_id):
        """
        Check if a specific client is connected
        
        Args:
            client_id (str): The client ID to check
            
        Returns:
            bool: True if the client is connected, False otherwise
        """
        with self.client_lock:
            return client_id in self.connected_clients
