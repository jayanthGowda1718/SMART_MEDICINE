let _currentConversationId = null;
let _peopleLookup = {};
async function loadConversations() {
    try {
        const people = await apiCall('/my-conversations');
        const select = document.getElementById('conversation_select');
        select.innerHTML = '<option value="">Select a person</option>';
        _peopleLookup = {};
        people.forEach(p => {
            _peopleLookup[p.id] = p;
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = `${p.name} (${p.role})`;
            select.appendChild(option);
        });
        if (people.length === 0) {
            document.getElementById('chatWindow').innerHTML =
                '<p class="loading">No conversations yet — assign a doctor first on the Doctor page.</p>';
        }
    } catch (error) {
        showAlert('Error loading conversations: ' + error.message, 'error');
    }
}

async function loadMessages(withUserId) {
    const chatWindow = document.getElementById('chatWindow');
    if (!withUserId) {
        chatWindow.innerHTML = '<p class="loading">Select a conversation above.</p>';
        return;
    }
    try {
        const messages = await apiCall(`/messages?with_user_id=${withUserId}`);
        const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

        if (messages.length === 0) {
            chatWindow.innerHTML = '<p class="loading">No messages yet — say hello!</p>';
            return;
        }

        chatWindow.innerHTML = messages.map(m => {
            const isMine = m.sender_id === currentUser.id;
            return `
                <div style="text-align:${isMine ? 'right' : 'left'}; margin:8px 0;">
                    <span style="display:inline-block; padding:8px 12px; border-radius:12px;
                        background:${isMine ? '#667eea' : '#eee'}; color:${isMine ? 'white' : '#333'};
                        max-width:70%;">
                        ${m.message}
                    </span>
                    <div style="font-size:11px; color:#999;">${m.sent_at}</div>
                </div>
            `;
        }).join('');
        chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch (error) {
        chatWindow.innerHTML = `<p class="loading">Error loading messages: ${error.message}</p>`;
    }
}

document.getElementById('conversation_select').addEventListener('change', (e) => {
    _currentConversationId = e.target.value || null;
    loadMessages(_currentConversationId);
});

document.getElementById('sendMessageForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!_currentConversationId) {
        showAlert('Select a conversation first', 'error');
        return;
    }
    const text = document.getElementById('messageText').value.trim();
    if (!text) return;

    try {
        await apiCall('/messages', 'POST', { receiver_id: _currentConversationId, message: text });
        document.getElementById('messageText').value = '';
        loadMessages(_currentConversationId);
    } catch (error) {
        showAlert('Error sending message: ' + error.message, 'error');
    }
});

setInterval(() => {
    if (_currentConversationId) loadMessages(_currentConversationId);
}, 10000);

loadConversations();