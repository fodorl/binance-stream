# Binance BBO Stream

A robust real-time application that connects to the Binance WebSocket API to stream Best Bid and Offer (BBO) data for cryptocurrency trading pairs. The application features a responsive web interface with real-time price updates and an interactive price history chart.

## Features

- **Real-time BBO Data**: Stream live Best Bid/Offer data directly from Binance
- **Interactive Price Chart**: Visualize price trends over multiple time periods (1m, 5m, 15m, 1h, 12h, 1d)
- **WebSocket Reliability**: Robust connection handling with automatic reconnection
- **Latency Monitoring**: Real-time tracking of data transmission delays
- **Responsive Design**: Mobile-friendly UI that works across devices
- **Secure Communication**: HTTPS support for secure client-server interaction
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Docker Support**: Easy deployment through containerization
- **Historical Data Visualization**: View and analyze historical BBO data
- **Caching System**: Store and retrieve historical BBO updates for efficient access

## Project Architecture

The project follows a modular architecture with clear separation of concerns:

### Backend Components

- **`main.py`**: Application entry point that initializes and orchestrates all components
- **`websocket_client.py`**: Establishes and maintains connection to Binance WebSocket API
- **`message_processor.py`**: Processes incoming WebSocket messages and formats data
- **`utils.py`**: Utility functions for data formatting, timing, and general helpers
- **`config.py`**: Configuration settings and environment variable handling
- **`cache`**: Package for storing and retrieving historical BBO updates
  - **`bbo_cache.py`**: Core caching functionality for BBO updates
  - **`cache_manager.py`**: Manages cache lifecycle and maintenance
  - **`rest_api.py`**: REST API for accessing historical data

#### Web Server Package

The web server functionality has been refactored into a modular package structure:

- **`web/`**: Package directory containing all web server components
  - **`__init__.py`**: Package initialization and exports
  - **`server.py`**: Core web server class that integrates all components
  - **`routes.py`**: HTTP route definitions for serving web pages
  - **`socket_handlers.py`**: Socket.IO event handlers for real-time communication
  - **`message_queue.py`**: Message queue processing for efficient broadcast
  - **`message_processor.py`**: BBO data processing from raw Binance messages
  - **`ssl_utils.py`**: SSL certificate management utilities
  - **`client_manager.py`**: Client connection tracking and management

This modular design provides several benefits:
- Improved maintainability with smaller, focused modules
- Better testability as components can be tested in isolation
- Enhanced readability through clear separation of concerns
- Easier extension with new features without modifying existing code

### Frontend Components

- **`templates/index.html`**: Main UI layout and structure
- **`static/js/app.js`**: Core application logic for the web interface
- **`static/js/modules/`**:
  - **`chart-controller.js`**: Manages the interactive price history chart
  - **`socket-handler.js`**: Handles WebSocket connections and event management
  - **`config.js`**: Frontend configuration settings
  - **`ui-updater.js`**: Manages UI updates and animations
- **`static/css/style.css`**: Custom styling for the web interface

## Technology Stack

The Binance BBO Stream application uses a modern technology stack to deliver real-time data processing and visualization:

### Backend Technologies

#### Core Backend
- **Python 3.9**: The primary programming language for the backend
- **asyncio**: Python's built-in asynchronous I/O framework for handling concurrent operations
- **websockets**: Library for WebSocket client/server communication with the Binance API
- **aiohttp**: Asynchronous HTTP client/server framework for additional API requests
- **numpy**: Scientific computing library used for statistical calculations on price data
- **eventlet**: Concurrent networking library for asynchronous socket operations

#### Web Server
- **Flask**: Lightweight WSGI web application framework serving the frontend UI
- **Flask-SocketIO**: Flask extension for Socket.IO integration providing real-time bidirectional communication
- **python-socketio**: Python implementation of the Socket.IO protocol
- **pyOpenSSL & cryptography**: Libraries for SSL/TLS implementation and certificate management
- **simple-websocket**: WebSocket implementation for Flask-SocketIO

#### Data Storage
- **Custom Caching System**: In-memory data structures with disk persistence for historical data
- **JSON**: Data serialization format for both API responses and cache persistence

#### Containerization & Deployment
- **Docker**: Application containerization for consistent deployment across environments
- **docker-compose**: Multi-container orchestration for development environments

### Frontend Technologies

#### Core Frontend
- **JavaScript (ES6+)**: Modern JavaScript for interactive UI elements
- **HTML5**: Semantic markup language for application structure
- **CSS3**: Styling language with modern features like flexbox and grid layout

