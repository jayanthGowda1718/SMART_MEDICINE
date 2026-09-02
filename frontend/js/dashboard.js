// Load dashboard data
async function loadDashboard() {
    try {
        if (window.authReady && !(await window.authReady)) return;

        // quick backend health-check so we can show a more useful message when API is unreachable
        await apiCall('/');
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = user.id;
        
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        
        // Load user-specific data concurrently, allow partial failures so the page can still render
        const endpoints = [
            { key: 'users', url: '/users' },
            { key: 'medicines', url: `/my-medicines?user_id=${userId}` },
            { key: 'schedules', url: `/my-schedules?user_id=${userId}` },
            { key: 'notifications', url: `/my-notifications?user_id=${userId}` },
        ];

        const promises = endpoints.map(e => apiCall(e.url));
        const results = await Promise.allSettled(promises);

        const users = results[0].status === 'fulfilled' ? results[0].value : [];
        const medicines = results[1].status === 'fulfilled' ? results[1].value : [];
        const schedules = results[2].status === 'fulfilled' ? results[2].value : [];
        const notifications = results[3].status === 'fulfilled' ? results[3].value : [];

        // If any endpoint failed, log details and show a non-blocking alert
        results.forEach((r, i) => {
            if (r.status === 'rejected') {
                console.error(`Dashboard: failed to load ${endpoints[i].key}:`, r.reason);
                showAlert(`Warning: failed to load ${endpoints[i].key} — ${r.reason.message || r.reason}`, 'error');
            }
        });
        
        // Update counts
        document.getElementById('totalUsers').textContent = users.length;
        document.getElementById('totalMedicines').textContent = medicines.length;
        document.getElementById('totalSchedules').textContent = schedules.length;
        document.getElementById('totalNotifications').textContent = notifications.length;
        
        // Show recent notifications for logged-in user only
        const tbody = document.querySelector('#recentActivity tbody');
        tbody.innerHTML = '';
        
        notifications.slice(0, 5).forEach(notif => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>Notification</td>
                <td>${notif.message}</td>
                <td>${notif.sent_time}</td>
            `;
        });
        
        if (notifications.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3">No recent notifications</td></tr>';
        }
    } catch (error) {
        // Provide a clearer actionable message for network/CORS errors vs other errors
        const msg = error.message || String(error);
        if (/could not reach API|Failed to fetch/i.test(msg)) {
            showAlert('Error loading dashboard: Cannot reach backend — check that the Flask server is running at http://127.0.0.1:5000 and CORS/port settings are correct.', 'error');
        } else {
            showAlert('Error loading dashboard: ' + msg, 'error');
        }
        console.error('Dashboard load error:', error);
    }
}

// Real-time notification listener (optional - enabled if Socket.IO server is active)
if (typeof io === 'function' && window.ENABLE_SOCKET_IO) {
    try {
        const socket = io('http://127.0.0.1:5000');

        socket.on('connect', () => {
            console.log('Dashboard socket connected:', socket.id);
        });

        socket.on('new_notification', (notification) => {
            console.log('New notification received:', notification);
            if (typeof showAlert === 'function') {
                showAlert(`🔔 ${notification.message}`, 'info');
            }
        });
    } catch (e) {
        console.warn('Socket.IO initialization skipped:', e);
    }
}
// Load on page load
loadDashboard();

// Smart Pill Box Simulation Handler (Flowchart Logic)
async function runPillBoxSimulation() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const weightBefore = parseFloat(document.getElementById('sim_weight_before').value);
    const weightAfter = parseFloat(document.getElementById('sim_weight_after').value);
    const threshold = parseFloat(document.getElementById('sim_threshold').value);
    const resultDiv = document.getElementById('sim_result');

    if (!user.id) {
        alert('Please log in first');
        return;
    }

    try {
        const response = await apiCall('/api/telemetry/weight', 'POST', {
            user_id: user.id,
            medicine_id: 1, // Default test medicine
            weight_before: weightBefore,
            weight_after: weightAfter,
            threshold: threshold
        });

        resultDiv.style.display = 'block';
        resultDiv.style.background = 'transparent';
        resultDiv.style.color = 'inherit';
        if (response.verified) {
            resultDiv.innerHTML = `${statusChip('taken')} Detected weight reduction ΔW = ${response.delta_weight.toFixed(2)}g (≥ threshold ${threshold}g). Logged via Weight Sensor.`;
        } else {
            resultDiv.innerHTML = `${statusChip('missed')} No sufficient weight reduction detected (ΔW = ${response.delta_weight.toFixed(2)}g < threshold ${threshold}g). Caregiver alert sent.`;
        }
        
        // Refresh dashboard metrics
        loadDashboard();
    } catch (err) {
        resultDiv.style.display = 'block';
        resultDiv.style.background = '#fef3c7';
        resultDiv.style.color = '#92400e';
        resultDiv.innerHTML = `⚠️ Simulation error: ${err.message}`;
    }
}


