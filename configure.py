#!/usr/bin/env python3
"""
Simple configuration script to set up OpenAI API key
"""

import os
from pathlib import Path

def configure_api_key():
    """Configure OpenAI API key"""
    print("=== OpenAI API Key Configuration ===")
    print("You need an OpenAI API key to use this literature agent.")
    print("Get your API key from: https://platform.openai.com/api-keys")
    print()
    
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return False
    
    # Update .env file
    env_file = Path(".env")
    if env_file.exists():
        # Read current content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace the placeholder
        updated_content = content.replace(
            "OPENAI_API_KEY=your_openai_api_key_here",
            f"OPENAI_API_KEY={api_key}"
        )
        
        # Write back
        with open(env_file, 'w') as f:
            f.write(updated_content)
        
        print("✓ API key configured successfully!")
        return True
    else:
        print("❌ .env file not found. Please run setup.py first.")
        return False

def check_neo4j():
    """Check if Neo4j is running"""
    print("\n=== Neo4j Check ===")
    print("Make sure Neo4j is installed and running:")
    print("1. Download from: https://neo4j.com/download/")
    print("2. Start Neo4j (default: bolt://localhost:7687)")
    print("3. Default credentials: username='neo4j', password='password'")
    print("4. Or update the .env file with your Neo4j credentials")
    print()

if __name__ == "__main__":
    if configure_api_key():
        check_neo4j()
        print("\n=== Ready to Run ===")
        print("You can now run: python Kb.py")
    else:
        print("Configuration failed. Please try again.")
