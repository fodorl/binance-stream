// history-chart.js - Chart functionality for the history page
// This module handles chart initialization, updates, and the reset zoom button

export default class HistoryChart {
    constructor() {
        this.chart = null;
        this.chartCanvas = document.getElementById('price-chart');
        this.resetZoomBtn = document.getElementById('reset-zoom-btn');
        
        // Initialize chart
        this.initChart();
        
        // Set up event listeners
        this.setupEventListeners();
    }
    
    /**
     * Initialize chart with Chart.js
     */
    initChart() {
        const ctx = this.chartCanvas.getContext('2d');
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Bid Price',
                        data: [],
                        borderColor: 'rgba(75, 192, 75, 1)',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2
                    },
                    {
                        label: 'Ask Price',
                        data: [],
                        borderColor: 'rgba(192, 75, 75, 1)',
                        tension: 0.1,
                        pointRadius: 0,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#ccc'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true
                            },
                            drag: {
                                enabled: true,
                                backgroundColor: 'rgba(75, 192, 192, 0.3)',
                                borderColor: 'rgba(75, 192, 192, 0.8)',
                                borderWidth: 1
                            },
                            mode: 'x',
                            onZoomComplete: () => {
                                this.onZoomComplete();
                            }
                        },
                        pan: {
                            enabled: true,
                            mode: 'xy'
                        }
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
                        title: {
                            display: true,
                            text: 'Time',
                            color: '#aaa'
                        },
                        ticks: {
                            color: '#aaa'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Price',
                            color: '#aaa'
                        },
                        ticks: {
                            color: '#aaa'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Update chart with new data
     * @param {Array} updates - Array of BBO updates
     */
    updateChart(updates) {
        if (!updates || updates.length === 0) {
            return;
        }
        
        // Prepare data for chart
        const bidData = [];
        const askData = [];
        
        updates.forEach(update => {
            const timestamp = new Date(update.timestamp);
            
            if (update.bidPrice) {
                bidData.push({
                    x: timestamp,
                    y: parseFloat(update.bidPrice)
                });
            }
            
            if (update.askPrice) {
                askData.push({
                    x: timestamp,
                    y: parseFloat(update.askPrice)
                });
            }
        });
        
        // Update datasets
        this.chart.data.datasets[0].data = bidData;
        this.chart.data.datasets[1].data = askData;
        
        // Adjust time scale unit based on data range
        this.adjustTimeScale(updates);
        
        // Update chart
        this.chart.update();
    }
    
    /**
     * Adjust time scale unit based on data range
     * @param {Array} updates - Array of BBO updates
     */
    adjustTimeScale(updates) {
        if (!updates || updates.length < 2) {
            return;
        }
        
        const firstTime = new Date(updates[0].timestamp);
        const lastTime = new Date(updates[updates.length - 1].timestamp);
        const durationInMinutes = (lastTime - firstTime) / (1000 * 60);
        
        // Determine appropriate time unit based on duration
        let timeUnit = 'minute';
        let displayFormat = 'HH:mm:ss';
        
        if (durationInMinutes > 60 * 12) {
            // More than 12 hours, show day
            timeUnit = 'day';
            displayFormat = 'MM/dd';
        } else if (durationInMinutes > 60 * 2) {
            // More than 2 hours, show hour
            timeUnit = 'hour';
            displayFormat = 'HH:mm';
        } else if (durationInMinutes > 30) {
            // More than 30 minutes, show minute
            timeUnit = 'minute';
            displayFormat = 'HH:mm';
        }
        
        // Update time scale
        this.chart.options.scales.x.time.unit = timeUnit;
        this.chart.options.scales.x.time.displayFormats = {
            [timeUnit]: displayFormat
        };
    }
    
    /**
     * Set up event listeners
     */
    setupEventListeners() {
        // Reset zoom button
        this.resetZoomBtn.addEventListener('click', () => {
            this.chart.resetZoom();
            this.resetZoomBtn.style.display = 'none';
        });
    }
    
    /**
     * Handle zoom complete event
     */
    onZoomComplete() {
        // Show reset zoom button when chart is zoomed
        this.resetZoomBtn.style.display = 'block';
    }
}
