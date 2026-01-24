#!/usr/bin/env python3
"""
Verify that changes are reflected in Neo4j
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_changes():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not password:
        raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("VERIFYING NEO4J CHANGES")
            print("=" * 80)
            
            # 1. Check if duplicate theories were merged
            print("\n1. CHECKING DUPLICATE THEORY MERGES:")
            print("-" * 80)
            
            # Check for "Dynamic Capabilities" (should not exist, should be merged)
            result = session.run("""
                MATCH (t:Theory)
                WHERE t.name CONTAINS "Dynamic Capabilities" 
                   AND t.name <> "Dynamic Capabilities Theory"
                RETURN t.name as theory_name, 
                       count{(p:Paper)-[:USES_THEORY]->(t)} as paper_count
            """)
            
            dc_duplicates = list(result)
            if dc_duplicates:
                print("   ⚠️  Found duplicate Dynamic Capabilities theories:")
                for record in dc_duplicates:
                    print(f"      - '{record['theory_name']}': {record['paper_count']} papers")
            else:
                print("   ✓ No duplicate 'Dynamic Capabilities' theories found")
            
            # Check for "Dynamic Capabilities Theory" (should exist with merged count)
            result = session.run("""
                MATCH (t:Theory {name: "Dynamic Capabilities Theory"})
                OPTIONAL MATCH (p:Paper)-[:USES_THEORY]->(t)
                RETURN count(DISTINCT p) as paper_count
            """)
            dc_count = result.single()['paper_count']
            print(f"   ✓ 'Dynamic Capabilities Theory' exists with {dc_count} papers (expected: ~42)")
            
            # Check for RBV variations (should not exist separately)
            result = session.run("""
                MATCH (t:Theory)
                WHERE t.name CONTAINS "RBV" 
                   AND t.name <> "Resource-Based View"
                RETURN t.name as theory_name,
                       count{(p:Paper)-[:USES_THEORY]->(t)} as paper_count
            """)
            
            rbv_duplicates = list(result)
            if rbv_duplicates:
                print("   ⚠️  Found RBV variations:")
                for record in rbv_duplicates:
                    print(f"      - '{record['theory_name']}': {record['paper_count']} papers")
            else:
                print("   ✓ No separate RBV variations found")
            
            # Check for "Resource-Based View" (should exist with merged count)
            result = session.run("""
                MATCH (t:Theory {name: "Resource-Based View"})
                OPTIONAL MATCH (p:Paper)-[:USES_THEORY]->(t)
                RETURN count(DISTINCT p) as paper_count
            """)
            rbv_count = result.single()['paper_count']
            print(f"   ✓ 'Resource-Based View' exists with {rbv_count} papers (expected: ~116)")
            
            # 2. Check total theory count
            print("\n2. CHECKING THEORY COUNTS:")
            print("-" * 80)
            result = session.run("MATCH (t:Theory) RETURN count(t) as total")
            total_theories = result.single()['total']
            print(f"   Total theories in graph: {total_theories} (expected: ~229)")
            
            # 3. Check for any theories with same normalized form
            print("\n3. CHECKING FOR REMAINING DUPLICATES:")
            print("-" * 80)
            result = session.run("""
                MATCH (t:Theory)
                WITH t.name as theory_name, 
                     toLower(replace(replace(replace(t.name, " Theory", ""), " (RBV)", ""), "RBV (", "")) as normalized
                WITH normalized, collect(theory_name) as names
                WHERE size(names) > 1
                RETURN normalized, names
                LIMIT 10
            """)
            
            remaining_duplicates = list(result)
            if remaining_duplicates:
                print("   ⚠️  Found potential duplicates:")
                for record in remaining_duplicates:
                    print(f"      Normalized: '{record['normalized']}'")
                    print(f"      Names: {record['names']}")
            else:
                print("   ✓ No obvious duplicates found")
            
            # 4. Summary
            print("\n" + "=" * 80)
            print("SUMMARY:")
            print("=" * 80)
            print(f"✓ Duplicate merges: {'Applied' if not dc_duplicates and not rbv_duplicates else 'Partially applied'}")
            print(f"✓ Total theories: {total_theories}")
            print(f"✓ Dynamic Capabilities Theory: {dc_count} papers")
            print(f"✓ Resource-Based View: {rbv_count} papers")
            print("\nNOTE: Code changes (normalization logic, extraction prompt) only affect")
            print("      NEW extractions. Existing papers in the graph are unchanged.")
            print("=" * 80)
            
    finally:
        driver.close()

if __name__ == "__main__":
    try:
        verify_changes()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

