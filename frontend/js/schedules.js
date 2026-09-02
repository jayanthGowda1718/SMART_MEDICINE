// Load family members and their medicines for dropdowns
async function loadDropdowns() {
    try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = currentUser.id;
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        // Load only family members
        const users = await apiCall(`/my-family?user_id=${userId}`);
        const userSelect = document.getElementById('user_id');
        userSelect.innerHTML = '<option value="">Select Family Member</option>';
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.id === userId
                ? `${user.name} (You)`
                : `${user.name} (${user.role})`;
            userSelect.appendChild(option);
        });

        // Load ONLY medicines for relevant users
        // Use /medicines?user_id=... for optimization if needed, or filter in JS as below
        const medicines = await apiCall('/medicines');
        const medSelect = document.getElementById('medicine_id');
        const familyUserIds = users.map(u => u.id);
        const familyMedicines = medicines.filter(med => familyUserIds.includes(med.user_id));
        medSelect.innerHTML = '<option value="">Select Medicine</option>';
        familyMedicines.forEach(med => {
            const owner = users.find(u => u.id === med.user_id);
            const option = document.createElement('option');
            option.value = med.id;
            option.textContent = `${med.name} - ${med.dosage} (${owner ? owner.name : 'Unknown'})`;
            medSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading dropdowns:', error);
    }
}

// Load all schedules for logged-in user ONLY
async function loadSchedules() {
    try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = user.id;
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        // Show schedules for yourself AND everyone in your family
        const schedules = await apiCall(`/family-schedules?user_id=${userId}`);
        const tbody = document.querySelector('#schedulesTable tbody');
        tbody.innerHTML = '';
        schedules.forEach(schedule => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${schedule.id}</td>
                <td>${schedule.user_name || schedule.user_id}</td>
                <td>${schedule.medicine_name || schedule.medicine_id}</td>
                <td>${schedule.schedule_time}</td>
                <td>${schedule.days_of_week}</td>
                <td>${schedule.start_date}</td>
                <td>${schedule.end_date || 'N/A'}</td>
                <td class="actions">
                    <button class="btn-sm" onclick='openEditScheduleModal(${schedule.id}, "${schedule.schedule_time}", "${schedule.days_of_week}", "${schedule.start_date}", "${schedule.end_date || ''}")'>Edit</button>
                    <button class="btn-sm delete" onclick="deleteSchedule(${schedule.id})">Delete</button>
                </td>
            `;
        });
        if (schedules.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8">No schedules found. Create your first schedule!</td></tr>';
        }
    } catch (error) {
        showAlert('Error loading schedules: ' + error.message, 'error');
    }
}

// Add new schedule
document.getElementById('addScheduleForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const scheduleData = {
        user_id: parseInt(document.getElementById('user_id').value),
        medicine_id: parseInt(document.getElementById('medicine_id').value),
        schedule_time: document.getElementById('schedule_time').value,
        days_of_week: document.getElementById('days_of_week').value,
        start_date: document.getElementById('start_date').value,
        end_date: document.getElementById('end_date').value || null
    };
    try {
        await apiCall('/schedules', 'POST', scheduleData);
        showAlert('Schedule added successfully!');
        document.getElementById('addScheduleForm').reset();
        loadSchedules();
    } catch (error) {
        showAlert('Error adding schedule: ' + error.message, 'error');
    }
});

// Open edit modal
function openEditScheduleModal(id, time, days, startDate, endDate) {
    document.getElementById('edit_schedule_id').value = id;
    document.getElementById('edit_schedule_time').value = time;
    document.getElementById('edit_days_of_week').value = days;
    document.getElementById('edit_start_date').value = startDate;
    document.getElementById('edit_end_date').value = endDate;
    document.getElementById('editScheduleModal').style.display = 'block';
}

// Close edit modal
function closeEditScheduleModal() {
    document.getElementById('editScheduleModal').style.display = 'none';
}

// The update schedule handler
document.getElementById('editScheduleForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const scheduleId = document.getElementById('edit_schedule_id').value;
    const updateData = {
        schedule_time: document.getElementById('edit_schedule_time').value,
        days_of_week: document.getElementById('edit_days_of_week').value,
        start_date: document.getElementById('edit_start_date').value,
        end_date: document.getElementById('edit_end_date').value || null
    };
    try {
        await apiCall(`/schedules/${scheduleId}`, 'PUT', updateData);
        showAlert('Schedule updated successfully!');
        closeEditScheduleModal();
        loadSchedules();
    } catch (error) {
        showAlert('Error updating schedule: ' + error.message, 'error');
    }
});

// Delete schedule
async function deleteSchedule(id) {
    if (!confirm('Are you sure you want to delete this schedule?')) return;
    try {
        await apiCall(`/schedules/${id}`, 'DELETE');
        showAlert('Schedule deleted successfully!');
        loadSchedules();
    } catch (error) {
        showAlert('Error deleting schedule: ' + error.message, 'error');
    }
}

// Reminder popups are now handled globally in config.js, on every
// page — no need for schedules.js to poll separately.

// Load data on page load
loadDropdowns();
loadSchedules();
