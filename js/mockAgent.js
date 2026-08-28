/* ================================
   CAMPUS FIX AI - LLM Agent Integration
   ================================
   
   This file now connects to the real LLM backend API.
   The mock logic has been replaced with actual API calls.
   ================================ */

// API Configuration
const CHAT_API_BASE_URL = 'http://localhost:5001/api';

// Conversation state
let conversationState = {
    conversation_id: null,
    category: null,
    issue: null,
    device: null,
    location: null,
    priority: null,
    diagnosticStep: 0,
    resolved: false,
    ticketCreated: false,
    conversationHistory: [],
    user_name: null
};

/**
 * Main function to send a message to the LLM agent
 * This connects to the real Flask backend with LLM integration
 * 
 * @param {string} message - User's message
 * @returns {Promise<Object>} - Agent response object
 */
async function sendMessageToAgent(message) {
    try {
        console.log('[CHAT DEBUG] ========================================');
        console.log('[CHAT DEBUG] sendMessageToAgent called');
        console.log('[CHAT DEBUG] Message:', message);
        
        // Get auth token
        const token = localStorage.getItem('campusfix_token');
        console.log('[CHAT DEBUG] Token exists:', !!token);
        console.log('[CHAT DEBUG] Token key used:', 'campusfix_token');
        
        if (token) {
            console.log('[CHAT DEBUG] Token length:', token.length);
            console.log('[CHAT DEBUG] Token starts with:', token.substring(0, 20) + '...');
        } else {
            console.log('[CHAT DEBUG] ❌ NO TOKEN FOUND IN LOCALSTORAGE');
            console.log('[CHAT DEBUG] LocalStorage keys:', Object.keys(localStorage));
        }
        
        if (!token) {
            // User not authenticated, show auth modal
            console.log('[CHAT DEBUG] No token found, user not authenticated');
            setTimeout(() => {
                if (typeof openAuthModal === 'function') {
                    openAuthModal();
                }
            }, 1000);
            return {
                message: "Please login to continue using CampusFix AI.",
                quickReplies: null,
                suggestTicket: false
            };
        }
        
        // Add to conversation history
        conversationState.conversationHistory.push({
            role: 'user',
            content: message,
            timestamp: new Date()
        });
        
        console.log('[CHAT DEBUG] Calling API:', `${CHAT_API_BASE_URL}/chat/send`);
        console.log('[CHAT DEBUG] Authorization header will be set');
        console.log('[CHAT DEBUG] Payload:', {
            message: message,
            conversation_id: conversationState.conversation_id,
            state: conversationState
        });
        
        // Make API call to real LLM backend
        const response = await fetch(`${CHAT_API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message: message,
                conversation_id: conversationState.conversation_id,
                state: conversationState
            })
        });
        
        console.log('[CHAT DEBUG] Response status:', response.status);
        console.log('[CHAT DEBUG] Response ok:', response.ok);
        
        if (!response.ok) {
            console.log('[CHAT DEBUG] ❌ Response not OK');
            // If authentication fails
            if (response.status === 401) {
                console.log('[CHAT DEBUG] 401 Unauthorized - clearing storage');
                localStorage.removeItem('campusfix_token');
                localStorage.removeItem('campusfix_user');
                return {
                    message: "Your session has expired. Please login again.",
                    quickReplies: null,
                    suggestTicket: false
                };
            }
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('[CHAT DEBUG] ✓ Response data received');
        console.log('[CHAT DEBUG] Response has conversation_id:', !!data.conversation_id);
        console.log('[CHAT DEBUG] Response has response:', !!data.response);
        console.log('[CHAT DEBUG] Response has response.message:', !!data.response?.message);
        
        if (data.response?.message) {
            console.log('[CHAT DEBUG] Message preview:', data.response.message.substring(0, 50) + '...');
        }
        
        // Update conversation ID
        if (data.conversation_id) {
            conversationState.conversation_id = data.conversation_id;
        }
        
        // Update state from backend (including stage)
        if (data.state) {
            conversationState = { ...conversationState, ...data.state };
        }
        
        // Update workflow stage
        if (data.response.stage) {
            conversationState.stage = data.response.stage;
            updateWorkflowProgress(data.response.stage);
        }
        
        // Add response to history
        conversationState.conversationHistory.push({
            role: 'assistant',
            content: data.response.message,
            timestamp: new Date()
        });
        
        console.log('[CHAT DEBUG] ✓ Returning response to chatbot.js');
        console.log('[CHAT DEBUG] ========================================');
        
        return data.response;
        
    } catch (error) {
        console.error('[CHAT ERROR] ========================================');
        console.error('[CHAT ERROR] Exception caught in sendMessageToAgent');
        console.error('[CHAT ERROR] Error type:', error.constructor.name);
        console.error('[CHAT ERROR] Error message:', error.message);
        console.error('[CHAT ERROR] Error stack:', error.stack);
        console.error('[CHAT ERROR] ========================================');
        
        return {
            message: "I'm having trouble connecting right now. Please try again in a moment.",
            quickReplies: null,
            suggestTicket: false
        };
    }
}

/**
 * Update workflow progress indicator
 */
function updateWorkflowProgress(stage) {
    console.log('Current workflow stage:', stage);
    conversationState.stage = stage;
    
    // Show progress indicator if not visible
    const progressBar = document.getElementById('workflowProgress');
    if (progressBar) {
        progressBar.style.display = 'flex';
        
        // Map of stages in order
        const stages = ['tell_us', 'ai_diagnoses', 'find_solution', 'troubleshoot', 'check_result', 'human_support'];
        const currentIndex = stages.indexOf(stage);
        
        // Update progress steps
        document.querySelectorAll('.progress-step').forEach((step, index) => {
            step.classList.remove('active', 'completed');
            
            if (index < currentIndex) {
                step.classList.add('completed');
            } else if (index === currentIndex) {
                step.classList.add('active');
            }
        });
    }
}

/**
 * Fallback response when API is unavailable
 * This allows the chatbot to work even without backend
 */
async function fallbackResponse(message) {
    await delay(1000);
    
    // Check if this is name collection (first message)
    if (conversationState.diagnosticStep === 0 && !conversationState.user_name) {
        conversationState.user_name = message.trim();
        conversationState.diagnosticStep = 1;
        
        return {
            message: `Nice to meet you, ${conversationState.user_name}! 😊\n\nI'm Fixie, your campus IT assistant. I'm here to help with IT issues. What problem can I help you solve today?`,
            quickReplies: ['Wi-Fi Issues', 'Login Problems', 'Software Help', 'Printer Issues'],
            suggestTicket: false
        };
    }
    
    // Basic fallback responses
    const message_lower = message.toLowerCase();
    
    if (message_lower.includes('wifi') || message_lower.includes('internet')) {
        return {
            message: "I can help with Wi-Fi issues. Let me ask you a few questions:\n\nAre other devices able to connect to the campus Wi-Fi network?",
            quickReplies: ['Yes', 'No', 'Not sure'],
            suggestTicket: false
        };
    }
    
    if (message_lower.includes('login') || message_lower.includes('password')) {
        return {
            message: "I can help with login and password issues. Which system are you trying to access?",
            quickReplies: ['Campus Portal', 'Email', 'Course Management', 'Other'],
            suggestTicket: false
        };
    }
    
    if (message_lower.includes('software') || message_lower.includes('install')) {
        return {
            message: "I can help with software installation. What software are you trying to install?",
            quickReplies: ['Microsoft Office', 'VS Code', 'MATLAB', 'Other'],
            suggestTicket: false
        };
    }
    
    if (message_lower.includes('print')) {
        return {
            message: "I can help with printer issues. Are you connected to the campus network?",
            quickReplies: ['Yes, on Wi-Fi', 'Yes, on Ethernet', 'No'],
            suggestTicket: false
        };
    }
    
    // Generic response
    return {
        message: "I'm here to help with your IT issue. Could you describe the problem you're experiencing in more detail?",
        quickReplies: null,
        suggestTicket: false
    };
}

/**
 * Continue conversation based on category and step
 */
function continueConversation(message) {
    // This is now handled by the LLM backend
    // Keeping this function for backward compatibility
    conversationState.diagnosticStep++;
    
    return {
        message: "Let me help you with that. Could you provide more details?",
        quickReplies: ['Yes', 'No', 'Need more help']
    };
}

/**
 * Reset conversation state
 */
function resetConversationState() {
    conversationState = {
        conversation_id: null,
        category: null,
        issue: null,
        device: null,
        location: null,
        priority: null,
        diagnosticStep: 0,
        resolved: false,
        ticketCreated: false,
        conversationHistory: [],
        user_name: null
    };
}

/**
 * Get current conversation state
 */
function getConversationState() {
    return conversationState;
}

// Make functions globally available
window.sendMessageToAgent = sendMessageToAgent;
window.resetConversationState = resetConversationState;
window.getConversationState = getConversationState;
