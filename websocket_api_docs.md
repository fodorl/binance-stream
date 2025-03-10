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
| `status` | status event | None |
| `connection_status` | connection_status event | None |
| `pong` | Response to client ping event | `{"time": <timestamp>}` |
| `bbo_update` | Real-time BBO data update | JSON object (see structure below) |
| `welcome` | Sent upon successful connection | `{"message": "Welcome to BBO Stream"}` |

#### Client → Server Events

| Event Name | Description | Payload |
|------------|-------------|---------|
| `request_initial_data` | Request current BBO state | None |
| `disconnect` | Connection closed event | None |
| `ready` | Indicate client is ready to receive data | None |
| `ping` | Client-initiated ping (for latency measurement) | None |
| `connect` | Automatic event upon connection | None |

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