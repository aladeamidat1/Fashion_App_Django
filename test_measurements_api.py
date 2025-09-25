#!/usr/bin/env python3
"""
Fashion App Measurements API Test Script

This script tests the measurements and relationship management APIs.
Run this script while the Django server is running to test all measurement endpoints.
"""

import requests
import json
from pprint import pprint

# Configuration
BASE_URL = "http://localhost:8000/api"
headers = {'Content-Type': 'application/json'}

def print_response(response, title):
    """Helper function to print API responses"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        pprint(response.json())
    except:
        print(response.text)
    print(f"{'='*60}\n")

def test_measurements_api():
    """Test all measurement-related API endpoints"""
    
    print("🚀 Starting Fashion App Measurements API Tests...")
    
    # Step 1: Login as Designer
    print("\n1. Logging in as Designer...")
    designer_login = {
        "username": "testuser",  # This user was created from our previous test
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", 
                           data=json.dumps(designer_login), 
                           headers=headers)
    
    if response.status_code != 200:
        print("❌ Designer login failed! Creating designer user...")
        # Create designer if doesn't exist
        designer_data = {
            "username": "testdesigner2",
            "email": "designer2@test.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "Designer2",
            "phone": "1111111111",
            "is_Designer": True,
            "is_Customer": False
        }
        
        response = requests.post(f"{BASE_URL}/auth/users/", 
                               data=json.dumps(designer_data), 
                               headers=headers)
        print_response(response, "Designer Registration")
        
        # Try login again
        designer_login["username"] = "testdesigner2"
        response = requests.post(f"{BASE_URL}/auth/jwt/create/", 
                               data=json.dumps(designer_login), 
                               headers=headers)
    
    print_response(response, "Designer Login")
    
    if response.status_code != 200:
        print("❌ Could not login as designer. Exiting...")
        return
    
    designer_token = response.json().get('access')
    designer_headers = headers.copy()
    designer_headers['Authorization'] = f'Bearer {designer_token}'
    
    # Step 2: Login as Customer
    print("\n2. Logging in as Customer...")
    customer_login = {
        "username": "testcustomer",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/jwt/create/", 
                           data=json.dumps(customer_login), 
                           headers=headers)
    print_response(response, "Customer Login")
    
    if response.status_code != 200:
        print("❌ Customer login failed!")
        return
    
    customer_token = response.json().get('access')
    customer_headers = headers.copy()
    customer_headers['Authorization'] = f'Bearer {customer_token}'
    
    # Step 3: Designer views available customers
    print("\n3. Designer views available customers...")
    response = requests.get(f"{BASE_URL}/measurements/available-customers/", 
                          headers=designer_headers)
    print_response(response, "Available Customers")
    
    # Get customer ID for creating measurements
    customer_id = None
    if response.status_code == 200:
        customers = response.json().get('available_customers', [])
        if customers:
            customer_id = customers[0]['id']
            print(f"Selected customer ID: {customer_id}")
    
    if not customer_id:
        print("❌ No customers available for measurements")
        return
    
    # Step 4: Create a designer-customer relationship
    print("\n4. Creating designer-customer relationship...")
    relationship_data = {
        "customer": customer_id,
        "status": "active",
        "notes": "Initial connection for measurements"
    }
    
    response = requests.post(f"{BASE_URL}/measurements/relationships/", 
                           data=json.dumps(relationship_data), 
                           headers=designer_headers)
    print_response(response, "Create Relationship")
    
    # Step 5: Designer creates measurements for customer
    print("\n5. Designer creates measurements for customer...")
    measurement_data = {
        "customer": customer_id,
        "bust": 90.0,
        "waist": 75.0,
        "hips": 95.0,
        "height": 165.0,
        "sleeve_length": 60.0,
        "inseam": 75.0,
        "notes": "Initial measurements taken",
        "measurement_type": "manual"
    }
    
    response = requests.post(f"{BASE_URL}/measurements/create/", 
                           data=json.dumps(measurement_data), 
                           headers=designer_headers)
    print_response(response, "Create Measurements")
    
    measurement_id = None
    if response.status_code == 201:
        measurement_id = response.json().get('id')
        print(f"Created measurement ID: {measurement_id}")
    
    # Step 6: Designer dashboard
    print("\n6. Designer dashboard...")
    response = requests.get(f"{BASE_URL}/measurements/dashboard/", 
                          headers=designer_headers)
    print_response(response, "Designer Dashboard")
    
    # Step 7: Customer dashboard
    print("\n7. Customer dashboard...")
    response = requests.get(f"{BASE_URL}/measurements/dashboard/", 
                          headers=customer_headers)
    print_response(response, "Customer Dashboard")
    
    print("\n✅ Measurements API Testing Complete!")
    print("\n📝 Available Measurement API Endpoints:")
    print("   • POST /api/measurements/create/ - Create measurements (designers only)")
    print("   • GET  /api/measurements/list/ - List measurements (role-based)")
    print("   • GET  /api/measurements/{id}/ - Get measurement details")
    print("   • PATCH /api/measurements/{id}/ - Update measurements (designers only)")
    print("   • DELETE /api/measurements/{id}/ - Deactivate measurements (designers only)")
    print("   • POST /api/measurements/quick-entry/ - Quick measurement entry")
    print("   • GET  /api/measurements/dashboard/ - Measurement dashboard")
    print("   • GET  /api/measurements/{id}/history/ - Measurement change history")
    print("   • GET  /api/measurements/available-customers/ - Available customers (designers)")
    print("   • GET  /api/measurements/available-designers/ - Available designers (customers)")
    print("   • GET  /api/measurements/relationships/ - Designer-customer relationships")
    print("   • POST /api/measurements/relationships/ - Create relationships")
    print("   • PATCH /api/measurements/relationships/{id}/ - Update relationships")
    
if __name__ == "__main__":
    test_measurements_api()