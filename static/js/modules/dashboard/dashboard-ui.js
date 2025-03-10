/**
 * Dashboard UI Updater module
 * Handles DOM manipulation and UI updates for the dashboard
 */
import { domElements, animationConfig } from './dashboard-config.js';

class DashboardUI {
    constructor() {
        // Price tracking for animations
        this.prevBidPrice = null;
        this.prevAskPrice = null;
        
        // Update counters
        this.updateCount = 0;
        this.updateRateInterval = null;
        this.updateCountInLastSecond = 0;
        this.lastUpdateTime = null;
        
        // Initialize update rate counter
        this.startUpdateRateCounter();
    }
    
    /**
     * Start the update rate counter
     */
    startUpdateRateCounter() {
        setInterval(() => {
            // Update the update rate display if element exists
            if (domElements.updateRateElement) {
                domElements.updateRateElement.textContent = this.updateCountInLastSecond.toString();
            }
            
            // Reset counter
            this.updateCountInLastSecond = 0;
        }, 1000);
    }
    
    /**
     * Update connection status UI based on detailed status
     * @param {string} status - 'connected', 'disconnected', 'connecting', 'reconnecting', or 'error'
     * @param {Object} extraData - Extra data about connection
     */
    updateConnectionStatus(status, extraData = {}) {
        const isConnected = status === 'connected';
        const isConnecting = status === 'connecting' || status === 'reconnecting';
        
        // Update connection badge
        if (domElements.connectionLight) {
            // Remove all status classes
            domElements.connectionLight.classList.remove('connected', 'disconnected');
            
            // Set appropriate class
            if (isConnected) {
                domElements.connectionLight.classList.add('connected');
                domElements.connectionLight.setAttribute('title', 'Connected');
            } else if (isConnecting) {
                // Default amber state (base class has amber color)
                domElements.connectionLight.setAttribute('title', 'Connecting...');
            } else {
                domElements.connectionLight.classList.add('disconnected');
                domElements.connectionLight.setAttribute('title', 'Disconnected');
            }
        }
        
        // Update connection status text
        if (domElements.connectionStatus) {
            if (isConnected) {
                domElements.connectionStatus.textContent = 'Connected';
            } else if (isConnecting) {
                domElements.connectionStatus.textContent = status === 'reconnecting' 
                    ? `Reconnecting (${extraData.attempt || 1})` 
                    : 'Connecting...';
            } else {
                domElements.connectionStatus.textContent = 'Disconnected';
            }
        }
        
        // Update connected count if provided
        if (extraData.connectedClients && domElements.connectedCount) {
            domElements.connectedCount.textContent = extraData.connectedClients.toString();
        }
        
        // Show reconnect button if disconnected
        if (domElements.reconnectButton) {
            domElements.reconnectButton.style.display = isConnected ? 'none' : 'inline-block';
        }
    }
    
    /**
     * Format price with appropriate animation based on previous value
     * @param {HTMLElement} element - Element to update
     * @param {number} price - New price
     * @param {number} prevPrice - Previous price
     */
    formatPrice(element, price, prevPrice) {
        if (!element) return;
        
        // Format price with appropriate decimal places based on value
        const formattedPrice = this.formatWithAppropriateDecimals(price);
        element.textContent = formattedPrice;
        
        // Remove any existing animation classes
        element.classList.remove(animationConfig.upClass, animationConfig.downClass);
        
        // Add appropriate animation class if price changed
        if (prevPrice !== null && price !== prevPrice) {
            const animationClass = price > prevPrice ? animationConfig.upClass : animationConfig.downClass;
            element.classList.add(animationClass);
            
            // Remove animation class after animation completes
            setTimeout(() => {
                element.classList.remove(animationClass);
            }, animationConfig.duration);
        }
    }
    
    /**
     * Format with appropriate number of decimal places based on price magnitude
     * @param {number} price - Price to format
     * @returns {string} - Formatted price string
     */
    formatWithAppropriateDecimals(price) {
        if (price >= 1000) {
            return price.toFixed(2); // Show 2 decimals for large prices (BTC, ETH)
        } else if (price >= 1) {
            return price.toFixed(4); // Show 4 decimals for medium prices
        } else if (price >= 0.01) {
            return price.toFixed(6); // Show 6 decimals for small prices
        } else {
            return price.toFixed(8); // Show 8 decimals for very small prices
        }
    }
    
