# test_login.py
"""
Test script for the login endpoint
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_login_success():
    """Test login with valid credentials"""
    print("=" * 60)
    print("TEST: Login with valid credentials")
    print("=" * 60)
    
    # This assumes you have a user registered with these credentials
    payload = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/user/login",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\n✓ Login successful!")
        else:
            print("\n✗ Login failed")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_login_failure():
    """Test login with invalid credentials"""
    print("\n" + "=" * 60)
    print("TEST: Login with invalid credentials")
    print("=" * 60)
    
    payload = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/user/login",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 401:
            print("\n✓ Correctly rejected invalid credentials")
        else:
            print("\n✗ Unexpected response")
            
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("LOGIN ENDPOINT TEST")
    print("█" * 60)
    print("\nNote: Make sure the FastAPI server is running!")
    print("Note: These tests assume you have a user registered.")
    print("      Use Swagger UI to register first if needed.\n")
    
    test_login_success()
    test_login_failure()
    
    print("\n" + "█" * 60)
    print("TESTS COMPLETE")
    print("█" * 60 + "\n")
