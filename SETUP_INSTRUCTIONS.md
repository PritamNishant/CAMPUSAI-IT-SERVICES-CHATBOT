# CampusFix AI - LLM Integration Setup Instructions

## ✅ COMPLETED

### 1. Groq SDK Installation
- ✓ Installed `groq==1.7.0` Python SDK
- ✓ Clean LLM service implementation created
- ✓ Connection test successful

### 2. LLM Service (`backend/llm_service.py`)
- ✓ Using official Groq Python SDK
- ✓ Reads `GROQ_API_KEY` from environment
- ✓ Reads `GROQ_MODEL` from environment (optional)
- ✓ Default model: `openai/gpt-oss-120b` (120B parameters, 500 tokens/sec)
- ✓ Temperature: 0.7 (as requested)
- ✓ Max tokens: 2048
- ✓ General-purpose system prompt (NOT IT-only)
- ✓ Conversation history: last 10 messages
- ✓ User personalization support

### 3. Flask Endpoints Updated
- ✓ `POST /api/chat/send` - simplified, uses new LLM service
- ✓ `GET /api/llm/test` - test LLM connection
- ✓ `GET /api/health` - shows MongoDB + LLM status
- ✓ `GET /` - updated API info

### 4. Removed/Cleaned
- ✓ Removed old complex IT-only workflow
- ✓ Removed category-based forcing
- ✓ Removed quick replies logic
- ✓ Removed workflow stages (tell_us, ai_diagnoses, etc.)
- ✓ Cleaned up endpoint responses

---

## ⚠️ IMPORTANT: MODEL CHANGE

### Why the Model Changed

**Original request:** `llama-3.3-70b-versatile`

**Current model:** `openai/gpt-oss-120b`