    /**
     * Process and display BBO update
     * @param {Object} data - BBO update data
     */
    processUpdate(data) {
        // Update the last update time
        this.lastUpdateTime = new Date();
        if (domElements.lastUpdateElement) {
            // Format the date as YYYY-MM-DD HH:MM.SSS
            const year = this.lastUpdateTime.getFullYear();
            const month = String(this.lastUpdateTime.getMonth() + 1).padStart(2, '0');
            const day = String(this.lastUpdateTime.getDate()).padStart(2, '0');
            const hours = String(this.lastUpdateTime.getHours()).padStart(2, '0');
            const minutes = String(this.lastUpdateTime.getMinutes()).padStart(2, '0');
            const seconds = String(this.lastUpdateTime.getSeconds()).padStart(2, '0');
            const milliseconds = String(this.lastUpdateTime.getMilliseconds()).padStart(3, '0');
            
            const formattedDate = `${year}-${month}-${day} ${hours}:${minutes}.${milliseconds.substring(0, 3)}`;
            domElements.lastUpdateElement.textContent = formattedDate;
        }
        
        // Update bid price and quantity
        if (domElements.bidPriceElement) {
            this.formatPrice(
                domElements.bidPriceElement,
                parseFloat(data.bidPrice),
                this.prevBidPrice
            );
            this.prevBidPrice = parseFloat(data.bidPrice);
        }
        
        // Update bid quantity if element exists
        if (domElements.bidQtyElement && data.bidQty) {
            domElements.bidQtyElement.textContent = parseFloat(data.bidQty).toFixed(4);
        }
        
        // Update ask price and quantity
        if (domElements.askPriceElement) {
            this.formatPrice(
                domElements.askPriceElement,
                parseFloat(data.askPrice),
                this.prevAskPrice
            );
            this.prevAskPrice = parseFloat(data.askPrice);
        }
        
        // Update ask quantity if element exists
        if (domElements.askQtyElement && data.askQty) {
            domElements.askQtyElement.textContent = parseFloat(data.askQty).toFixed(4);
        }
        
        // Calculate and update spread
        if (domElements.spreadElement) {
            const spread = parseFloat(data.askPrice) - parseFloat(data.bidPrice);
            // Convert to basis points (1 bps = 0.01%)
            const spreadBps = (spread / parseFloat(data.bidPrice)) * 10000;
            // Display spread with 2 decimal places
            domElements.spreadElement.textContent = spreadBps.toFixed(2) + ' bps';
        }
        
        // Hide the spread percentage
        if (domElements.spreadPercentElement) {
            domElements.spreadPercentElement.style.display = 'none';
        }
        
        // Update latency if available (check both formats from backend)
        if (domElements.latencyElement) {
            let latencyValue = null;
            
            // New format: latency object with backend property
            if (data.latency && typeof data.latency.backend !== 'undefined') {
                latencyValue = data.latency.backend;
            } 
            // Legacy format: backendLatency property 
            else if (typeof data.backendLatency !== 'undefined') {
                latencyValue = data.backendLatency;
            }
            
            if (latencyValue !== null) {
                // Format latency as integer milliseconds
                domElements.latencyElement.textContent = Math.round(latencyValue) + ' ms';
            }
        }
        
        // Update counters
        this.updateCount++;
        this.updateCountInLastSecond++;
        if (domElements.updateCountElement) {
            domElements.updateCountElement.textContent = this.updateCount.toString();
        }
    }
    
    /**
     * Update the symbol status display
     * @param {string} symbol - Current symbol
     */
    updateSymbolStatus(symbol) {
        if (domElements.symbolStatus) {
            domElements.symbolStatus.textContent = symbol;
        }
    }
}

// Create and export dashboard UI singleton
const dashboardUI = new DashboardUI();
export default dashboardUI;
