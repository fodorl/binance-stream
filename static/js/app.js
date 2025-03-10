/**
 * Main application script for the BBO Stream
 */

import { domElements } from './modules/dashboard/dashboard-config.js';
import DashboardChart from './modules/dashboard/dashboard-chart.js';
import dashboardSocket from './modules/dashboard/dashboard-socket.js';
import dashboardUI from './modules/dashboard/dashboard-ui.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing application');
    
    // Initialize chart controller
    const chartController = new DashboardChart();
    window.chartController = chartController; // Make it accessible for debugging
    
    // Initialize socket handler
    console.log('Initializing socket handler');
    dashboardSocket.initialize();
    window.socketHandler = dashboardSocket; // Make it accessible for debugging
    
    // Set up export CSV button
    domElements.exportCSVButton.addEventListener('click', () => {
        chartController.exportCSV();
    });
    
    // Set up reconnect button
    domElements.reconnectButton.addEventListener('click', () => {
        dashboardSocket.reconnect();
    });
    
    // Set up symbol selector
    if (domElements.symbolSelect && typeof domElements.symbolSelect.addEventListener === 'function') {
        domElements.symbolSelect.addEventListener('change', () => {
            const symbol = domElements.symbolSelect.value;
            dashboardSocket.changeSymbol(symbol);
            dashboardUI.updateSymbolStatus(symbol);
        });
    } else {
        console.log('Symbol selector not available or not a DOM element');
        // Use default symbol (BTCUSDT)
        dashboardSocket.changeSymbol('BTCUSDT');
        dashboardUI.updateSymbolStatus('BTCUSDT');
    }
    
    // Set up socket event handlers
    dashboardSocket.addListener('connectionStatus', (status, extraData) => {
        console.log('Connection status changed:', status);
        dashboardUI.updateConnectionStatus(status, extraData);
        
        // No need to set title attribute here as it's already handled in dashboardUI.updateConnectionStatus
    });
    
    dashboardSocket.addListener('bbo_update', (data) => {
        // Process BBO update
        dashboardUI.processUpdate(data);
        
        // Add data point to chart
        chartController.addDataPoint(
            parseFloat(data.bidPrice),
            parseFloat(data.askPrice)
        );
    });
    
    dashboardSocket.addListener('welcome', (data) => {
        console.log('Welcome message received:', data);
    });
    
    dashboardSocket.addListener('serverStatus', (data) => {
        console.log('Server status update:', data);
    });
    
    // Initial symbol status
    let defaultSymbol = 'BTCUSDT';
    dashboardUI.updateSymbolStatus(defaultSymbol);
    
    // Initial connection status - will be updated by socket events
    dashboardUI.updateConnectionStatus('connecting');
});
