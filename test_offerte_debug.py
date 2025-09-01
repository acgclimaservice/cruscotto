#!/usr/bin/env python3
"""
Test script to debug JSON parsing errors in offerte routes
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_route(method, url, expect_json=True):
    """Test a route and check response"""
    print(f"\n=== Testing {method} {url} ===")
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json={})
        else:
            response = requests.request(method, url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        if expect_json:
            try:
                json_data = response.json()
                print(f"JSON Response: {json_data}")
                return True, json_data
            except json.JSONDecodeError as e:
                print(f"❌ JSON PARSING ERROR: {e}")
                print(f"Raw response: {response.text[:200]}...")
                return False, None
        else:
            print(f"HTML Response length: {len(response.text)}")
            if "expected token" in response.text.lower():
                print("❌ Found 'expected token' in HTML response!")
            return True, response.text
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running?")
        return False, None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False, None

def main():
    """Run all tests"""
    print("🔍 Testing offerte routes for JSON parsing errors...")
    
    # Test offerte che non esistono (dovrebbero causare l'errore)
    test_ids = [1, 2, 3, 99, 999]
    
    for test_id in test_ids:
        print(f"\n{'='*50}")
        print(f"Testing with offerta ID: {test_id}")
        print(f"{'='*50}")
        
        # Test GET dettaglio offerta (should return HTML 404)
        test_route("GET", f"{BASE_URL}/offerte/{test_id}", expect_json=False)
        
        # Test POST crea-ddt (should return JSON 404)
        test_route("POST", f"{BASE_URL}/offerte/{test_id}/crea-ddt", expect_json=True)
        
        # Test POST elimina (should return JSON 404) 
        test_route("POST", f"{BASE_URL}/offerte/{test_id}/elimina", expect_json=True)
    
    print(f"\n{'='*50}")
    print("✅ Test completati! Controlla i log del server per vedere i messaggi DEBUG.")

if __name__ == "__main__":
    main()