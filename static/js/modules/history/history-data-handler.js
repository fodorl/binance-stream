// history-data-handler.js - Data handling functionality for the history page
// This module handles loading symbols, BBO updates, and latency statistics

export default class HistoryDataHandler {
    constructor(domElements, tableUpdater) {
        this.domElements = domElements;
        this.tableUpdater = tableUpdater;
        
        // Cache variables
        this.availableSymbols = [];
    }
    
    /**
     * Load available symbols
     * @returns {Promise} Promise resolving when symbols are loaded
     */
    async loadSymbols() {
        try {
            const response = await fetch('/api/history/symbols');
            const data = await response.json();
            
            if (data && data.status === 'success' && data.data && data.data.symbols) {
                this.availableSymbols = data.data.symbols;
                
                // Clear existing options except the first one (BTCUSDT)
                const fragment = document.createDocumentFragment();
                
                // Add all symbols to the select
                this.availableSymbols.forEach(symbol => {
                    const option = document.createElement('option');
                    option.value = symbol;
                    option.textContent = symbol;
                    fragment.appendChild(option);
                });
                
                // Clear and rebuild the select
                this.domElements.symbolSelect.innerHTML = '';
                this.domElements.symbolSelect.appendChild(fragment);
                
                // Set default selection to BTCUSDT if available
                const btcIndex = this.availableSymbols.findIndex(s => s === 'BTCUSDT');
                if (btcIndex !== -1) {
                    this.domElements.symbolSelect.selectedIndex = btcIndex;
                }
            }
        } catch (error) {
            console.error('Error loading symbols:', error);
        }
    }
    
    /**
     * Load BBO updates based on selected time range and symbol
     * @returns {Promise<Array>} Promise resolving to the loaded updates
     */
    async loadBBOUpdates() {
        const symbol = this.domElements.symbolSelect.value;
        const timeRange = this.domElements.timeRangeSelect.value;
        let startTime, endTime;
        
        if (timeRange === 'custom') {
            startTime = new Date(this.domElements.startTimeInput.value).getTime();
            endTime = new Date(this.domElements.endTimeInput.value).getTime();
        } else {
            // Calculate time range based on selection (e.g., '5m' = 5 minutes)
            const now = new Date();
            const minutes = timeRange === '1h' ? 60 :
                          timeRange === '6h' ? 360 :
                          timeRange === '24h' ? 1440 :
                          timeRange === '15m' ? 15 : 
                          timeRange === '5m' ? 5 : 1;  // '1m' = 1 minute
            
            endTime = now.getTime();
            startTime = endTime - (minutes * 60 * 1000);
        }
        
        try {
            const response = await fetch(`/api/history/updates?symbol=${symbol}&start_time=${startTime}&end_time=${endTime}`);
            const data = await response.json();
            
            if (data && data.status === 'success' && data.data && data.data.updates) {
                // Sort updates by timestamp
                data.data.updates.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                
                // Update table
                this.tableUpdater.updateDataTable(data.data.updates);
                
                return data.data.updates;
            }
            
            return [];
        } catch (error) {
            console.error('Error loading BBO updates:', error);
            return [];
        }
    }
    
    /**
     * Load latency statistics
     * @returns {Promise} Promise resolving when latency stats are loaded
     */
    async loadLatencyStats() {
        const symbol = this.domElements.symbolSelect.value;
        const timeRange = this.domElements.timeRangeSelect.value;
        let startTime, endTime;
        
        if (timeRange === 'custom') {
            startTime = new Date(this.domElements.startTimeInput.value).getTime();
            endTime = new Date(this.domElements.endTimeInput.value).getTime();
        } else {
            // Calculate time range based on selection
            const now = new Date();
            const minutes = timeRange === '1h' ? 60 :
                          timeRange === '6h' ? 360 :
                          timeRange === '24h' ? 1440 :
                          timeRange === '15m' ? 15 :
                          timeRange === '5m' ? 5 : 1;  // '1m' = 1 minute
            
            endTime = now.getTime();
            startTime = endTime - (minutes * 60 * 1000);
        }
        
        try {
            const response = await fetch(`/api/history/latency?symbol=${symbol}&start_time=${startTime}&end_time=${endTime}`);
            const data = await response.json();
            
            if (data && data.status === 'success' && data.data && data.data.stats) {
                const stats = data.data.stats;
                // Update latency stats in the UI
                this.domElements.avgLatencyEl.textContent = stats.avg ? stats.avg.toFixed(2) + ' ms' : '-';
                this.domElements.minLatencyEl.textContent = stats.min ? stats.min.toFixed(2) + ' ms' : '-';
                this.domElements.maxLatencyEl.textContent = stats.max ? stats.max.toFixed(2) + ' ms' : '-';
                this.domElements.p50LatencyEl.textContent = stats.p50 ? stats.p50.toFixed(2) + ' ms' : '-';
                this.domElements.p95LatencyEl.textContent = stats.p95 ? stats.p95.toFixed(2) + ' ms' : '-';
                this.domElements.sampleCountEl.textContent = stats.count || '0';
            } else {
                this.resetLatencyStats();
            }
        } catch (error) {
            console.error('Error loading latency stats:', error);
            this.resetLatencyStats();
        }
    }
    
    /**
     * Reset latency statistics display
     */
    resetLatencyStats() {
        this.domElements.avgLatencyEl.textContent = '-';
        this.domElements.minLatencyEl.textContent = '-';
        this.domElements.maxLatencyEl.textContent = '-';
        this.domElements.p50LatencyEl.textContent = '-';
        this.domElements.p95LatencyEl.textContent = '-';
        this.domElements.sampleCountEl.textContent = '0';
    }
    
    /**
     * Load all data and update chart
     * @param {HistoryChart} chartInstance - Instance of the HistoryChart class
     */
    async loadAllData(chartInstance) {
        // Load BBO updates
        const updates = await this.loadBBOUpdates();
        
        // Load latency stats
        await this.loadLatencyStats();
        
        // Update chart
        if (updates && updates.length > 0) {
            chartInstance.updateChart(updates);
        }
    }
}
