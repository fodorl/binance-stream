#!/usr/bin/env python3
"""
REST API handlers for accessing historical BBO data from the cache.
"""

import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, Response

from .bbo_cache import BBOCache
from utils import current_time_ms

logger = logging.getLogger(__name__)

class BBOHistoryAPI:
    """
    Flask Blueprint for BBO history API endpoints.
    Provides REST API access to the cached BBO data.
    """
    
    def __init__(self, cache: BBOCache):
        """
        Initialize the BBO History API.
        
        Args:
            cache: BBOCache instance to use for data retrieval
        """
        self.cache = cache
        self.blueprint = Blueprint('bbo_history', __name__)
        
        # Register routes
        self.blueprint.route('/api/history/symbols', methods=['GET'])(self.get_symbols)
        self.blueprint.route('/api/history/updates', methods=['GET'])(self.get_updates)
        self.blueprint.route('/api/history/latency', methods=['GET'])(self.get_latency_stats)
        self.blueprint.route('/api/history/stats', methods=['GET'])(self.get_cache_stats)
        
        logger.info("BBO History API initialized")
    
    def get_symbols(self) -> Response:
        """
        Get a list of all symbols in the cache.
        
        Returns:
            JSON response with list of symbols
        """
        try:
            logger.info("API request: /api/history/symbols")
            symbols = self.cache.get_symbol_list()
            logger.info(f"Retrieved {len(symbols)} symbols: {symbols}")
            return jsonify({
                "status": "success",
                "data": {
                    "symbols": symbols,
                    "count": len(symbols)
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving symbols: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": f"Failed to retrieve symbols: {str(e)}"
            }), 500
    
    def get_updates(self) -> Response:
        """
        Get BBO updates for a given symbol and time range.
        
        Query parameters:
            symbol (required): Trading pair symbol
            start_time: Start timestamp in ms (default: 1 hour ago)
            end_time: End timestamp in ms (default: current time)
            limit: Maximum number of updates to return (default: 10000000)
            
        Returns:
            JSON response with BBO updates
        """
        try:
            logger.info("API request: /api/history/updates")
            # Parse parameters
            symbol = request.args.get('symbol')
            if not symbol:
                return jsonify({
                    "status": "error",
                    "message": "Symbol is required"
                }), 400
            
            # Parse timestamps
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            limit = request.args.get('limit')
            
            if start_time:
                start_time = int(start_time)
            else:
                # Default to 1 hour ago
                start_time = current_time_ms() - 3600000
            
            if end_time:
                end_time = int(end_time)
                
            if limit:
                limit = int(limit)
            else:
                limit = 10000000  # Effectively unlimited
            
            logger.info(f"Request parameters: symbol={symbol}, start_time={start_time}, end_time={end_time}, limit={limit}")
            # Get data from cache
            updates = self.cache.get_updates(symbol, start_time, end_time, limit)
            logger.info(f"Retrieved {len(updates)} updates for symbol {symbol}")
            
            # Format timestamps for readability
            for update in updates:
                if 'timestamp' in update:
                    update['timestamp_formatted'] = datetime.fromtimestamp(
                        update['timestamp'] / 1000
                    ).strftime('%Y%m%d %H:%M:%S.%f')[:-3]
            
            return jsonify({
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "start_time": start_time,
                    "end_time": end_time,
                    "count": len(updates),
                    "updates": updates
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving updates: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": f"Failed to retrieve updates: {str(e)}"
            }), 500
    
    def get_latency_stats(self) -> Response:
        """
        Get latency statistics for a given symbol and time range.
        
        Query parameters:
            symbol (required): Trading pair symbol
            start_time: Start timestamp in ms (default: 1 hour ago)
            end_time: End timestamp in ms (default: current time)
            
        Returns:
            JSON response with latency statistics
        """
        try:
            logger.info("API request: /api/history/latency")
            # Parse parameters
            symbol = request.args.get('symbol')
            if not symbol:
                return jsonify({
                    "status": "error",
                    "message": "Symbol is required"
                }), 400
            
            # Parse timestamps
            start_time = request.args.get('start_time')
            end_time = request.args.get('end_time')
            
            if start_time:
                start_time = int(start_time)
            else:
                # Default to 1 hour ago
                start_time = current_time_ms() - 3600000
            
            if end_time:
                end_time = int(end_time)
            
            logger.info(f"Request parameters: symbol={symbol}, start_time={start_time}, end_time={end_time}")
            # Get latency stats from cache
            stats = self.cache.get_latency_stats(symbol, start_time, end_time)
            logger.info(f"Retrieved latency stats for symbol {symbol}")
            
            return jsonify({
                "status": "success",
                "data": {
                    "symbol": symbol,
                    "start_time": start_time,
                    "end_time": end_time,
                    "stats": stats
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving latency stats: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": f"Failed to retrieve latency stats: {str(e)}"
            }), 500
    
    def get_cache_stats(self) -> Response:
        """
        Get cache statistics.
        
        Returns:
            JSON response with cache statistics
        """
        try:
            logger.info("API request: /api/history/stats")
            stats = self.cache.get_cache_stats()
            logger.info(f"Retrieved cache stats: {stats}")
            
            return jsonify({
                "status": "success",
                "data": stats
            })
        except Exception as e:
            logger.error(f"Error retrieving cache stats: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                "status": "error",
                "message": f"Failed to retrieve cache stats: {str(e)}"
            }), 500
