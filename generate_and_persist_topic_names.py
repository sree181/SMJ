#!/usr/bin/env python3
"""
Generate topic names and persist to Neo4j
This script will trigger topic evolution calculation which will generate names for all topics
"""

import os
import sys
from dotenv import load_dotenv
from advanced_analytics_endpoints import AdvancedAnalytics

load_dotenv()

def main():
    """Generate topic names for all intervals and persist to Neo4j"""
    print("=" * 60)
    print("Topic Name Generation and Persistence")
    print("=" * 60)
    
    # Check OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not set")
        print("   Topic names will use fallback (representative paper titles)")
        print("   Set OPENAI_API_KEY in .env to enable AI-generated names\n")
    else:
        print(f"✓ OPENAI_API_KEY found (length: {len(api_key)})\n")
    
    # Initialize analytics
    print("Initializing AdvancedAnalytics...")
    try:
        analytics = AdvancedAnalytics()
        print("✓ Connected to Neo4j\n")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return
    
    # Generate topic evolution (this will trigger name generation)
    print("Calculating topic evolution (this will generate topic names)...")
    print("Note: This may take a few minutes and will use OpenAI API (~$0.01-0.02)\n")
    
    try:
        result = analytics.calculate_topic_evolution(start_year=1985, end_year=2025)
        
        # Count topics with names
        total_topics = 0
        topics_with_names = 0
        topics_with_generated_names = 0
        
        print("\n" + "=" * 60)
        print("Topic Name Generation Results")
        print("=" * 60)
        
        for interval_data in result.get('intervals', []):
            interval = interval_data.get('interval')
            topics = interval_data.get('topics', [])
            
            if topics:
                print(f"\n📊 {interval}:")
                for topic in topics:
                    total_topics += 1
                    topic_name = topic.get('name', '')
                    topic_id = topic.get('topic_id', '')
                    paper_count = topic.get('paper_count', 0)
                    
                    if topic_name:
                        topics_with_names += 1
                        # Check if it's a generated name (not just paper title)
                        rep_paper_title = topic.get('representative_paper', {}).get('title', '')
                        if topic_name != rep_paper_title:
                            topics_with_generated_names += 1
                            print(f"  ✓ {topic_id}: '{topic_name}' ({paper_count} papers) [Generated]")
                        else:
                            print(f"  → {topic_id}: '{topic_name}' ({paper_count} papers) [Fallback]")
                    else:
                        print(f"  ✗ {topic_id}: No name ({paper_count} papers)")
        
        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)
        print(f"Total topics: {total_topics}")
        print(f"Topics with names: {topics_with_names}")
        print(f"Topics with generated names: {topics_with_generated_names}")
        print(f"Topics using fallback: {topics_with_names - topics_with_generated_names}")
        
        # Verify persistence in Neo4j
        print("\n" + "=" * 60)
        print("Verifying Neo4j Persistence")
        print("=" * 60)
        
        with analytics.driver.session() as session:
            result = session.run("""
                MATCH (t:Topic)
                RETURN count(t) as total_topics,
                       count(DISTINCT t.interval) as intervals,
                       collect(DISTINCT t.interval) as interval_list
            """)
            
            record = result.single()
            if record:
                total_in_neo4j = record['total_topics']
                intervals_count = record['intervals']
                print(f"✓ Total Topic nodes in Neo4j: {total_in_neo4j}")
                print(f"✓ Intervals with topics: {intervals_count}")
                
                # Check relationships
                rel_result = session.run("""
                    MATCH (p:Paper)-[:BELONGS_TO_TOPIC]->(t:Topic)
                    RETURN count(*) as paper_topic_relationships
                """)
                rel_record = rel_result.single()
                if rel_record:
                    print(f"✓ Paper-Topic relationships: {rel_record['paper_topic_relationships']}")
        
        print("\n✅ Topic name generation and persistence complete!")
        print("\nNext steps:")
        print("1. Restart your backend server to load the new topic names")
        print("2. Go to the 'Topics Proportions' tab in the UI")
        print("3. Pie charts should now show generated topic names")
        
    except Exception as e:
        print(f"\n✗ Error during topic evolution calculation: {e}")
        import traceback
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
