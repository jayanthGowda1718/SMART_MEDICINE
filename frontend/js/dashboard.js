// Computes the nearest upcoming scheduled dose from the user's schedules,
// so the pill-box panel can show a live countdown + idle/alerting state
// (paper section 5.2: idle/alert/detection/timeout states).
function findNextDose(schedules) {
    const dayMap = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
    const now = new Date();
    let best = null;

    schedules.forEach(sched => {
        const days = (sched.days_of_week || '').split(',').map(d => {
            const t = d.trim();
            return t ? t.charAt(0).toUpperCase() + t.substring(1, 3).toLowerCase() : '';
        });
        const [h, m] = sched.schedule_time.split(':').map(Number);

        for (let offset = 0; offset < 8; offset++) {
            const candidate = new Date(now);
            candidate.setDate(now.getDate() + offset);
            candidate.setHours(h, m, 0, 0);

            const dayName = Object.keys(dayMap).find(k => dayMap[k] === candidate.getDay());
            if (!days.includes(dayName)) continue;
            if (candidate <= now) continue;

            const startOk = !sched.start_date || new Date(sched.start_date) <= candidate;
            const endOk = !sched.end_date || new Date(sched.end_date) >= candidate;
            if (!startOk || !endOk) continue;

            if (!best || candidate < best.time) {
                best = { time: candidate, medicine_name: sched.medicine_name, dosage: sched.dosage };
            }
            break;
        }
    });

    return best;
}

// Renders the live status card: current state chip + next-dose countdown.
// "Alerting" state = within 2 minutes of a scheduled dose (matches how
// close the reminder engine's own check granularity is on the backend).
async function refreshPillBoxStatusCard() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!user.id) return;

    const stateChip = document.getElementById('pillbox_state_chip');
    const nextDoseText = document.getElementById('pillbox_next_dose');
    if (!stateChip || !nextDoseText) return;

    try {
        const schedules = await apiCall(`/my-schedules?user_id=${user.id}`);
        const next = findNextDose(schedules);

        if (!next) {
            stateChip.innerHTML = statusChip('idle');
            nextDoseText.textContent = 'No upcoming doses scheduled.';
            return;
        }

        const msUntil = next.time - new Date();
        const minsUntil = Math.round(msUntil / 60000);

        if (minsUntil <= 2) {
            stateChip.innerHTML = statusChip('alerting');
        } else {
            stateChip.innerHTML = statusChip('idle');
        }

        const dosagePart = next.dosage ? ` (${next.dosage})` : '';
        nextDoseText.textContent =
            `${next.medicine_name}${dosagePart} — ${next.time.toLocaleString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' })} (in ${minsUntil} min)`;
    } catch (error) {
        console.error('Could not refresh pill-box status card:', error);
    }
}

setInterval(refreshPillBoxStatusCard, 30000);

// Loads and renders the adherence analytics section (paper's
// Reporting/Analytics module): overall % + per-medicine breakdown.
async function loadAdherenceSummary() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!user.id) return;

    try {
        const summary = await apiCall(`/my-adherence-summary?user_id=${user.id}`);

        document.getElementById('adherence_taken_pct').textContent = `${summary.overall_percent.taken}%`;
        document.getElementById('adherence_missed_pct').textContent = `${summary.overall_percent.missed}%`;
        document.getElementById('adherence_pending_pct').textContent = `${summary.overall_percent.pending}%`;

        const tbody = document.querySelector('#adherenceTable tbody');
        tbody.innerHTML = '';

        if (summary.per_medicine.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No intake data yet.</td></tr>';
            return;
        }

        summary.per_medicine.forEach(med => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${med.medicine_name}</td>
                <td>${med.taken}</td>
                <td>${med.missed}</td>
                <td>${med.pending}</td>
                <td>${med.adherence_percent}%</td>
            `;
        });
    } catch (error) {
        console.error('Could not load adherence summary:', error);
    }
}

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
refreshPillBoxStatusCard();
loadAdherenceSummary();

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


