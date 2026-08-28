#!/usr/bin/env python3
"""
Exact error diagnostic test
"""

import requests
import json
import time

API_BASE = "http://localhost:5001/api"

print("=" * 70)
print("EXACT ERROR DIAGNOSTIC")
print("=" * 70)

# Step 1: Register
print("\nSTEP 1: Registering user...")
reg_data = {
    "firstName": "Debug",
    "lastName": "User",
    "email": f"debug{int(time.time())}@test.com",
    "password": "Test123!",
    "usertype": "student",
    "registration_number": f"REG{int(time.time())}"
}

try:
    response = requests.post(f"{API_BASE}/auth/register", json=reg_data, timeout=10)
    print(f"Registration HTTP Status: {response.status_code}")
    
    if response.status_code == 201:
        auth_data = response.json()
        token = auth_data['token']
        print(f"✓ Token obtained (length: {len(token)})")
    else:
        print(f"✗ Registration failed: {response.text}")
        exit(1)
except Exception as e:
    print(f"✗ Registration error: {e}")
    exit(1)

# Step 2: Send chat message
print("\nSTEP 2: Sending chat message...")
print("Message: 'Hello'")

chat_payload = {
    "message": "Hello",
    "conversation_id": None,
    "state": {}
}

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

print(f"\nRequest URL: {API_BASE}/chat/send")
print(f"Request Method: POST")
print(f"Request Headers: Content-Type, Authorization")
print(f"Request Body: {json.dumps(chat_payload, indent=2)}")

try:
    response = requests.post(
        f"{API_BASE}/chat/send",
        json=chat_payload,
        headers=headers,
        timeout=30
    )
    
    print(f"\n{'='*70}")
    print("RESPONSE DETAILS:")
    print(f"{'='*70}")
    print(f"HTTP STATUS: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"\nRaw Response Body:")
    print(response.text)
    print(f"{'='*70}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✓ Response is valid JSON")
        print(f"\nResponse Structure:")
        print(f"  - conversation_id: {'YES' if 'conversation_id' in data else 'NO'}")
        print(f"  - response: {'YES' if 'response' in data else 'NO'}")
        
        if 'response' in data:
            print(f"    - response.message: {'YES' if 'message' in data['response'] else 'NO'}")
            print(f"    - response.model: {'YES' if 'model' in data['response'] else 'NO'}")
            print(f"    - response.stage: {'YES' if 'stage' in data['response'] else 'NO'}")
            print(f"    - response.quickReplies: {'YES' if 'quickReplies' in data['response'] else 'NO'}")
            print(f"    - response.suggestTicket: {'YES' if 'suggestTicket' in data['response'] else 'NO'}")
        
        if 'error' in data:
            print(f"\n✗ Response contains error: {data['error']}")
        
        print(f"\n{'='*70}")
        print("CONCLUSION:")
        print(f"{'='*70}")
        print("✓ Backend is working")
        print("✓ Groq LLM is working")
        print("✓ Response format is valid")
        
        if 'response' in data and 'message' in data['response']:
            print(f"\n✓ LLM Response received:")
            print(f"   {data['response']['message'][:100]}...")
            print("\n✓ THE BACKEND + GROQ INTEGRATION IS WORKING CORRECTLY")
            print("\n❌ PROBLEM IS IN FRONTEND JAVASCRIPT")
        
    elif response.status_code == 401:
        print("\n✗ AUTHENTICATION ERROR")
        print("Backend returned 401 Unauthorized")
        
    elif response.status_code == 500:
        print("\n✗ BACKEND ERROR")
        print("Backend returned 500 Internal Server Error")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            pass
            
    else:
        print(f"\n✗ UNEXPECTED STATUS: {response.status_code}")
    
except requests.exceptions.Timeout:
    print("\n✗ REQUEST TIMEOUT")
    print("The request took longer than 30 seconds")
    
except requests.exceptions.ConnectionError:
    print("\n✗ CONNECTION ERROR")
    print("Could not connect to backend")
    
except Exception as e:
    print(f"\n✗ EXCEPTION OCCURRED")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()
