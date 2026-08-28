# CampusFix AI - Backend API

Flask-based REST API for CampusFix AI campus IT support system with MongoDB integration.

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python init_db.py
```

This will:
- Create all required collections
- Set up indexes for optimal performance
- Insert sample knowledge base articles

### 3. Run the Backend

```bash
python app.py
```

Server will start at: **http://localhost:5000**

---

## 📊 Database Schema

### Collections

#### 1. **users**
```javascript
{
  _id: ObjectId,
  username: String,
  registration_number: String (unique),  // Student ID or Employee ID
  email: String (unique),
  usertype: String,  // "student" or "employee"
  password: String (hashed),
  phone: String,
  department: String,
  created_at: DateTime,
  updated_at: DateTime,
  last_login: DateTime,
  is_active: Boolean
}
```

**Indexes:**
- registration_number (unique)
- email (unique)
- usertype
- created_at

#### 2. **conversations**
```javascript
{
  _id: ObjectId,
  user_id: String,
  registration_number: String,
  started_at: DateTime,
  updated_at: DateTime,
  messages: [
    {
      role: String,  // "user" or "assistant"
      content: String,
      timestamp: DateTime
    }
  ],
  state: Object,  // Conversation state from frontend
  status: String,  // "active", "ticket_created", "resolved"
  ticket_id: String  // If ticket was created
}
```

**Indexes:**
- user_id
- registration_number
- updated_at
- status

#### 3. **tickets**
```javascript
{
  _id: ObjectId,
  ticket_id: String (unique),  // Format: IT-YYYY-00001
  user_id: String,
  registration_number: String,
  username: String,
  email: String,
  usertype: String,
  issue: String,
  category: String,  // wifi, login, software, printer, hardware, other
  description: String,
  priority: String,  // low, medium, high, urgent
  location: String,
  department: String,  // Auto-assigned based on category
  status: String,  // open, in_progress, resolved, closed
  assigned_to: String,
  conversation_id: ObjectId,
  created_at: DateTime,
  updated_at: DateTime,
  resolved_at: DateTime,
  notes: [
    {
      author: String,
      content: String,
      timestamp: DateTime
    }
  ]
}
```

**Indexes:**
- ticket_id (unique)
- user_id
- registration_number
- status
- priority
- category
- department
- created_at

#### 4. **knowledge_base**
```javascript
{
  _id: ObjectId,
  title: String,
  category: String,
  tags: [String],
  content: String,
  views: Number,
  helpful_count: Number,
  created_at: DateTime,
  updated_at: DateTime
}
```

**Indexes:**
- category
- tags
- Full-text index on title and content

---

## 🔌 API Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "John Doe",
  "registration_number": "STU2024001",  // or EMP2024001
  "email": "john.doe@campus.edu",
  "password": "SecurePass123!",
  "usertype": "student",  // or "employee"
  "phone": "+1234567890",
  "department": "Computer Science"
}

Response 201:
{
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "...",
    "username": "John Doe",
    "registration_number": "STU2024001",
    "email": "john.doe@campus.edu",
    "usertype": "student"
  }
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "registration_number": "STU2024001",
  "password": "SecurePass123!"
}

Response 200:
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <token>

Response 200:
{
  "user": { ... }
}
```

---

### Chat

#### Send Message
```http
POST /api/chat/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "My Wi-Fi is not working",
  "conversation_id": "...",  // Optional, omit for new conversation
  "state": { ... }  // Conversation state
}

Response 200:
{
  "conversation_id": "...",
  "response": {
    "message": "I can help with that...",
    "quickReplies": ["Yes", "No"],
    "suggestTicket": false
  }
}
```

#### Get Chat History
```http
GET /api/chat/history
Authorization: Bearer <token>

Response 200:
{
  "conversations": [
    {
      "_id": "...",
      "messages": [...],
      "started_at": "...",
      "status": "active"
    }
  ]
}
```

---

### Tickets

