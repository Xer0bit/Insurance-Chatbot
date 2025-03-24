function addMessage(message, isUser) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    // Create avatar
    const avatar = document.createElement('img');
    avatar.className = 'avatar';
    avatar.src = isUser ? 
        '/static/images/user-avtar.svg' : 
        '/static/images/bot-avatar.png';
    avatar.alt = isUser ? 'User' : 'Bito';

    // Create message content
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;

    // Add timestamp
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    contentDiv.appendChild(timeDiv);

    // Assemble message
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    indicator.style.display = 'block';
    document.getElementById('chat-messages').scrollTop = document.getElementById('chat-messages').scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typing-indicator').style.display = 'none';
}

// Add initialization function
window.onload = async function() {
    // Display initial greeting
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: "START_CHAT" }),
        });

        const data = await response.json();
        addMessage(data.response, false);
    } catch (error) {
        console.error('Error:', error);
    }
};

function showContactForm() {
    document.getElementById('contact-form-overlay').style.display = 'flex';
}

function hideContactForm() {
    document.getElementById('contact-form-overlay').style.display = 'none';
}

function handleContactFormSubmission(event) {
    event.preventDefault();
    const form = event.target;
    const formData = {
        name: form.querySelector('#name').value,
        email: form.querySelector('#email').value,
        phone: form.querySelector('#phone').value,
        message: form.querySelector('#message').value
    };

    fetch('/submit-contact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        form.remove(); // Remove the form after submission
        addMessage("Thank you for your information! Our team will contact you shortly.", false);
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage("Sorry, there was an error submitting your information.", false);
    });
}

document.getElementById('contact-form').addEventListener('submit', handleContactFormSubmission);

function addContactForm() {
    const messagesDiv = document.getElementById('chat-messages');
    const formDiv = document.createElement('div');
    formDiv.className = 'message bot-message';
    formDiv.innerHTML = `
        <img src="/static/images/bot-avatar.png" class="avatar" alt="Bito">
        <div class="message-content">
            <form id="contact-form" class="chat-contact-form">
                <input type="text" id="name" placeholder="Your Name" required>
                <input type="email" id="email" placeholder="Your Email" required>
                <input type="tel" id="phone" placeholder="Phone Number" required>
                <textarea id="message" placeholder="How can we help you?" rows="3"></textarea>
                <button type="submit">Submit</button>
            </form>
        </div>
    `;
    messagesDiv.appendChild(formDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    // Add submit handler to the new form
    formDiv.querySelector('#contact-form').addEventListener('submit', handleContactFormSubmission);
}

async function sendMessage() {
    const inputElement = document.getElementById('user-input');
    const message = inputElement.value.trim();
    
    if (message) {
        addMessage(message, true);
        inputElement.value = '';

        // Check for contact-related keywords
        const contactKeywords = ['contact', 'call', 'talk', 'reach', 'connect'];
        if (contactKeywords.some(keyword => message.toLowerCase().includes(keyword))) {
            addMessage("Please fill out this form and we'll get back to you shortly:", false);
            addContactForm();
            return;
        }

        showTypingIndicator();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message }),
            });

            hideTypingIndicator();
            const data = await response.json();
            addMessage(data.response, false);
        } catch (error) {
            hideTypingIndicator();
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request.', false);
        }
    }
}

document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
