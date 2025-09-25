#!/usr/bin/env python3
"""
Fashion App API Test Script

This script tests the authentication and user management APIs.
Run this script while the Django server is running to test all endpoints.
"""

import requests
import json
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:8000/api"
headers = {'Content-Type': 'application/json'}

def print_response(response, title):
    """Helper function to print API responses"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    try:
        pprint(response.json())
    except:
        print(response.text)
    print(f"{'='*50}\n")

def test_api_endpoints():
    """Test all available API endpoints"""
    
    print("🚀 Starting Fashion App API Tests...")
    
    # Test 1: API Root
    print("\n1. Testing API Root...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_response(response, "API Root")
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running! Please start the server with:")
        print("   uv run uvicorn fashion_app.asgi:application --reload --host 0.0.0.0 --port 8000")
        return
    
    # Test 2: User Registration
    print("\n2. Testing User Registration...")
    register_data = {
        "username": "testdesigner",
        "email": "designer@test.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "Designer",
        "phone": "1234567890",
        "is_Designer": True,
        "is_Customer": False
    }
    
    response = requests.post(f"{BASE_URL}/auth/users/", 
                           data=json.dumps(register_data), 
                           headers=headers)
    print_response(response, "User Registration (Designer)")
    
    # Register a customer too
    customer_data = {
        "username": "testcustomer",
        "email": "customer@test.com",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "Customer",
        "phone": "0987654321",
        "is_Designer": False,
        "is_Customer": True
    }
    
    response = requests.post(f"{BASE_URL}/auth/users/", 
                           data=json.dumps(customer_data), 
                           headers=headers)
    print_response(response, "User Registration (Customer)")
    
    # Test 3: User Login (JWT)
    print("\n3. Testing User Login...")
    login_data = {
        "username": "testdesigner",  # Djoser uses username for login by default
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", 
                           data=json.dumps(login_data), 
                           headers=headers)
    print_response(response, "User Login")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access')
        
        if access_token:
            # Update headers with authentication
            auth_headers = headers.copy()
            auth_headers['Authorization'] = f'Bearer {access_token}'
            
            # Test 4: Get Current User Profile
            print("\n4. Testing User Profile Retrieval...")
            response = requests.get(f"{BASE_URL}/auth/users/me/", 
                                  headers=auth_headers)
            print_response(response, "Current User Profile")
            
            # Test 5: User Dashboard
            print("\n5. Testing User Dashboard...")
            response = requests.get(f"{BASE_URL}/users/dashboard/", 
                                  headers=auth_headers)
            print_response(response, "User Dashboard")
            
            # Test 6: Get Customers List (for designers)
            print("\n6. Testing Customers List (Designer View)...")
            response = requests.get(f"{BASE_URL}/users/customers/", 
                                  headers=auth_headers)
            print_response(response, "Customers List")
    
    # Test 7: Login as Customer and test customer endpoints
    print("\n7. Testing Customer Login...")
    customer_login = {
        "username": "testcustomer",  # Djoser uses username for login by default
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", 
                           data=json.dumps(customer_login), 
                           headers=headers)
    print_response(response, "Customer Login")
    
    if response.status_code == 200:
        token_data = response.json()
        customer_token = token_data.get('access')
        
        if customer_token:
            customer_headers = headers.copy()
            customer_headers['Authorization'] = f'Bearer {customer_token}'
            
            # Test 8: Customer Dashboard
            print("\n8. Testing Customer Dashboard...")
            response = requests.get(f"{BASE_URL}/users/dashboard/", 
                                  headers=customer_headers)
            print_response(response, "Customer Dashboard")
            
            # Test 9: Get Designers List (for customers)
            print("\n9. Testing Designers List (Customer View)...")
            response = requests.get(f"{BASE_URL}/users/designers/", 
                                  headers=customer_headers)
            print_response(response, "Designers List")
    
    print("\n✅ API Testing Complete!")
    print("\n📝 Available API Endpoints:")
    print("   • POST /api/auth/users/ - User registration")
    print("   • POST /api/auth/jwt/create/ - User login (get JWT token)")
    print("   • GET  /api/auth/users/me/ - Get current user profile")
    print("   • GET  /api/users/profile/ - Get user profile")
    print("   • PATCH /api/users/profile/ - Update user profile")
    print("   • GET  /api/users/dashboard/ - User dashboard")
    print("   • GET  /api/users/designers/ - List designers (customers only)")
    print("   • GET  /api/users/customers/ - List customers (designers only)")
    print("   • PATCH /api/users/role/update/ - Update user roles")
    
if __name__ == "__main__":
    test_api_endpoints()