#!/usr/bin/env python3
"""
Analyze theories for a specific paper to understand if extraction is too permissive
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def analyze_paper(paper_id: str):
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print(f"ANALYZING PAPER: {paper_id}")
            print("=" * 80)
            
            # Get paper info
            result = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})
                RETURN p.title as title, 
                       p.publication_year as year,
                       p.abstract as abstract
            """, paper_id=paper_id)
            
            paper_info = result.single()
            if not paper_info:
                print(f"Paper {paper_id} not found in database")
                return
            
            print(f"\nTitle: {paper_info['title']}")
            print(f"Year: {paper_info['year']}")
            if paper_info['abstract']:
                print(f"Abstract: {paper_info['abstract'][:200]}...")
            
            # Get all theories with their roles
            result = session.run("""
                MATCH (p:Paper {paper_id: $paper_id})-[r:USES_THEORY]->(t:Theory)
                RETURN t.name as theory_name,
                       r.role as role,
                       r.section as section,
                       r.usage_context as usage_context
                ORDER BY 
                    CASE r.role
                        WHEN 'primary' THEN 1
                        WHEN 'extending' THEN 2
                        WHEN 'supporting' THEN 3
                        WHEN 'challenging' THEN 4
                        ELSE 5
                    END,
                    t.name
            """, paper_id=paper_id)
            
            theories = list(result)
            
            print(f"\n{'='*80}")
            print(f"THEORIES ({len(theories)} total):")
            print("=" * 80)
            
            if not theories:
                print("No theories found for this paper")
                return
            
            # Group by role
            by_role = {}
            for record in theories:
                role = record['role'] or 'unknown'
                if role not in by_role:
                    by_role[role] = []
                by_role[role].append(record)
            
            # Print by role
            role_order = ['primary', 'extending', 'supporting', 'challenging', 'unknown']
            for role in role_order:
                if role in by_role:
                    print(f"\n{role.upper()} THEORIES ({len(by_role[role])}):")
                    print("-" * 80)
                    for theory in by_role[role]:
                        print(f"  • {theory['theory_name']}")
                        if theory['section']:
                            print(f"    Section: {theory['section']}")
                        if theory['usage_context']:
                            context = theory['usage_context']
                            if len(context) > 100:
                                context = context[:100] + "..."
                            print(f"    Context: {context}")
                        print()
            
            # Compare with other papers
            print("=" * 80)
            print("COMPARISON WITH OTHER PAPERS:")
            print("=" * 80)
            
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WITH p.paper_id as pid, count(DISTINCT t) as theory_count
                RETURN 
                    avg(theory_count) as avg_theories,
                    min(theory_count) as min_theories,
                    max(theory_count) as max_theories
            """)
            
            stats = result.single()
            print(f"Average theories per paper: {stats['avg_theories']:.1f}")
            print(f"Min theories: {stats['min_theories']}")
            print(f"Max theories: {stats['max_theories']}")
            print(f"\nThis paper ({paper_id}): {len(theories)} theories")
            
            if len(theories) > stats['avg_theories'] * 1.5:
                print(f"⚠️  This paper has SIGNIFICANTLY MORE theories than average")
            elif len(theories) > stats['avg_theories']:
                print(f"⚠️  This paper has MORE theories than average")
            else:
                print(f"✓ This paper has a normal number of theories")
            
            # Check for common theory combinations
            print("\n" + "=" * 80)
            print("COMMON THEORY COMBINATIONS:")
            print("=" * 80)
            
            theory_names = [t['theory_name'] for t in theories]
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE t.name IN $theory_names
                WITH p.paper_id as pid, collect(DISTINCT t.name) as paper_theories
                WHERE size(paper_theories) >= size($theory_names) * 0.8
                RETURN count(DISTINCT pid) as similar_papers
            """, theory_names=theory_names)
            
            similar = result.single()['similar_papers']
            print(f"Papers with similar theory sets (≥80% overlap): {similar}")
            
            if similar > 10:
                print(f"⚠️  Many papers share similar theory sets - possible over-extraction")
            
            print("=" * 80)
            
    finally:
        driver.close()

if __name__ == "__main__":
    paper_id = sys.argv[1] if len(sys.argv) > 1 else "2021_4373"
    try:
        analyze_paper(paper_id)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

