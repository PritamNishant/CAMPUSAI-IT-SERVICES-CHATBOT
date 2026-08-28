# 🧪 CampusFix AI - Testing Guide

## Quick Start

### Terminal 1: Start Backend
```bash
cd "/Users/pritu_mac/Desktop/CAMPUS AI CHATBOT"
source venv/bin/activate
cd backend
python3 app.py
```

**Expected output:**
```
* Running on http://127.0.0.1:5001
* Running on http://192.168.1.46:5001
```

---

### Terminal 2: Start Frontend
```bash
cd "/Users/pritu_mac/Desktop/CAMPUS AI CHATBOT"
python3 -m http.server 8000
```

**Expected output:**
```
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```

---

### Browser: Open Chatbot
Open: **http://localhost:8000**

---

## Test Cases

### ✅ Test 1: Name Collection
**Action:** Type your name (e.g., "John")

**Expected:**
```
Bot: Nice to meet you, John! 😊

I'm here to help you with any IT issues you're experiencing on campus. 
What problem can I help you solve today?

[Wi-Fi Issues] [Login Problems] [Software Help] [Printer Issues]
```

---

### ✅ Test 2: Wi-Fi Issue
**Action:** Type "My campus Wi-Fi isn't working"

**Expected:** Specific Wi-Fi troubleshooting questions like:
- "Can other devices connect to Campus_WiFi?"
- "Can you see the network in your available networks?"
- "What building are you in?"

**NOT Expected:** Generic "provide more information"

**Backend Log Should Show:**
```
=== NEW MESSAGE RECEIVED ===
User message: My campus Wi-Fi isn't working
===========================

=== LLM API CALL ===
Temperature: 1.5
Last user message: My campus Wi-Fi isn't working...
===================

=== LLM RESPONSE ===
Response (first 150 chars): I'd be happy to help...
====================
```

---

### ✅ Test 3: Password Issue
**Action:** Type "I forgot my student portal password"

**Expected:** Different response about password reset:
- Should mention password.campus.edu
- Should ask which system
- Should provide reset instructions

**NOT:** Same response as Wi-Fi question

---

### ✅ Test 4: Printer Issue
**Action:** Type "My printer isn't working"

**Expected:** Printer-specific questions:
- Network connection status
- Printer name/location
- Print queue issues

**NOT:** Wi-Fi or password troubleshooting

---

### ✅ Test 5: Software Issue
**Action:** Type "I need help installing software"

**Expected:** Software installation questions:
- What software?
- What operating system?
- Any error messages?
- Mention software.campus.edu

---

### ✅ Test 6: Multi-Turn Conversation
**Conversation Flow:**

1. You: "My Wi-Fi isn't working"
2. Bot: [Asks diagnostic questions]
3. You: "I'm using a MacBook"
4. Bot: [Should respond in context of Wi-Fi + MacBook]
5. You: "I already restarted it"
6. Bot: [Should understand "it" = MacBook/Wi-Fi, suggest next steps]

**Expected:** Bot remembers the conversation context

**NOT:** Bot asks "what problem are you having?" again

---

## Backend Log Checklist

When testing, your Terminal 1 (backend) should show:

✅ **For each message:**
```
=== NEW MESSAGE RECEIVED ===
User message: [DIFFERENT MESSAGE EACH TIME]
Conversation ID: [ID or None]
===========================

=== LLM API CALL ===
Model: llama3-70b-8192
Temperature: 1.5
Number of messages in history: [INCREASING NUMBER]
Last user message: [MATCHES USER INPUT]
===================

=== LLM RESPONSE ===
Response (first 150 chars): [DIFFERENT EACH TIME]
====================
```

---

## Troubleshooting

### ❌ Problem: Same response for every message

**Check Terminal 1 logs:**

**If you see:**
```
Error: 401 Unauthorized
```
→ The fix didn't apply. Make sure you restarted the backend.

**If you DON'T see "LLM API CALL":**
→ LLM is not being called. Check for errors in backend.

**If "Last user message" is always the same:**
→ Frontend issue. Check browser console (F12).

---

### ❌ Problem: Backend won't start

**Error:** `ModuleNotFoundError: No module named 'flask'`
**Solution:**
```bash
source venv/bin/activate  # Must activate venv first!
cd backend
python3 app.py
```

**Error:** `Port 5001 is in use`
**Solution:**
```bash
# Find and kill process on port 5001
lsof -ti:5001 | xargs kill -9
# Then restart
python3 app.py
```

---

### ❌ Problem: Frontend shows "Cannot connect to backend"

**Check:**
1. Is backend running? (Terminal 1 should show "Running on...")
2. Is it on port 5001? (Check terminal output)
3. Open http://localhost:5001 - should show API info

**If backend is on different port:**
Edit `js/mockAgent.js`:
```javascript
const API_BASE_URL = 'http://localhost:5001/api';  // Change port here
```

---

### ❌ Problem: LLM returns errors

**Error in logs:** `401 Unauthorized from Groq API`
**Solution:** Check `.env` file has correct `GROQ_API_KEY`

**Error in logs:** `Timeout`
**Solution:** Check internet connection, Groq API might be slow

**Error in logs:** `Rate limit exceeded`
**Solution:** Wait a few minutes, Groq has rate limits

---

## Success Indicators

✅ **You'll know it's working when:**

1. **Different messages get different responses** ✓
2. **Backend logs show "LLM API CALL" for every message** ✓
3. **"Last user message" changes in logs** ✓
4. **Temperature shows as 1.5** ✓
5. **No 401 errors in logs** ✓
6. **Conversation history grows (message count increases)** ✓
7. **Multi-turn conversations maintain context** ✓

---

## Browser Console Debugging (Optional)

Press **F12** in Chrome → Console tab

**Type this to check state:**
```javascript
getConversationState()
```

**Should show:**
```javascript
{
  conversation_id: "some_id",
  user_name: "John",
  category: "wifi",
  diagnosticStep: 3,
  conversationHistory: [
    { role: "user", content: "My Wi-Fi isn't working" },
    { role: "assistant", content: "..." },
    // etc
  ]
}
```

**Check if messages are being sent:**
```javascript
// Open Network tab in F12
// Send a message
// Look for POST to http://localhost:5001/api/chat/send
// Click on it
// Check "Payload" tab - should show your message
// Check "Response" tab - should show LLM response
```

---

## Performance Notes

- **First message:** May take 2-5 seconds (LLM cold start)
- **Subsequent messages:** Should be 1-3 seconds
- **If slower:** Check internet connection or Groq API status

---

## Final Checklist

Before considering the bug fixed, verify:

- [ ] Started backend successfully (Terminal 1)
- [ ] Started frontend successfully (Terminal 2)
- [ ] Opened http://localhost:8000 in browser
- [ ] Name collection works
- [ ] Tested at least 4 different message types
- [ ] Each message got a DIFFERENT response
- [ ] Backend logs show LLM calls
- [ ] Backend logs show correct temperature (1.5)
- [ ] Multi-turn conversation works
- [ ] No errors in backend logs
- [ ] No errors in browser console

**If all checked:** 🎉 **BUG IS FIXED!**

---

**Last Updated:** 2026-08-21
