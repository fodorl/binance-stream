#!/usr/bin/env python3
"""
Test script for the BBOCache functionality.
"""

import os
import time
import json
import random
import logging
from datetime import datetime, timedelta

from cache import BBOCache, CacheManager
from utils import current_time_ms

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_sample_bbo_updates(symbol, count=100):
    """
    Generate sample BBO updates for testing.
    
    Args:
        symbol: Trading pair symbol
        count: Number of updates to generate
        
    Returns:
        List of sample BBO updates
    """
    base_price = 50000.0 if symbol == 'BTCUSDT' else 2000.0
    updates = []
    
    for i in range(count):
        # Create a timestamp within the last hour
        timestamp = current_time_ms() - random.randint(0, 3600000)
        
        # Generate a random price movement
        price_movement = random.uniform(-50, 50)
        bid_price = base_price + price_movement
        ask_price = bid_price + random.uniform(0.1, 1.0)
        
        # Create the update
        update = {
            'symbol': symbol,
            'timestamp': timestamp,
            'bidPrice': str(round(bid_price, 2)),
            'bidQty': str(round(random.uniform(0.1, 2.0), 8)),
            'askPrice': str(round(ask_price, 2)),
            'askQty': str(round(random.uniform(0.1, 2.0), 8)),
            'backendLatency': random.randint(50, 200)
        }
        
        updates.append(update)
    
    # Sort by timestamp
    updates.sort(key=lambda x: x['timestamp'])
    return updates

def test_cache_basic():
    """Test basic cache functionality."""
    logger.info("Testing basic cache functionality...")
    
    # Create cache directory if it doesn't exist
    os.makedirs("test_cache", exist_ok=True)
    
    # Initialize the cache
    cache = BBOCache(
        max_items_per_symbol=1000,
        persist_to_disk=True,
        cache_dir="test_cache"
    )
    
    # Generate sample updates for two symbols
    btc_updates = generate_sample_bbo_updates("BTCUSDT", 100)
    eth_updates = generate_sample_bbo_updates("ETHUSDT", 100)
    
    # Add updates to the cache
    for update in btc_updates:
        cache.add_update(update)
    
    for update in eth_updates:
        cache.add_update(update)
    
    # Get symbol list
    symbols = cache.get_symbol_list()
    logger.info(f"Symbols in cache: {symbols}")
    
    # Get updates for BTCUSDT
    retrieved_updates = cache.get_updates("BTCUSDT")
    logger.info(f"Retrieved {len(retrieved_updates)} updates for BTCUSDT")
    
    # Get latency stats for ETHUSDT
    latency_stats = cache.get_latency_stats("ETHUSDT")
    logger.info(f"Latency stats for ETHUSDT: {latency_stats}")
    
    # Get cache stats
    cache_stats = cache.get_cache_stats()
    logger.info(f"Cache stats: {json.dumps(cache_stats, indent=2)}")
    
    # Persist cache to disk
    cache._persist_cache()
    logger.info("Cache persisted to disk")
    
    # Create a new cache and load from disk
    new_cache = BBOCache(
        max_items_per_symbol=1000,
        persist_to_disk=True,
        cache_dir="test_cache"
    )
    new_cache.load_from_disk()
    
    # Verify data was loaded
    new_symbols = new_cache.get_symbol_list()
    logger.info(f"Symbols in loaded cache: {new_symbols}")
    
    new_updates = new_cache.get_updates("BTCUSDT")
    logger.info(f"Retrieved {len(new_updates)} updates for BTCUSDT from loaded cache")
    
    # Clean up
    os.system("rm -rf test_cache")
    logger.info("Test completed and cleanup done")

def test_cache_manager():
    """Test the cache manager functionality."""
    logger.info("Testing cache manager functionality...")
    
    # Create a cache manager
    manager = CacheManager(
        max_items_per_symbol=1000,
        persist_to_disk=True,
        cache_dir="test_cache",
        cleanup_interval_hours=0.01  # Set to 36 seconds for testing
    )
    
    # Start the manager
    manager.start()
    
    # Add some updates
    for _ in range(100):
        update = generate_sample_bbo_updates("BTCUSDT", 1)[0]
        manager.process_bbo_update(update)
    
    # Wait for a bit to let the cache manager process updates
    logger.info("Waiting for cache manager to process updates...")
    time.sleep(5)
    
    # Get the cache and check its contents
    cache = manager.get_cache()
    
    symbols = cache.get_symbol_list()
    logger.info(f"Symbols in cache: {symbols}")
    
    updates = cache.get_updates("BTCUSDT")
    logger.info(f"Retrieved {len(updates)} updates for BTCUSDT")
    
    # Wait for cleanup to happen
    logger.info("Waiting for cleanup to happen...")
    time.sleep(40)
    
    # Stop the manager
    manager.stop()
    
    # Clean up
    os.system("rm -rf test_cache")
    logger.info("Test completed and cleanup done")

if __name__ == "__main__":
    logger.info("Starting BBOCache tests...")
    
    test_cache_basic()
    test_cache_manager()
    
    logger.info("All tests completed successfully!")
