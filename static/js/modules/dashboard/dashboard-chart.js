/**
 * Dashboard Chart Controller
 * Handles price chart initialization and updates for the dashboard
 */
import { domElements, chartConfig } from './dashboard-config.js';

export default class DashboardChart {
    constructor() {
        this.chart = null;
        this.timeframe = chartConfig.defaultTimeframe; // Default timeframe in minutes
        this.maxDataPoints = chartConfig.maxDataPoints;
        
        // Data storage
        this.timestamps = [];
        this.bidPrices = [];
        this.askPrices = [];
        
        // Initialize chart
        this.initChart();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Try to restore data from localStorage
        this.restoreDataFromStorage();
    }
    
    /**
     * Initialize the price chart
     */
    initChart() {
        // Get the chart container
        const chartContainer = document.getElementById('chart-container');
        
        if (!chartContainer) {
            console.error('Chart container not found in the DOM');
            return;
        }
        
        // Create canvas element if it doesn't exist
        let canvas = chartContainer.querySelector('canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'price-chart';
            chartContainer.appendChild(canvas);
        }
        
        const ctx = canvas.getContext('2d');
        
        // Initialize Chart.js
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [], // Will be populated with timestamps
                datasets: [
                    {
                        label: 'Bid Price',
                        data: [],
                        borderColor: chartConfig.bidColor,
                        backgroundColor: chartConfig.bidColor,
                        fill: false,
                        tension: 0.2,
                        pointRadius: 0,
                        borderWidth: 2
                    },
                    {
                        label: 'Ask Price',
                        data: [],
                        borderColor: chartConfig.askColor,
                        backgroundColor: chartConfig.askColor,
                        fill: false,
                        tension: 0.2,
                        pointRadius: 0,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#ccc'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(tooltipItems) {
                                let date = new Date(tooltipItems[0].parsed.x);
                                return date.toLocaleTimeString();
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: `Price Chart (${this.timeframe}m)`,
                        color: '#ccc'
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'minute',
                            displayFormats: {
                                minute: 'HH:mm:ss'
                            }
                        },
                        ticks: {
                            color: '#aaa'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        ticks: {
                            color: '#aaa'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                },
                animation: {
                    duration: 0 // Disable animations for performance
                },
                elements: {
                    line: {
                        borderWidth: 2
                    }
                }
            }
        });
    }
    
    /**
     * Set up event listeners for chart controls
     */
    setupEventListeners() {
        // Timeframe buttons
        domElements.timeframeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Remove active class from all buttons
                domElements.timeframeButtons.forEach(b => b.classList.remove('active'));
                
                // Add active class to clicked button
                btn.classList.add('active');
                
                // Update timeframe
                this.timeframe = parseInt(btn.dataset.minutes);
                
                // Update chart title
                this.chart.options.plugins.title.text = `Price Chart (${this.timeframe}m)`;
                
                // Update chart with filtered data
                this.updateChartWithTimeframe();
            });
        });
        
        // Mobile toggle button
        if (domElements.toggleChartBtn) {
            domElements.toggleChartBtn.addEventListener('click', () => {
                const chartContainer = domElements.chartContainer;
                
                if (chartContainer.style.display === 'none' || !chartContainer.style.display) {
                    chartContainer.style.display = 'block';
                    domElements.toggleChartBtn.textContent = 'Hide Chart';
                } else {
                    chartContainer.style.display = 'none';
                    domElements.toggleChartBtn.textContent = 'Show Chart';
                }
            });
        }
    }
    
    /**
     * Add new data point to the chart
     * @param {number} bidPrice - Current bid price
     * @param {number} askPrice - Current ask price
     */
    addDataPoint(bidPrice, askPrice) {
        const now = Date.now();
        
        // Add data to arrays
        this.timestamps.push(now);
        this.bidPrices.push(bidPrice);
        this.askPrices.push(askPrice);
        
        // Clean up old data points (older than 15 minutes)
        this.cleanupOldData();
        
        // Limit array sizes to prevent memory issues
        if (this.timestamps.length > this.maxDataPoints) {
            this.timestamps.shift();
            this.bidPrices.shift();
            this.askPrices.shift();
        }
        
        // Save data to localStorage
        this.saveDataToStorage();
        
        // Update chart with filtered data
        this.updateChartWithTimeframe();
    }
    
    /**
     * Remove data points older than 15 minutes to keep frontend performance snappy
     */
    cleanupOldData() {
        const cutoffTime = Date.now() - (15 * 60 * 1000); // 15 minutes in milliseconds
        
        // Find the index of the first item newer than the cutoff
        let firstValidIndex = 0;
        while (firstValidIndex < this.timestamps.length && this.timestamps[firstValidIndex] < cutoffTime) {
            firstValidIndex++;
        }
        
        // If we found old items, remove them
        if (firstValidIndex > 0) {
            this.timestamps = this.timestamps.slice(firstValidIndex);
            this.bidPrices = this.bidPrices.slice(firstValidIndex);
            this.askPrices = this.askPrices.slice(firstValidIndex);
            console.debug(`Removed ${firstValidIndex} data points older than 15 minutes`);
        }
    }
    
    /**
     * Update chart with data filtered by selected timeframe
     */
    updateChartWithTimeframe() {
        // Get current time
        const now = Date.now();
        
        // Calculate cutoff time based on selected timeframe
        const cutoffTime = now - (this.timeframe * 60 * 1000);
        
        // Filter data based on timeframe
        const filteredData = this.timestamps.reduce((result, timestamp, i) => {
            if (timestamp >= cutoffTime) {
                result.timestamps.push(new Date(timestamp));
                result.bidPrices.push(this.bidPrices[i]);
                result.askPrices.push(this.askPrices[i]);
            }
            return result;
        }, { timestamps: [], bidPrices: [], askPrices: [] });
        
        // Update chart data
        this.chart.data.labels = filteredData.timestamps;
        this.chart.data.datasets[0].data = filteredData.bidPrices;
        this.chart.data.datasets[1].data = filteredData.askPrices;
        
        // Calculate appropriate y-axis range with padding
        if (filteredData.bidPrices.length > 0 && filteredData.askPrices.length > 0) {
            // Find min and max values
            const allPrices = [...filteredData.bidPrices, ...filteredData.askPrices];
            const minPrice = Math.min(...allPrices);
            const maxPrice = Math.max(...allPrices);
            const range = maxPrice - minPrice;
            
            // Add padding (10% of range)
            const padding = range * 0.1;
            
            // Update y-axis min and max
            this.chart.options.scales.y.min = minPrice - padding;
            this.chart.options.scales.y.max = maxPrice + padding;
        }
        
        // Update chart
        this.chart.update();
    }
    
    /**
     * Save current data to localStorage
     */
    saveDataToStorage() {
        try {
            localStorage.setItem(chartConfig.storageKeys.timestamps, JSON.stringify(this.timestamps));
            localStorage.setItem(chartConfig.storageKeys.bidPrices, JSON.stringify(this.bidPrices));
            localStorage.setItem(chartConfig.storageKeys.askPrices, JSON.stringify(this.askPrices));
            localStorage.setItem(chartConfig.storageKeys.lastSaved, Date.now().toString());
        } catch (error) {
            console.error('Failed to save chart data to localStorage:', error);
        }
    }
    
    /**
     * Restore data from localStorage
     */
    restoreDataFromStorage() {
        try {
            const lastSaved = localStorage.getItem(chartConfig.storageKeys.lastSaved);
            
            // Only restore data if it was saved recently (within the last hour)
            if (lastSaved && (Date.now() - parseInt(lastSaved)) < 3600000) {
                const timestamps = JSON.parse(localStorage.getItem(chartConfig.storageKeys.timestamps));
                const bidPrices = JSON.parse(localStorage.getItem(chartConfig.storageKeys.bidPrices));
                const askPrices = JSON.parse(localStorage.getItem(chartConfig.storageKeys.askPrices));
                
                if (timestamps && bidPrices && askPrices) {
                    this.timestamps = timestamps;
                    this.bidPrices = bidPrices;
                    this.askPrices = askPrices;
                    
                    // Clean up old data points immediately after restoration
                    this.cleanupOldData();
                    
                    // Update chart with restored data
                    this.updateChartWithTimeframe();
                    console.log('Restored chart data from localStorage');
                }
            }
        } catch (error) {
            console.error('Failed to restore chart data from localStorage:', error);
        }
    }
    
    /**
     * Export current chart data as CSV
     */
    exportCSV() {
        // Get data filtered by current timeframe
        const now = Date.now();
        const cutoffTime = now - (this.timeframe * 60 * 1000);
        
        const filteredData = this.timestamps.reduce((result, timestamp, i) => {
            if (timestamp >= cutoffTime) {
                result.push({
                    timestamp: new Date(timestamp).toISOString(),
                    bidPrice: this.bidPrices[i],
                    askPrice: this.askPrices[i],
                    spread: this.askPrices[i] - this.bidPrices[i]
                });
            }
            return result;
        }, []);
        
        // Create CSV content
        let csvContent = 'data:text/csv;charset=utf-8,';
        
        // Add header row
        csvContent += 'Timestamp,Bid Price,Ask Price,Spread\n';
        
        // Add data rows
        filteredData.forEach(row => {
            csvContent += `${row.timestamp},${row.bidPrice},${row.askPrice},${row.spread}\n`;
        });
        
        // Create download link
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement('a');
        link.setAttribute('href', encodedUri);
        link.setAttribute('download', `bbo_data_${this.timeframe}m_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.csv`);
        
        // Append, click and remove link
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    /**
     * Clear all chart data
     */
    clearData() {
        this.timestamps = [];
        this.bidPrices = [];
        this.askPrices = [];
        
        // Clear localStorage
        localStorage.removeItem(chartConfig.storageKeys.timestamps);
        localStorage.removeItem(chartConfig.storageKeys.bidPrices);
        localStorage.removeItem(chartConfig.storageKeys.askPrices);
        localStorage.removeItem(chartConfig.storageKeys.lastSaved);
        
        // Update chart
        this.chart.data.labels = [];
        this.chart.data.datasets[0].data = [];
        this.chart.data.datasets[1].data = [];
        this.chart.update();
    }
    
    /**
     * Helper function to convert hex color to rgba
     * @param {string} hex - Hex color string
     * @param {number} alpha - Alpha channel value (0-1)
     * @returns {string} RGBA color string
     */
    _hexToRgba(hex, alpha) {
        // If hex is already rgba format, just return it
        if (hex.startsWith('rgba')) {
            return hex;
        }
        
        // Remove # if present
        hex = hex.replace('#', '');
        
        // Parse hex values
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        
        // Return rgba format
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
}
