/**
 * Configuration settings for Binance BBO Stream
 * Contains constants and application settings
 */

// DOM element IDs - centralize all DOM element references
export const domElements = {
    // Main containers
    connectionStatus: '.connection-status',
    connectionStatusText: '#status-text',
    statusIcon: '#status-icon',
    
    // Price display
    bidPrice: '#bid-price',
    bidQty: '#bid-qty',
    askPrice: '#ask-price',
    askQty: '#ask-qty',
    spreadValue: '#spread-value',
    spreadPercent: '#spread-percent',
    
    // Stats
    lastUpdateTimestamp: '#last-update-time',
    latencyValue: '#latency-value',
    
    // Chart
    chartContainer: '#chart-container',  
    timespanButtons: '.timespan-btn'
};

// Socket.IO configuration
export const socketConfig = {
    // Base URL derived from current URL if not specified
    baseURL: null,
    
    // Socket.IO path
    path: '/socket.io',
    
    // Get the Socket.IO URL (either specified or derived from window.location)
    getSocketURL: function() {
        if (this.baseURL) {
            return this.baseURL;
        }
        
        // If no base URL is specified, derive it from the current URL
        if (typeof window !== 'undefined') {
            const protocol = window.location.protocol === 'https:' ? 'https:' : 'http:';
            const host = window.location.hostname;
            const port = window.location.port;
            
            return `${protocol}//${host}${port ? `:${port}` : ''}`;
        }
        
        // Default fallback
        return 'http://localhost:5000';
    },
    
    reconnection: true,
    reconnectionAttempts: 20,
    reconnectionDelay: 2000,
    timeout: 30000,
    transports: ['polling', 'websocket'],
    forceNew: true,
    autoConnect: true,
    withCredentials: false,
    upgrade: true,
    secure: true,
    rejectUnauthorized: false  // Important for self-signed certificates
};

// Chart configuration
export const chartConfig = {
    // Max data points to keep in memory
    maxDataPoints: 100,
    
    // Default timespan in minutes
    defaultTimespan: 1,
    
    // Available timespans in minutes
    timespans: [1, 5, 15],
    
    // Colors
    bidColor: 'rgb(40, 167, 69)',    // Green
    askColor: 'rgb(220, 53, 69)',     // Red
    
    // Other settings
    animationDuration: 0,  // Disable animations for better performance
    gridColor: '#f0f0f0',
    textColor: '#333333',
    backgroundColor: '#ffffff',
    borderColor: '#d6d6d6'
};

// Backend API Configuration
export const apiConfig = {
    // Base API URL (if different from Socket.IO URL)
    baseURL: null,
    
    // Get the API URL
    getAPIURL: function() {
        if (this.baseURL) {
            return this.baseURL;
        }
        
        return socketConfig.getSocketURL();
    },
    
    // API endpoints
    endpoints: {
        status: '/api/status',
        config: '/api/config'
    }
};

// Animation settings
export const animationConfig = {
    flashDuration: 1000 // Duration in ms for price change animations
};

// Connection check intervals (in milliseconds)
export const intervals = {
    connectionCheck: 5000,
    serverPing: 20000,
    staleThreshold: 10000 // Time after which connection is considered stale
};