#### Libraries & Frameworks
- **Chart.js (v3.9.1 & v4.3.0)**: JavaScript charting library for data visualization
- **chartjs-plugin-zoom (v1.2.1)**: Chart.js plugin enabling interactive zooming and panning
- **Socket.IO Client (v4.5.4)**: Real-time bidirectional event-based communication
- **Bootstrap (v5.3.0)**: CSS framework for responsive UI components
- **Bootstrap Icons (v1.10.0)**: Icon toolkit for visual elements
- **Hammer.js (v2.0.8)**: Touch gesture recognition library for mobile interaction
- **Luxon (v2.3.1)**: DateTime library for handling time-based data
- **date-fns**: JavaScript date utility library for time formatting with Chart.js

#### Data Flow
- **WebSockets**: For real-time data streaming from server to client
- **JSON**: Data interchange format between backend and frontend
- **localStorage**: Browser storage for persisting chart data between sessions

#### Browser APIs
- **DOM API**: For manipulating page elements and handling user interactions
- **Fetch API**: For making HTTP requests to the backend REST endpoints
- **Web Storage API**: For client-side data persistence

This technology stack was selected to provide a balance of performance, maintainability, and developer experience while enabling the real-time data processing capabilities required for cryptocurrency market data visualization.

## Technical Implementation Details

### Socket.IO Connection

The application uses Socket.IO for real-time bidirectional communication between the backend and frontend:

- **Transport Fallback**: Primary transport is WebSocket with automatic fallback to HTTP polling
- **Connection Resilience**: Comprehensive reconnection logic with exponential backoff
- **Stale Connection Detection**: Monitors connection health with heartbeat mechanism
- **Cross-Origin Support**: CORS headers for cross-domain compatibility
- **Standardized Messaging**: Consistent JSON data format across all communications

### Real-time Price History Chart

The price history visualization uses Chart.js to display bid and ask prices over time:

- **Multiple Timeframes**: Support for 1m, 5m, 15m, 1h, 12h, and 1d time periods
- **Dynamic Data Storage**: Maintains up to 1,000,000 data points in memory
- **Responsive Scaling**: Automatically adjusts y-axis to highlight price movements
- **Visual Distinction**: Color-coded lines for bid (green) and ask (red) prices
- **Time-Based Formatting**: Intelligent time axis formatting based on selected timespan
- **Data Persistence**: Optional localStorage saving of recent price data

### WebSocket Data Flow

The data flows through the application as follows:

1. **Binance API** → WebSocket connection established by `websocket_client.py`
2. **WebSocket Messages** → Processed by `message_processor.py`
3. **Processed Data** → Handled by the web package:
   - Processed by `web.message_processor.py`
   - Queued by `web.message_queue.py`
   - Emitted to clients via Socket.IO by `web.socket_handlers.py`
4. **Browser Client** → Receives data through `socket-handler.js`
5. **UI Updates** → Display refreshed by `app.js` and `chart-controller.js`

## WebSocket API Documentation

The application provides a Socket.IO-based WebSocket API that external clients can use to consume real-time BBO data. This allows you to build custom clients that connect to the same data stream as the web interface.

### Connection Details

- **Base URL**: `http://your-server-address:5000`
- **Socket.IO Path**: `/socket.io/`
- **Namespace**: `/` (default namespace)
- **Transport**: WebSocket (preferred) with fallback to HTTP long-polling
- **Protocol**: Socket.IO v4.5.4 or compatible

### Events

#### Server → Client Events

| Event Name | Description | Payload Format |
|------------|-------------|----------------|
| `bbo_update` | Real-time BBO data update | JSON object (see structure below) |
| `welcome` | Sent upon successful connection | `{"message": "Welcome to BBO Stream"}` |
| `pong` | Response to client `ping` event | `{"time": <timestamp>}` |

#### Client → Server Events

| Event Name | Description | Payload |
|------------|-------------|---------|
| `connect` | Automatic event upon connection | None |
| `ready` | Indicate client is ready to receive data | None |
| `request_initial_data` | Request current BBO state | None |
| `ping` | Client-initiated ping (for latency measurement) | None |

### BBO Update Payload Structure

```json
{
  "symbol": "BTCUSDT",          // Trading pair symbol
  "bidPrice": "28750.00",       // Best bid price
  "bidQty": "1.2345",           // Best bid quantity
  "askPrice": "28755.00",       // Best ask price
  "askQty": "0.9876",           // Best ask quantity
  "timestamp": 1677721200000,   // Event timestamp (exchange time)
  "serverTimestamp": 1677721200100, // Server processing timestamp
  "backendLatency": 100         // Latency between exchange and server (ms)
}
```

