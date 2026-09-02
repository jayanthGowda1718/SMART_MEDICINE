// Load intake logs for logged-in user ONLY
async function loadLogs() {
    try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = user.id;
        
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        
        // Use new user-specific endpoint
        const logs = await apiCall(`/my-intake-logs?user_id=${userId}`);
        const tbody = document.querySelector('#logsTable tbody');
        tbody.innerHTML = '';
        
        logs.forEach(log => {
            const row = tbody.insertRow();
            const statusClass = log.status === 'taken' ? 'success' : 
                               log.status === 'missed' ? 'error' : '';
            row.innerHTML = `
                <td>${log.id}</td>
                <td>${log.user_id}</td>
                <td>${log.medicine_id}</td>
                <td>${log.scheduled_time}</td>
                <td>${log.actual_time || 'N/A'}</td>
                <td><span class="alert alert-${statusClass}">${log.status}</span></td>
            `;
        });
        
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No intake logs yet</td></tr>';
        }
    } catch (error) {
        showAlert('Error loading logs: ' + error.message, 'error');
    }
}


// Load logs on page load
loadLogs();