#### Create Ticket
```http
POST /api/tickets/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "issue": "Wi-Fi Connection Failure",
  "category": "wifi",
  "description": "Cannot connect to campus Wi-Fi...",
  "priority": "high",
  "location": "Library Building, Floor 3",
  "conversation_id": "..."  // Optional
}

Response 201:
{
  "message": "Ticket created successfully",
  "ticket": {
    "id": "...",
    "ticket_id": "IT-2026-00001",
    "status": "open",
    "department": "Network Support",
    "priority": "high",
    "created_at": "..."
  }
}
```

#### Get My Tickets
```http
GET /api/tickets/my-tickets
Authorization: Bearer <token>

Response 200:
{
  "tickets": [
    {
      "_id": "...",
      "ticket_id": "IT-2026-00001",
      "issue": "...",
      "status": "open",
      "created_at": "..."
    }
  ]
}
```

#### Get Ticket Details
```http
GET /api/tickets/<ticket_id>
Authorization: Bearer <token>

Response 200:
{
  "ticket": {
    "ticket_id": "IT-2026-00001",
    "issue": "...",
    "description": "...",
    "status": "open",
    "priority": "high",
    ...
  }
}
```

---

### Health Check

```http
GET /api/health

Response 200:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "..."
}
```

---

## 🔒 Authentication

All protected endpoints require JWT token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens expire after 7 days.

---

## 📝 User Types

### Student
- Registration number format: `STU` prefix
- Example: `STU2024001`, `STU2025042`

### Employee
- Registration number format: `EMP` prefix  
- Example: `EMP2024001`, `EMP2025015`

---

## 🎫 Ticket System

### Categories and Department Routing

| Category | Department |
|----------|-----------|
| wifi | Network Support |
| login | Account Services |
| software | Software Support |
| printer | Hardware Support |
| hardware | Hardware Support |
| other | General IT Support |

### Priority Levels
- `low` - Not urgent, can wait
- `medium` - Normal priority (default)
- `high` - Important, needs attention soon
- `urgent` - Critical, immediate attention required

### Ticket Status Flow
```
open → in_progress → resolved → closed
```

---

## 🔧 Environment Variables

Create `.env` file in project root:

```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
SECRET_KEY=your-secret-key-here
```

---

## 🧪 Testing

### Test with cURL

**Register:**
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Test User",
    "registration_number": "STU2024999",
    "email": "test@campus.edu",
    "password": "Test123!",
    "usertype": "student"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number": "STU2024999",
    "password": "Test123!"
  }'
```

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

---

## 🚀 Deployment

### Production Setup

1. Set environment to production:
```python
app.config.from_object('config.ProductionConfig')
```

2. Use production WSGI server:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. Set strong SECRET_KEY in production .env

4. Enable HTTPS

5. Configure CORS for your frontend domain

---

## 📊 Performance

- **Database Indexes**: Optimized queries with 15+ indexes
- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure authentication with 7-day expiration
- **Connection Pooling**: MongoDB driver handles connection pooling

---

## 🔐 Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ CORS protection
- ✅ Input validation
- ✅ SQL injection prevention (NoSQL)
- ✅ Unique constraints on critical fields
- ✅ Token expiration

---

## 📈 Next Steps

### TODO: LLM Integration

Replace mock response in `/api/chat/send` with actual LLM:

```python
# Add to requirements.txt
# openai==1.3.0
# langchain==0.1.0

from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are CampusFix AI..."},
        {"role": "user", "content": user_message}
    ]
)

bot_response = response.choices[0].message.content
```

---

## 🆘 Troubleshooting

**MongoDB Connection Error:**
- Check MONGO_URI in .env file
- Ensure IP is whitelisted in MongoDB Atlas
- Verify network connectivity

**Import Errors:**
- Reinstall dependencies: `pip install -r requirements.txt`
- Use virtual environment

**Port Already in Use:**
- Change port in app.py: `app.run(port=5001)`

---

## 📞 Support

For issues or questions:
- Check logs in terminal
- Verify .env configuration
- Test with health check endpoint

---

**Backend Ready! 🚀**

Connect your frontend and start building intelligent IT support!
