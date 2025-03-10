#!/usr/bin/env python3
"""
Utility functions for the Binance BBO stream application.
"""
import time
import json
import logging

logger = logging.getLogger(__name__)

def current_time_ms():
    """Get current time in milliseconds"""
    return time.time() * 1000

def parse_json_message(message):
    """Parse a JSON message and handle any errors"""
    try:
        return json.loads(message)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse message: {message}")
        return None
    except Exception as e:
        logger.error(f"Error processing message data: {e}")
        return None

def format_price(price, decimal_places=2):
    """Format price with specified decimal places"""
    return f"{float(price):.{decimal_places}f}"

def format_quantity(qty, decimal_places=5):
    """Format quantity with specified decimal places"""
    return f"{float(qty):.{decimal_places}f}"

def calculate_spread(bid_price, ask_price, decimal_places=2):
    """Calculate and format the price spread"""
    return f"{(float(ask_price) - float(bid_price)):.{decimal_places}f}"
