#!/usr/bin/env python3
"""
BBOCache: A component for caching historical BBO updates and latency data.
This module provides in-memory storage with optional persistence for BBO updates.
"""

import logging
import time
import json
import os
import threading
import bisect
from collections import defaultdict, deque
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

from utils import current_time_ms

logger = logging.getLogger(__name__)

class BBOCache:
    """
    Cache for storing historical BBO updates and latency data.
    Provides methods to store and retrieve historical BBO data with time-based filtering.
    """
    
    def __init__(self, max_items_per_symbol: int = 1000000, persist_to_disk: bool = False,
                 cache_dir: str = "cache_data"):
        """
        Initialize the BBO cache.
        
        Args:
            max_items_per_symbol: Maximum number of BBO updates to store per symbol (default: 1,000,000)
            persist_to_disk: Whether to persist cache to disk periodically (default: False)
            cache_dir: Directory for disk-based cache storage (default: "cache_data")
        """
        self._updates = defaultdict(deque)  # Symbol -> deque of updates
        self._timestamps = defaultdict(list)  # Symbol -> list of timestamps (for binary search)
        self._latency_stats = defaultdict(list)  # Symbol -> list of latency values
        self._max_items = max_items_per_symbol
        self._persist_to_disk = persist_to_disk
        self._cache_dir = cache_dir
        self._lock = threading.RLock()
        
        # Create cache directory if it doesn't exist and persistence is enabled
        if self._persist_to_disk and not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir, exist_ok=True)
        
        # Cache metadata
        self._insert_count = 0
        self._last_persistence_time = 0
        self._persistence_interval = 300000  # 5 minutes in ms
        
        logger.info(f"BBOCache initialized with max_items_per_symbol={max_items_per_symbol}, "
                  f"persist_to_disk={persist_to_disk}")
    
    def add_update(self, bbo_update: Dict) -> None:
        """
        Add a new BBO update to the cache.
        
        Args:
            bbo_update: Dictionary containing BBO update data
                Must include: 'symbol', 'timestamp', 'bidPrice', 'bidQty', 'askPrice', 'askQty'
                May include: 'serverTimestamp', 'backendLatency'
        """
        if not isinstance(bbo_update, dict):
            logger.warning(f"Invalid BBO update format (not a dict): {type(bbo_update)}")
            return
            
        if 'symbol' not in bbo_update:
            logger.warning(f"Invalid BBO update format (missing symbol): {bbo_update}")
            return
        
        symbol = bbo_update['symbol']
        
        # Check for timestamp field or alternatives
        if 'timestamp' not in bbo_update:
            logger.info(f"No 'timestamp' field in update, looking for alternatives")
            
            # Try exchange_time field first
            if 'exchange_time' in bbo_update:
                bbo_update['timestamp'] = bbo_update['exchange_time']
            # Then try received_timestamp
            elif 'received_timestamp' in bbo_update:
                bbo_update['timestamp'] = int(bbo_update['received_timestamp'])
            # Default to current time
            else:
                bbo_update['timestamp'] = current_time_ms()
        
        timestamp = bbo_update['timestamp']
        
        # Handle field name inconsistencies - convert snake_case to camelCase if needed
        field_mappings = {
            'bid_price': 'bidPrice',
            'bid_qty': 'bidQty',
            'ask_price': 'askPrice',
            'ask_qty': 'askQty'
        }
        
        # Convert any snake_case fields to camelCase
        for snake_case, camel_case in field_mappings.items():
            if snake_case in bbo_update and camel_case not in bbo_update:
                bbo_update[camel_case] = bbo_update[snake_case]
        
        # Check for required fields after field name conversion
        required_fields = ['bidPrice', 'bidQty', 'askPrice', 'askQty']
        missing_fields = [field for field in required_fields if field not in bbo_update]
        if missing_fields:
            logger.warning(f"Missing required fields in BBO update: {missing_fields}")
            return  # Skip this update if still missing required fields
        
        # Store latency data if available
        if 'backendLatency' in bbo_update:
            latency = bbo_update['backendLatency']
            with self._lock:
                self._latency_stats[symbol].append((timestamp, latency))
                # Trim latency stats if they grow too large
                if len(self._latency_stats[symbol]) > self._max_items:
                    self._latency_stats[symbol].pop(0)
        elif 'latency' in bbo_update and bbo_update['latency'] is not None:
            # Try alternative field name
            latency = bbo_update['latency']
            with self._lock:
                self._latency_stats[symbol].append((timestamp, latency))
                # Trim latency stats if they grow too large
                if len(self._latency_stats[symbol]) > self._max_items:
                    self._latency_stats[symbol].pop(0)
        
        # Store the BBO update
        with self._lock:
            # Find the insertion point to maintain sorted order
            self._insert_update(symbol, timestamp, bbo_update)
            
            # Increment the insert counter
            self._insert_count += 1
            
            # Periodically persist cache to disk if enabled
            if (self._persist_to_disk and 
                current_time_ms() - self._last_persistence_time > self._persistence_interval):
                self._persist_cache()
    
    def _insert_update(self, symbol: str, timestamp: int, bbo_update: Dict) -> None:
        """
        Insert a BBO update into the cache, maintaining timestamp order.
        
        Args:
            symbol: Trading pair symbol
            timestamp: Update timestamp
            bbo_update: Dictionary containing BBO update data
        """
        # Ensure the symbol exists in the maps
        if symbol not in self._updates:
            logger.info(f"Creating new entry for symbol: {symbol}")
            self._updates[symbol] = deque()
            self._timestamps[symbol] = []
        
        # If we've reached the max items, remove the oldest
        if len(self._updates[symbol]) >= self._max_items:
            self._updates[symbol].popleft()
            self._timestamps[symbol].pop(0)
        
        # Add new item to the end (most updates will be in sequence)
        if not self._timestamps[symbol] or timestamp >= self._timestamps[symbol][-1]:
            self._updates[symbol].append(bbo_update)
            self._timestamps[symbol].append(timestamp)
        else:
            # Find the correct position using binary search
            idx = bisect.bisect_left(self._timestamps[symbol], timestamp)
            # Convert deque to list, insert, and convert back to deque
            data_list = list(self._updates[symbol])
            data_list.insert(idx, bbo_update)
            self._updates[symbol] = deque(data_list)
            self._timestamps[symbol].insert(idx, timestamp)
    
    def get_updates(self, symbol: str, start_time: Optional[int] = None, 
                   end_time: Optional[int] = None, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve BBO updates for a given symbol and time range.
        
        Args:
            symbol: Trading pair symbol
            start_time: Start timestamp in ms (default: None - no lower bound)
            end_time: End timestamp in ms (default: None - no upper bound)
            limit: Maximum number of updates to return (default: None - no limit)
            
        Returns:
            List of BBO updates matching the criteria
        """
        with self._lock:
            if symbol not in self._updates:
                return []
            
            # If no time range specified, return the most recent 'limit' items
            if start_time is None and end_time is None:
                if limit is None:
                    return list(self._updates[symbol])
                return list(self._updates[symbol])[-limit:]
            
            # Use binary search to find the start and end indices
            start_idx = 0
            end_idx = len(self._timestamps[symbol])
            
            if start_time is not None:
                start_idx = bisect.bisect_left(self._timestamps[symbol], start_time)
            
            if end_time is not None:
                end_idx = bisect.bisect_right(self._timestamps[symbol], end_time)
            
            # Convert to list for slicing
            result = list(self._updates[symbol])[start_idx:end_idx]
            
            # Apply limit if specified
            if limit is not None and len(result) > limit:
                result = result[-limit:]
            
            return result
    
    def get_latency_stats(self, symbol: str, start_time: Optional[int] = None,
                         end_time: Optional[int] = None) -> Dict:
        """
        Calculate latency statistics for a given symbol and time range.
        
        Args:
            symbol: Trading pair symbol
            start_time: Start timestamp in ms (default: None - no lower bound)
            end_time: End timestamp in ms (default: None - no upper bound)
            
        Returns:
            Dictionary with latency statistics:
                - avg: Average latency
                - min: Minimum latency
                - max: Maximum latency
                - p50: 50th percentile (median) latency
                - p95: 95th percentile latency
                - p99: 99th percentile latency
                - count: Number of samples
        """
        with self._lock:
            if symbol not in self._latency_stats:
                return {
                    "avg": 0, "min": 0, "max": 0,
                    "p50": 0, "p95": 0, "p99": 0, "count": 0
                }
            
            # Filter latency samples by time range
            latency_samples = []
            for ts, latency in self._latency_stats[symbol]:
                if (start_time is None or ts >= start_time) and (end_time is None or ts <= end_time):
                    latency_samples.append(latency)
            
            if not latency_samples:
                return {
                    "avg": 0, "min": 0, "max": 0,
                    "p50": 0, "p95": 0, "p99": 0, "count": 0
                }
            
            # Calculate statistics
            avg_latency = sum(latency_samples) / len(latency_samples)
            min_latency = min(latency_samples)
            max_latency = max(latency_samples)
            
            # Calculate percentiles
            p50 = np.percentile(latency_samples, 50)
            p95 = np.percentile(latency_samples, 95)
            p99 = np.percentile(latency_samples, 99)
            
            return {
                "avg": avg_latency,
                "min": min_latency,
                "max": max_latency,
                "p50": p50,
                "p95": p95,
                "p99": p99,
                "count": len(latency_samples)
            }
    
    def get_symbol_list(self) -> List[str]:
        """
        Get a list of all symbols in the cache.
        
        Returns:
            List of symbols
        """
        with self._lock:
            return sorted(list(self._updates.keys()))
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        with self._lock:
            stats = {
                "total_symbols": len(self._updates),
                "total_updates": sum(len(updates) for updates in self._updates.values()),
                "updates_per_symbol": {
                    symbol: len(updates) for symbol, updates in self._updates.items()
                },
                "latency_stats_count": {
                    symbol: len(latencies) for symbol, latencies in self._latency_stats.items()
                },
                "cache_size_limit": self._max_items,
                "persist_to_disk": self._persist_to_disk,
                "cache_dir": self._cache_dir
            }
            return stats
    
    def _persist_cache(self) -> None:
        """
        Persist the cache to disk if enabled.
        """
        if not self._persist_to_disk:
            return
        
        try:
            # Get current timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save each symbol's data to a separate file
            for symbol in self._updates.keys():
                # Get the most recent data (last 10,000 items to avoid huge files)
                recent_data = list(self._updates[symbol])[-10000:]
                if not recent_data:
                    continue
                
                filename = f"{self._cache_dir}/{symbol}_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(recent_data, f)
            
            # Update the persistence timestamp
            self._last_persistence_time = current_time_ms()
            logger.info(f"Cache persisted to disk at {timestamp}")
        
        except Exception as e:
            logger.error(f"Error persisting cache to disk: {str(e)}")
    
    def clear_old_data(self, max_age_ms: int = 86400000) -> None:
        """
        Clear data older than the specified age.
        
        Args:
            max_age_ms: Maximum age of data to keep, in milliseconds (default: 24 hours)
        """
        cutoff_time = current_time_ms() - max_age_ms
        
        with self._lock:
            for symbol in list(self._updates.keys()):
                if not self._timestamps[symbol]:
                    continue
                
                # Find the index of the first item to keep
                idx = bisect.bisect_left(self._timestamps[symbol], cutoff_time)
                
                if idx > 0:
                    # Remove all items before the cutoff
                    self._updates[symbol] = deque(list(self._updates[symbol])[idx:])
                    self._timestamps[symbol] = self._timestamps[symbol][idx:]
                    
                    # Also clean up latency stats
                    if symbol in self._latency_stats:
                        self._latency_stats[symbol] = [(ts, lat) for ts, lat in self._latency_stats[symbol] if ts >= cutoff_time]
            
            logger.info(f"Cleared data older than {timedelta(milliseconds=max_age_ms)}")
    
    def load_from_disk(self, symbol: Optional[str] = None) -> None:
        """
        Load cached data from disk if available.
        
        Args:
            symbol: Specific symbol to load (default: None - load all available)
        """
        if not self._persist_to_disk or not os.path.exists(self._cache_dir):
            return
        
        try:
            # List cache files
            files = os.listdir(self._cache_dir)
            
            # Filter by symbol if specified
            if symbol:
                files = [f for f in files if f.startswith(f"{symbol}_")]
            
            if not files:
                logger.info(f"No cache files found for {'all symbols' if symbol is None else symbol}")
                return
            
            # Sort files by timestamp (newest first)
            files.sort(reverse=True)
            
            # Process each symbol
            processed_symbols = set()
            for file in files:
                try:
                    # Extract symbol from filename (format: SYMBOL_TIMESTAMP.json)
                    parts = file.split('_')
                    if len(parts) < 2:
                        continue
                    
                    current_symbol = parts[0]
                    
                    # Skip if we've already processed this symbol
                    if current_symbol in processed_symbols:
                        continue
                    
                    # Load the file
                    with open(f"{self._cache_dir}/{file}", 'r') as f:
                        data = json.load(f)
                    
                    # Add to cache
                    with self._lock:
                        for update in data:
                            if isinstance(update, dict) and 'symbol' in update and 'timestamp' in update:
                                self.add_update(update)
                    
                    processed_symbols.add(current_symbol)
                    logger.info(f"Loaded cache for {current_symbol} from {file}")
                
                except Exception as e:
                    logger.error(f"Error loading cache file {file}: {str(e)}")
            
            logger.info(f"Loaded cache from disk for {len(processed_symbols)} symbols")
        
        except Exception as e:
            logger.error(f"Error loading cache from disk: {str(e)}")
