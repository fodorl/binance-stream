#!/usr/bin/env python3
"""
Web server package for the Binance BBO stream application.
Provides a web interface for displaying real-time BBO data.
"""
from .server import WebServer

# For backward compatibility, re-export these to maintain the same API
__all__ = ['WebServer']
