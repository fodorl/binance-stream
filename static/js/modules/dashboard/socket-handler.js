/**
 * Socket.IO connection handler
 * Manages the WebSocket connection and events
 */
import { socketConfig, intervals } from './config.js';

class SocketHandler {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.lastUpdateTime = Date.now();
        this.lastPong = Date.now();
        this.listeners = {};
        
        // Namespace information for debugging
        this.namespace = '/';
        this.initialize();
    }

    /**
     * Initialize the Socket.IO connection
     */
    initialize() {
        console.log('Initializing Socket.IO connection...');

        // Get the hostname - handle both cases with and without ports
        const host = window.location.hostname;
        // Determine the port - use current port if available, or default to 5000
        const port = window.location.port || '5000';
        
        // Create the connection URL dynamically based on current page location
        let socketUrl = window.location.protocol + '//' + host;
        
        // If we're using a non-standard port, append it to the URL
        if ((window.location.protocol === 'https:' && port !== '443') || 
            (window.location.protocol === 'http:' && port !== '80')) {
            socketUrl += ':' + port;
        }
        
        // Log Socket.IO configuration for debugging
        const debugConfig = {...socketConfig};
        console.log(`Connecting to Socket.IO at: ${socketUrl} with options:`, debugConfig);
        
        try {
            // Create a single socket instance with fallback capability
            this.socket = io(socketUrl, {
                ...socketConfig,
                reconnection: true,
                reconnectionAttempts: 10,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                randomizationFactor: 0.5,
                timeout: 20000,
                autoConnect: true,
                // First try websocket, then fallback to polling if needed
                transports: ['websocket', 'polling']
            });
            
            // Set up internal event listeners
            this._setupEventListeners();
            
            // Start periodic checks
            this._startPeriodicChecks();
        } catch (error) {
            console.error('Error initializing Socket.IO connection:', error);
        }
        
        return this;
    }

    /**
     * Set up Socket.IO event listeners
     */
    _setupEventListeners() {
        if (!this.socket) {
            console.error('Cannot setup event listeners: socket is null');
            return;
        }
    
        // Connection events
        this.socket.on('connect', () => {
            console.log('Socket.IO connected!');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.lastPong = Date.now();
            
            // Log the transport being used
            const transport = this.socket.io.engine.transport.name;
            console.log(`Socket.IO connected using transport: ${transport}`);
            
            // Display transport info
            this._trigger('connectionStatus', 'connected', { transport });
            
            // Let the server know we're ready
            this.socket.emit('ready');
            
            // Request initial data
            this.socket.emit('request_initial_data');
            
            // Listen for transport upgrade
            this.socket.io.engine.on('upgrade', () => {
                const newTransport = this.socket.io.engine.transport.name;
                console.log(`Socket.IO transport upgraded to: ${newTransport}`);
                this._trigger('connectionStatus', 'connected', { transport: newTransport });
            });
        });
        
        // Welcome message from the server
        this.socket.on('welcome', (data) => {
            console.log('Received welcome message from server:', data);
            // Forward welcome messages to listeners
            this._trigger('welcome', data);
        });
        
        // BBO updates
        this.socket.on('bbo_update', (data) => {
            console.log('Received BBO update:', data);
            
            // Update last update time
            this.lastUpdateTime = Date.now();
            
            // Forward to listeners
            this._trigger('bbo_update', data);
        });
        
        // Generic status messages
        this.socket.on('status', (data) => {
            console.log('Received status from server:', data);
            this._trigger('serverStatus', data);
        });
        
        // Error events
        this.socket.on('connect_error', (error) => {
            console.error('Socket.IO connect error:', error);
            this.isConnected = false;
            this._trigger('connectionStatus', 'error');
            
            // Increment reconnection attempts
            this.reconnectAttempts++;
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket.IO error:', error);
            this._trigger('connectionStatus', 'error');
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log('Socket.IO disconnected, reason:', reason);
            this.isConnected = false;
            this._trigger('connectionStatus', 'disconnected');
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`Socket.IO reconnected after ${attemptNumber} attempts`);
            this.isConnected = true;
            this._trigger('connectionStatus', 'connected');
        });
        
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Socket.IO reconnect attempt #${attemptNumber}`);
            this._trigger('connectionStatus', 'connecting');
        });
        
        this.socket.on('reconnect_error', (error) => {
            console.error('Socket.IO reconnect error:', error);
            this._trigger('connectionStatus', 'error');
        });
        
        this.socket.on('reconnect_failed', () => {
            console.error('Socket.IO reconnect failed after all attempts');
            this._trigger('connectionStatus', 'failed');
        });
        
        // Debug - log all events
        const originalOnevent = this.socket.onevent;
        this.socket.onevent = (packet) => {
            const args = packet.data || [];
            console.log('Socket.IO received event:', args[0]);
            
            // Use the original handler
            originalOnevent.call(this.socket, packet);
        };
    }
    
    /**
     * Start periodic connection checks
     */
    _startPeriodicChecks() {
        // Check for stale connection (no messages for a while)
        setInterval(() => {
            const now = Date.now();
            const timeSinceLastUpdate = now - this.lastUpdateTime;
            
            // If it's been more than 30 seconds since the last update, the connection might be stale
            if (this.isConnected && timeSinceLastUpdate > 30000) {
                console.warn(`No updates received for ${timeSinceLastUpdate/1000} seconds, connection may be stale`);
                this._trigger('connectionStatus', 'stale');
                
                // Try to reconnect
                this.socket.disconnect().connect();
            }
        }, intervals.connectionCheck);
    }

    /**
     * Perform a manual reconnection
     */
    reconnect() {
        console.log('Manually reconnecting Socket.IO...');
        if (this.socket) {
            // First disconnect if already connected
            this.socket.disconnect();
            
            // Wait a moment then reconnect
            setTimeout(() => {
                this.socket.connect();
            }, 1000);
        } else {
            // If socket doesn't exist, reinitialize
            this.initialize();
        }
        
        return this;
    }

    /**
     * Check connection health
     */
    checkConnection() {
        // Only check if we believe we're connected
        if (this.isConnected) {
            // Time since last pong
            const now = Date.now();
            const timeSinceLastPong = now - this.lastPong;
            
            // If it's been too long since we got a pong, reconnect
            if (timeSinceLastPong > 30000) {  // 30 seconds
                console.warn(`Stale connection detected (${timeSinceLastPong}ms since last pong). Reconnecting...`);
                this.reconnect();
            }
        }
        
        return this;
    }

    /**
     * Terminate all connections and clean up
     */
    destroy() {
        console.log('Destroying socket connections...');
        
        // Clear checking interval
        if (this.periodicChecksInterval) {
            clearInterval(this.periodicChecksInterval);
            this.periodicChecksInterval = null;
        }
        
        // Disconnect the sockets
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.isConnected = false;
        this.listeners = {};
        
        return this;
    }

    /**
     * Register an event listener
     * @param {string} event - Event name
     * @param {function} callback - Callback function
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
        return this;
    }
    
    /**
     * Alias of 'on' method for compatibility with existing code
     * @param {string} event - Event name
     * @param {function} callback - Callback function
     */
    addListener(event, callback) {
        return this.on(event, callback);
    }

    /**
     * Trigger an event on all registered listeners
     * @param {string} event - Event name
     * @param {any} data - Event data
     */
    _trigger(event, data, extraData) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data, extraData);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }
}

// Export a singleton instance
const socketHandler = new SocketHandler();
export default socketHandler;
