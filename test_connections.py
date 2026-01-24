#!/usr/bin/env python3
"""
Test script to verify OpenAI and Neo4j connections
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

def test_openai_connection():
    """Test OpenAI API connection"""
    print("Testing OpenAI connection...")
    try:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ OpenAI API key not found in environment")
            return False
        
        client = OpenAI(api_key=api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10
        )
        
        print("✓ OpenAI connection successful!")
        print(f"Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

def test_neo4j_connection():
    """Test Neo4j connection"""
    print("\nTesting Neo4j connection...")
    try:
        load_dotenv()
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, user, password]):
            print("❌ Neo4j credentials not found in environment")
            return False
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 'Hello Neo4j!' as message")
            record = result.single()
            print("✓ Neo4j connection successful!")
            print(f"Response: {record['message']}")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

def main():
    """Run all connection tests"""
    print("=== Connection Tests ===")
    
    openai_ok = test_openai_connection()
    neo4j_ok = test_neo4j_connection()
    
    print("\n=== Test Results ===")
    if openai_ok and neo4j_ok:
        print("✓ All connections successful! Ready to run the literature agent.")
        return True
    else:
        print("❌ Some connections failed. Please check your configuration.")
        return False

if __name__ == "__main__":
    main()
