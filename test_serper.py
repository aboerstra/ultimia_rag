#!/usr/bin/env python3
"""Test Serper API connectivity and search"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_serper():
    """Test Serper API with a simple search"""
    
    api_key = os.getenv('SERPER_API_KEY')
    
    if not api_key:
        print("❌ SERPER_API_KEY not found in environment")
        return False
    
    print(f"✅ Found Serper API key: {api_key[:20]}...")
    
    # Test 1: Simple celebrity search (should always work)
    print("\n🧪 Test 1: Celebrity search (Elon Musk)")
    test_query_1 = "Elon Musk CEO Tesla"
    
    try:
        response = requests.post(
            'https://google.serper.dev/search',
            headers={
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            },
            json={'q': test_query_1},
            timeout=10
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API Working!")
            print(f"  Search Time: {data.get('searchParameters', {}).get('time', 'N/A')}")
            
            # Check for results
            if 'organic' in data:
                print(f"  Found {len(data['organic'])} organic results")
                print(f"  First result: {data['organic'][0].get('title', 'N/A')}")
            
            if 'knowledgeGraph' in data:
                print(f"  Knowledge Graph: {data['knowledgeGraph'].get('title', 'N/A')}")
        else:
            print(f"  ❌ API Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Request Error: {e}")
        return False
    
    # Test 2: Actual search we're using
    print("\n🧪 Test 2: Michael Kianmahd search")
    test_query_2 = "Michael Kianmahd Maxim Commercial Capital, LLC CEO president executive professional background"
    
    try:
        response = requests.post(
            'https://google.serper.dev/search',
            headers={
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            },
            json={'q': test_query_2},
            timeout=10
        )
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n  📊 Results Summary:")
            print(f"  Organic Results: {len(data.get('organic', []))}")
            
            if data.get('organic'):
                print(f"\n  🔍 Top 3 Results:")
                for i, result in enumerate(data['organic'][:3], 1):
                    print(f"\n  Result {i}:")
                    print(f"    Title: {result.get('title', 'N/A')}")
                    print(f"    Snippet: {result.get('snippet', 'N/A')[:100]}...")
            else:
                print(f"  ⚠️  NO organic results found for Michael Kianmahd")
            
            if 'knowledgeGraph' in data:
                print(f"\n  Knowledge Graph Found:")
                print(f"    Title: {data['knowledgeGraph'].get('title', 'N/A')}")
                print(f"    Description: {data['knowledgeGraph'].get('description', 'N/A')[:100]}...")
            else:
                print(f"  ℹ️  No knowledge graph")
                
            # Save full response for debugging
            with open('serper_test_response.json', 'w') as f:
                json.dump(data, f, indent=2)
            print(f"\n  💾 Full response saved to serper_test_response.json")
            
        else:
            print(f"  ❌ API Error: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Request Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("SERPER API TEST")
    print("=" * 60)
    
    success = test_serper()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ SERPER API IS WORKING")
    else:
        print("❌ SERPER API TEST FAILED")
    print("=" * 60)
