// Load schedules (user name, medicine, time, day) for the dropdown —
// same source the Manage Schedule page uses, so it matches exactly.
let _scheduleLookup = {};

async function loadSchedulesDropdown() {
    try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = currentUser.id;

        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }

        const schedules = await apiCall(`/family-schedules?user_id=${userId}`);
        const select = document.getElementById('schedule_id');

        select.innerHTML = '<option value="">Select Schedule</option>';
        _scheduleLookup = {};
        schedules.forEach(s => {
            _scheduleLookup[s.id] = s;
            const option = document.createElement('option');
            option.value = s.id;
            option.textContent = `${s.user_name} - ${s.medicine_name} - ${s.schedule_time} - ${s.days_of_week}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading schedules:', error);
    }
}

// Build the same style of message the automatic reminder engine uses,
// straight from the selected schedule's own data.
function _buildMessageFromSchedule(schedule) {
    const dosagePart = schedule.dosage ? ` (${schedule.dosage})` : '';
    return `Time to take ${schedule.medicine_name}${dosagePart} at ${schedule.schedule_time} on ${schedule.days_of_week}`;
}

document.getElementById('schedule_id').addEventListener('change', (e) => {
    const schedule = _scheduleLookup[e.target.value];
    const preview = document.getElementById('messagePreview');
    preview.textContent = schedule ? _buildMessageFromSchedule(schedule) : 'Select a schedule above...';
});

// Make sure to call it on page load
loadSchedulesDropdown();

// Load notifications for logged-in user ONLY
async function loadNotifications() {
    try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = user.id;
        
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        
        // Use new user-specific endpoint
        const notifications = await apiCall(`/my-notifications?user_id=${userId}`);
        const tbody = document.querySelector('#notificationsTable tbody');
        tbody.innerHTML = '';
        
        notifications.forEach(notif => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${notif.id}</td>
                <td>${notif.user_id}</td>
                <td>${notif.message}</td>
                <td>${notif.type}</td>
                <td>${notif.sent_time}</td>
            `;
        });
        
        if (notifications.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No notifications yet</td></tr>';
        }
    } catch (error) {
        showAlert('Error loading notifications: ' + error.message, 'error');
    }
}


// Add new notification, built from the selected schedule's own user + message
document.getElementById('addNotificationForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const schedule = _scheduleLookup[document.getElementById('schedule_id').value];
    if (!schedule) {
        showAlert('Please select a schedule', 'error');
        return;
    }

    // Schedule the notification for today at the schedule's own time,
    // so it only appears/triggers once that moment actually arrives —
    // not immediately when this button is clicked.
    const today = new Date().toISOString().slice(0, 10); // YYYY-MM-DD
    const sentTime = `${today} ${schedule.schedule_time}`;

    const notifData = {
        user_id: schedule.user_id,
        message: _buildMessageFromSchedule(schedule),
        type: document.getElementById('type').value,
        sent_time: sentTime
    };

    try {
        await apiCall('/notifications', 'POST', notifData);
        showAlert(`Notification scheduled for ${schedule.schedule_time} today!`);
        document.getElementById('addNotificationForm').reset();
        document.getElementById('messagePreview').textContent = 'Select a schedule above...';
        loadNotifications();
    } catch (error) {
        showAlert('Error setting notification: ' + error.message, 'error');
    }
});

// Load data on page load
loadSchedulesDropdown();
loadNotifications();
