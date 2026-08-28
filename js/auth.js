/* ================================
   CAMPUS FIX AI - Authentication
   ================================ */

const API_BASE_URL = 'http://localhost:5001/api';

// Auth state
const authState = {
    userType: null,
    userId: null,
    userExists: false,
    currentScreen: 'userType'
};

/**
 * Open authentication modal
 */
function openAuthModal() {
    // Check if user is already authenticated
    const token = localStorage.getItem('campusfix_token');
    if (token) {
        // Verify token is still valid
        verifyToken().then(valid => {
            if (valid) {
                // User is authenticated, open chatbot directly
                openAuthenticatedChatbot();
            } else {
                // Token invalid, show auth modal
                showAuthModal();
            }
        });
    } else {
        showAuthModal();
    }
}

/**
 * Show authentication modal
 */
function showAuthModal() {
    const overlay = document.getElementById('authModalOverlay');
    if (overlay) {
        overlay.classList.add('active');
        showScreen('userType');
    }
}

/**
 * Close authentication modal
 */
function closeAuthModal() {
    const overlay = document.getElementById('authModalOverlay');
    if (overlay) {
        overlay.classList.remove('active');
        resetAuthState();
    }
}

/**
 * Reset auth state
 */
function resetAuthState() {
    authState.userType = null;
    authState.userId = null;
    authState.userExists = false;
    authState.currentScreen = 'userType';
    clearError();
}

/**
 * Show specific auth screen
 */
function showScreen(screenName) {
    // Hide all screens
    document.querySelectorAll('.auth-screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Show requested screen
    const screen = document.getElementById(`${screenName}Screen`);
    if (screen) {
        screen.classList.add('active');
        authState.currentScreen = screenName;
    }
}

/**
 * Select user type
 */
function selectUserType(type) {
    authState.userType = type;
    
    // Update UI
    document.querySelectorAll('.user-type-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    const selectedCard = document.querySelector(`[onclick="selectUserType('${type}')"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
    }
    
    // Enable continue button
    const continueBtn = document.getElementById('userTypeContinueBtn');
    if (continueBtn) {
        continueBtn.disabled = false;
    }
}

/**
 * Continue from user type selection
 */
function continueFromUserType() {
    if (!authState.userType) {
        showError('Please select your user type');
        return;
    }
    
    showScreen('idInput');
    
    // Update ID input label
    const label = document.getElementById('idInputLabel');
    const input = document.getElementById('idInput');
    
    if (authState.userType === 'student') {
        label.textContent = 'Student Registration ID';
        input.placeholder = 'Enter your registration ID';
    } else {
        label.textContent = 'Employee ID';
        input.placeholder = 'Enter your employee ID';
    }
    
    // Focus input
    setTimeout(() => input.focus(), 100);
}

/**
 * Check if user exists
 */
async function checkUser() {
    const input = document.getElementById('idInput');
    const userId = input.value.trim();
    
    if (!userId) {
        showError('Please enter your ID');
        return;
    }
    
    authState.userId = userId;
    
    // Show loading
    const btn = document.getElementById('idCheckBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="auth-loading"></span>Checking...';
    
    clearError();
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/check-user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usertype: authState.userType,
                id: userId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authState.userExists = data.exists;
            
            if (data.exists) {
                // User exists, show login
                showScreen('login');
                document.getElementById('loginUserTypeDisplay').textContent = 
                    authState.userType === 'student' ? 'Student' : 'Employee';
                document.getElementById('loginIdDisplay').textContent = userId;
            } else {
                // New user, show registration
                showScreen('register');
            }
        } else {
            showError(data.error || 'Failed to check user');
        }
    } catch (error) {
        console.error('Check user error:', error);
        showError('Connection error. Please try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Continue';
    }
}

/**
 * Handle login
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const password = document.getElementById('loginPassword').value;
    
    if (!password) {
        showError('Please enter your password');
        return;
    }
    
    const btn = document.getElementById('loginBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="auth-loading"></span>Logging in...';
    
    clearError();
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usertype: authState.userType,
                id: authState.userId,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token and user info
            localStorage.setItem('campusfix_token', data.token);
            localStorage.setItem('campusfix_user', JSON.stringify(data.user));
            
            // Show success and open chatbot
            showSuccess('Login successful!');
            
            setTimeout(() => {
                closeAuthModal();
                openAuthenticatedChatbot();
            }, 1000);
        } else {
            showError(data.error || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('Connection error. Please try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Login';
    }
}

/**
 * Handle registration
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const firstName = document.getElementById('registerFirstName').value.trim();
    const lastName = document.getElementById('registerLastName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('registerConfirmPassword').value;
    
    // Validation
    if (!firstName || !lastName || !email || !password || !confirmPassword) {
        showError('Please fill in all fields');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('Passwords do not match');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }
    
    const btn = document.getElementById('registerBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="auth-loading"></span>Creating account...';
    
    clearError();
    
    try {
        const requestBody = {
            firstName: firstName,
            lastName: lastName,
            email: email,
            password: password,
            usertype: authState.userType
        };
        
        // Add ID field based on user type
        if (authState.userType === 'student') {
            requestBody.registration_number = authState.userId;
        } else {
            requestBody.employee_id = authState.userId;
        }
        
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store token and user info
            localStorage.setItem('campusfix_token', data.token);
            localStorage.setItem('campusfix_user', JSON.stringify(data.user));
            
            // Show success and open chatbot
            showSuccess('Account created successfully!');
            
            setTimeout(() => {
                closeAuthModal();
                openAuthenticatedChatbot();
            }, 1000);
        } else {
            showError(data.error || 'Registration failed');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('Connection error. Please try again.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }
}

/**
 * Verify token validity
 */
async function verifyToken() {
    const token = localStorage.getItem('campusfix_token');
    if (!token) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('campusfix_user', JSON.stringify(data.user));
            return true;
        } else {
            // Token invalid, clear storage
            localStorage.removeItem('campusfix_token');
            localStorage.removeItem('campusfix_user');
            return false;
        }
    } catch (error) {
        console.error('Token verification error:', error);
        return false;
    }
}

