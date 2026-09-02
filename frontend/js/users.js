// Load user and their family members ONLY
async function loadUsers() {
    try {
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
        const userId = currentUser.id;
        
        if (!userId) {
            showAlert('User not logged in', 'error');
            return;
        }
        
        // Use new family members endpoint
        const users = await apiCall(`/my-family?user_id=${userId}`);
        const tbody = document.querySelector('#usersTable tbody');
        tbody.innerHTML = '';
        
        users.forEach(user => {
            const isCurrentUser = user.id === userId;
            const isFamilyMember = user.created_by === userId;
            
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.name} ${isCurrentUser ? '<span style="color:#28a745; font-weight:600;">(You)</span>' : ''}</td>
                <td>${user.role}</td>
                <td>${user.contact_info || 'N/A'}</td>
                <td>${user.email}</td>
                <td class="actions">
                    <button class="btn-sm" onclick="openEditUserModal(${user.id}, '${user.name}', '${user.role}', '${user.contact_info || ''}', '${user.email}')">Edit</button>
                    <button class="btn-sm delete" onclick="deleteUser(${user.id})" ${isCurrentUser ? 'disabled title="Cannot delete yourself"' : ''}>Delete</button>
                </td>
            `;
        });
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No family members yet. Add your first family member!</td></tr>';
        }
    } catch (error) {
        showAlert('Error loading family: ' + error.message, 'error');
    }
}


// Add new family member
// Small client-side validation helpers
function validateEmailSimple(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhoneSimple(phone) {
    if (!phone) return false; // contact is required in this form
    const digits = phone.replace(/\D/g, '');
    return digits.length === 10;
}

document.getElementById('addUserForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
    
    const nameVal = document.getElementById('name').value.trim();
    const contactVal = document.getElementById('contact_info').value.trim();
    const emailVal = document.getElementById('email').value.trim();
    const passwordVal = document.getElementById('password').value;

    // validate
    if (!nameVal) { showAlert('Name is required', 'error'); return; }
    if (!validatePhoneSimple(contactVal)) { showAlert('Contact must be a 10-digit phone number', 'error'); return; }
    if (!validateEmailSimple(emailVal)) { showAlert('Enter a valid email address', 'error'); return; }
    if (!passwordVal || passwordVal.length < 6) { showAlert('Password must be at least 6 characters', 'error'); return; }

    const userData = {
        name: document.getElementById('name').value,
        role: document.getElementById('role').value,
        contact_info: contactVal,
        email: emailVal,
        password: passwordVal,
        created_by: currentUser.id  // Track who created this user
    };
    
    try {
        await apiCall('/users', 'POST', userData);
        showAlert('Family member added successfully!');
        document.getElementById('addUserForm').reset();
        loadUsers();
    } catch (error) {
        showAlert('Error adding family member: ' + error.message, 'error');
    }
});


// Open edit modal
function openEditUserModal(id, name, role, contact, email) {
    document.getElementById('edit_user_id').value = id;
    document.getElementById('edit_name').value = name;
    document.getElementById('edit_role').value = role;
    document.getElementById('edit_contact_info').value = contact;
    document.getElementById('edit_email').value = email;
    document.getElementById('editUserModal').style.display = 'block';
}

// Close edit modal
function closeEditUserModal() {
    document.getElementById('editUserModal').style.display = 'none';
}

// Update user
document.getElementById('editUserForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = document.getElementById('edit_user_id').value;
    const nameVal = document.getElementById('edit_name').value.trim();
    const contactVal = document.getElementById('edit_contact_info').value.trim();
    const emailVal = document.getElementById('edit_email').value.trim();

    if (!nameVal) { showAlert('Name is required', 'error'); return; }
    if (contactVal && !validatePhoneSimple(contactVal)) { showAlert('Contact must be a 10-digit phone number', 'error'); return; }
    if (!validateEmailSimple(emailVal)) { showAlert('Enter a valid email address', 'error'); return; }

    const userData = {
        name: nameVal,
        role: document.getElementById('edit_role').value,
        contact_info: contactVal,
        email: emailVal
    };
    
    try {
        await apiCall(`/users/${userId}`, 'PUT', userData);
        showAlert('User updated successfully!');
        closeEditUserModal();
        loadUsers();
    } catch (error) {
        showAlert('Error updating user: ' + error.message, 'error');
    }
});

// Delete user
async function deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user?')) return;
    
    try {
        await apiCall(`/users/${id}`, 'DELETE');
        showAlert('User deleted successfully!');
        loadUsers();
    } catch (error) {
        showAlert('Error deleting user: ' + error.message, 'error');
    }
}

// Load users on page load
loadUsers();
