const _currentUser = JSON.parse(localStorage.getItem('user') || '{}');
const _isDoctor = _currentUser.role === 'doctor';

if (!_isDoctor) {
    document.getElementById('requestFormContainer').style.display = 'block';
    document.getElementById('colOtherParty').textContent = 'Doctor';
} else {
    document.getElementById('listHeading').textContent = 'Appointment Requests';
    document.getElementById('colOtherParty').textContent = 'Patient';
}

async function loadPatientDropdown() {
    try {
        const users = await apiCall(`/my-family?user_id=${_currentUser.id}`);
        const select = document.getElementById('patient_id');
        select.innerHTML = '<option value="">Select Family Member</option>';
        users.forEach(u => {
            const option = document.createElement('option');
            option.value = u.id;
            option.textContent = u.id === _currentUser.id ? `${u.name} (You)` : `${u.name} (${u.role})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading family members:', error);
    }
}

async function loadDoctorDropdown() {
    try {
        const doctors = await apiCall('/doctors');
        const select = document.getElementById('doctor_id');
        select.innerHTML = '<option value="">Select Doctor</option>';
        doctors.forEach(d => {
            const option = document.createElement('option');
            option.value = d.id;
            option.textContent = d.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading doctors:', error);
    }
}

async function loadAppointments() {
    const tbody = document.querySelector('#appointmentsTable tbody');
    try {
        const appts = await apiCall(`/my-appointments?user_id=${_currentUser.id}`);
        tbody.innerHTML = '';

        if (appts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7">No appointments yet</td></tr>';
            return;
        }

        appts.forEach(a => {
            const row = tbody.insertRow();
            const actions = (_isDoctor && a.status === 'pending')
                ? `<button class="btn-sm" onclick="respondAppointment(${a.id}, 'accepted')">Accept</button>
                   <button class="btn-sm delete" onclick="respondAppointment(${a.id}, 'declined')">Decline</button>`
                : '-';
            row.innerHTML = `
                <td>${a.id}</td>
                <td>${a.other_party_name}</td>
                <td>${a.requested_date}</td>
                <td>${a.requested_time}</td>
                <td>${a.notes || ''}</td>
                <td>${a.status}</td>
                <td>${actions}</td>
            `;
        });
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="7">Error: ${error.message}</td></tr>`;
    }
}

async function respondAppointment(id, status) {
    try {
        await apiCall(`/appointments/${id}`, 'PUT', { status });
        showAlert(`Appointment ${status}!`);
        loadAppointments();
    } catch (error) {
        showAlert('Error updating appointment: ' + error.message, 'error');
    }
}

if (!_isDoctor) {
    document.getElementById('requestAppointmentForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            patient_id: document.getElementById('patient_id').value,
            doctor_id: document.getElementById('doctor_id').value,
            requested_date: document.getElementById('requested_date').value,
            requested_time: document.getElementById('requested_time').value,
            notes: document.getElementById('notes').value
        };
        try {
            await apiCall('/appointments', 'POST', data);
            showAlert('Appointment requested!');
            document.getElementById('requestAppointmentForm').reset();
            loadAppointments();
        } catch (error) {
            showAlert('Error requesting appointment: ' + error.message, 'error');
        }
    });
    loadPatientDropdown();
    loadDoctorDropdown();
}

loadAppointments();