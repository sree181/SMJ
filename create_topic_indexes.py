#!/usr/bin/env python3
"""
Create Neo4j indexes for Topic nodes
Run this once to set up the indexes for topic naming feature
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def create_topic_indexes():
    """Create indexes for Topic nodes"""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        print("Error: NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        return
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # Create index on topic_id (unique identifier)
            print("Creating index on Topic.topic_id...")
            session.run("""
                CREATE INDEX topic_id_index IF NOT EXISTS
                FOR (t:Topic)
                ON (t.topic_id)
            """)
            print("✓ Index on topic_id created")
            
            # Create index on interval for faster lookups
            print("Creating index on Topic.interval...")
            session.run("""
                CREATE INDEX topic_interval_index IF NOT EXISTS
                FOR (t:Topic)
                ON (t.interval)
            """)
            print("✓ Index on interval created")
            
            # Create composite index for interval + cluster_id lookups
            print("Creating composite index on Topic.interval and cluster_id...")
            session.run("""
                CREATE INDEX topic_interval_cluster_index IF NOT EXISTS
                FOR (t:Topic)
                ON (t.interval, t.cluster_id)
            """)
            print("✓ Composite index created")
            
            print("\n✅ All Topic indexes created successfully!")
            
    except Exception as e:
        print(f"Error creating indexes: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    create_topic_indexes()
