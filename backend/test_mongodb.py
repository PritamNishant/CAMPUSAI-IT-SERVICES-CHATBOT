#!/usr/bin/env python3
"""
Test MongoDB connection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("Testing MongoDB Connection")
print("=" * 60)
print()

# Check if MONGO_URI exists
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    print("✗ MONGO_URI not found in .env file")
    sys.exit(1)

print("✓ MONGO_URI found in .env")

# Check URI format
if not MONGO_URI.startswith('mongodb'):
    print("✗ MONGO_URI does not start with 'mongodb://' or 'mongodb+srv://'")
    sys.exit(1)

protocol = MONGO_URI.split('://')[0]
print(f"✓ Protocol: {protocol}")
print()

# Try to connect
print("Attempting connection...")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    
    # Test with ping command
    client.admin.command('ping')
    
    print("✓ MongoDB connection: SUCCESS")
    print()
    
    # Get database info
    db = client['campusfix_ai']
    collections = db.list_collection_names()
    
    print(f"✓ Database: campusfix_ai")
    print(f"✓ Collections found: {len(collections)}")
    if collections:
        print(f"  Collections: {', '.join(collections[:5])}")
    print()
    
    print("=" * 60)
    print("✓ MongoDB is working correctly!")
    print("=" * 60)
    
except Exception as e:
    error_msg = str(e)
    print("✗ MongoDB connection: FAILED")
    print()
    print("Error:")
    
    # Sanitize error message to avoid exposing credentials
    if '@' in error_msg and 'mongodb' in error_msg.lower():
        # Remove potential credentials from error message
        sanitized = error_msg
        import re
        sanitized = re.sub(r'mongodb(?:\+srv)?://[^@]+@', 'mongodb://***:***@', sanitized)
        print(f"  {sanitized}")
    else:
        print(f"  {error_msg}")
    
    print()
    
    if 'escaped according to RFC 3986' in error_msg:
        print("Issue: Password contains special characters")
        print("Solution: Run 'python3 backend/encode_mongo_password.py'")
    elif 'authentication failed' in error_msg.lower():
        print("Issue: Invalid username or password")
    elif 'network' in error_msg.lower() or 'timeout' in error_msg.lower():
        print("Issue: Network connectivity or firewall")
    elif 'name or service not known' in error_msg.lower():
        print("Issue: Invalid cluster address")
    
    sys.exit(1)
