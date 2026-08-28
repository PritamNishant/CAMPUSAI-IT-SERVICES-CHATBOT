/* ================================
   CAMPUS FIX AI - Chatbot UI
   ================================ */

// Initialize chatbot when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeChatbot();
});

/**
 * Initialize chatbot functionality
 */
function initializeChatbot() {
    const chatbotForm = document.getElementById('chatbotForm');
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSendBtn = document.getElementById('chatbotSendBtn');
    
    if (!chatbotForm || !chatbotInput) return;
    
    // Load initial greeting from backend
    loadInitialGreeting();
    
    // Handle form submission
    chatbotForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleUserMessage();
    });
    
    // Auto-resize textarea
    chatbotInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
    
    // Handle Enter key (send) and Shift+Enter (new line)
    chatbotInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatbotForm.dispatchEvent(new Event('submit'));
        }
    });
}

/**
 * Load initial greeting from LLM backend
 */
async function loadInitialGreeting() {
    // Check if user is authenticated
    const token = localStorage.getItem('campusfix_token');
    const userStr = localStorage.getItem('campusfix_user');
    
    if (!token || !userStr) {
        console.log('User not authenticated, skipping greeting load');
        return;
    }
    
    try {
        const user = JSON.parse(userStr);
        const firstName = user.firstName || 'there';
        
        const messagesContainer = document.getElementById('chatbotMessages');
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        
        if (welcomeMessage) {
            // Update welcome message with user's name
            welcomeMessage.innerHTML = `
                <div class="welcome-icon">
                    <i class="fas fa-robot"></i>
                </div>
                <h3>Hello, ${firstName}! I'm Fixie 👋</h3>
                <p>I'm here to help you troubleshoot IT problems. What issue are you experiencing?</p>
                <div class="quick-issues">
                    <button class="quick-issue-btn" onclick="sendQuickMessage('My Wi-Fi is not working')">
                        <i class="fas fa-wifi"></i>
                        Wi-Fi Issues
                    </button>
                    <button class="quick-issue-btn" onclick="sendQuickMessage('I cannot login to my account')">
                        <i class="fas fa-lock"></i>
                        Login Problems
                    </button>
                    <button class="quick-issue-btn" onclick="sendQuickMessage('I need help installing software')">
                        <i class="fas fa-download"></i>
                        Software Help
                    </button>
                    <button class="quick-issue-btn" onclick="sendQuickMessage('The printer is not working')">
                        <i class="fas fa-print"></i>
                        Printer Issues
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.log('Error loading greeting:', error);
    }
}

/**
 * Handle user message submission
 */
async function handleUserMessage() {
    const chatbotInput = document.getElementById('chatbotInput');
    const chatbotSendBtn = document.getElementById('chatbotSendBtn');
    const message = chatbotInput.value.trim();
    
    if (!message) return;
    
    // Clear and reset input
    chatbotInput.value = '';
    chatbotInput.style.height = 'auto';
    
    // Disable send button
    chatbotSendBtn.disabled = true;
    
    // Remove welcome message if present
    removeWelcomeMessage();
    
    // Add user message to chat
    addUserMessage(message);
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        // Send message to agent and get response
        const response = await sendMessageToAgent(message);
        
        // Hide typing indicator
        hideTypingIndicator();
        
        // Add bot response
        addBotMessage(response.message, response.quickReplies);

        if (response.ticket) {
            addTicketConfirmation(response.ticket);
        }
        
        // Check if we should suggest ticket creation
        if (response.suggestTicket) {
            setTimeout(() => {
                addTicketSuggestion();
            }, 500);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addBotMessage("I apologize, but I'm having trouble processing your request right now. Please try again.");
    } finally {
        // Re-enable send button and focus input
        chatbotSendBtn.disabled = false;
        chatbotInput.focus();
    }
}

/**
 * Send a quick message (from buttons)
 */
async function sendQuickMessage(message) {
    const chatbotInput = document.getElementById('chatbotInput');
    chatbotInput.value = message;
    await handleUserMessage();
}

/**
 * Remove welcome message from chat
 */
function removeWelcomeMessage() {
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            welcomeMessage.remove();
        }, 300);
    }
}

/**
 * Add user message to chat
 */
function addUserMessage(text) {
    const messagesContainer = document.getElementById('chatbotMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message user';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-bubble">${escapeHtml(text)}</div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
        <div class="message-avatar">
            <i class="fas fa-user"></i>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Add bot message to chat
 */
function addBotMessage(text, quickReplies = null) {
    const messagesContainer = document.getElementById('chatbotMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message bot';
    
    const formattedText = renderMarkdown(text);
    
    let quickRepliesHTML = '';
    if (quickReplies && quickReplies.length > 0) {
        quickRepliesHTML = '<div class="quick-replies">';
        quickReplies.forEach(reply => {
            quickRepliesHTML += `
                <button class="quick-reply-btn" onclick="handleQuickReply('${escapeHtml(reply)}')">
                    ${escapeHtml(reply)}
                </button>
            `;
        });
        quickRepliesHTML += '</div>';
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">${formattedText}</div>
            ${quickRepliesHTML}
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Render untrusted assistant text as sanitized Markdown.
 */
function renderMarkdown(text) {
    const source = String(text || '');

    if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') {
        return escapeHtml(source).replace(/\n/g, '<br>');
    }

    const html = marked.parse(source, {
        breaks: true,
        gfm: true
    });

    return DOMPurify.sanitize(html, {
        ALLOWED_TAGS: [
            'a', 'blockquote', 'br', 'code', 'del', 'em', 'h1', 'h2', 'h3',
            'h4', 'h5', 'h6', 'hr', 'li', 'ol', 'p', 'pre', 'strong',
            'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'ul'
        ],
        ALLOWED_ATTR: ['href', 'title', 'target', 'rel']
    });
}

/**
 * Handle quick reply button click
 */
async function handleQuickReply(reply) {
    // Disable all quick reply buttons
    const quickReplyButtons = document.querySelectorAll('.quick-reply-btn');
    quickReplyButtons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.5';
    });
    
    // Send the reply as a user message
    await sendQuickMessage(reply);
}

/**
 * Add ticket suggestion notification
 */
function addTicketSuggestion() {
    const messagesContainer = document.getElementById('chatbotMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message bot';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="ticket-notification">
                <div class="ticket-notification-header">
                    <i class="fas fa-ticket-alt"></i>
                    <h4>Need Further Assistance?</h4>
                </div>
                <p>I recommend creating a support ticket so our IT team can help resolve this issue.</p>
                <button onclick="openTicketModal()">
                    <i class="fas fa-plus-circle"></i>
                    Create Support Ticket
                </button>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function addTicketConfirmation(ticket) {
    const messagesContainer = document.getElementById('chatbotMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message bot';
    messageDiv.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <div class="ticket-notification">
                <div class="ticket-notification-header">
                    <i class="fas fa-ticket-alt"></i>
                    <h4>IT Support Ticket Created</h4>
                </div>
                <p>I've forwarded this issue to the Campus IT Support Team.</p>
                <p><strong>Ticket ID: ${escapeHtml(ticket.ticket_id)}</strong></p>
                <p>You can track its status from My Tickets.</p>
            </div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Show typing indicator
 */
function showTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.classList.add('active');
        scrollToBottom();
    }
}

/**
 * Hide typing indicator
 */
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.classList.remove('active');
    }
}

/**
 * Scroll chat to bottom
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('chatbotMessages');
    if (messagesContainer) {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 100);
    }
}

/**
 * Reset conversation
 */
function resetConversation() {
    const messagesContainer = document.getElementById('chatbotMessages');
    
    if (!messagesContainer) return;
    
    // Confirm before resetting
    if (!confirm('Are you sure you want to reset the conversation? All chat history will be cleared.')) {
        return;
    }
    
    // Clear messages
    messagesContainer.innerHTML = '';
    
    // Reset conversation state
    resetConversationState();
    
    // Add welcome message back
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <i class="fas fa-robot"></i>
            </div>
            <h3>Hello! I'm Fixie, your campus IT assistant.</h3>
            <p>I'm here to help you troubleshoot IT problems. What issue are you experiencing?</p>
            <div class="quick-issues">
                <button class="quick-issue-btn" onclick="sendQuickMessage('My Wi-Fi is not working')">
                    <i class="fas fa-wifi"></i>
                    Wi-Fi Issues
                </button>
                <button class="quick-issue-btn" onclick="sendQuickMessage('I cannot login to my account')">
                    <i class="fas fa-lock"></i>
                    Login Problems
                </button>
                <button class="quick-issue-btn" onclick="sendQuickMessage('I need help installing software')">
                    <i class="fas fa-download"></i>
                    Software Help
                </button>
                <button class="quick-issue-btn" onclick="sendQuickMessage('The printer is not working')">
                    <i class="fas fa-print"></i>
                    Printer Issues
                </button>
            </div>
        </div>
    `;
    
    // Focus input
    const chatbotInput = document.getElementById('chatbotInput');
    if (chatbotInput) {
        chatbotInput.focus();
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make functions globally available
window.sendQuickMessage = sendQuickMessage;
window.handleQuickReply = handleQuickReply;
window.resetConversation = resetConversation;
