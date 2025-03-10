// Chart Controller for Binance BBO Stream
// This implementation uses Chart.js as per the MEMORY
import { domElements } from './config.js';

// Chart configuration
const chartConfig = {
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

export default class ChartController {
    constructor() {
        // Timespan options in minutes
        this.timespans = [1, 5, 15, 60, 720, 1440];
        this.currentTimespan = 1; // Default to 1 minute
        
        // Chart data storage
        this.chartData = {
            timestamps: [],
            bidPrices: [],
            askPrices: []
        };
        
        // Maximum data points to store (increased to store enough data)
        this.maxDataPoints = 1000000;
        
        // Persistence configuration
        this.persistenceEnabled = true;
        this.saveInterval = 100; // Save every 100 data points
        this.lastSaveIndex = 0;
        
        // Chart initialization
        this.chart = null;
        this.initialized = false;
        
        // Debug logging
        console.log('ChartController initialized with timespans:', this.timespans);
        
        // Load data from localStorage if available
        this._loadDataFromStorage();
        
        // Check for Chart.js in window/global context
        if (typeof window !== 'undefined' && window.Chart) {
            this._initChart();
            this._setupEventHandlers();
        } else {
            // Add a listener for when Chart.js is loaded
            document.addEventListener('DOMContentLoaded', () => {
                this._initChart();
                this._setupEventHandlers();
            });
        }
    }
    
    /**
     * Load Chart.js library dynamically
     * @private
     */
    _loadChartLibrary() {
        console.log('Attempting to load Chart.js library dynamically');
        const scriptElement = document.createElement('script');
        scriptElement.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.3.0/dist/chart.umd.min.js';
        
        scriptElement.onload = () => {
            console.log('Chart.js library loaded dynamically');
            setTimeout(() => this._initChart(), 500);
        };
        
        scriptElement.onerror = () => {
            console.error('Failed to load Chart.js library dynamically');
        };
        
        document.head.appendChild(scriptElement);
    }
    
    /**
     * Initialize the chart
     * @private
     */
    _initChart() {
        const chartContainer = document.getElementById(domElements.chartContainer.replace('#', ''));
        
        if (!chartContainer) {
            console.error(`Chart container with ID "${domElements.chartContainer}" not found!`);
            return;
        }
        
        console.log('Initializing chart in container:', chartContainer);
        
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error('Chart.js library is not loaded!');
            this._loadChartLibrary();
            return;
        }
        
        // Create canvas element for Chart.js
        const canvas = document.createElement('canvas');
        canvas.id = 'price-chart-canvas';
        chartContainer.innerHTML = '';
        chartContainer.appendChild(canvas);
        
        // Create the chart
        try {
            const ctx = canvas.getContext('2d');
            
            // Calculate time range for initial chart display
            const now = Date.now();
            const startTime = now - (this.currentTimespan * 60 * 1000);
            
            // Set up chart data
            const chartData = {
                labels: [],
                datasets: [
                    {
                        label: 'Bid Price',
                        data: [],
                        borderColor: chartConfig.bidColor,
                        backgroundColor: chartConfig.bidColor + '20',
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 3,
                        tension: 0.4
                    },
                    {
                        label: 'Ask Price',
                        data: [],
                        borderColor: chartConfig.askColor,
                        backgroundColor: chartConfig.askColor + '20',
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 3,
                        tension: 0.4
                    }
                ]
            };
            
            // Configure chart
            this.chart = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 0
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: `Price History (Last ${this.currentTimespan}m)`,
                            font: {
                                size: 16
                            }
                        },
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            enabled: true,
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                title: function(tooltipItems) {
                                    if (tooltipItems.length > 0) {
                                        const date = new Date(tooltipItems[0].parsed.x);
                                        // Format with specific format YYYYMMDD HH:MM:SS.mmm
                                        const year = date.getFullYear();
                                        const month = String(date.getMonth() + 1).padStart(2, '0');
                                        const day = String(date.getDate()).padStart(2, '0');
                                        const hours = String(date.getHours()).padStart(2, '0');
                                        const minutes = String(date.getMinutes()).padStart(2, '0');
                                        const seconds = String(date.getSeconds()).padStart(2, '0');
                                        const milliseconds = String(date.getMilliseconds()).padStart(3, '0');
                                        
                                        return `${year}${month}${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;
                                    }
                                    return '';
                                },
                                label: function(context) {
                                    const label = context.dataset.label || '';
                                    const value = context.raw && typeof context.raw === 'object' ? 
                                        context.raw.y : context.parsed.y;
                                    return `${label}: ${value.toFixed(2)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            min: startTime,
                            max: now,
                            time: {
                                unit: this.currentTimespan >= 15 ? 'minute' : 'second',
                                displayFormats: {
                                    second: 'HH:mm:ss.SSS',
                                    minute: 'HH:mm:ss.SSS'
                                },
                                tooltipFormat: 'YYYYMMDD HH:mm:ss.SSS'
                            },
                            grid: {
                                display: true,
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                autoSkip: true,
                                maxTicksLimit: 8,
                                source: 'auto'
                            },
                            title: {
                                display: true,
                                text: 'Time'
                            }
                        },
                        y: {
                            beginAtZero: false,
                            grid: {
                                display: true,
                                color: 'rgba(0, 0, 0, 0.1)'
                            },
                            ticks: {
                                precision: 2
                            },
                            title: {
                                display: true,
                                text: 'Price (USDT)'
                            }
                        }
                    },
                    interaction: {
                        mode: 'index',
                        intersect: false
                    }
                }
            });
            
            console.log('Chart created with initial time range:', new Date(startTime).toLocaleTimeString(), '-', new Date(now).toLocaleTimeString());
            
            // Mark as initialized
            this.initialized = true;
            
            // Check if we have any pending data to display
            if (this.chartData.timestamps.length > 0) {
                this.updateChart();
            }
        } catch (error) {
            console.error('Error initializing chart:', error);
        }
    }
    
    /**
     * Set up event handlers
     * @private
     */
    _setupEventHandlers() {
        console.log('Setting up event handlers');
        
        // Use event delegation pattern to handle button clicks
        document.addEventListener('click', (event) => {
            const button = event.target.closest('.timespan-btn');
            if (!button) return; // Not a timespan button
            
            event.preventDefault();
            const minutes = parseInt(button.getAttribute('data-minutes'), 10);
            
            console.log(`Timespan button clicked: ${minutes}m`);
            
            // Find all buttons with the same class
            const buttons = document.querySelectorAll('.timespan-btn');
            
            // Remove active class from all buttons
            buttons.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Set timespan
            this.setTimespan(minutes);
        });
        
        // Set active class to default timespan button
        const defaultButton = document.querySelector(`.timespan-btn[data-minutes="${this.currentTimespan}"]`);
        if (defaultButton) {
            defaultButton.classList.add('active');
            console.log(`Set default timespan button to ${this.currentTimespan}m`);
        } else {
            console.warn(`Default timespan button for ${this.currentTimespan}m not found`);
        }
        
        console.log('Event handlers set up with event delegation');
    }
    
    /**
     * Add new data point to the chart
     * @param {number} timestamp - Timestamp in milliseconds
     * @param {number} bidPrice - Bid price
     * @param {number} askPrice - Ask price
     */
    addDataPoint(timestamp, bidPrice, askPrice) {
        // Debug input values
        console.log(`ChartController.addDataPoint() - timestamp: ${timestamp}, bid: ${bidPrice}, ask: ${askPrice}`);
        
        // Validate inputs
        if (isNaN(timestamp) || isNaN(bidPrice) || isNaN(askPrice)) {
            console.error(`Invalid data point: timestamp=${timestamp}, bid=${bidPrice}, ask=${askPrice}`);
            return;
        }
        
        // Add to data arrays
        this.chartData.timestamps.push(timestamp);
        this.chartData.bidPrices.push(bidPrice);
        this.chartData.askPrices.push(askPrice);
        
        // Periodically log data points for debugging
        if (this.chartData.timestamps.length % 10 === 0) {
            console.log(`Added data point #${this.chartData.timestamps.length}: ${new Date(timestamp).toISOString()} - Bid: ${bidPrice}, Ask: ${askPrice}`);
            
            // Calculate and log the time range of stored data
            if (this.chartData.timestamps.length > 1) {
                const oldestTimestamp = this.chartData.timestamps[0];
                const newestTimestamp = this.chartData.timestamps[this.chartData.timestamps.length - 1];
                const timeRangeMinutes = (newestTimestamp - oldestTimestamp) / (60 * 1000);
                console.log(`Current stored data spans ${timeRangeMinutes.toFixed(2)} minutes (${this.chartData.timestamps.length} points)`);
            }
        }
        
        // Only remove old data if we exceed maxDataPoints AND the data is older than our max timespan
        // This ensures we keep data in the buffer for all supported timespans
        if (this.chartData.timestamps.length > this.maxDataPoints) {
            // Calculate the cutoff time for the maximum supported timespan (15 minutes by default)
            const now = Date.now();
            const maxTimespan = Math.max(...this.timespans); // Get max value from timespans array
            const maxCutoffTime = now - (maxTimespan * 60 * 1000);
            
            // Only remove data points older than the max cutoff time
            while (this.chartData.timestamps.length > this.maxDataPoints && 
                   this.chartData.timestamps[0] < maxCutoffTime) {
                this.chartData.timestamps.shift();
                this.chartData.bidPrices.shift();
                this.chartData.askPrices.shift();
                console.log(`Removed oldest data point, now storing ${this.chartData.timestamps.length} points`);
            }
        }
        
        // Save data to localStorage periodically
        if (this.persistenceEnabled) {
            const currentIndex = this.chartData.timestamps.length;
            if (currentIndex - this.lastSaveIndex >= this.saveInterval) {
                this._saveDataToStorage();
                this.lastSaveIndex = currentIndex;
            }
        }
        
        // Only update if chart has been initialized
        if (this.initialized && this.chart) {
            this.updateChart();
        } else {
            console.log('Chart not initialized yet, data point stored for later display');
        }
    }
    
    /**
     * Update the chart with filtered data
     */
    updateChart() {
        if (!this.initialized || !this.chart) {
            console.error('Chart not initialized or components missing');
            return;
        }
        
        // Filter the data based on the selected timespan
        const now = Date.now();
        const cutoffTime = now - (this.currentTimespan * 60 * 1000);
        
        console.log(`Updating chart with timespan: ${this.currentTimespan}m`);
        console.log(`Total data points in memory: ${this.chartData.timestamps.length}`);
        console.log(`Cutoff time: ${new Date(cutoffTime).toISOString()}`);
        
        // Filter data points that are within the selected timespan
        const filteredIndices = this.chartData.timestamps.map((time, index) => ({
            index,
            time
        })).filter(item => item.time >= cutoffTime).map(item => item.index);
        
        // Extract the data we need for the chart
        const labels = filteredIndices.map(i => new Date(this.chartData.timestamps[i]));
        const bidData = filteredIndices.map(i => this.chartData.bidPrices[i]);
        const askData = filteredIndices.map(i => this.chartData.askPrices[i]);
        
        console.log(`Filtered data points for display: ${labels.length} (from last ${this.currentTimespan} minutes)`);
        
        // Display a message if no data points are available
        if (labels.length === 0) {
            console.warn('No data points available for the selected timespan');
        }
        
        // Update chart data
        try {
            this.chart.data.labels = labels;
            this.chart.data.datasets[0].data = bidData.map((value, index) => ({
                x: labels[index],
                y: value
            }));
            this.chart.data.datasets[1].data = askData.map((value, index) => ({
                x: labels[index], 
                y: value
            }));
            
            // Set min/max for x-axis
            if (this.chart.options.scales.x.min === undefined || this.chart.options.scales.x.max === undefined) {
                this.chart.options.scales.x = {
                    ...this.chart.options.scales.x,
                    min: cutoffTime,
                    max: now
                };
            } else {
                this.chart.options.scales.x.min = cutoffTime;
                this.chart.options.scales.x.max = now;
            }
            
            // Update the chart title to show the time range
            this.chart.options.plugins.title = {
                display: true,
                text: `Price History (Last ${this.currentTimespan}m) - ${labels.length} data points`
            };
            
            // Update the chart
            this.chart.update('none');
            
            console.log('Chart updated successfully with time range:', new Date(cutoffTime).toLocaleTimeString(), '-', new Date(now).toLocaleTimeString());
        } catch (error) {
            console.error('Error updating chart data:', error);
        }
    }
    
    /**
     * Set the chart timespan
     * @param {number} minutes - Timespan in minutes
     */
    setTimespan(minutes) {
        console.log(`Setting chart timespan to ${minutes} minutes`);
        if (!this.timespans.includes(minutes)) {
            console.warn(`Invalid timespan: ${minutes}m, using default instead`);
            minutes = this.timespans[0];
        }
        
        this.currentTimespan = minutes;
        
        // Update chart title
        if (this.chart) {
            // Format the time value - show as minutes, hours, or days
            let timeDisplay;
            if (minutes < 60) {
                timeDisplay = `${minutes}m`;
            } else if (minutes === 60) {
                timeDisplay = '1h';
            } else if (minutes === 720) {
                timeDisplay = '12h';
            } else if (minutes === 1440) {
                timeDisplay = '1d';
            } else {
                // For any other values, use hours or days as appropriate
                const hours = minutes / 60;
                if (hours < 24) {
                    timeDisplay = `${hours}h`;
                } else {
                    const days = hours / 24;
                    timeDisplay = `${days}d`;
                }
            }
            
            this.chart.options.plugins.title.text = `Price History (Last ${timeDisplay})`;
            
            // Adjust time scale units based on timespan
            const scales = this.chart.options.scales;
            if (scales && scales.x) {
                if (minutes <= 1) {
                    scales.x.time.unit = 'second';
                    scales.x.time.displayFormats.second = 'HH:mm:ss.SSS';
                    scales.x.time.tooltipFormat = 'YYYYMMDD HH:mm:ss.SSS';
                } else if (minutes <= 60) {
                    scales.x.time.unit = 'minute';
                    scales.x.time.displayFormats.minute = 'HH:mm:ss.SSS';
                    scales.x.time.tooltipFormat = 'YYYYMMDD HH:mm:ss.SSS';
                } else if (minutes <= 720) {
                    scales.x.time.unit = 'hour';
                    scales.x.time.displayFormats.hour = 'HH:mm:ss.SSS';
                    scales.x.time.tooltipFormat = 'YYYYMMDD HH:mm:ss.SSS';
                } else {
                    scales.x.time.unit = 'hour';
                    scales.x.time.displayFormats.hour = 'DD/MM HH:mm:ss.SSS';
                    scales.x.time.tooltipFormat = 'YYYYMMDD HH:mm:ss.SSS';
                }
            }
        }
        
        // Update the chart
        this.updateChart();
    }
    
    /**
     * Load data from localStorage
     * @private
     */
    _loadDataFromStorage() {
        try {
            console.log('Loading data from localStorage');
            
            // Check if data is available in localStorage
            if (localStorage.getItem(chartConfig.storageKeys.timestamps) !== null) {
                const lastSaved = localStorage.getItem(chartConfig.storageKeys.lastSaved);
                const lastSavedTime = lastSaved ? new Date(parseInt(lastSaved)) : 'unknown';
                console.log(`Found data in localStorage, last saved: ${lastSavedTime}`);
                
                // Load data from localStorage
                const timestamps = JSON.parse(localStorage.getItem(chartConfig.storageKeys.timestamps));
                const bidPrices = JSON.parse(localStorage.getItem(chartConfig.storageKeys.bidPrices));
                const askPrices = JSON.parse(localStorage.getItem(chartConfig.storageKeys.askPrices));
                
                // Validate data integrity
                if (!Array.isArray(timestamps) || !Array.isArray(bidPrices) || !Array.isArray(askPrices)) {
                    console.error('Corrupted data in localStorage, ignoring');
                    return;
                }
                
                // Ensure all arrays are the same length
                const minLength = Math.min(timestamps.length, bidPrices.length, askPrices.length);
                if (timestamps.length !== bidPrices.length || bidPrices.length !== askPrices.length) {
                    console.warn('Data length mismatch in localStorage, trimming to match');
                    
                    // Add data to chartData, trimming to ensure equal length
                    this.chartData.timestamps = timestamps.slice(0, minLength);
                    this.chartData.bidPrices = bidPrices.slice(0, minLength);
                    this.chartData.askPrices = askPrices.slice(0, minLength);
                    
                    console.log(`Loaded ${minLength} data points from localStorage (after trimming)`);
                } else {
                    // Add data to chartData
                    this.chartData.timestamps = timestamps;
                    this.chartData.bidPrices = bidPrices;
                    this.chartData.askPrices = askPrices;
                    
                    console.log(`Loaded ${timestamps.length} data points from localStorage`);
                }
                
                // Print time range of loaded data
                if (timestamps.length > 0) {
                    const oldestTimestamp = new Date(timestamps[0]);
                    const newestTimestamp = new Date(timestamps[timestamps.length - 1]);
                    const timeRangeMinutes = (newestTimestamp - oldestTimestamp) / (60 * 1000);
                    
                    console.log(`Loaded data spans from ${oldestTimestamp.toLocaleTimeString()} to ${newestTimestamp.toLocaleTimeString()} (${timeRangeMinutes.toFixed(2)} minutes)`);
                }
            } else {
                console.log('No data found in localStorage');
            }
        } catch (error) {
            console.error('Error loading data from localStorage:', error);
            
            // Clear localStorage on error to prevent future issues
            localStorage.removeItem(chartConfig.storageKeys.timestamps);
            localStorage.removeItem(chartConfig.storageKeys.bidPrices);
            localStorage.removeItem(chartConfig.storageKeys.askPrices);
            localStorage.removeItem(chartConfig.storageKeys.lastSaved);
        }
    }
    
    /**
     * Save data to localStorage
     * @private
     */
    _saveDataToStorage() {
        try {
            console.log(`Saving ${this.chartData.timestamps.length} data points to localStorage`);
            
            // Calculate estimated size
            const timestampsJSON = JSON.stringify(this.chartData.timestamps);
            const bidPricesJSON = JSON.stringify(this.chartData.bidPrices);
            const askPricesJSON = JSON.stringify(this.chartData.askPrices);
            
            const totalSizeBytes = timestampsJSON.length + bidPricesJSON.length + askPricesJSON.length;
            const totalSizeKB = totalSizeBytes / 1024;
            
            console.log(`Estimated data size: ${totalSizeKB.toFixed(2)} KB`);
            
            // Check if size is reasonable (localStorage typically has a 5-10MB limit)
            if (totalSizeKB > 4000) {
                console.warn('Data size too large for localStorage, reducing data set');
                
                // Keep only the most recent 500 data points to avoid localStorage limits
                const keepCount = 500;
                if (this.chartData.timestamps.length > keepCount) {
                    const startIndex = this.chartData.timestamps.length - keepCount;
                    
                    const reducedTimestamps = this.chartData.timestamps.slice(startIndex);
                    const reducedBidPrices = this.chartData.bidPrices.slice(startIndex);
                    const reducedAskPrices = this.chartData.askPrices.slice(startIndex);
                    
                    // Save reduced dataset
                    localStorage.setItem(chartConfig.storageKeys.timestamps, JSON.stringify(reducedTimestamps));
                    localStorage.setItem(chartConfig.storageKeys.bidPrices, JSON.stringify(reducedBidPrices));
                    localStorage.setItem(chartConfig.storageKeys.askPrices, JSON.stringify(reducedAskPrices));
                    
                    console.log(`Saved reduced dataset with ${reducedTimestamps.length} data points to localStorage`);
                    return;
                }
            }
            
            // Save full dataset
            localStorage.setItem(chartConfig.storageKeys.timestamps, timestampsJSON);
            localStorage.setItem(chartConfig.storageKeys.bidPrices, bidPricesJSON);
            localStorage.setItem(chartConfig.storageKeys.askPrices, askPricesJSON);
            localStorage.setItem(chartConfig.storageKeys.lastSaved, String(Date.now()));
            
            console.log(`Successfully saved ${this.chartData.timestamps.length} data points to localStorage`);
        } catch (error) {
            console.error('Error saving data to localStorage:', error);
            
            // If we hit a quota error, try to clear some space
            if (error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
                console.warn('localStorage quota exceeded, clearing old data');
                
                // Clear data older than max timespan
                const now = Date.now();
                const maxTimespan = Math.max(...this.timespans); 
                const maxCutoffTime = now - (maxTimespan * 2 * 60 * 1000); // 2x max timespan
                
                // Keep only data from last 2x maxTimespan
                const filteredIndices = this.chartData.timestamps
                    .map((time, index) => ({ index, time }))
                    .filter(item => item.time >= maxCutoffTime)
                    .map(item => item.index);
                
                const filteredTimestamps = filteredIndices.map(i => this.chartData.timestamps[i]);
                const filteredBidPrices = filteredIndices.map(i => this.chartData.bidPrices[i]);
                const filteredAskPrices = filteredIndices.map(i => this.chartData.askPrices[i]);
                
                try {
                    // Try saving the reduced dataset
                    localStorage.setItem(chartConfig.storageKeys.timestamps, JSON.stringify(filteredTimestamps));
                    localStorage.setItem(chartConfig.storageKeys.bidPrices, JSON.stringify(filteredBidPrices));
                    localStorage.setItem(chartConfig.storageKeys.askPrices, JSON.stringify(filteredAskPrices));
                    console.log(`Saved reduced dataset with ${filteredTimestamps.length} data points`);
                } catch (innerError) {
                    // If still having issues, clear everything
                    console.error('Still unable to save to localStorage, clearing all data:', innerError);
                    localStorage.removeItem(chartConfig.storageKeys.timestamps);
                    localStorage.removeItem(chartConfig.storageKeys.bidPrices);
                    localStorage.removeItem(chartConfig.storageKeys.askPrices);
                    localStorage.removeItem(chartConfig.storageKeys.lastSaved);
                }
            }
        }
    }
    
    /**
     * Export chart data to a CSV file
     * Uses the current timespan to filter data points
     */
    exportToCSV() {
        console.log('Exporting chart data to CSV');
        
        if (!this.chartData.timestamps.length) {
            console.warn('No data to export');
            alert('No data available to export.');
            return;
        }
        
        try {
            // Filter data based on current timespan
            const now = Date.now();
            const cutoffTime = now - (this.currentTimespan * 60 * 1000);
            
            // Filter data points within the selected timespan
            const filteredData = [];
            for (let i = 0; i < this.chartData.timestamps.length; i++) {
                const timestamp = this.chartData.timestamps[i];
                if (timestamp >= cutoffTime) {
                    filteredData.push({
                        timestamp: timestamp,
                        bidPrice: this.chartData.bidPrices[i],
                        askPrice: this.chartData.askPrices[i]
                    });
                }
            }
            
            console.log(`Filtered ${filteredData.length} data points for CSV export`);
            
            if (filteredData.length === 0) {
                alert('No data available for the selected time period.');
                return;
            }
            
            // Create CSV header
            let csvContent = 'Timestamp,DateTime,Bid Price,Ask Price,Spread\n';
            
            // Add data rows
            filteredData.forEach(data => {
                const dateTime = new Date(data.timestamp).toISOString();
                const spread = (data.askPrice - data.bidPrice).toFixed(2);
                const row = `${data.timestamp},${dateTime},${data.bidPrice.toFixed(2)},${data.askPrice.toFixed(2)},${spread}`;
                csvContent += row + '\n';
            });
            
            // Create a blob and download link
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            
            // Format timestamp for filename
            const dateStr = new Date().toISOString().replace(/:/g, '-').split('.')[0];
            const symbol = 'BTCUSDT';
            const filename = `${symbol}_price_history_${dateStr}.csv`;
            
            // Create temporary link and trigger download
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log(`CSV export complete: ${filename}`);
        } catch (error) {
            console.error('Error exporting data to CSV:', error);
            alert('Error exporting data. Please try again.');
        }
    }
}
