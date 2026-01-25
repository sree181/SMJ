#!/usr/bin/env python3
"""
Verify topic names stored in Neo4j
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
    print("Topic Names in Neo4j")
    print("=" * 60)
    
    with driver.session() as session:
        # Get all topics grouped by interval
        result = session.run("""
            MATCH (t:Topic)
            RETURN t.interval as interval,
                   t.topic_id as topic_id,
                   t.name as name,
                   t.paper_count as paper_count,
                   t.cluster_id as cluster_id
            ORDER BY t.interval, t.cluster_id
        """)
        
        topics_by_interval = {}
        for record in result:
            interval = record['interval']
            if interval not in topics_by_interval:
                topics_by_interval[interval] = []
            
            topics_by_interval[interval].append({
                'topic_id': record['topic_id'],
                'name': record['name'],
                'paper_count': record['paper_count'],
                'cluster_id': record['cluster_id']
            })
        
        # Display results
        total_topics = 0
        for interval, topics in sorted(topics_by_interval.items()):
            print(f"\n📊 {interval}: {len(topics)} topics")
            for topic in topics[:10]:  # Show first 10 per interval
                name = topic['name'] or 'No name'
                print(f"  • {topic['topic_id']}: '{name[:60]}...' ({topic['paper_count']} papers)")
            if len(topics) > 10:
                print(f"  ... and {len(topics) - 10} more topics")
            total_topics += len(topics)
        
        print("\n" + "=" * 60)
        print(f"Total topics in Neo4j: {total_topics}")
        
        # Check relationships
        rel_result = session.run("""
            MATCH (p:Paper)-[:BELONGS_TO_TOPIC]->(t:Topic)
            RETURN count(*) as relationships
        """)
        rel_count = rel_result.single()['relationships']
        print(f"Paper-Topic relationships: {rel_count}")
        
        # Check if names are generated or fallback
        name_result = session.run("""
            MATCH (t:Topic)
            WHERE t.name IS NOT NULL AND t.name <> ''
            RETURN count(t) as topics_with_names
        """)
        topics_with_names = name_result.single()['topics_with_names']
        print(f"Topics with names: {topics_with_names}")
        
    driver.close()
    print("\n✅ Verification complete!")

if __name__ == "__main__":
    main()
