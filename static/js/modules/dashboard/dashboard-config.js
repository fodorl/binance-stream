/**
 * Dashboard configuration module
 * Contains DOM elements references and configuration values for the dashboard
 */

// Create a safe DOM element getter that returns null for missing elements
const safeGetElement = (id) => document.getElementById(id);

// DOM elements used in the dashboard
export const domElements = {
    // Symbol selector elements
    symbolSelect: { value: 'BTCUSDT' }, // Hardcoded since it doesn't exist in index.html
    symbolStatus: document.getElementById('symbol-status') || { textContent: '' },
    
    // Price elements
    bidPriceElement: safeGetElement('bid-price'),
    askPriceElement: safeGetElement('ask-price'),
    bidQtyElement: safeGetElement('bid-qty'),
    askQtyElement: safeGetElement('ask-qty'),
    spreadElement: safeGetElement('spread-value'),
    spreadPercentElement: safeGetElement('spread-percent'),
    
    // Connection status elements
    connectionStatus: safeGetElement('status-text'),
    connectionLight: safeGetElement('status-icon'),
    connectedCount: { textContent: '0' }, // Fallback object
    reconnectButton: { style: {}, addEventListener: () => {} }, // Fallback object
    lastUpdateElement: safeGetElement('last-update-time'),
    
    // Stats elements
    updateCountElement: { textContent: '0' }, // Fallback object
    updateRateElement: { textContent: '0' }, // Fallback object
    latencyElement: safeGetElement('latency-value'),
    
    // Chart elements
    chartContainer: safeGetElement('chart-container'),
    timeframeButtons: document.querySelectorAll('.timespan-btn'),
    
    // Control elements
    exportCSVButton: safeGetElement('export-csv-btn'),
    
    // Mobile toggle
    toggleChartBtn: { addEventListener: () => {} } // Fallback object
};

// Socket configuration
export const socketConfig = {
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    timeout: 20000,
    pingInterval: 25000,  // Socket.IO will ping every 25 seconds
    pingTimeout: 20000    // Wait 20 seconds for ping response
};

// Chart configuration
export const chartConfig = {
    // Default timeframe in minutes
    defaultTimeframe: 5,
    
    // Maximum number of data points to keep in memory
    maxDataPoints: 100,
    
    // Colors
    bidColor: 'rgba(0, 153, 51, 1)',   // Green for bid
    askColor: 'rgba(204, 0, 0, 1)',    // Red for ask
    
    // LocalStorage keys
    storageKeys: {
        timestamps: 'bbo_timestamps',
        bidPrices: 'bbo_bid_prices',
        askPrices: 'bbo_ask_prices',
        lastSaved: 'bbo_last_saved'
    }
};

// Animation configuration
export const animationConfig = {
    duration: 800,
    upClass: 'price-up',
    downClass: 'price-down'
};
