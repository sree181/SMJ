#!/usr/bin/env python3
"""
Update Neo4j configuration in .env file
"""

import os
from pathlib import Path

def update_env_file():
    """Update .env file with new Neo4j Aura credentials"""
    env_file = Path(".env")
    
    # New Neo4j Aura configuration
    new_config = {
        "NEO4J_URI": "neo4j+s://d1a3de49.databases.neo4j.io",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "QGaIl1PSNjXlNIFV1vghPbOBC5yKQPuFFqwb8gMU04I",
        "NEO4J_DATABASE": "neo4j",
        "NEO4J_USER": "neo4j",  # Alias for compatibility
        "AURA_INSTANCEID": "d1a3de49",
        "AURA_INSTANCENAME": "SMJ"
    }
    
    # Read existing .env if it exists
    existing_lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            existing_lines = f.readlines()
    
    # Update or add Neo4j config
    updated_lines = []
    neo4j_keys = set(new_config.keys())
    found_keys = set()
    
    for line in existing_lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith('#'):
            updated_lines.append(line)
            continue
        
        key = line_stripped.split('=')[0].strip()
        if key in neo4j_keys:
            # Update existing line
            updated_lines.append(f"{key}={new_config[key]}\n")
            found_keys.add(key)
        else:
            updated_lines.append(line)
    
    # Add missing keys
    for key, value in new_config.items():
        if key not in found_keys:
            updated_lines.append(f"{key}={value}\n")
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.writelines(updated_lines)
    
    print("✅ Updated .env file with new Neo4j Aura configuration")
    print("\nUpdated configuration:")
    for key, value in new_config.items():
        if key == "NEO4J_PASSWORD":
            print(f"  {key}={value[:10]}...")
        else:
            print(f"  {key}={value}")

if __name__ == "__main__":
    update_env_file()
