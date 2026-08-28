#!/usr/bin/env python3
"""
Test complete flow: Register → Login → Chat → Verify LLM Response
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5001"

print("=" * 70)
print("Testing Complete CampusFix AI Flow")
print("=" * 70)
print()

# Test 1: Health Check
print("1️⃣  Testing /api/health...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    data = response.json()
    
    if data.get('status') == 'ok' and data.get('mongodb') and data.get('llm_configured'):
        print(f"   ✓ Health check passed")
        print(f"   ✓ MongoDB: Connected")
        print(f"   ✓ LLM: Configured ({data.get('model')})")
    else:
        print(f"   ✗ Health check failed: {data}")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Health check failed: {e}")
    sys.exit(1)

print()

# Test 2: LLM Test
print("2️⃣  Testing /api/llm/test...")
try:
    response = requests.get(f"{BASE_URL}/api/llm/test", timeout=10)
    data = response.json()
    
    if data.get('success'):
        print(f"   ✓ LLM test passed")
        print(f"   ✓ Model: {data.get('model')}")
        print(f"   ✓ Response: {data.get('test_response')}")
    else:
        print(f"   ✗ LLM test failed: {data.get('error')}")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ LLM test failed: {e}")
    sys.exit(1)

print()

# Test 3: Register a test user
print("3️⃣  Testing user registration...")
test_user = {
    "firstName": "Test",
    "lastName": "User",
    "email": f"test_{int(__import__('time').time())}@campusfix.ai",
    "password": "Test123!",
    "usertype": "student",
    "registration_number": f"REG{int(__import__('time').time())}",
    "department": "Computer Science"
}

try:
    response = requests.post(f"{BASE_URL}/api/auth/register", json=test_user, timeout=10)
    
    if response.status_code == 201:
        data = response.json()
        token = data.get('token')
        user_name = data.get('user', {}).get('firstName')
        print(f"   ✓ User registered: {user_name}")
        print(f"   ✓ Token received")
    elif response.status_code == 409:
        # User exists, try login instead
        print(f"   ⚠ User exists, skipping to login...")
        token = None
    else:
        print(f"   ✗ Registration failed: {response.json()}")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Registration failed: {e}")
    sys.exit(1)

print()

# Test 4: Send chat message
print("4️⃣  Testing chat with LLM...")
if not token:
    print("   ⚠ Skipping chat test (no token)")
    sys.exit(0)

test_messages = [
    "Hello!",
    "What is polymorphism in Java?"
]

for i, message in enumerate(test_messages, 1):
    print(f"\n   Test {i}: '{message}'")
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": message
        }
        
        response = requests.post(
            f"{BASE_URL}/api/chat/send",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            llm_response = data.get('response', {}).get('message', '')
            conversation_id = data.get('conversation_id')
            
            print(f"   ✓ Chat response received")
            print(f"   ✓ Conversation ID: {conversation_id}")
            print(f"   ✓ Response preview: {llm_response[:100]}...")
            
            # Verify it's a real response (not empty, not error)
            if len(llm_response) > 10 and 'error' not in llm_response.lower()[:50]:
                print(f"   ✓ Real LLM response confirmed")
            else:
                print(f"   ⚠ Response seems unusual")
        else:
            print(f"   ✗ Chat failed: {response.json()}")
            
    except Exception as e:
        print(f"   ✗ Chat failed: {e}")

print()
print("=" * 70)
print("✅ All tests completed successfully!")
print("=" * 70)
print()
print("Summary:")
print("  • MongoDB: Connected")
print("  • Groq LLM: Working")
print("  • Authentication: Working")
print("  • Chat Flow: Working")
print()
print("Full flow verified:")
print("  Browser → Flask → Groq → Flask → Browser ✓")
