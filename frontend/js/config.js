// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5000';

// Helper function to make API calls
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        credentials: 'include'  // Add this for session cookies
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

        // attempt to parse JSON safely; fall back to text when necessary
        let data;
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            try { data = await response.json(); } catch (err) { data = null; }
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            const message = (data && data.error) ? data.error : `HTTP ${response.status}`;
            throw new Error(message);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);

        if (error instanceof TypeError || /Failed to fetch/i.test(error.message)) {
            throw new Error(`Network error: could not reach API at ${API_BASE_URL}. ${error.message}`);
        }

        throw error;
    }
}

// Show alert message
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const main = document.querySelector('main');
    main.insertBefore(alertDiv, main.firstChild);
    
    setTimeout(() => alertDiv.remove(), 3000);
}

// Check if user is logged in
function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    if (!isLoggedIn || !user.id) {
        window.location.href = 'login.html';
        return Promise.resolve(false);
    }

    const userInfo = document.getElementById('userInfo');
    if (userInfo && user.name) {
        userInfo.textContent = `👤 ${user.name} (${user.role})`;
    }

    window.authReady = apiCall('/check-session')
        .then(session => {
            if (!session.logged_in || !session.user || session.user.id !== user.id) {
                localStorage.removeItem('user');
                localStorage.removeItem('isLoggedIn');
                window.location.href = 'login.html';
                return false;
            }
            return true;
        })
        .catch(error => {
            console.error('Session validation failed:', error);
            localStorage.removeItem('user');
            localStorage.removeItem('isLoggedIn');
            window.location.href = 'login.html';
            return false;
        });

    return window.authReady;
}

// Logout function
async function logout() {
    if (!confirm('Are you sure you want to logout?')) return;
    
    try {
        await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    localStorage.removeItem('user');
    localStorage.removeItem('isLoggedIn');
    window.location.href = 'login.html';
}

// ============================================================
// GLOBAL REMINDER POLLING
// ============================================================
let _lastSeenNotificationId = parseInt(localStorage.getItem('lastSeenNotificationId') || '0', 10);

if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
}

function _showSystemNotification(message) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('💊 Time to Take Your Medicine!', {
            body: message,
            requireInteraction: true
        });
    }
}

// Play the alert sound from THIS already-open page, not the new popup.
// Chrome blocks audio autoplay in windows that open without a direct
// click — but a page you already logged into (a real click) is trusted,
// so playing it here is far more reliable than the popup's own audio tag.
function _playAlertSound() {
    try {
        const audio = new Audio('sounds/alert.mp3');
        audio.play().catch(err => {
            console.warn('Alert sound blocked by browser autoplay policy:', err);
        });
    } catch (err) {
        console.warn('Could not play alert sound:', err);
    }
}

async function _checkForReminders() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (!isLoggedIn || !user.id) return;

    try {
        const notifications = await apiCall(`/my-notifications?user_id=${user.id}`);
        const fresh = (notifications || [])
            .filter(n => n.type === 'reminder' && n.id > _lastSeenNotificationId)
            .sort((a, b) => a.id - b.id);

        fresh.forEach(n => {
            _openReminderPopup(n);
            if (n.id > _lastSeenNotificationId) _lastSeenNotificationId = n.id;
        });
        if (fresh.length) {
            localStorage.setItem('lastSeenNotificationId', String(_lastSeenNotificationId));
        }
    } catch (error) {
        console.error('Reminder check error:', error);
    }
}

function _openReminderPopup(notification) {
    _showSystemNotification(notification.message);
    _playAlertSound();
    window.open(`reminder.html?_=${Date.now()}`, '_blank', 'width=500,height=400');
    localStorage.setItem('activeReminder', JSON.stringify(notification));
}

setInterval(_checkForReminders, 20000);
_checkForReminders();