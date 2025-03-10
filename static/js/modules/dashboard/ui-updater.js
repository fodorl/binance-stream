/**
 * UI Updater module
 * Handles DOM manipulation and UI updates
 */
import { domElements, animationConfig } from './config.js';

class UIUpdater {
    constructor() {
        // Price tracking for animations
        this.prevBidPrice = null;
        this.prevAskPrice = null;
        
        // Cache DOM elements
        this.elements = {};
        this._cacheDOMElements();
    }
    
    /**
     * Cache DOM elements for better performance
     */
    _cacheDOMElements() {
        // For all single ID elements
        Object.keys(domElements).forEach(key => {
            const selector = domElements[key];
            if (selector && !selector.startsWith('.')) {
                this.elements[key] = document.getElementById(selector);
            }
        });
    }
    
    /**
     * Update BBO data display on the page
     * @param {Object} data - BBO data from server
     */
    updateBBO(data) {
        if (!data) {
            console.error('No data received in updateBBO');
            return null;
        }
        
        console.log('Processing BBO update:', data);
        
        // Calculate UI latency (client time - server receive time)
        const serverTime = data.timestamp ? parseInt(data.timestamp) : Date.now();
        const serverReceiveTime = data.serverTimestamp ? parseInt(data.serverTimestamp) : Date.now();
        const clientTime = Date.now();
        
        // UI latency is the time between server sending message and client processing it
        const uiLatency = clientTime - serverReceiveTime;
        
        // Backend latency is the time between Binance sending message and our server receiving it
        let backendLatency = null;
        if (data.backendLatency !== null && data.backendLatency !== undefined) {
            // Ensure we're working with a number
            backendLatency = parseInt(data.backendLatency, 10) || null;
        }
        
        // Log latency data infrequently to avoid console spam
        if (Math.random() < 0.01) { // Log only 1% of messages
            console.log('Calculated latencies:', {
                serverTime,
                serverReceiveTime,
                clientTime,
                uiLatency,
                backendLatency,
                rawBackendLatency: data.backendLatency
            });
        }
        
        // Total latency (Binance to browser)
        const totalLatency = backendLatency !== null ? backendLatency + uiLatency : null;
        
        // Update BBO display
        const bidPrice = parseFloat(data.bidPrice).toFixed(2);
        const askPrice = parseFloat(data.askPrice).toFixed(2);
        const bidQty = parseFloat(data.bidQty).toFixed(4);
        const askQty = parseFloat(data.askQty).toFixed(4);
        
        // Highlight changes
        if (this.prevBidPrice !== null && bidPrice !== this.prevBidPrice) {
            this.flashElement('#bid-price', bidPrice > this.prevBidPrice ? 'flash-green' : 'flash-red');
        }
        
        if (this.prevAskPrice !== null && askPrice !== this.prevAskPrice) {
            this.flashElement('#ask-price', askPrice > this.prevAskPrice ? 'flash-green' : 'flash-red');
        }
        
        // Update the UI elements
        this._updateElement('symbol', data.symbol || 'UNKNOWN');
        this._updateElement('bidPrice', bidPrice);
        this._updateElement('bidQty', bidQty);
        this._updateElement('askPrice', askPrice);
        this._updateElement('askQty', askQty);
        
        // Update spread
        const spread = (parseFloat(askPrice) - parseFloat(bidPrice)).toFixed(2);
        this._updateElement('spread', spread);
        
        // Update timestamps
        const updateTime = new Date().toLocaleTimeString();
        this._updateElement('lastUpdate', updateTime);
        this._updateElement('exchangeTime', new Date(serverTime).toLocaleTimeString());
        
        // Format backend latency display with color coding
        let backendLatencyText = backendLatency !== null ? `Backend: ${backendLatency} ms` : 'Backend: N/A';
        let backendLatencyClass = '';
        
        if (backendLatency === null) {
            backendLatencyClass = 'text-secondary'; // Gray for unknown latency
        } else if (backendLatency < 100) {
            backendLatencyClass = 'text-success'; // Green for good latency
        } else if (backendLatency < 500) {
            backendLatencyClass = 'text-warning'; // Yellow for moderate latency
        } else {
            backendLatencyClass = 'text-danger'; // Red for high latency
        }
        
        // Format UI latency display with color coding
        let uiLatencyText = `UI: ${uiLatency} ms`;
        let uiLatencyClass = '';
        
        if (uiLatency < 100) {
            uiLatencyClass = 'text-success'; // Green for good latency
        } else if (uiLatency < 300) {
            uiLatencyClass = 'text-warning'; // Yellow for moderate latency
        } else {
            uiLatencyClass = 'text-danger'; // Red for high latency
        }
        
        // Update latency displays
        if (this.elements.backendLatency) {
            this.elements.backendLatency.textContent = backendLatencyText;
            this.elements.backendLatency.className = ''; // Remove badge and background class
            this.elements.backendLatency.classList.add(backendLatencyClass);
        }
        
        if (this.elements.uiLatency) {
            this.elements.uiLatency.textContent = uiLatencyText;
            this.elements.uiLatency.className = ''; // Remove badge and background class
            this.elements.uiLatency.classList.add(uiLatencyClass);
        }
        
        // Store for next comparison
        this.prevBidPrice = bidPrice;
        this.prevAskPrice = askPrice;
        
        // For chart update - ensure we return the original raw price values, not the formatted ones
        return {
            serverTime,
            bidPrice: parseFloat(data.bidPrice),
            askPrice: parseFloat(data.askPrice)
        };
    }

    /**
     * Update connection status display
     * @param {string} status - Connection status
     */
    updateConnectionStatus(status) {
        const element = this.elements.connectionStatus;
        
        if (!element) {
            console.error('connection-status element not found');
            return;
        }
        
        // Remove existing classes
        element.classList.remove('text-success', 'text-danger', 'text-warning');
        
        // Set status text and class
        switch (status) {
            case 'connected':
                element.textContent = 'Connected';
                element.classList.add('text-success');
                break;
            case 'disconnected':
                element.textContent = 'Disconnected';
                element.classList.add('text-danger');
                break;
            case 'reconnecting':
                element.textContent = 'Reconnecting...';
                element.classList.add('text-warning');
                break;
            case 'connecting':
                element.textContent = 'Connecting...';
                element.classList.add('text-warning');
                break;
            case 'stale':
                element.textContent = 'Connection stale - no updates';
                element.classList.add('text-warning');
                break;
            case 'error':
                element.textContent = 'Connection error';
                element.classList.add('text-danger');
                break;
            default:
                element.textContent = status;
                element.classList.add('text-warning');
        }
    }

    /**
     * Flash an element for price change animation
     * @param {string} selector - Element selector
     * @param {string} className - Class to add temporarily
     */
    flashElement(selector, className) {
        const element = document.querySelector(selector);
        if (!element) return;
        
        element.classList.add(className);
        setTimeout(() => {
            element.classList.remove(className);
        }, animationConfig.flashDuration);
    }

    /**
     * Helper to update element text if the element exists
     * @param {string} elementKey - Key of the element in elements cache
     * @param {string} value - New text value
     */
    _updateElement(elementKey, value) {
        if (this.elements[elementKey]) {
            this.elements[elementKey].textContent = value;
        }
    }
}

// Create and export a singleton instance
const uiUpdater = new UIUpdater();
export default uiUpdater;
