// history-table-updater.js - Table functionality for the history page
// This module handles updating the data table with BBO updates

export default class HistoryTableUpdater {
    constructor(dataTableBody) {
        this.dataTableBody = dataTableBody;
    }
    
    /**
     * Update data table with BBO updates
     * @param {Array} updates - Array of BBO updates
     */
    updateDataTable(updates) {
        // Clear existing data
        this.dataTableBody.innerHTML = '';
        
        if (!updates || updates.length === 0) {
            this.dataTableBody.innerHTML = '<tr><td colspan="6">No data available</td></tr>';
            return;
        }
        
        // Create table rows
        updates.forEach(update => {
            const row = document.createElement('tr');
            
            // Format timestamp with specific format YYYYMMDD HH:MM:SS.mmm
            const date = new Date(update.timestamp);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            const seconds = String(date.getSeconds()).padStart(2, '0');
            const milliseconds = String(date.getMilliseconds()).padStart(3, '0');
            
            const formattedTime = `${year}${month}${day} ${hours}:${minutes}:${seconds}.${milliseconds}`;
            
            row.innerHTML = `
                <td>${formattedTime}</td>
                <td>${update.bidPrice}</td>
                <td>${update.bidQty}</td>
                <td>${update.askPrice}</td>
                <td>${update.askQty}</td>
                <td>${update.latency ? update.latency.toFixed(2) : '-'}</td>
            `;
            
            this.dataTableBody.appendChild(row);
        });
    }
}
