#!/usr/bin/env python3
"""
Message processing module for the Binance BBO stream application.
"""
import logging
import json
import random
import asyncio
from utils import current_time_ms, format_price, format_quantity, calculate_spread

logger = logging.getLogger(__name__)

class MessageProcessor:
    def __init__(self, symbol, web_server=None, cache_manager=None):
        self.symbol = symbol.upper()
        self.web_server = web_server
        self.cache_manager = cache_manager
        # Create an async queue for processed messages
        self.processed_message_queue = asyncio.Queue()
        # Flag to control the dispatch loop
        self.is_running = True
        # Start the dispatch task
        self.dispatch_task = None
        
        if self.cache_manager:
            logger.info(f"MessageProcessor initialized with cache_manager")
        else:
            logger.warning(f"MessageProcessor initialized WITHOUT cache_manager")
    
    async def start(self):
        """Start the message dispatch task"""
        self.is_running = True
        self.dispatch_task = asyncio.create_task(self._dispatch_messages())
        logger.info("Message dispatch task started")
        
    async def stop(self):
        """Stop the message dispatch task"""
        self.is_running = False
        if self.dispatch_task:
            self.dispatch_task.cancel()
            try:
                await self.dispatch_task
            except asyncio.CancelledError:
                pass
            self.dispatch_task = None
        logger.info("Message dispatch task stopped")
    
    async def process_message(self, message):
        """Process a message from the WebSocket"""
        received_timestamp = current_time_ms()
        
        try:
            # First, parse the message
            data = json.loads(message)
            
            # Track whether this has already been processed
            processed = False
            
            # Binance stream sometimes returns data in the form {"stream":"","data":{}}
            if "data" in data and isinstance(data["data"], dict):
                data = data["data"]
            
            # Detect known Binance BBO stream format: has "u" (update ID), "s" (symbol), "b" (bid), "a" (ask)
            if all(k in data for k in ["s", "b", "a"]):
                logger.debug(f"Processing Binance BBO update format")
                # Call our new method to handle BBO updates
                await self._process_bbo_update(data, received_timestamp)
                processed = True
            
            # Handle 24hr ticker format
            elif all(k in data for k in ["e", "s", "p", "P"]) and data["e"] == "24hrTicker":
                # Format the 24hr ticker data for the web UI
                symbol = data["s"]
                price_change = float(data["p"])
                price_change_percent = float(data["P"])
                last_price = float(data["c"])
                volume = float(data["v"])
                
                # Determine if price went up or down
                is_positive = price_change >= 0
                
                # Create a formatted version for the UI
                formatted_data = {
                    "symbol": symbol,
                    "priceChange": price_change,
                    "priceChangePercent": price_change_percent,
                    "lastPrice": last_price,
                    "volume": volume,
                    "isPositive": is_positive,
                    "exchange_time": data.get("E", current_time_ms()),
                    "received_timestamp": received_timestamp,
                    "latency": latency
                }
                
                # Add to processed message queue instead of direct forwarding
                await self.processed_message_queue.put(formatted_data)
                processed = True
                
                # Log with moderate frequency to avoid overwhelming logs
                # but still provide visibility into the message flow
                if random.random() < 0.01:  # Log approximately 1% of messages
                    logger.debug(f"Processed {symbol} BBO: bid={best_bid:.2f}, ask={best_ask:.2f}, " +
                                f"latency={latency:.2f}ms")
            
            if not processed:
                # Extract and format the BBO data
                if "b" in data and "a" in data:
                    await self._handle_bbo_data(data, received_timestamp)
            
            if random.random() < 0.01:  # Log approximately 1% of messages
                logger.info(f"Received: {message}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _handle_bbo_data(self, data, received_timestamp):
        """Handle BBO (Best Bid and Offer) data"""
        bid_price = float(data["b"])
        bid_qty = float(data["B"])
        ask_price = float(data["a"])
        ask_qty = float(data["A"])
        
        # Calculate latency if timestamp is available
        exchange_time = None
        latency_ms = None
        if "E" in data:  # Binance includes event time in field "E" (milliseconds)
            exchange_time = int(data["E"])
            calculated_latency = received_timestamp - exchange_time
            
            # Only use reasonable latency values (less than 10 seconds)
            if calculated_latency < 10000:  # 10 seconds max
                latency_ms = calculated_latency
                latency_info = f" | Latency: {latency_ms:.2f}ms"
            else:
                latency_info = f" | Latency: too high ({calculated_latency:.2f}ms, showing as N/A)"
            
            # Add detailed logging for latency calculation
            if random.random() < 0.01:  # Log approximately 1% of messages
                logger.info(f"Latency calculation: exchange_time={exchange_time}, received_timestamp={received_timestamp}, calculated_latency={calculated_latency}, used_latency={latency_ms}")
        else:
            exchange_time = int(received_timestamp)
            latency_info = " | No exchange timestamp"
            
        if random.random() < 0.01:  # Log approximately 1% of messages
            logger.info(
                f"BBO: {self.symbol} - "
                f"Bid: {format_price(bid_price)} ({format_quantity(bid_qty)}) | "
                f"Ask: {format_price(ask_price)} ({format_quantity(ask_qty)}) | "
                f"Spread: {calculate_spread(bid_price, ask_price)}{latency_info}"
            )
        
        # Create formatted data for the queue
        web_data = {
            "symbol": self.symbol,
            "bid_price": bid_price,
            "bid_qty": bid_qty,
            "ask_price": ask_price,
            "ask_qty": ask_qty,
            "spread": ask_price - bid_price,
            "latency": latency_ms,  # Can be None
            "exchange_time": exchange_time,
            "received_timestamp": received_timestamp  # Add the timestamp when we received the message
        }
        
        # Add to the processed message queue
        await self.processed_message_queue.put(web_data)

    async def _process_bbo_update(self, data, received_timestamp):
        """Process a BBO update message"""
        # Extract the timestamp (E field) from the message
        exchange_time = data.get('E')
        
        # Set the receive timestamp for calculating latency
        data['received_timestamp'] = received_timestamp
        
        # Calculate latency
        if exchange_time:
            latency = received_timestamp - exchange_time
            data['latency'] = latency
            
            # Only log a small percentage of messages to avoid flooding logs
            if random.random() < 0.01:  # Log ~1% of messages
                logger.debug(f"Backend latency: {latency}ms | exchange_time: {exchange_time}, received_time: {received_timestamp}")
        
        # Process message into a standardized format
        formatted_data = {
            'symbol': data.get('s', self.symbol),        # Symbol
            'bid_price': data.get('b', 0),               # Best bid price
            'bid_qty': data.get('B', 0),                 # Best bid qty
            'ask_price': data.get('a', 0),               # Best ask price
            'ask_qty': data.get('A', 0),                 # Best ask qty
            'exchange_time': exchange_time,              # Event time
            'received_timestamp': received_timestamp,    # Time received by our system
            'latency': data.get('latency')               # Calculated latency
        }
        
        # Also add camelCase versions for compatibility with cache system
        formatted_data['bidPrice'] = formatted_data['bid_price']
        formatted_data['bidQty'] = formatted_data['bid_qty']
        formatted_data['askPrice'] = formatted_data['ask_price']
        formatted_data['askQty'] = formatted_data['ask_qty']
        formatted_data['timestamp'] = exchange_time or received_timestamp
        
        # Add to cache if cache_manager is available
        if self.cache_manager:
            try:
                logger.debug(f"MessageProcessor sending {formatted_data['symbol']} update to cache with timestamp {exchange_time}")
                self.cache_manager.process_bbo_update(formatted_data)
            except Exception as e:
                logger.error(f"MessageProcessor error adding update to cache: {str(e)}")
        
        # Add message to the queue asynchronously for dispatching
        await self.processed_message_queue.put(formatted_data)
        
        # Return the processed data
        return formatted_data

    async def _dispatch_messages(self):
        """Dispatch processed messages to subscribers"""
        logger.info("Starting message dispatch task")
        
        while self.is_running:
            try:
                # Get a message from the queue (with timeout to allow for stopping)
                try:
                    # Wait for a message with timeout
                    message = await asyncio.wait_for(self.processed_message_queue.get(), timeout=1.0)
                    
                    # Forward to web server if available
                    if self.web_server:
                        self.web_server.broadcast_message(message)
                    
                    # Mark task as done
                    self.processed_message_queue.task_done()
                    
                    # Log queue size occasionally
                    queue_size = self.processed_message_queue.qsize()
                    if queue_size > 10 and random.random() < 0.1:
                        logger.warning(f"Processed message queue is growing: size={queue_size}")
                        
                except asyncio.TimeoutError:
                    # No message available, continue loop
                    continue
                    
            except Exception as e:
                logger.error(f"Error in message dispatch task: {e}")