/**
 * Logout user
 */
async function logoutUser() {
    try {
        const token = localStorage.getItem('campusfix_token');
        
        if (token) {
            await fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Clear local storage
        localStorage.removeItem('campusfix_token');
        localStorage.removeItem('campusfix_user');
        
        // Reset conversation state
        if (typeof resetConversationState === 'function') {
            resetConversationState();
        }
        
        // Reload page to reset UI
        window.location.reload();
    }
}

/**
 * Open authenticated chatbot
 */
function openAuthenticatedChatbot() {
    // Update UI to show user is logged in
    updateNavbarForAuth();
    
    // Show the chatbot section
    const chatbotSection = document.getElementById('chatbot-demo');
    if (chatbotSection) {
        chatbotSection.style.display = 'block';
    }
    
    // Open chatbot (scroll to it)
    if (typeof openChatbot === 'function') {
        openChatbot();
    }
}

/**
 * Update navbar for authenticated user
 */
function updateNavbarForAuth() {
    const user = JSON.parse(localStorage.getItem('campusfix_user') || '{}');
    
    if (user.firstName) {
        const navActions = document.querySelector('.nav-actions');
        if (navActions) {
            navActions.innerHTML = `
                <span style="color: rgba(255, 255, 255, 0.8); margin-right: 1rem;">
                    Hi, ${user.firstName}!
                </span>
                <button class="nav-btn-secondary" onclick="loadMyTickets()">My Tickets</button>
                <button class="nav-btn-secondary" onclick="logoutUser()">Logout</button>
                <button class="nav-btn-primary" onclick="openChatbot()">Get Support</button>
            `;
        }
    }
}

/**
 * Show error message
 */
function showError(message) {
    const errorDiv = document.querySelector(`#${authState.currentScreen}Screen .auth-error`);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.add('active');
    }
}

/**
 * Show success message
 */
function showSuccess(message) {
    const successDiv = document.querySelector(`#${authState.currentScreen}Screen .auth-success`);
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.classList.add('active');
    }
}

/**
 * Clear error message
 */
function clearError() {
    document.querySelectorAll('.auth-error, .auth-success').forEach(el => {
        el.classList.remove('active');
    });
}

/**
 * Go back to previous screen
 */
function goBackToScreen(screenName) {
    showScreen(screenName);
    clearError();
}

/**
 * Initialize auth on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in and update UI
    const token = localStorage.getItem('campusfix_token');
    if (token) {
        verifyToken().then(valid => {
            if (valid) {
                updateNavbarForAuth();
                // Show chatbot section for authenticated users
                const chatbotSection = document.getElementById('chatbot-demo');
                if (chatbotSection) {
                    chatbotSection.style.display = 'block';
                }
            }
        });
    }
});

/**
 * Global openChatbot function with authentication check
 * This will be called by onclick handlers in HTML
 */
window.openChatbot = function() {
    const token = localStorage.getItem('campusfix_token');
    if (token) {
        // User is authenticated, show and scroll to chatbot
        const chatbotSection = document.getElementById('chatbot-demo');
        if (chatbotSection) {
            chatbotSection.style.display = 'block';
            
            const navbarHeight = 100;
            const targetPosition = chatbotSection.offsetTop - navbarHeight;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
            
            // Focus on chatbot input after scrolling
            setTimeout(() => {
                const chatbotInput = document.getElementById('chatbotInput');
                if (chatbotInput) {
                    chatbotInput.focus();
                }
            }, 800);
        }
    } else {
        // User not authenticated, show auth modal
        openAuthModal();
    }
};

// Make functions globally available
window.openAuthModal = openAuthModal;
window.closeAuthModal = closeAuthModal;
window.selectUserType = selectUserType;
window.continueFromUserType = continueFromUserType;
window.checkUser = checkUser;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.logoutUser = logoutUser;
window.goBackToScreen = goBackToScreen;
