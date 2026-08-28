# 🔌 Backend Integration Guide

Complete guide to connect your CampusFix AI frontend to the Flask backend.

---

## 📊 What's Included

### Backend Features ✅
- ✅ **User Authentication** (Register/Login with JWT)
- ✅ **MongoDB Integration** (4 collections with indexes)
- ✅ **Chat History Storage** (Persistent conversations)
- ✅ **Ticket Management** (Create and track tickets)
- ✅ **Knowledge Base** (Sample IT support articles)
- ✅ **Department Routing** (Auto-assign tickets)
- ✅ **RESTful API** (Clean, documented endpoints)

### Database Schema
1. **users** - Student/Employee accounts
2. **conversations** - Chat history
3. **tickets** - Support tickets
4. **knowledge_base** - IT documentation

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Or use the setup script:**
```bash
cd backend
chmod +x setup.sh
./setup.sh
```

### Step 2: Initialize Database

```bash
python3 init_db.py
```

This creates collections, indexes, and sample data.

### Step 3: Start Backend Server

```bash
python3 app.py
```

Server runs at: **http://localhost:5000**

---

## 🔧 Frontend Integration

### Update `js/mockAgent.js`

Replace the mock agent with real API calls:

```javascript
// At the top of mockAgent.js
const API_BASE_URL = 'http://localhost:5000/api';
let authToken = localStorage.getItem('campusfix_token');

/**
 * Send message to real backend API
 */
async function sendMessageToAgent(message) {
    try {
        const response = await fetch(`${API_BASE_URL}/chat/send`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                message: message,
                state: conversationState,
                conversation_id: conversationState.conversation_id
            })
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // Redirect to login
                window.location.href = '/login.html';
                return;
            }
            throw new Error('API request failed');
        }
        
        const data = await response.json();
        
        // Update conversation ID
        if (data.conversation_id) {
            conversationState.conversation_id = data.conversation_id;
        }
        
        return data.response;
        
    } catch (error) {
        console.error('Error:', error);
        return {
            message: "I'm having trouble connecting to the server. Please try again.",
            quickReplies: null,
            suggestTicket: false
        };
    }
}
```

### Update `js/tickets.js`

Replace mock ticket creation with real API:

```javascript
/**
 * Handle ticket form submission - REAL API VERSION
 */
async function handleTicketSubmission(e) {
    e.preventDefault();
    
    const authToken = localStorage.getItem('campusfix_token');
    if (!authToken) {
        alert('Please login to create a ticket');
        window.location.href = '/login.html';
        return;
    }
    
    const formData = {
        issue: document.getElementById('ticketIssue').value,
        category: document.getElementById('ticketCategory').value,
        description: document.getElementById('ticketDescription').value,
        priority: document.getElementById('ticketPriority').value,
        location: document.getElementById('ticketLocation').value,
        conversation_id: getConversationState()?.conversation_id
    };
    
    try {
        const response = await fetch('http://localhost:5000/api/tickets/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to create ticket');
        }
        
        const data = await response.json();
        
        // Close ticket modal
        closeTicketModal();
        
        // Show success modal with real ticket data
        showTicketSuccessModal(data.ticket);
        
    } catch (error) {
        console.error('Error creating ticket:', error);
        alert('Failed to create ticket. Please try again.');
    }
}
```

---

## 🔐 Add Authentication Pages

### Create `login.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - CampusFix AI</title>
    <link rel="stylesheet" href="css/global.css">
    <link rel="stylesheet" href="css/auth.css">
</head>
<body>
    <div class="auth-container">
        <div class="auth-card">
            <img src="assets/logo.svg" alt="CampusFix AI" class="auth-logo">
            <h1>Welcome Back</h1>
            <p>Sign in to access IT support</p>
            
            <form id="loginForm" class="auth-form">
                <div class="form-group">
                    <label>Registration Number / Employee ID</label>
                    <input type="text" id="regNumber" required 
                           placeholder="STU2024001 or EMP2024001">
                </div>
                
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" required>
                </div>
                
                <button type="submit" class="btn-primary btn-full">
                    Sign In
                </button>
            </form>
            
            <p class="auth-footer">
                Don't have an account? 
                <a href="register.html">Register here</a>
            </p>
        </div>
    </div>
    
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                registration_number: document.getElementById('regNumber').value,
                password: document.getElementById('password').value
            };
            
            try {
                const response = await fetch('http://localhost:5000/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    localStorage.setItem('campusfix_token', result.token);
                    localStorage.setItem('campusfix_user', JSON.stringify(result.user));
                    window.location.href = 'index.html';
                } else {
                    alert(result.error || 'Login failed');
                }
            } catch (error) {
                alert('Connection error. Please try again.');
            }
        });
    </script>
</body>
</html>
```

### Create `register.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register - CampusFix AI</title>
    <link rel="stylesheet" href="css/global.css">
    <link rel="stylesheet" href="css/auth.css">
