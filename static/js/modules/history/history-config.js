// history-config.js - Configuration for the history page
// This module exports DOM elements and constants used in the history page

// DOM elements
export const domElements = {
    // Selects and inputs
    symbolSelect: document.getElementById('symbol-select'),
    timeRangeSelect: document.getElementById('time-range'),
    customTimeGroup: document.getElementById('custom-time-group'),
    customTimeEndGroup: document.getElementById('custom-time-end-group'),
    startTimeInput: document.getElementById('start-time'),
    endTimeInput: document.getElementById('end-time'),
    loadDataBtn: document.getElementById('load-data-btn'),
    
    // Table elements
    dataTableBody: document.getElementById('data-table-body'),
    
    // Latency stat elements
    avgLatencyEl: document.getElementById('avg-latency'),
    minLatencyEl: document.getElementById('min-latency'),
    maxLatencyEl: document.getElementById('max-latency'),
    p50LatencyEl: document.getElementById('p50-latency'),
    p95LatencyEl: document.getElementById('p95-latency'),
    sampleCountEl: document.getElementById('sample-count')
};
