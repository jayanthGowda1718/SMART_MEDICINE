let myMedicinesForBot = [];
let mySchedulesForBot = [];

function addBotMessage(messages, text, type) {
    const message = document.createElement('div');
    message.className = `medicine-bot-message ${type}`;
    message.textContent = text;
    messages.appendChild(message);
    return message;
}

async function answerWithOfficialDetails(question) {
    const user = JSON.parse(localStorage.getItem('user') || '{}');

    try {
        const response = await fetch('http://127.0.0.1:5000/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                message: question,
                user_id: user.id || null
            })
        });

        const data = await response.json();
        if (response.ok && data.reply) {
            return data.reply;
        }
        if (data && data.error) {
            return data.error;
        }
    } catch (error) {
        console.warn('Chatbot unavailable:', error);
        return 'The chatbot is currently unavailable. Please check the Schedules page or ask a doctor or pharmacist for the next medicine plan.';
    }

    return 'The chatbot could not answer this request right now. Please check your schedules or contact your doctor or pharmacist.';
}

function createMedicineBot() {
    const bot = document.createElement('aside');
    bot.className = 'medicine-bot';
    bot.setAttribute('aria-label', 'Medicine information assistant');
    bot.innerHTML = `
        <div class="medicine-bot-panel" id="medicineBotPanel" hidden>
            <div class="medicine-bot-header">
                <div><strong>Medicine Assistant</strong><small>General information only</small></div>
                <button type="button" id="closeMedicineBot" class="medicine-bot-close" aria-label="Close medicine assistant">&times;</button>
            </div>
            <div id="medicineBotMessages" class="medicine-bot-messages" aria-live="polite">
                <div class="medicine-bot-message bot">Hi! Ask me what a tablet is commonly used for.</div>
            </div>
            <form id="medicineQuestionForm" class="medicine-bot-form">
                <input type="text" id="medicineQuestion" placeholder="Ask about a tablet..." autocomplete="off" required>
                <button type="submit">Send</button>
            </form>
        </div>
        <button type="button" id="openMedicineBot" class="medicine-bot-toggle" aria-expanded="false" aria-controls="medicineBotPanel">
            <span aria-hidden="true">&#128138;</span> Ask about medicine
        </button>`;
    document.body.appendChild(bot);

    const panel = bot.querySelector('#medicineBotPanel');
    const toggle = bot.querySelector('#openMedicineBot');
    const close = bot.querySelector('#closeMedicineBot');
    const input = bot.querySelector('#medicineQuestion');
    const messages = bot.querySelector('#medicineBotMessages');

    toggle.addEventListener('click', () => {
        panel.hidden = false;
        toggle.setAttribute('aria-expanded', 'true');
        input.focus();
    });
    close.addEventListener('click', () => {
        panel.hidden = true;
        toggle.setAttribute('aria-expanded', 'false');
    });
    bot.querySelector('#medicineQuestionForm').addEventListener('submit', (event) => {
        event.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        const userMessage = document.createElement('div');
        userMessage.className = 'medicine-bot-message user';
        userMessage.textContent = question;
        messages.appendChild(userMessage);
        const botMessage = addBotMessage(messages, 'Checking the official medicine information...', 'bot');
        answerWithOfficialDetails(question).then(answer => {
            botMessage.textContent = answer;
            messages.scrollTop = messages.scrollHeight;
        });
        input.value = '';
        messages.scrollTop = messages.scrollHeight;
    });

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    if (user.id && typeof apiCall === 'function') {
        apiCall(`/my-medicines?user_id=${user.id}`)
            .then(medicines => { myMedicinesForBot = medicines; })
            .catch(error => console.warn('Medicine assistant could not load saved medicines:', error));
        apiCall(`/my-schedules?user_id=${user.id}`)
            .then(schedules => { mySchedulesForBot = schedules; })
            .catch(error => console.warn('Medicine assistant could not load schedules:', error));
    }
}

createMedicineBot();
