#!/usr/bin/env python3
"""
Helper script to encode MongoDB password for URI
Run this to properly encode your MongoDB password
"""

from urllib.parse import quote_plus
import sys

print("=" * 60)
print("MongoDB Password Encoder")
print("=" * 60)
print()

if len(sys.argv) > 1:
    password = sys.argv[1]
else:
    password = input("Enter your MongoDB password: ")

encoded = quote_plus(password)

print()
print("Encoded password:")
print(encoded)
print()
print("Update your .env file MONGO_URI with this encoded password")
print("Example:")
print(f"MONGO_URI=mongodb+srv://username:{encoded}@cluster.mongodb.net/database")
print()
