#!/usr/bin/env python3
"""
Force regenerate topic names by deleting existing names from Neo4j
This will force the system to regenerate names on next API call
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def main():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, user, password]):
        print("✗ Neo4j credentials not found")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    print("=" * 60)
    print("Force Regenerate Topic Names")
    print("=" * 60)
    print("\n⚠️  WARNING: This will delete existing topic names from Neo4j")
    print("   The system will regenerate names on the next API call")
    print("   (if OpenAI quota is available)\n")
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Cancelled.")
        driver.close()
        return
    
    with driver.session() as session:
        # Count existing topics
        count_result = session.run("MATCH (t:Topic) RETURN count(t) as count")
        total_count = count_result.single()['count']
        print(f"\nFound {total_count} Topic nodes in Neo4j")
        
        # Delete topic names (set to null)
        result = session.run("""
            MATCH (t:Topic)
            SET t.name = null
            RETURN count(t) as updated
        """)
        updated = result.single()['updated']
        print(f"✓ Cleared names from {updated} Topic nodes")
        
        # Optionally, you could delete the Topic nodes entirely:
        # result = session.run("MATCH (t:Topic) DETACH DELETE t RETURN count(t) as deleted")
        # But that would also delete relationships, so we just clear names
    
    driver.close()
    print("\n✅ Topic names cleared from Neo4j")
    print("\nNext steps:")
    print("1. Ensure OpenAI API quota is available")
    print("2. Call the topic evolution endpoint or run generate_and_persist_topic_names.py")
    print("3. System will regenerate names using OpenAI")

if __name__ == "__main__":
    main()
