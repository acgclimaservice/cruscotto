#!/usr/bin/env python3
"""
Test the new logging system
"""

import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_logging_system():
    """Test if our logging system captures the JSON error"""
    print("🔍 Testing detailed logging system...")
    print(f"📡 Server URL: {BASE_URL}")
    
    try:
        # Test the error logging endpoint first
        print("\n1. Testing error logging endpoint...")
        test_error = {
            "type": "TEST_ERROR",
            "data": {
                "message": "This is a test error",
                "timestamp": "2025-01-01T10:00:00Z"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/log-error", json=test_error)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test routes that might cause JSON parsing errors
        problematic_routes = [
            f"{BASE_URL}/offerte/2",
            f"{BASE_URL}/offerte/2/accetta",
            f"{BASE_URL}/offerte/2/crea-ddt", 
            f"{BASE_URL}/offerte/2/elimina"
        ]
        
        print("\n2. Testing potentially problematic routes...")
        for route in problematic_routes:
            print(f"\n   Testing: {route}")
            try:
                if '/accetta' in route or '/crea-ddt' in route or '/elimina' in route:
                    # POST routes
                    response = requests.post(route, headers={'Content-Type': 'application/json'})
                else:
                    # GET routes
                    response = requests.get(route)
                    
                print(f"   Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                
                # Try to parse as JSON if it claims to be JSON
                if 'application/json' in response.headers.get('Content-Type', ''):
                    try:
                        json_data = response.json()
                        print(f"   JSON: {json_data}")
                    except json.JSONDecodeError as e:
                        print(f"   ❌ JSON ERROR: {e}")
                        print(f"   Raw: {response.text[:100]}...")
                        
            except requests.exceptions.ConnectionError:
                print(f"   ❌ Connection refused - server not running?")
                break
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print("\n✅ Check the following files for detailed logs:")
        print("   📄 flask_debug.log - Server-side logs")
        print("   🌐 Browser console - Client-side logs")
        print("\n🔍 Look for these markers:")
        print("   🚨 JAVASCRIPT ERROR - Client-side errors")
        print("   ❌ INVALID JSON RESPONSE - Server JSON errors")
        print("   🔍 FETCH_JSON_PARSE_ERROR - The error we're hunting!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_logging_system()