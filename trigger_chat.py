import requests
import json

url = "http://127.0.0.1:8000/sakhi/chat"
payload = {
    "user_id": "test_user",
    "message": "What is the cost of IVF?",
    "language": "en"
}
headers = {"Content-Type": "application/json"}

import random
import string

def random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

# Register user first
register_url = "http://127.0.0.1:8000/user/register"
reg_payload = {
    "name": "Test User",
    "email": f"{random_string()}@example.com",
    "password": "password123",
    "phone_number": f"9{random.randint(100000000, 999999999)}"
}
try:
    with open("trigger_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Registering user at {register_url}...\n")
        reg_resp = requests.post(register_url, json=reg_payload)
        f.write(f"Registration Status: {reg_resp.status_code}\n")
        
        if reg_resp.status_code == 200:
            user_id = reg_resp.json().get("user_id")
            f.write(f"Registered user_id: {user_id}\n")
            
            # Now chat
            chat_payload = {
                "user_id": user_id,
                "message": "What is the cost of IVF?",
                "language": "en"
            }
            f.write(f"Sending chat request to {url}...\n")
            response = requests.post(url, json=chat_payload, headers=headers)
            f.write(f"Chat Status Code: {response.status_code}\n")
            f.write("Response Body:\n")
            f.write(json.dumps(response.json(), indent=2))
        else:
            f.write(f"Registration failed: {reg_resp.text}\n")

except Exception as e:
    with open("trigger_result.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
