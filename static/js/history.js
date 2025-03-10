// history.js - Main JavaScript for the history page
// This module imports all the necessary modules and initializes the history page functionality

import { domElements } from './modules/history/history-config.js';
import HistoryChart from './modules/history/history-chart.js';
import HistoryTableUpdater from './modules/history/history-table-updater.js';
import HistoryDataHandler from './modules/history/history-data-handler.js';

// Initialize page when DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
    // Initialize Socket.IO connection
    window.historySocket = io();
    
    // Initialize table updater
    const tableUpdater = new HistoryTableUpdater(domElements.dataTableBody);
    
    // Initialize data handler
    const dataHandler = new HistoryDataHandler(domElements, tableUpdater);
    
    // Initialize chart
    const historyChart = new HistoryChart();
    
    // Set default time range values
    const now = new Date();
    const oneMinuteAgo = new Date(now.getTime() - 60 * 1000);
    
    domElements.startTimeInput.value = oneMinuteAgo.toISOString().slice(0, 16);
    domElements.endTimeInput.value = now.toISOString().slice(0, 16);
    
    // Set up event listeners
    domElements.timeRangeSelect.addEventListener('change', () => {
        const isCustom = domElements.timeRangeSelect.value === 'custom';
        domElements.customTimeGroup.style.display = isCustom ? 'flex' : 'none';
        domElements.customTimeEndGroup.style.display = isCustom ? 'flex' : 'none';
    });
    
    domElements.loadDataBtn.addEventListener('click', () => {
        dataHandler.loadAllData(historyChart);
    });
    
    // Load symbols
    dataHandler.loadSymbols().then(() => {
        // Load initial data
        dataHandler.loadAllData(historyChart);
    });
});
