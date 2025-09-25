"""
Simple test script to create a user directly
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fashion_app.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.serializers import UserCreateSerializer

User = get_user_model()

def test_user_creation():
    print("Testing user creation...")
    
    # Test data
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "re_password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
        "phone": "1234567890",
        "is_Designer": True,
        "is_Customer": False
    }
    
    # Test serializer
    serializer = UserCreateSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        print(f"✅ User created successfully: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Designer: {user.is_Designer}")
        print(f"   Customer: {user.is_Customer}")
    else:
        print("❌ Validation errors:")
        print(serializer.errors)

if __name__ == "__main__":
    test_user_creation()