#!/usr/bin/env python3
"""
Simple test to verify the basic functionality without OpenAI
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
import fitz

def test_pdf_processing():
    """Test PDF text extraction"""
    print("Testing PDF processing...")
    
    # Find a PDF file to test
    pdf_files = list(Path(".").glob("*/1988_305.pdf"))
    if not pdf_files:
        print("❌ No test PDF found")
        return False
    
    pdf_path = pdf_files[0]
    print(f"Testing with: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        print(f"✓ PDF processed successfully! Extracted {len(text)} characters")
        print(f"First 200 characters: {text[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ PDF processing failed: {e}")
        return False

def test_neo4j_operations():
    """Test basic Neo4j operations"""
    print("\nTesting Neo4j operations...")
    
    load_dotenv()
    uri = os.getenv('NEO4J_URI')
    user = os.getenv('NEO4J_USER')
    password = os.getenv('NEO4J_PASSWORD')
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Create a test node
            session.run("CREATE (t:Test {name: 'Literature Agent Test', timestamp: datetime()})")
            
            # Query the test node
            result = session.run("MATCH (t:Test) RETURN t.name as name, t.timestamp as timestamp")
            record = result.single()
            
            print(f"✓ Neo4j operations successful!")
            print(f"Created test node: {record['name']}")
            
            # Clean up
            session.run("MATCH (t:Test) DELETE t")
            print("✓ Test node cleaned up")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j operations failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== Simple Functionality Tests ===")
    
    pdf_ok = test_pdf_processing()
    neo4j_ok = test_neo4j_operations()
    
    print("\n=== Test Results ===")
    if pdf_ok and neo4j_ok:
        print("✓ All basic functionality tests passed!")
        print("Ready to proceed with the full literature agent.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    main()
