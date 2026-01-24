#!/usr/bin/env python3
"""
Test Graph RAG API Integration
Tests comprehensive questions to verify Graph RAG is working
"""

import requests
import json
from typing import List, Dict

BASE_URL = "http://localhost:5000"

test_queries = [
    {
        "query": "What theories explain competitive advantage?",
        "description": "Theory-focused question"
    },
    {
        "query": "How do firms allocate resources?",
        "description": "Phenomenon-focused question"
    },
    {
        "query": "What methods are used to study innovation?",
        "description": "Method-focused question"
    },
    {
        "query": "What is the relationship between resource-based view and dynamic capabilities?",
        "description": "Multi-theory comparison question"
    },
    {
        "query": "How has strategic management research evolved over time?",
        "description": "Temporal/evolution question"
    },
    {
        "query": "What are the key findings about organizational performance?",
        "description": "Finding-focused question"
    }
]

def test_query(query: str, description: str) -> Dict:
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"Test: {description}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"query": query},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✓ Success")
            print(f"Answer length: {len(data.get('answer', ''))} characters")
            print(f"Sources: {len(data.get('sources', []))} papers")
            
            # Show first part of answer
            answer = data.get('answer', '')
            if answer:
                print(f"\nAnswer preview:")
                print(answer[:300] + "..." if len(answer) > 300 else answer)
            
            # Show sources
            sources = data.get('sources', [])
            if sources:
                print(f"\nTop 3 Sources:")
                for i, source in enumerate(sources[:3], 1):
                    title = source.get('title', 'N/A')
                    print(f"  {i}. {title[:60]}...")
            
            return {
                "success": True,
                "answer_length": len(answer),
                "sources_count": len(sources),
                "answer_preview": answer[:200]
            }
        else:
            print(f"✗ Error: {response.status_code}")
            print(response.text)
            return {"success": False, "error": response.status_code}
    
    except Exception as e:
        print(f"✗ Exception: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Run all test queries"""
    print("="*80)
    print("GRAPH RAG API INTEGRATION TEST")
    print("="*80)
    print(f"\nTesting against: {BASE_URL}")
    print("Make sure the API server is running!")
    
    results = []
    
    for test in test_queries:
        result = test_query(test["query"], test["description"])
        result["query"] = test["query"]
        result["description"] = test["description"]
        results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    successful = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    print(f"\nSuccessful: {successful}/{total}")
    print(f"Success rate: {successful/total*100:.1f}%")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✓" if result.get("success") else "✗"
        print(f"{status} {result.get('description')}")
        if result.get("success"):
            print(f"   Answer: {result.get('answer_length')} chars, "
                  f"Sources: {result.get('sources_count')} papers")
        else:
            print(f"   Error: {result.get('error')}")
    
    # Save results
    with open("graphrag_api_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: graphrag_api_test_results.json")

if __name__ == "__main__":
    main()
