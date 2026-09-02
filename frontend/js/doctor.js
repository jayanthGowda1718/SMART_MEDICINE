// Load family members into the "assign for" dropdown
async function loadFamilyDropdown() {
    try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = currentUser.id;
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        const users = await apiCall(`/my-family?user_id=${userId}`);
        const select = document.getElementById('patient_id');
        select.innerHTML = '<option value="">Select Family Member</option>';
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.id === userId
                ? `${user.name} (You)`
                : `${user.name} (${user.role})`;
            select.appendChild(option);
        });
    } catch (error) {
        showAlert('Error loading family members: ' + error.message, 'error');
    }
}

// Load all doctors into the "assign this doctor" dropdown
async function loadDoctorsDropdown() {
    try {
        const doctors = await apiCall('/doctors');
        const select = document.getElementById('doctor_id');
        select.innerHTML = '<option value="">Select Doctor</option>';
        doctors.forEach(doc => {
            const option = document.createElement('option');
            option.value = doc.id;
            option.textContent = doc.name;
            select.appendChild(option);
        });
    } catch (error) {
        showAlert('Error loading doctors: ' + error.message, 'error');
    }
}

// Show the currently assigned doctor's contact info for the selected family member
async function loadAssignedDoctor(patientId) {
    const card = document.getElementById('doctorCard');
    if (!patientId) {
        card.innerHTML = '<p class="loading">Select a family member above to see their assigned doctor.</p>';
        return;
    }
    card.innerHTML = '<p class="loading">Loading...</p>';
    try {
        const doctor = await apiCall(`/my-doctor?user_id=${patientId}`);
        if (!doctor) {
            card.innerHTML = '<p>No doctor assigned yet.</p>';
            return;
        }
        card.innerHTML = `
            <p><strong>Name:</strong> ${doctor.name}</p>
            <p><strong>Phone/Contact:</strong> ${doctor.contact_info || 'Not provided'}</p>
            <p><strong>Email:</strong> ${doctor.email}</p>
        `;
    } catch (error) {
        card.innerHTML = `<p class="loading">Error loading doctor: ${error.message}</p>`;
    }
}

document.getElementById('patient_id').addEventListener('change', (e) => {
    loadAssignedDoctor(e.target.value);
});

document.getElementById('assignDoctorForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const patient_id = document.getElementById('patient_id').value;
    const doctor_id = document.getElementById('doctor_id').value;
    if (!patient_id || !doctor_id) {
        showAlert('Please select both a family member and a doctor', 'error');
        return;
    }
    try {
        await apiCall('/assign-doctor', 'POST', { patient_id, doctor_id });
        showAlert('Doctor assigned successfully!');
        loadAssignedDoctor(patient_id);
    } catch (error) {
        showAlert('Error assigning doctor: ' + error.message, 'error');
    }
});

loadFamilyDropdown();
loadDoctorsDropdown();