#!/usr/bin/env python3
"""
Script to merge duplicate theories in Neo4j
Fixes normalization issues by merging theories that should be the same
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
from entity_normalizer import get_normalizer

# Load environment variables
load_dotenv()

class TheoryMerger:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.uri or not self.password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.normalizer = get_normalizer()
    
    def close(self):
        self.driver.close()
    
    def find_duplicate_theories(self):
        """Find theories that should be normalized to the same canonical form"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)
                RETURN t.name as theory_name, t.original_name as original_name
                ORDER BY t.name
            """)
            
            # Group by normalized name
            normalized_groups = {}
            for record in result:
                theory_name = record['theory_name']
                original_name = record['original_name'] or theory_name
                
                # Normalize using the improved normalizer
                normalized = self.normalizer.normalize_theory(theory_name)
                
                if normalized not in normalized_groups:
                    normalized_groups[normalized] = []
                
                normalized_groups[normalized].append({
                    'current_name': theory_name,
                    'original_name': original_name
                })
            
            # Find groups with multiple theories (duplicates)
            duplicates = {}
            for canonical, theories in normalized_groups.items():
                if len(theories) > 1:
                    # Get paper counts for each theory to find the most common
                    theory_counts = {}
                    for theory in theories:
                        with self.driver.session() as count_session:
                            result = count_session.run("""
                                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: $theory_name})
                                RETURN count(DISTINCT p) as paper_count
                            """, theory_name=theory['current_name'])
                            count = result.single()['paper_count']
                            theory_counts[theory['current_name']] = count
                    
                    # Choose the most common name as canonical
                    canonical_name = max(theory_counts.items(), key=lambda x: x[1])[0]
                    
                    # If there's a tie, prefer the normalized canonical name or longest
                    max_count = max(theory_counts.values())
                    candidates = [name for name, count in theory_counts.items() if count == max_count]
                    if len(candidates) > 1:
                        # Prefer the name that matches the normalized canonical form
                        if canonical in candidates:
                            canonical_name = canonical
                        else:
                            # Otherwise use longest (most complete)
                            canonical_name = max(candidates, key=len)
                    
                    duplicates[canonical] = {
                        'canonical_name': canonical_name,
                        'duplicates': [t for t in theories if t['current_name'] != canonical_name],
                        'theory_counts': theory_counts
                    }
            
            return duplicates
    
    def merge_theory(self, canonical_name: str, duplicate_name: str, dry_run: bool = True):
        """Merge a duplicate theory into the canonical one"""
        with self.driver.session() as session:
            if dry_run:
                # Just check what would be merged
                result = session.run("""
                    MATCH (t1:Theory {name: $canonical_name})
                    MATCH (t2:Theory {name: $duplicate_name})
                    OPTIONAL MATCH (p:Paper)-[r:USES_THEORY]->(t2)
                    RETURN count(DISTINCT p) as paper_count,
                           collect(DISTINCT p.paper_id) as paper_ids
                """, canonical_name=canonical_name, duplicate_name=duplicate_name)
                
                record = result.single()
                return {
                    'canonical': canonical_name,
                    'duplicate': duplicate_name,
                    'paper_count': record['paper_count'],
                    'paper_ids': record['paper_ids']
                }
            else:
                # Actually merge
                with session.begin_transaction() as tx:
                    # Move all relationships from duplicate to canonical
                    tx.run("""
                        MATCH (p:Paper)-[r:USES_THEORY]->(t2:Theory {name: $duplicate_name})
                        MATCH (t1:Theory {name: $canonical_name})
                        MERGE (p)-[r2:USES_THEORY {
                            role: r.role,
                            section: r.section,
                            usage_context: r.usage_context
                        }]->(t1)
                        DELETE r
                    """, duplicate_name=duplicate_name, canonical_name=canonical_name)
                    
                    # Update canonical theory with original names from duplicate
                    tx.run("""
                        MATCH (t1:Theory {name: $canonical_name})
                        MATCH (t2:Theory {name: $duplicate_name})
                        SET t1.original_name = CASE 
                            WHEN t1.original_name IS NULL OR t1.original_name = '' 
                            THEN t2.original_name
                            WHEN t2.original_name IS NOT NULL AND t2.original_name <> ''
                            THEN t1.original_name + ', ' + t2.original_name
                            ELSE t1.original_name
                        END
                    """, canonical_name=canonical_name, duplicate_name=duplicate_name)
                    
                    # Delete duplicate theory node
                    tx.run("""
                        MATCH (t:Theory {name: $duplicate_name})
                        DELETE t
                    """, duplicate_name=duplicate_name)
                    
                    tx.commit()
                
                return {'merged': True}
    
    def fix_all_duplicates(self, dry_run: bool = True):
        """Fix all duplicate theories"""
        print("=" * 80)
        print("THEORY DUPLICATE MERGE")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE MERGE'}")
        print()
        
        duplicates = self.find_duplicate_theories()
        
        if not duplicates:
            print("✓ No duplicate theories found!")
            return
        
        print(f"Found {len(duplicates)} groups of duplicate theories:\n")
        
        total_merges = 0
        total_papers_affected = 0
        
        for canonical, group in duplicates.items():
            print(f"📋 Group: '{canonical}'")
            print(f"   Canonical name: '{group['canonical_name']}' ({group['theory_counts'].get(group['canonical_name'], 0)} papers)")
            print(f"   Duplicates to merge: {len(group['duplicates'])}")
            
            for dup in group['duplicates']:
                result = self.merge_theory(
                    group['canonical_name'],
                    dup['current_name'],
                    dry_run=dry_run
                )
                
                if dry_run:
                    print(f"   - '{dup['current_name']}' → '{group['canonical_name']}'")
                    print(f"     Affects {result['paper_count']} papers")
                    total_papers_affected += result['paper_count']
                else:
                    print(f"   ✓ Merged '{dup['current_name']}' → '{group['canonical_name']}'")
                
                total_merges += 1
            
            print()
        
        print("=" * 80)
        print(f"Summary:")
        print(f"  Total merges: {total_merges}")
        if dry_run:
            print(f"  Total papers affected: {total_papers_affected}")
        print("=" * 80)
        
        if dry_run:
            print("\n⚠️  This was a DRY RUN. No changes were made.")
            print("   Run with --execute to actually merge theories.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Merge duplicate theories in Neo4j')
    parser.add_argument('--execute', action='store_true', 
                       help='Actually perform the merge (default is dry run)')
    
    args = parser.parse_args()
    
    try:
        merger = TheoryMerger()
        merger.fix_all_duplicates(dry_run=not args.execute)
        merger.close()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

