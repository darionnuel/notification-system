"""Test script for API Gateway"""
import requests
import json

url = "http://localhost:3000/api/notifications"

headers = {
    "Authorization": "Bearer supersecretapikey123",
    "Content-Type": "application/json"
}

payload = {
    "type": "email",
    "user_id": "user_123",
    "template_code": "welcome_email",
    "variables": {
        "user_name": "John Doe",
        "user_email": "john.doe@example.com",
        "app_name": "GatewayApp",
        "link": "https://example.com"
    },
    "priority": 8
}

print("🚀 Sending notification request to API Gateway...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📦 Response:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to API Gateway at http://localhost:3000")
    print("   Make sure the API Gateway is running")
except Exception as e:
    print(f"❌ ERROR: {e}")
