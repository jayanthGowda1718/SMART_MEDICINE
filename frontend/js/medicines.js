// Load ONLY family members for dropdown
async function loadUsersDropdown() {
    try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = currentUser.id;
        
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        
        // Get only family members
        const users = await apiCall(`/my-family?user_id=${userId}`);
        const select = document.getElementById('user_id');
        
        // Clear existing options
        select.innerHTML = '<option value="">Select Family Member</option>';
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.id === userId 
                ? `${user.name} (You)` 
                : `${user.name} (${user.role})`;
            select.appendChild(option);
        });
        
        // Auto-select current user if only one option
        if (users.length === 1) {
            select.value = userId;
        }
    } catch (error) {
        console.error('Error loading family members:', error);
    }
}


// Load all medicines
// Load medicines for logged-in user ONLY
async function loadMedicines() {
    try {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = user.id;
        
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        
        // Use new user-specific endpoint
        const medicines = await apiCall(`/my-medicines?user_id=${userId}`);
        const tbody = document.querySelector('#medicinesTable tbody');
        tbody.innerHTML = '';
        
        medicines.forEach(med => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${med.id}</td>
                <td>${med.user_id}</td>
                <td>${med.name}</td>
                <td>${med.dosage}</td>
                <td>${med.instructions}</td>
                <td class="actions">
                    <button class="btn-sm" onclick='openEditMedicineModal(${med.id}, "${med.name}", "${med.dosage}", "${med.instructions}")'>Edit</button>
                    <button class="btn-sm delete" onclick="deleteMedicine(${med.id})">Delete</button>
                </td>
            `;
        });
        
        if (medicines.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No medicines found. Add your first medicine!</td></tr>';
        }
    } catch (error) {
        showAlert('Error loading medicines: ' + error.message, 'error');
    }
}


// Add new medicine with logged-in user's ID
document.getElementById('addMedicineForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    const nameVal = document.getElementById('med_name').value.trim();
    const dosageVal = document.getElementById('dosage').value.trim();
    const instructionsVal = document.getElementById('instructions').value.trim();

    if (!nameVal) { showAlert('Medicine name is required', 'error'); return; }
    if (!dosageVal) { showAlert('Dosage is required', 'error'); return; }

    const medData = {
        user_id: user.id,  // Auto-fill with logged-in user
        name: nameVal,
        dosage: dosageVal,
        instructions: instructionsVal
    };
    
    try {
        await apiCall('/medicines', 'POST', medData);
        showAlert('Medicine added successfully!');
        document.getElementById('addMedicineForm').reset();
        loadMedicines();
    } catch (error) {
        showAlert('Error adding medicine: ' + error.message, 'error');
    }
});


// Open edit modal
function openEditMedicineModal(id, name, dosage, instructions) {
    document.getElementById('edit_medicine_id').value = id;
    document.getElementById('edit_med_name').value = name;
    document.getElementById('edit_dosage').value = dosage;
    document.getElementById('edit_instructions').value = instructions;
    document.getElementById('editMedicineModal').style.display = 'block';
}

// Close edit modal
function closeEditMedicineModal() {
    document.getElementById('editMedicineModal').style.display = 'none';
}

// Update medicine
document.getElementById('editMedicineForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const medicineId = document.getElementById('edit_medicine_id').value;
    const nameVal = document.getElementById('edit_med_name').value.trim();
    const dosageVal = document.getElementById('edit_dosage').value.trim();
    const instructionsVal = document.getElementById('edit_instructions').value.trim();

    if (!nameVal) { showAlert('Medicine name is required', 'error'); return; }
    if (!dosageVal) { showAlert('Dosage is required', 'error'); return; }

    const medData = {
        name: nameVal,
        dosage: dosageVal,
        instructions: instructionsVal
    };
    
    try {
        await apiCall(`/medicines/${medicineId}`, 'PUT', medData);
        showAlert('Medicine updated successfully!');
        closeEditMedicineModal();
        loadMedicines();
    } catch (error) {
        showAlert('Error updating medicine: ' + error.message, 'error');
    }
});

// Delete medicine
async function deleteMedicine(id) {
    if (!confirm('Are you sure you want to delete this medicine?')) return;
    
    try {
        await apiCall(`/medicines/${id}`, 'DELETE');
        showAlert('Medicine deleted successfully!');
        loadMedicines();
    } catch (error) {
        showAlert('Error deleting medicine: ' + error.message, 'error');
    }
}

// Load data on page load
loadUsersDropdown();
loadMedicines();
