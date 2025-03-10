#!/usr/bin/env python3
"""
Cache manager for orchestrating cache initialization, maintenance, and cleanup.
"""

import logging
import threading
import time
import os
from typing import Optional
import bisect
from .bbo_cache import BBOCache

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Manager for BBOCache lifecycle and maintenance.
    Handles initialization, periodic cleanup, and shutdown of the cache.
    """
    
    def __init__(self, max_items_per_symbol=1000000, persist_to_disk=False, 
                cache_dir="cache_data", cleanup_interval_hours=6):
        """
        Initialize the cache manager.
        
        Args:
            max_items_per_symbol: Maximum number of BBO updates to store per symbol
            persist_to_disk: Whether to persist cache to disk periodically
            cache_dir: Directory for disk-based cache storage
            cleanup_interval_hours: How often to clean up old data (in hours)
        """
        self.cache = BBOCache(
            max_items_per_symbol=max_items_per_symbol,
            persist_to_disk=persist_to_disk,
            cache_dir=cache_dir
        )
        
        self.cleanup_interval_ms = cleanup_interval_hours * 3600 * 1000
        self.running = False
        self.cleanup_thread = None
        
        logger.info(f"CacheManager initialized with cleanup interval: {cleanup_interval_hours} hours")
    
    def start(self) -> None:
        """
        Start the cache manager.
        Initializes the cache and starts the cleanup thread.
        """
        if self.running:
            logger.warning("CacheManager is already running")
            return
        
        logger.info("Starting CacheManager")
        self.running = True
        
        # Load any persisted data
        if self.cache._persist_to_disk:
            self.cache.load_from_disk()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_task,
            daemon=True,
            name="cache-cleanup-thread"
        )
        self.cleanup_thread.start()
        
        logger.info("CacheManager started")
    
    def stop(self) -> None:
        """
        Stop the cache manager.
        Stops the cleanup thread and performs final persistence if enabled.
        """
        if not self.running:
            logger.warning("CacheManager is not running")
            return
        
        logger.info("Stopping CacheManager")
        self.running = False
        
        # Perform final persistence if enabled
        if self.cache._persist_to_disk:
            self.cache._persist_cache()
        
        # Wait for cleanup thread to terminate
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=2.0)
        
        logger.info("CacheManager stopped")
    
    def _cleanup_task(self) -> None:
        """
        Periodic task to clean up old data from the cache.
        """
        logger.info("Cache cleanup thread started")
        
        while self.running:
            try:
                # Sleep for a while (check every minute if we should stop)
                for _ in range(60):
                    if not self.running:
                        break
                    time.sleep(1)
                
                if not self.running:
                    break
                
                # Check if it's time to clean up
                if (self.cache._insert_count % 10000 == 0) or \
                   (time.time() * 1000 - self.cache._last_persistence_time > self.cleanup_interval_ms):
                    
                    # Keep the last 24 hours of data by default
                    self.cache.clear_old_data(max_age_ms=24 * 3600 * 1000)
            
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {str(e)}")
        
        logger.info("Cache cleanup thread terminated")
    
    def process_bbo_update(self, bbo_update) -> None:
        """
        Process a BBO update and add it to the cache.
        This is the main entry point for new data to be cached.
        
        Args:
            bbo_update: Dictionary containing BBO update data
        """
        try:
            # Ensure cache is properly initialized
            if not self.running:
                logger.warning("CacheManager not running, starting it now")
                self.start()
                
            if self.contains_update(bbo_update):
                logger.debug(f"Skipping duplicate update for {bbo_update.get('symbol')} with timestamp {bbo_update.get('timestamp')}")
                return
                
            self.cache.add_update(bbo_update)
        except Exception as e:
            logger.error(f"Error adding update to cache: {str(e)}")
            logger.error(f"Full update data: {bbo_update}")
    
    def contains_update(self, bbo_update) -> bool:
        """
        Check if an update with the same timestamp already exists in the cache.
        
        Args:
            bbo_update: Dictionary containing BBO update data
            
        Returns:
            bool: True if the update already exists, False otherwise
        """
        try:
            if not isinstance(bbo_update, dict):
                return False
                
            symbol = bbo_update.get('symbol')
            timestamp = bbo_update.get('timestamp')
            
            if not symbol or not timestamp:
                return False
                
            # Use binary search to efficiently check if this timestamp exists
            with self.cache._lock:
                if symbol not in self.cache._timestamps:
                    return False
                    
                timestamps = self.cache._timestamps[symbol]
                if not timestamps:
                    return False
                    
                # Use binary search to find the timestamp
                idx = bisect.bisect_left(timestamps, timestamp)
                
                # Check if the timestamp was found
                if idx < len(timestamps) and timestamps[idx] == timestamp:
                    logger.debug(f"Found duplicate update for {symbol} with timestamp {timestamp}")
                    return True
                    
            return False
        except Exception as e:
            logger.error(f"Error checking for duplicate update: {str(e)}")
            return False
    
    def get_cache(self) -> BBOCache:
        """
        Get the BBOCache instance managed by this CacheManager.
        
        Returns:
            BBOCache instance
        """
        return self.cache
