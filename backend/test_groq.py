#!/usr/bin/env python3
"""
Test Groq LLM connection standalone
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("Testing Groq LLM Connection")
print("=" * 60)
print()

# Check API key
api_key = os.getenv('GROQ_API_KEY')
if not api_key:
    print("✗ GROQ_API_KEY not found in .env file")
    sys.exit(1)

print(f"✓ GROQ_API_KEY found (length: {len(api_key)})")

# Check model
model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
print(f"✓ Model: {model}")
print()

# Try to import and initialize Groq
try:
    from groq import Groq
    print("✓ Groq SDK imported successfully")
except ImportError as e:
    print(f"✗ Failed to import Groq SDK: {e}")
    print("  Install with: pip install groq")
    sys.exit(1)

# Initialize client
try:
    client = Groq(api_key=api_key)
    print("✓ Groq client initialized")
except Exception as e:
    print(f"✗ Failed to initialize Groq client: {e}")
    sys.exit(1)

# Test API call
print()
print("Testing API call...")
try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from Groq!' if you can read this."}
        ],
        temperature=0.7,
        max_tokens=100
    )
    
    message = response.choices[0].message.content
    usage = response.usage
    
    print("✓ API call successful!")
    print()
    print("Response:")
    print(f"  {message}")
    print()
    print("Usage:")
    print(f"  Prompt tokens: {usage.prompt_tokens}")
    print(f"  Completion tokens: {usage.completion_tokens}")
    print(f"  Total tokens: {usage.total_tokens}")
    print()
    print("=" * 60)
    print("✓ Groq LLM is working correctly!")
    print("=" * 60)
    
except Exception as e:
    print(f"✗ API call failed: {e}")
    print()
    print("Possible issues:")
    print("  1. Invalid API key")
    print("  2. Network connectivity")
    print("  3. Model not available")
    print("  4. Rate limit exceeded")
    sys.exit(1)
