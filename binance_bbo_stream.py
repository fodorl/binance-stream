#!/usr/bin/env python3
import json
import logging
import asyncio
import websockets
import time
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BinanceBBOStream:
    def __init__(self, symbol="btcusdt", auto_reconnect=True, max_retries=10):
        self.symbol = symbol.lower()
        self.auto_reconnect = auto_reconnect
        self.max_retries = max_retries
        self.websocket = None
        self.retry_count = 0
        self.backoff_time = 1  # Start with 1 second backoff

    async def connect(self):
        """Connect to Binance WebSocket and subscribe to bookTicker stream"""
        url = f"wss://fstream.binance.com/ws/{self.symbol}@bookTicker"
        logger.info(f"Connecting to {url}")
        
        try:
            self.websocket = await websockets.connect(url)
            logger.info(f"Successfully connected to Binance WebSocket for {self.symbol}")
            self.retry_count = 0
            self.backoff_time = 1
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            return False

    async def handle_messages(self):
        """Process incoming WebSocket messages"""
        while True:
            try:
                if not self.websocket:
                    success = await self.connect()
                    if not success:
                        await self.handle_reconnection()
                        continue

                message = await self.websocket.recv()
                await self.process_message(message)
                
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
                if self.auto_reconnect:
                    await self.handle_reconnection()
                else:
                    break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                if self.auto_reconnect:
                    await self.handle_reconnection()
                else:
                    break

    async def handle_reconnection(self):
        """Handle reconnection with exponential backoff"""
        if self.retry_count >= self.max_retries:
            logger.error(f"Maximum retry attempts ({self.max_retries}) reached. Stopping.")
            return False

        self.retry_count += 1
        
        # Check if error might be related to rate limiting
        if self.retry_count > 3:
            # Apply extended backoff for potential rate limit issues
            backoff = max(30, self.backoff_time * 2)
        else:
            # Regular exponential backoff
            backoff = self.backoff_time * 2
        
        self.backoff_time = backoff
        logger.warning(f"Attempting to reconnect in {backoff} seconds (attempt {self.retry_count}/{self.max_retries})")
        await asyncio.sleep(backoff)
        
        # Close existing websocket if it exists
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None
            
        return await self.connect()

    async def process_message(self, message):
        """Process and log WebSocket message"""
        try:
            data = json.loads(message)
            received_timestamp = time.time() * 1000  # Current time in milliseconds
            
            logger.info(f"Received: {message}")
            
            # Extract and format the BBO data
            if "b" in data and "a" in data:
                bid_price = float(data["b"])
                bid_qty = float(data["B"])
                ask_price = float(data["a"])
                ask_qty = float(data["A"])
                
                # Calculate latency if timestamp is available
                latency_ms = None
                if "E" in data:  # Binance includes event time in field "E" (milliseconds)
                    exchange_timestamp = int(data["E"])
                    latency_ms = received_timestamp - exchange_timestamp
                    
                logger.info(
                    f"BBO: {self.symbol.upper()} - "
                    f"Bid: {bid_price:.2f} ({bid_qty:.5f}) | "
                    f"Ask: {ask_price:.2f} ({ask_qty:.5f}) | "
                    f"Spread: {(ask_price - bid_price):.2f}" +
                    (f" | Latency: {latency_ms:.2f}ms" if latency_ms is not None else "")
                )
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message: {message}")
        except Exception as e:
            logger.error(f"Error processing message data: {e}")

    async def run(self):
        """Run the BBO stream"""
        try:
            success = await self.connect()
            if not success:
                logger.error("Failed to establish initial connection")
                return
                
            await self.handle_messages()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        finally:
            if self.websocket:
                await self.websocket.close()
            logger.info("WebSocket connection closed")

async def main():
    bbo_stream = BinanceBBOStream(symbol="btcusdt")
    await bbo_stream.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user. Exiting...")
