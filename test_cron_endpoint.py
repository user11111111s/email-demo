"""
Test script for cron birthday endpoint
Run this after starting the Flask app with: python run.py
"""

import requests
import os

# Load environment to get CRON_SECRET
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "http://127.0.0.1:5000"
CRON_SECRET = os.getenv("CRON_SECRET")

print("🧪 Testing Cron Birthday Endpoint\n")
print("=" * 60)

# Test 1: Unauthorized access (no key)
print("\n1️⃣  Test: Unauthorized access (no key)")
response = requests.get(f"{BASE_URL}/cron/birthday-check")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 403, "Should return 403 Forbidden"
print("   ✅ PASSED")

# Test 2: Wrong secret
print("\n2️⃣  Test: Wrong secret key")
response = requests.get(f"{BASE_URL}/cron/birthday-check?key=wrong_key")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 403, "Should return 403 Forbidden"
print("   ✅ PASSED")

# Test 3: Correct secret
print("\n3️⃣  Test: Authorized access (correct key)")
response = requests.get(f"{BASE_URL}/cron/birthday-check?key={CRON_SECRET}")
print(f"   Status: {response.status_code}")
print(f"   Response: {response.json()}")
assert response.status_code == 200, "Should return 200 OK"
assert response.json()['status'] == 'ok', "Should have status 'ok'"
print("   ✅ PASSED")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("\n💡 Check the Flask terminal for birthday check logs")
