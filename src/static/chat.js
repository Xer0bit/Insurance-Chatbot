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

    // Create message content with markdown support
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (!isUser) {
        // Add loading state
        contentDiv.innerHTML = '<div class="loading">...</div>';
        renderMarkdown(message).then(html => {
            contentDiv.innerHTML = html;
            // Add timestamp after content is rendered
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            contentDiv.appendChild(timeDiv);
        });
    } else {
        contentDiv.textContent = message;
        // Add timestamp for user messages
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        contentDiv.appendChild(timeDiv);
    }

    // Assemble message
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function renderMarkdown(text) {
    try {
        // Configure marked options
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false,
            smartLists: true,
            smartypants: true
        });
        
        // Clean up the text before parsing
        text = text.replace(/\*\*/g, '**').trim();  // Fix double asterisks
        text = text.replace(/\n\s*\n\s*\n/g, '\n\n');  // Fix multiple line breaks
        
        // Parse markdown and sanitize
        const html = await marked.parse(text);
        return DOMPurify.sanitize(html, {
            ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'strong', 'em', 'ul', 'ol', 'li', 'p', 'br', 'code', 'pre']
        });
    } catch (error) {
        console.error('Error parsing markdown:', error);
        return text;
    }
}

function showTypingIndicator() {
    const messagesDiv = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <img src="/static/images/bot-avatar.png" class="avatar" alt="Bito">
        <div class="message-content">
            <div class="thinking-animation">
                <div class="thinking-dots">
                    <div class="dot dot1"></div>
                    <div class="dot dot2"></div>
                    <div class="dot dot3"></div>
                </div>
            </div>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
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

async function resetChat() {
    try {
        // Clear chat messages
        const messagesDiv = document.getElementById('chat-messages');
        messagesDiv.innerHTML = '';
        
        // Reset conversation on server
        const response = await fetch('/reset-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();
        addMessage(data.response, false);
        
    } catch (error) {
        console.error('Error resetting chat:', error);
        addMessage('Error resetting chat. Please try again.', false);
    }
}

function handleKeyPress(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
}
