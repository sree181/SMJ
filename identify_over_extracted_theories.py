#!/usr/bin/env python3
"""
Identify papers with over-extracted theories (theories just mentioned, not used)
Focus on theories marked as "supporting" from "literature_review" with generic contexts
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def identify_over_extraction():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("IDENTIFYING OVER-EXTRACTED THEORIES")
            print("=" * 80)
            
            # Find theories that are likely over-extracted
            # Criteria: supporting role, from literature_review, with generic contexts
            result = session.run("""
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                WHERE r.role = 'supporting' 
                  AND r.section = 'literature_review'
                  AND (
                    toLower(r.usage_context) CONTAINS 'mentioned in literature review but not central'
                    OR toLower(r.usage_context) CONTAINS 'mentioned in literature review'
                    OR toLower(r.usage_context) CONTAINS 'used to contextualize'
                    OR r.usage_context IS NULL
                  )
                WITH p.paper_id as paper_id, 
                     p.title as title,
                     count(DISTINCT t) as suspect_theories,
                     collect(t.name) as theory_names
                WHERE suspect_theories >= 5
                RETURN paper_id, title, suspect_theories, theory_names
                ORDER BY suspect_theories DESC
                LIMIT 20
            """)
            
            papers = list(result)
            
            print(f"\nFound {len(papers)} papers with 5+ potentially over-extracted theories:")
            print("(Supporting theories from literature_review with generic contexts)\n")
            
            for i, record in enumerate(papers, 1):
                print(f"{i}. {record['paper_id']}: {record['suspect_theories']} suspect theories")
                print(f"   Title: {record['title'][:80]}...")
                print(f"   Theories: {', '.join(record['theory_names'][:5])}")
                if len(record['theory_names']) > 5:
                    print(f"   ... and {len(record['theory_names']) - 5} more")
                print()
            
            # Get statistics
            result = session.run("""
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                WHERE r.role = 'supporting' AND r.section = 'literature_review'
                RETURN count(DISTINCT p) as papers_with_supporting_lr,
                       count(r) as total_supporting_lr_relationships
            """)
            
            stats = result.single()
            print("=" * 80)
            print("STATISTICS:")
            print("=" * 80)
            print(f"Papers with 'supporting' theories from 'literature_review': {stats['papers_with_supporting_lr']}")
            print(f"Total 'supporting' + 'literature_review' relationships: {stats['total_supporting_lr_relationships']}")
            
            # Get average supporting theories per paper
            result = session.run("""
                MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
                WHERE r.role = 'supporting' AND r.section = 'literature_review'
                WITH p.paper_id as pid, count(DISTINCT t) as count
                RETURN avg(count) as avg_supporting_lr
            """)
            avg = result.single()['avg_supporting_lr']
            print(f"Average 'supporting' + 'literature_review' theories per paper: {avg:.1f}")
            
            print("\n" + "=" * 80)
            print("RECOMMENDATION:")
            print("=" * 80)
            print("These 'supporting' theories from 'literature_review' with generic contexts")
            print("are likely just mentioned in passing, not actively used.")
            print("\nOptions:")
            print("1. Keep as-is (they provide context but may clutter the graph)")
            print("2. Remove relationships with generic contexts (requires manual review)")
            print("3. Re-extract with stricter prompt (time-intensive)")
            print("=" * 80)
            
    finally:
        driver.close()

if __name__ == "__main__":
    try:
        identify_over_extraction()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