**Reason:** According to [Groq's official documentation](https://console.groq.com/docs/models), `llama-3.3-70b-versatile` is now an **Enterprise model** that requires "Contact Sales" access. It's not available on free developer plans.

### Available Models (as of August 2026)

**Production models (public access):**
- `openai/gpt-oss-120b` - 120B params, 500 t/s, $0.15 input / $0.60 output per 1M tokens ✅ **USING THIS**
- `openai/gpt-oss-20b` - 20B params, 1000 t/s, $0.075 input / $0.30 output per 1M tokens

**Enterprise models (require sales contact):**
- `llama-3.1-8b-instant` - 8B params, 560 t/s
- `llama-3.3-70b-versatile` - 70B params, 280 t/s

### If You Have Enterprise Access

If you have paid Groq Enterprise access and want to use `llama-3.3-70b-versatile`, add this to your `.env`:

```bash
GROQ_MODEL=llama-3.3-70b-versatile
```

Otherwise, the system will use `openai/gpt-oss-120b` by default, which is a powerful 120B parameter model.

---

## 🔧 PENDING: MongoDB Connection

### Issue

Your MongoDB URI contains special characters in the password that need URL encoding.

### Solution

**Option 1: Use the encoding helper script**

```bash
cd "/Users/pritu_mac/Desktop/CAMPUS AI CHATBOT"
source venv/bin/activate
python3 backend/encode_mongo_password.py
```

Then update your `.env` file with the encoded password.

**Option 2: Manual encoding**

1. Extract your password from `MONGO_URI` in `.env`
2. Use Python to encode it:

```python
from urllib.parse import quote_plus
password = "your_password_here"
encoded = quote_plus(password)
print(encoded)
```

3. Update `.env`:

```bash
MONGO_URI=mongodb+srv://username:ENCODED_PASSWORD@cluster.mongodb.net/campusfix_ai?retryWrites=true&w=majority
```

**Example:**
- Original password: `P@ssw0rd!#123`
- Encoded password: `P%40ssw0rd%21%23123`

---

## 🚀 STARTING THE APPLICATION

### Terminal 1: Backend (Flask)

```bash
cd "/Users/pritu_mac/Desktop/CAMPUS AI CHATBOT"
source venv/bin/activate
cd backend
python3 app.py
```

**Expected output:**
```
✓ MongoDB connected successfully
✓ Groq client initialized successfully
✓ Model: openai/gpt-oss-120b
✓ Temperature: 0.7
 * Running on http://0.0.0.0:5001
```

### Terminal 2: Frontend (HTTP Server)

```bash
cd "/Users/pritu_mac/Desktop/CAMPUS AI CHATBOT"
python3 -m http.server 8000
```

**Open browser:** http://localhost:8000

---

## ✅ TESTING CHECKLIST

### 1. Test LLM Connection (before starting backend)

```bash
cd "/Users/pritu_mac/Desktop/CAMPUS AI CHATBOT"
source venv/bin/activate
python3 backend/test_groq.py
```

Expected: `✓ Groq LLM is working correctly!`

### 2. Test Health Endpoint

```bash
curl http://localhost:5001/api/health
```

Expected:
```json
{
  "status": "ok",
  "mongodb": true,
  "llm_configured": true,
  "model": "openai/gpt-oss-120b"
}
```

### 3. Test LLM Endpoint

```bash
curl http://localhost:5001/api/llm/test
```

Expected:
```json
{
  "success": true,
  "model": "openai/gpt-oss-120b",
  "message": "LLM connection successful"
}
```

### 4. Test Chat Questions

After logging into the frontend, test these questions:

1. ✅ "Hello"
2. ✅ "What is polymorphism in Java?"
3. ✅ "Explain DBMS normalization."
4. ✅ "Write a C program for binary search."
5. ✅ "What is machine learning?"
6. ✅ "My Wi-Fi is not working."
7. ✅ "What is inheritance in Java?" → "Give me an example." (context test)

**Expected:** Different real LLM responses for each question. No forced IT workflow for non-IT questions.

---

## 📁 FILES MODIFIED

1. `backend/llm_service.py` - Complete rewrite using Groq SDK
2. `backend/app.py` - Updated `/api/chat/send`, added `/api/llm/test`, updated `/api/health`

## 📁 FILES CREATED

1. `backend/test_groq.py` - Standalone LLM connection test
2. `backend/encode_mongo_password.py` - MongoDB password encoder
3. `SETUP_INSTRUCTIONS.md` - This file

## 📁 FILES TO DELETE (optional cleanup)

1. `backend/llm_config.json` - No longer used
2. Any old LLM config files

---

## 🎯 DESIGN DECISIONS

### Temperature: 0.7
- Rejected: 1.5 (old config)
- Reason: User requested 0.7 for balanced creativity and consistency

### System Prompt: General-purpose
- Rejected: IT-only troubleshooting workflow
- Reason: User explicitly said "I do NOT want the LLM to be restricted only to IT troubleshooting"

### Conversation Memory: Last 10 messages
- Provides context without overwhelming the model
- Supports follow-up questions

### No Workflow Stages
- Rejected: Old tell_us → ai_diagnoses → find_solution → troubleshoot → check_result → human_support
- Reason: Forced every conversation into IT workflow

### No Quick Replies
- Rejected: Auto-generated button suggestions
- Reason: Simplifies frontend, lets user type naturally

---

## ❌ KNOWN ISSUES

### 1. MongoDB Connection
**Status:** Blocked - waiting for user to encode password

**Error:** `Username and password must be escaped according to RFC 3986`

**Solution:** Run `python3 backend/encode_mongo_password.py` and update `.env`

### 2. Old Config File
`backend/llm_config.json` still exists but is no longer used. Can be deleted.

---

## 📊 GROQ API PRICING (as of August 2026)

**Model:** `openai/gpt-oss-120b`
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Speed: 500 tokens/second
- Context window: 131,072 tokens
- Rate limits (free tier): 250K TPM, 1K RPM

---

## 🔒 SECURITY NOTES

- ✅ API keys stored in `.env` (not in code)
- ✅ `.env` should be in `.gitignore`
- ✅ API key never exposed to frontend
- ✅ JWT authentication still in place
- ✅ No credentials printed in logs

---

## 📞 NEXT STEPS

1. **Fix MongoDB URI** by encoding the password
2. **Start backend** and verify both MongoDB and Groq connect
3. **Start frontend** at http://localhost:8000
4. **Login/Register** through the UI
5. **Test all 7 questions** listed above
6. **Verify conversation memory** works (context retained)

---

## 🐛 DEBUGGING

### LLM not working?
```bash
python3 backend/test_groq.py
```

### MongoDB not connecting?
```bash
python3 backend/encode_mongo_password.py
```

### Backend errors?
Check terminal output for detailed error messages with stack traces.

### Frontend not loading?
Make sure you're accessing `http://localhost:8000` (not `file://`)

---

**Created:** August 21, 2026
**Status:** LLM integration complete, MongoDB connection pending user action
