#!/usr/bin/env python3
"""
Configuration module for the Binance BBO stream application.
"""
import logging
import sys
import os
from datetime import datetime

# Default settings with environment variable support
DEFAULT_SYMBOL = os.environ.get("SYMBOL", "btcusdt")
# New setting to support multiple symbols
DEFAULT_SYMBOLS = os.environ.get("SYMBOLS", "btcusdt,ethusdt,bnbusdt,xrpusdt").lower().split(',')
DEFAULT_AUTO_RECONNECT = os.environ.get("AUTO_RECONNECT", "true").lower() == "true"
DEFAULT_MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "10"))
# Use Binance Futures WebSocket by default (fstream.binance.com instead of stream.binance.com)
WEBSOCKET_BASE_URL = os.environ.get("WEBSOCKET_BASE_URL", "wss://fstream.binance.com/ws")

# Connection timeout settings
CONNECTION_TIMEOUT = int(os.environ.get("CONNECTION_TIMEOUT", "30"))  # seconds
DNS_TIMEOUT = int(os.environ.get("DNS_TIMEOUT", "5"))  # seconds

# Reconnection settings
INITIAL_BACKOFF = float(os.environ.get("INITIAL_BACKOFF", "1"))  # seconds
EXTENDED_BACKOFF_THRESHOLD = int(os.environ.get("EXTENDED_BACKOFF_THRESHOLD", "3"))  # attempts

# Logging settings
LOG_TO_FILE = os.environ.get("LOG_TO_FILE", "").lower() == "true"
LOG_DIR = os.environ.get("LOG_DIR", "logs")

# Configure logging
def setup_logging(level=None):
    """Set up logging configuration"""
    if level is None:
        level = logging.DEBUG if os.environ.get("DEBUG", "").lower() == "true" else logging.INFO
    
    # Create handlers list
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if enabled
    if LOG_TO_FILE:
        # Create logs directory if it doesn't exist
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = DEFAULT_SYMBOL.upper()
        log_file = f"{LOG_DIR}/binance_bbo_{symbol}_{timestamp}.log"
        
        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handlers.append(file_handler)
        
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    # Set Flask-SocketIO related loggers to DEBUG level
    logging.getLogger('engineio').setLevel(logging.DEBUG)
    logging.getLogger('socketio').setLevel(logging.DEBUG)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask debug logs
    
    logger = logging.getLogger(__name__)
    if LOG_TO_FILE:
        logger.info(f"Logging to file: {log_file}")
        
    return logger