</head>
<body>
    <div class="auth-container">
        <div class="auth-card">
            <img src="assets/logo.svg" alt="CampusFix AI" class="auth-logo">
            <h1>Create Account</h1>
            <p>Get started with CampusFix AI</p>
            
            <form id="registerForm" class="auth-form">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" id="username" required>
                </div>
                
                <div class="form-group">
                    <label>Registration Number / Employee ID</label>
                    <input type="text" id="regNumber" required 
                           placeholder="STU2024001 or EMP2024001">
                </div>
                
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="email" required>
                </div>
                
                <div class="form-group">
                    <label>User Type</label>
                    <select id="usertype" required>
                        <option value="student">Student</option>
                        <option value="employee">Employee</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="password" required 
                           minlength="8">
                </div>
                
                <button type="submit" class="btn-primary btn-full">
                    Create Account
                </button>
            </form>
            
            <p class="auth-footer">
                Already have an account? 
                <a href="login.html">Sign in</a>
            </p>
        </div>
    </div>
    
    <script>
        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                username: document.getElementById('username').value,
                registration_number: document.getElementById('regNumber').value,
                email: document.getElementById('email').value,
                usertype: document.getElementById('usertype').value,
                password: document.getElementById('password').value
            };
            
            try {
                const response = await fetch('http://localhost:5000/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    localStorage.setItem('campusfix_token', result.token);
                    localStorage.setItem('campusfix_user', JSON.stringify(result.user));
                    alert('Registration successful!');
                    window.location.href = 'index.html';
                } else {
                    alert(result.error || 'Registration failed');
                }
            } catch (error) {
                alert('Connection error. Please try again.');
            }
        });
    </script>
</body>
</html>
```

---

## 🎨 Add Auth Styles

Create `css/auth.css`:

```css
.auth-container {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background: var(--color-bg-darker);
}

.auth-card {
    background: rgba(30, 41, 59, 0.5);
    backdrop-filter: blur(20px);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-xl);
    padding: 3rem;
    max-width: 450px;
    width: 100%;
    box-shadow: var(--shadow-xl);
}

.auth-logo {
    width: 80px;
    height: 80px;
    margin: 0 auto 2rem;
    display: block;
}

.auth-card h1 {
    text-align: center;
    margin-bottom: 0.5rem;
    font-size: 2rem;
}

.auth-card > p {
    text-align: center;
    color: var(--color-text-secondary);
    margin-bottom: 2rem;
}

.auth-form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
}

.btn-full {
    width: 100%;
}

.auth-footer {
    text-align: center;
    margin-top: 2rem;
    color: var(--color-text-secondary);
}

.auth-footer a {
    color: var(--color-primary);
    font-weight: 600;
}
```

---

## 🔄 Update Navigation

Add authentication to navigation in `index.html`:

```javascript
// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem('campusfix_token');
    const user = JSON.parse(localStorage.getItem('campusfix_user') || '{}');
    
    if (!token) {
        // Redirect to login for protected actions
        return false;
    }
    
    // Update navigation with user info
    const navActions = document.querySelector('.nav-actions');
    if (navActions && user.username) {
        navActions.innerHTML = `
            <span class="user-greeting">Hi, ${user.username}</span>
            <button class="nav-btn-secondary" onclick="logout()">Logout</button>
            <button class="nav-btn-primary" onclick="openChatbot()">Get Support</button>
        `;
    }
    
    return true;
}

function logout() {
    localStorage.removeItem('campusfix_token');
    localStorage.removeItem('campusfix_user');
    window.location.href = 'login.html';
}

// Call on page load
document.addEventListener('DOMContentLoaded', checkAuth);
```

---

## ✅ Testing Checklist

### Backend Tests

```bash
# 1. Health check
curl http://localhost:5000/api/health

# 2. Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Test Student",
    "registration_number": "STU2024999",
    "email": "test@campus.edu",
    "password": "Test123!",
    "usertype": "student"
  }'

# 3. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number": "STU2024999",
    "password": "Test123!"
  }'
```

### Integration Tests

1. ✅ Register new account
2. ✅ Login with credentials
3. ✅ Chat sends to backend
4. ✅ Ticket creates in MongoDB
5. ✅ View ticket history
6. ✅ Logout works

---

## 📊 Project Structure After Integration

```
CAMPUS AI CHATBOT/
├── backend/
│   ├── app.py              ← Flask API
│   ├── config.py           ← Configuration
│   ├── init_db.py          ← Database setup
│   ├── requirements.txt    ← Dependencies
│   ├── setup.sh            ← Setup script
│   └── README.md           ← Backend docs
├── index.html              ← Landing page
├── login.html              ← NEW: Login page
├── register.html           ← NEW: Register page
├── css/
│   ├── auth.css            ← NEW: Auth styles
│   └── ...
├── js/
│   ├── mockAgent.js        ← UPDATE: Connect to API
│   ├── tickets.js          ← UPDATE: Real tickets
│   └── ...
└── .env                    ← MongoDB URI + SECRET_KEY
```

---

## 🚀 Deployment

### Development
```bash
# Terminal 1: Backend
cd backend
python3 app.py

# Terminal 2: Frontend
python3 -m http.server 8000
```

### Production

**Backend (Heroku/Railway/Render):**
```bash
# Add Procfile
web: gunicorn app:app

# Deploy
git push heroku main
```

**Frontend (Netlify/Vercel):**
- Update API_BASE_URL to production URL
- Deploy frontend files

---

## 🎉 You're Done!

Your CampusFix AI is now a **full-stack application** with:

✅ MongoDB database
✅ Flask REST API  
✅ JWT authentication
✅ Real chat persistence
✅ Ticket management
✅ User accounts

**Next: Add LLM integration to make chat intelligent!**