### Connection Example (JavaScript)

```javascript
// Using Socket.IO v4.5.4 client library
const socket = io('http://your-server-address:5000', {
  path: '/socket.io/',
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  timeout: 20000
});

// Connection events
socket.on('connect', () => {
  console.log('Connected to BBO Stream server');
  socket.emit('ready'); // Indicate that client is ready
});

socket.on('disconnect', () => {
  console.log('Disconnected from BBO Stream server');
});

// Listen for BBO updates
socket.on('bbo_update', (data) => {
  console.log(`${data.symbol}: Bid ${data.bidPrice} (${data.bidQty}) | Ask ${data.askPrice} (${data.askQty})`);
});

// Listen for welcome message
socket.on('welcome', (data) => {
  console.log('Server welcome message:', data.message);
  socket.emit('request_initial_data'); // Request current data
});
```

### Connection Example (Python)

```python
import socketio
import time

# Create Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to BBO Stream server")
    sio.emit('ready')  # Indicate client is ready

@sio.event
def disconnect():
    print("Disconnected from BBO Stream server")

@sio.on('bbo_update')
def on_bbo_update(data):
    print(f"{data['symbol']}: Bid {data['bidPrice']} ({data['bidQty']}) | Ask {data['askPrice']} ({data['askQty']})")

@sio.on('welcome')
def on_welcome(data):
    print(f"Server welcome message: {data['message']}")
    sio.emit('request_initial_data')  # Request current data

# Connect to server
try:
    sio.connect('http://your-server-address:5000', 
                transports=['websocket', 'polling'],
                wait_timeout=20)
    
    # Keep the process running
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Error: {e}")
finally:
    if sio.connected:
        sio.disconnect()
```

## Requirements

- **Python 3.8+**
- **Node.js** (for development only)
- **Modern web browser** with JavaScript enabled
- **Internet connection** for accessing Binance API

## Dependencies

### Backend Dependencies

- **websockets**: WebSocket client for Python
- **flask**: Web framework
- **flask-socketio**: Socket.IO integration for Flask
- **eventlet**: Concurrent networking library
- **requests**: HTTP client
- **cryptography**: Cryptographic recipes and primitives
- **aiohttp**: Asynchronous HTTP client/server
- **dnspython**: DNS toolkit

### Frontend Dependencies

- **Socket.IO Client**: Real-time communication with server
- **Chart.js**: Interactive time-series visualization
- **Bootstrap**: Responsive UI framework
- **date-fns**: Date manipulation utilities for Chart.js

## Installation and Setup

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/binance-bbo-stream.git
cd binance-bbo-stream

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Docker Installation

```bash
# Build and run with Docker Compose (recommended)
docker-compose up -d

# Alternative: Build and run with Docker
docker build -t binance-bbo-stream .
docker run -d -p 5000:5000 --name binance-bbo-stream binance-bbo-stream
```

## SSL Configuration

The application supports HTTPS for secure connections:

1. **Generate SSL Certificates** (for development):
   ```bash
   mkdir -p certs
   openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365
   ```

2. **Set Proper File Permissions**:
   ```bash
   chmod 755 certs
   chmod 644 certs/*.pem
   ```

3. **Configure SSL** through environment variables:
   - `USE_SSL`: Set to "true" to enable HTTPS (default: true)
   - `SSL_CERT_PATH`: Path to certificate file (default: /app/certs/cert.pem)
   - `SSL_KEY_PATH`: Path to key file (default: /app/certs/key.pem)

## Configuration Options

The application can be configured using environment variables:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| `SYMBOL` | Trading pair to stream | `btcusdt` |
| `AUTO_RECONNECT` | Enable auto-reconnection | `true` |
| `MAX_RETRIES` | Maximum reconnection attempts | `10` |
| `INITIAL_BACKOFF` | Initial backoff time in seconds | `1` |
| `EXTENDED_BACKOFF_THRESHOLD` | Threshold for extended backoff | `3` |
| `DEBUG` | Enable debug logging | `false` |
| `WEBSOCKET_BASE_URL` | Base URL for Binance WebSocket | `wss://fstream.binance.com/ws` |
| `LOG_TO_FILE` | Enable logging to file | `false` |
| `LOG_DIR` | Directory for log files | `logs` |
| `WEB_ENABLED` | Enable web interface | `true` |
| `WEB_HOST` | Host for web server | `0.0.0.0` |
| `WEB_PORT` | Port for web server | `5000` |
| `USE_SSL` | Enable HTTPS | `true` |
| `SSL_CERT_PATH` | Path to SSL certificate | `/app/certs/cert.pem` |
| `SSL_KEY_PATH` | Path to SSL key | `/app/certs/key.pem` |
| `CACHE_DIR` | Directory for cache data | `cache_data` |
| `CACHE_ENABLED` | Enable the caching system | `true` |
| `CACHE_MAX_ITEMS` | Maximum number of items per symbol | `1000000` |
| `CACHE_PERSIST` | Whether to persist cache to disk | `true` |
| `CACHE_CLEANUP_HOURS` | Hours between cache cleanup | `6` |

