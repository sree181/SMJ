#!/usr/bin/env python3
"""
Test Railway API to see what it's actually returning
"""

import requests
import json
import os

# You'll need to set your Railway backend URL
RAILWAY_BACKEND_URL = os.getenv("RAILWAY_BACKEND_URL", "https://your-backend.railway.app")

def test_railway_api():
    """Test what Railway API is returning"""
    
    print("=" * 80)
    print("🔍 TESTING RAILWAY API")
    print("=" * 80)
    print()
    print(f"Backend URL: {RAILWAY_BACKEND_URL}")
    print()
    
    # Test the paper counts endpoint
    url = f"{RAILWAY_BACKEND_URL}/api/analytics/papers/by-interval"
    
    print(f"📡 Calling: {url}")
    print()
    
    try:
        # Test with default parameters (should use end_year=2026)
        response = requests.get(url, params={"start_year": 1985, "end_year": 2026}, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            intervals = data.get("intervals", [])
            
            print(f"✅ Received {len(intervals)} intervals")
            print()
            
            total_papers = 0
            for interval in intervals:
                count = interval.get("count", 0)
                interval_name = interval.get("interval", "Unknown")
                total_papers += count
                print(f"   {interval_name}: {count} papers")
            
            print()
            print("=" * 80)
            print(f"📊 TOTAL PAPERS FROM API: {total_papers}")
            print("=" * 80)
            print()
            
            if total_papers == 1029:
                print("✅ SUCCESS! API returns all 1029 papers")
            elif total_papers == 751:
                print("⚠️  API still returns 751 papers (old code)")
                print("   Railway needs to redeploy with latest code")
            else:
                print(f"⚠️  Unexpected count: {total_papers}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Railway: {e}")
        print()
        print("💡 Make sure to set RAILWAY_BACKEND_URL environment variable")
        print("   Example: export RAILWAY_BACKEND_URL=https://your-backend.railway.app")
    
    print()
    print("=" * 80)
    print("🔍 TESTING WITH EXPLICIT END_YEAR=2026")
    print("=" * 80)
    print()
    
    try:
        # Test with explicit end_year=2026
        response = requests.get(url, params={"start_year": 1985, "end_year": 2026}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            intervals = data.get("intervals", [])
            
            total_papers = sum(interval.get("count", 0) for interval in intervals)
            print(f"📊 Total with explicit end_year=2026: {total_papers}")
            
            if total_papers == 1029:
                print("✅ Explicit parameter works!")
            else:
                print(f"⚠️  Still returns {total_papers} (Railway needs redeploy)")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_railway_api()
