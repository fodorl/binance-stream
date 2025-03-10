#!/usr/bin/env python3
"""
HTTP route definitions for the Binance BBO stream web server.
"""
import logging
import time
from flask import render_template, make_response, Response, jsonify, send_from_directory
import os

logger = logging.getLogger(__name__)

class RouteHandler:
    """
    Handles HTTP routes for the web server.
    Serves HTML pages and other static resources.
    """
    def __init__(self, app):
        """
        Initialize the route handler
        
        Args:
            app (Flask): The Flask application instance
        """
        self.app = app
        self._configure_routes()
        
    def _configure_routes(self):
        """Configure all HTTP routes"""
        @self.app.route("/")
        def index():
            return self.index()
            
        @self.app.route("/api/docs")
        def api_docs():
            return self.api_docs()
            
        @self.app.route("/history")
        def history():
            """
            Render the BBO history visualization page.
            """
            return render_template('history.html')
            
        @self.app.route("/favicon.ico")
        def favicon():
            """
            Serve the favicon.ico file
            """
            return send_from_directory(os.path.join(self.app.root_path, '../static'),
                                      'favicon.ico', mimetype='image/vnd.microsoft.icon')
            
        @self.app.route("/api/ping")
        def ping():
            """Simple API endpoint to check if the server is running."""
            return jsonify({
                "status": "ok",
                "timestamp": time.time(),
                "message": "pong"
            })
            
    def index(self):
        """
        Serve the index page
        
        Returns:
            str: Rendered HTML template
        """
        return render_template('index.html')
    
    def api_docs(self):
        """
        Serve the API documentation page
        
        Returns:
            str: Rendered HTML template or error response
        """
        try:
            return render_template('api_docs.html')
        except Exception as e:
            logger.error(f"Error rendering API docs: {str(e)}")
            return str(e), 500
