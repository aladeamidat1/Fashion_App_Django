#!/usr/bin/env python3
"""
AI Measurement Service Test Script

This script tests the AI measurement extraction service endpoints.
Run this script while the AI service is running to test all endpoints.
"""

import requests
import json
import base64
import time
from pathlib import Path
from PIL import Image, ImageDraw
import io
import numpy as np

# Configuration
AI_SERVICE_URL = "http://localhost:8001/api/v1"
headers = {'Content-Type': 'application/json'}


def print_response(response, title):
    """Helper function to print API responses"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        if isinstance(data, dict) and len(str(data)) > 1000:
            # Summarize large responses
            summary = {k: v for k, v in data.items() if k != 'measurements'}
            if 'measurements' in data:
                summary['measurements_count'] = len(data['measurements'])
                if data['measurements']:
                    summary['sample_measurement'] = data['measurements'][0]
            print(json.dumps(summary, indent=2, default=str))
        else:
            print(json.dumps(data, indent=2, default=str))
    except:
        print(response.text)
    print(f"{'='*60}\n")


def create_test_image():
    """Create a simple test image with a basic human figure"""
    # Create a 400x600 image (portrait orientation)
    img = Image.new('RGB', (400, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple stick figure
    # Head
    draw.ellipse([180, 50, 220, 90], outline='black', width=3)
    
    # Body
    draw.line([200, 90, 200, 250], fill='black', width=5)  # Torso
    
    # Arms
    draw.line([200, 120, 150, 180], fill='black', width=3)  # Left arm
    draw.line([200, 120, 250, 180], fill='black', width=3)  # Right arm
    
    # Legs
    draw.line([200, 250, 170, 350], fill='black', width=4)  # Left leg
    draw.line([200, 250, 230, 350], fill='black', width=4)  # Right leg
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    base64_data = base64.b64encode(img_data).decode()
    
    return base64_data


def test_ai_service():
    """Test all AI measurement service endpoints"""
    
    print("🤖 Starting AI Measurement Service Tests...")
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{AI_SERVICE_URL}/health/")
        print_response(response, "Health Check")
    except requests.exceptions.ConnectionError:
        print("❌ AI Service is not running! Please start with:")
        print("   cd ai_measurement_service && uv run python main.py")
        return
    
    # Test 2: Detailed Health Check
    print("\n2. Testing Detailed Health Check...")
    response = requests.get(f"{AI_SERVICE_URL}/health/detailed")
    print_response(response, "Detailed Health Check")
    
    # Test 3: Processing Stats
    print("\n3. Testing Processing Stats...")
    response = requests.get(f"{AI_SERVICE_URL}/health/stats")
    print_response(response, "Processing Stats")
    
    # Test 4: Service Test Endpoint
    print("\n4. Testing Service Test Endpoint...")
    response = requests.get(f"{AI_SERVICE_URL}/measurements/test")
    print_response(response, "Service Test")
    
    # Test 5: Model Info
    print("\n5. Testing Model Info...")
    response = requests.get(f"{AI_SERVICE_URL}/measurements/models/info")
    print_response(response, "Model Info")
    
    # Test 6: Create and Test Image Processing
    print("\n6. Creating test image and testing measurement extraction...")
    test_image_data = create_test_image()
    
    measurement_request = {
        "image_data": test_image_data,
        "image_type": "image/jpeg",
        "filename": "test_image.jpg",
        "customer_id": 1,
        "reference_height": 170.0
    }
    
    response = requests.post(
        f"{AI_SERVICE_URL}/measurements/extract",
        data=json.dumps(measurement_request),
        headers=headers
    )
    print_response(response, "Image Measurement Extraction")
    
    # Test 7: Test with Invalid Image Data
    print("\n7. Testing with invalid image data...")
    invalid_request = {
        "image_data": "invalid_base64_data",
        "image_type": "image/jpeg",
        "filename": "invalid.jpg"
    }
    
    response = requests.post(
        f"{AI_SERVICE_URL}/measurements/extract",
        data=json.dumps(invalid_request),
        headers=headers
    )
    print_response(response, "Invalid Image Test")
    
    # Test 8: Test with unsupported image type
    print("\n8. Testing with unsupported image type...")
    unsupported_request = {
        "image_data": test_image_data,
        "image_type": "image/gif",
        "filename": "test.gif"
    }
    
    response = requests.post(
        f"{AI_SERVICE_URL}/measurements/extract",
        data=json.dumps(unsupported_request),
        headers=headers
    )
    print_response(response, "Unsupported Image Type Test")
    
    # Test 9: Batch Processing
    print("\n9. Testing batch processing...")
    batch_request = {
        "images": [
            {
                "image_data": test_image_data,
                "image_type": "image/jpeg",
                "filename": "batch_1.jpg",
                "customer_id": 1,
                "reference_height": 170.0
            },
            {
                "image_data": test_image_data,
                "image_type": "image/jpeg", 
                "filename": "batch_2.jpg",
                "customer_id": 2,
                "reference_height": 165.0
            }
        ],
        "customer_id": 1,
        "processing_options": {"priority": "normal"}
    }
    
    response = requests.post(
        f"{AI_SERVICE_URL}/measurements/batch",
        data=json.dumps(batch_request),
        headers=headers
    )
    print_response(response, "Batch Processing")
    
    # Test 10: Check stats after processing
    print("\n10. Final processing stats...")
    response = requests.get(f"{AI_SERVICE_URL}/health/stats")
    print_response(response, "Final Processing Stats")
    
    print("\n✅ AI Service Testing Complete!")
    print("\n📝 Available AI Service Endpoints:")
    print("   Health & Monitoring:")
    print("   • GET  /api/v1/health/ - Basic health check")
    print("   • GET  /api/v1/health/detailed - Detailed health with system info")
    print("   • GET  /api/v1/health/stats - Processing statistics")
    print("")
    print("   AI Measurement Processing:")
    print("   • POST /api/v1/measurements/extract - Extract measurements from base64 image")
    print("   • POST /api/v1/measurements/extract-file - Extract measurements from uploaded file")
    print("   • POST /api/v1/measurements/batch - Batch process multiple images")
    print("   • GET  /api/v1/measurements/test - Test service availability")
    print("   • GET  /api/v1/measurements/models/info - AI model information")
    print("")
    print("🔗 Integration Notes:")
    print("   • AI Service runs on port 8001")
    print("   • Django Fashion App runs on port 8000") 
    print("   • Services can be integrated via HTTP requests")
    print("   • Consider implementing authentication for production")


def test_performance():
    """Test performance with multiple requests"""
    print("\n🚀 Performance Testing...")
    
    test_image_data = create_test_image()
    request_data = {
        "image_data": test_image_data,
        "image_type": "image/jpeg",
        "filename": "perf_test.jpg"
    }
    
    num_requests = 5
    total_time = 0
    successful_requests = 0
    
    for i in range(num_requests):
        start_time = time.time()
        try:
            response = requests.post(
                f"{AI_SERVICE_URL}/measurements/extract",
                data=json.dumps(request_data),
                headers=headers,
                timeout=30
            )
            
            request_time = time.time() - start_time
            total_time += request_time
            
            if response.status_code == 200:
                successful_requests += 1
                print(f"   Request {i+1}: {request_time:.2f}s ✅")
            else:
                print(f"   Request {i+1}: {request_time:.2f}s ❌ (Status: {response.status_code})")
                
        except Exception as e:
            request_time = time.time() - start_time
            print(f"   Request {i+1}: {request_time:.2f}s ❌ (Error: {str(e)})")
    
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        print(f"\n📊 Performance Results:")
        print(f"   • Successful requests: {successful_requests}/{num_requests}")
        print(f"   • Average response time: {avg_time:.2f}s")
        print(f"   • Total time: {total_time:.2f}s")
    else:
        print("\n❌ No successful requests in performance test")


if __name__ == "__main__":
    test_ai_service()
    
    # Uncomment to run performance tests
    # test_performance()