## Example Usage

### Start with Custom Configuration

```bash
# Using environment variables
SYMBOL=ethusdt DEBUG=true LOG_TO_FILE=true python main.py

# Using Docker with environment variables
docker run -d -p 5000:5000 --name binance-bbo-stream \
  -e SYMBOL=ethusdt \
  -e DEBUG=true \
  -e LOG_TO_FILE=true \
  -v $(pwd)/logs:/app/logs \
  binance-bbo-stream
```

## Web Interface

The application includes an interactive web interface accessible at https://localhost:5000 (or http://localhost:5000 if SSL is disabled).

### Key UI Components

1. **Connection Status**: Displays current connection state with the server
2. **Current BBO Display**:
   - Real-time bid and ask prices with quantities
   - Visual spread indicator
   - Color highlighting for price changes

3. **Price History Chart**:
   - Interactive time-series chart showing bid and ask prices
   - Multiple timeframe options (1m, 5m, 15m, 1h, 12h, 1d)
   - Automatic scaling for best visualization
   - Color-coded lines for bid and ask prices

4. **Connection Statistics**:
   - Latency monitoring with color-coded indicators
   - Message count and connection duration
   - Transport method indication (WebSocket/Polling)

5. **Historical Data Visualization**:
   - View historical BBO data for any available symbol
   - Select different time ranges for data visualization
   - View latency statistics for the selected time range
   - Access a table of recent updates

## REST API

The application exposes a REST API for accessing historical data:

### Endpoints

- `/api/history/symbols` - Get a list of available symbols
- `/api/history/updates` - Get historical BBO updates for a symbol and time range
- `/api/history/latency` - Get latency statistics for a symbol and time range
- `/api/history/stats` - Get cache statistics

### Example Usage

```bash
# Get available symbols
curl http://localhost:5000/api/history/symbols

# Get historical updates for BTCUSDT over the last hour
curl http://localhost:5000/api/history/updates?symbol=BTCUSDT&limit=100

# Get latency statistics for ETHUSDT over a specific time range
curl http://localhost:5000/api/history/latency?symbol=ETHUSDT&start_time=1620000000000&end_time=1620100000000
```

## Troubleshooting

### Common Issues

1. **Connection Problems**:
   - Ensure your internet connection is stable
   - Check if Binance API is accessible from your location
   - Verify that no firewall is blocking WebSocket connections

2. **SSL Certificate Issues**:
   - For development, accept the self-signed certificate in your browser
   - For production, use properly signed certificates

3. **Data Not Updating**:
   - Check browser console for JavaScript errors
   - Verify Socket.IO connection in Network tab
   - Ensure backend is receiving data from Binance

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Binance for providing the WebSocket API
- Flask-SocketIO team for the excellent library
- Chart.js contributors for the visualization library

## Running the Application

### Using Python Directly

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python main.py
   ```

3. Access the web interface at:
   - HTTPS: `https://localhost:5000` (default)
   - HTTP: `http://localhost:5000` (if SSL is disabled)

### Using Docker

1. Build the Docker image:
   ```
   docker build -t binance-bbo-stream .
   ```

2. Run the container:
   ```
   docker run -d -p 5000:5000 --name binance-bbo-stream binance-bbo-stream
   ```

3. Access the web interface at:
   - HTTPS: `https://localhost:5000` (default)
   - HTTP: `http://localhost:5000` (if SSL is disabled)

## Development

When extending the application, follow the modular architecture pattern:

1. For web server enhancements, modify the appropriate module in the `web/` package:
   - User interface routes → `web/routes.py`
   - Socket.IO event handling → `web/socket_handlers.py`
   - Message processing → `web/message_processor.py`
   - Client management → `web/client_manager.py`

2. For WebSocket connection changes, modify `websocket_client.py`

3. For global message processing logic, modify `message_processor.py`

4. For configuration changes, update environment variables or `config.py`

5. For caching system changes, modify the `cache` package:
   - `bbo_cache.py`: Core caching functionality for BBO updates
   - `cache_manager.py`: Manages cache lifecycle and maintenance
   - `rest_api.py`: REST API for accessing historical data
