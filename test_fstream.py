#!/usr/bin/env python3
"""
Test script to check Binance Futures stream message format
"""
import asyncio
import json
import logging
import time
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def connect_to_binance_fstream():
    """Connect to Binance Futures WebSocket and check message structure"""
    symbol = "btcusdt"
    url = f"wss://fstream.binance.com/ws/{symbol}@bookTicker"
    
    logger.info(f"Connecting to {url}...")
    
    async with websockets.connect(url) as ws:
        logger.info("Connection established")
        
        # Record 5 messages
        for i in range(1, 6):
            message = await ws.recv()
            data = json.loads(message)
            
            logger.info(f"Message {i} structure:")
            logger.info(f"Message keys: {list(data.keys())}")
            
            # Print each field and its data type
            for key, value in data.items():
                logger.info(f"  {key}: {value} (type: {type(value).__name__})")
            
            logger.info("-" * 40)
            
            # Brief pause
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(connect_to_binance_fstream())
