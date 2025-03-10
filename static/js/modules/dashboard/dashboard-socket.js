/**
 * Socket.IO connection handler for the dashboard
 * Manages the WebSocket connection and events
 */
import { socketConfig } from './dashboard-config.js';

class DashboardSocket {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.lastUpdateTime = Date.now();
        this.listeners = {};
        this.pendingSymbol = null; // Store pending symbol change
        
        // Namespace information for debugging
        this.namespace = '/';
    }
    
    /**
     * Initialize the socket connection
     */
    initialize() {
        if (this.socket) {
            console.log('Socket already initialized, reconnecting...');
            this.socket.connect();
            return;
        }
        
        // Notify that we're connecting
        this.notifyListeners('connectionStatus', 'connecting');
        
        // Initialize socket with configuration
        this.socket = io(this.namespace, {
            reconnectionAttempts: socketConfig.reconnectionAttempts,
            reconnectionDelay: socketConfig.reconnectionDelay,
            reconnectionDelayMax: socketConfig.reconnectionDelayMax,
            timeout: socketConfig.timeout,
            pingInterval: socketConfig.pingInterval,
            pingTimeout: socketConfig.pingTimeout
        });
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Set up socket event listeners
     */
    setupEventListeners() {
        // Connection events
        this.socket.on('connect', () => {
            console.log('Socket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.notifyListeners('connectionStatus', 'connected');
            
            // Process any pending symbol change
            if (this.pendingSymbol) {
                console.log(`Processing pending symbol change to ${this.pendingSymbol}`);
                this.changeSymbol(this.pendingSymbol);
                this.pendingSymbol = null;
            }
        });
        
        this.socket.on('disconnect', (reason) => {
            console.log(`Socket disconnected: ${reason}`);
            this.isConnected = false;
            this.notifyListeners('connectionStatus', 'disconnected', { reason });
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Socket connection error:', error);
            this.notifyListeners('connectionStatus', 'error', { error: error.message });
        });
        
        this.socket.on('connecting', () => {
            console.log('Socket connecting');
            this.notifyListeners('connectionStatus', 'connecting');
        });
        
        this.socket.on('reconnect_attempt', (attemptNumber) => {
            console.log(`Reconnect attempt ${attemptNumber}`);
            this.reconnectAttempts = attemptNumber;
            this.notifyListeners('connectionStatus', 'reconnecting', { attempt: attemptNumber });
        });
        
        // BBO Update event
        this.socket.on('bbo_update', (data) => {
            // Update last update time
            this.lastUpdateTime = Date.now();
            
            // Notify listeners with event name that matches what's in app.js
            this.notifyListeners('bbo_update', data);
        });
        
        // Stats event
        this.socket.on('stats', (data) => {
            this.notifyListeners('stats', data);
        });
    }
    
    /**
     * Add event listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    addListener(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }
    
    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} callback - Callback function
     */
    removeListener(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }
    
    /**
     * Notify all listeners for an event
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    notifyListeners(event, ...args) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(...args));
        }
    }
    
    /**
     * Reconnect the socket
     */
    reconnect() {
        if (this.socket) {
            // Disconnect if connected
            if (this.socket.connected) {
                this.socket.disconnect();
            }
            
            // Reconnect
            this.socket.connect();
        } else {
            // Initialize if socket doesn't exist
            this.initialize();
        }
    }
    
    /**
     * Get time since last update
     * @returns {number} Milliseconds since last update
     */
    getTimeSinceLastUpdate() {
        return Date.now() - this.lastUpdateTime;
    }
    
    /**
     * Change symbol subscription
     * @param {string} symbol - Symbol to subscribe to
     */
    changeSymbol(symbol) {
        if (this.isConnected) {
            console.log(`Changing symbol to ${symbol}`);
            this.socket.emit('change_symbol', { symbol });
        } else {
            console.log('Socket not connected, queueing symbol change for when connected');
            this.pendingSymbol = symbol; // Store for when we connect
        }
    }
}

// Create and export singleton instance
const dashboardSocket = new DashboardSocket();
export default dashboardSocket;
