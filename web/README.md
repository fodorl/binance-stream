# Web Server Package

This package contains the web server components for the Binance BBO Stream application. It provides a web interface for displaying real-time BBO data from the Binance WebSocket API.

## Package Structure

The web server has been refactored into a modular structure with separation of concerns:

- **__init__.py**: Package initialization and exports.
- **server.py**: Core web server class that integrates all components.
- **routes.py**: HTTP route definitions for serving pages.
- **socket_handlers.py**: Socket.IO event handlers for real-time communication.
- **message_queue.py**: Message queue processing for efficient broadcast.
- **message_processor.py**: BBO data processing from raw Binance messages.
- **ssl_utils.py**: SSL certificate management utilities.
- **client_manager.py**: Client connection tracking and management.

## Key Components

### WebServer

The main entry point that initializes and coordinates all other components. It handles:
- Flask application setup
- Socket.IO initialization
- SSL configuration
- Component lifecycle management

### ClientManager

Manages connected Socket.IO clients and provides thread-safe access to the client list.

### MessageQueueProcessor

Processes queued messages and broadcasts them to clients. Features include:
- Message throttling to prevent overwhelming clients
- Batch processing for efficiency
- Special handling for pre-formatted messages

### BBOProcessor

Processes raw Binance WebSocket messages and prepares them for delivery to clients.

### RouteHandler

Defines HTTP routes for serving web pages and static assets.

### SocketHandler

Handles Socket.IO events and manages real-time communication with clients.

## Configuration

The web server can be configured via environment variables:

- `WEB_HOST`: The host to bind to (default: "0.0.0.0")
- `WEB_PORT`: The port to bind to (default: 5000)
- `USE_SSL`: Whether to use SSL/HTTPS (default: true)
- `SSL_CERT_PATH`: Path to SSL certificate (default: "certs/cert.pem")
- `SSL_KEY_PATH`: Path to SSL key (default: "certs/key.pem")
- `DEBUG`: Enable debug mode (default: false)

## Usage

Import and use the `WebServer` class:

```python
from web import WebServer

# Create and start the web server
web_server = WebServer(host="0.0.0.0", port=5000, debug=False)
web_server.start()

# Process a BBO update
web_server.process_bbo_update(message)

# Stop the web server
web_server.stop()
```
