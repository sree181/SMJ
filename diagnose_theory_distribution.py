#!/usr/bin/env python3
"""
Diagnostic script to check theory distribution across papers
Identifies if the same theories are being assigned to all papers
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

class TheoryDiagnostic:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not self.uri or not self.password:
            raise ValueError("NEO4J_URI and NEO4J_PASSWORD must be set in .env file")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def get_all_theories(self):
        """Get all theories and their paper counts"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)
                OPTIONAL MATCH (p:Paper)-[:USES_THEORY]->(t)
                RETURN t.name as theory_name, 
                       t.original_name as original_name,
                       count(DISTINCT p) as paper_count,
                       collect(DISTINCT p.paper_id) as paper_ids
                ORDER BY paper_count DESC
            """)
            
            theories = []
            for record in result:
                theories.append({
                    'name': record['theory_name'],
                    'original_name': record['original_name'],
                    'paper_count': record['paper_count'],
                    'paper_ids': record['paper_ids']
                })
            return theories
    
    def get_paper_theory_distribution(self):
        """Get theory distribution per paper"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)
                OPTIONAL MATCH (p)-[r:USES_THEORY]->(t:Theory)
                RETURN p.paper_id as paper_id,
                       p.title as title,
                       count(DISTINCT t) as theory_count,
                       collect(DISTINCT t.name) as theories
                ORDER BY p.paper_id
            """)
            
            papers = []
            for record in result:
                papers.append({
                    'paper_id': record['paper_id'],
                    'title': record['title'],
                    'theory_count': record['theory_count'],
                    'theories': record['theories']
                })
            return papers
    
    def check_duplicate_theories(self):
        """Check if multiple theories are being normalized to the same canonical form"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (t:Theory)
                RETURN t.name as theory_name,
                       collect(DISTINCT t.original_name) as original_names
                ORDER BY size(collect(DISTINCT t.original_name)) DESC
            """)
            
            duplicates = []
            for record in result:
                original_names = [name for name in record['original_names'] if name]
                if len(original_names) > 1:
                    duplicates.append({
                        'canonical_name': record['theory_name'],
                        'original_names': original_names
                    })
            return duplicates
    
    def get_most_common_theories(self, limit=20):
        """Get most commonly used theories"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                RETURN t.name as theory_name,
                       count(DISTINCT p) as paper_count,
                       count(*) as relationship_count
                ORDER BY paper_count DESC
                LIMIT $limit
            """, limit=limit)
            
            common = []
            for record in result:
                common.append({
                    'theory_name': record['theory_name'],
                    'paper_count': record['paper_count'],
                    'relationship_count': record['relationship_count']
                })
            return common
    
    def analyze_theory_overlap(self):
        """Check if papers share the same set of theories"""
        papers = self.get_paper_theory_distribution()
        
        # Group papers by their theory sets
        theory_sets = defaultdict(list)
        for paper in papers:
            theory_set = tuple(sorted(paper['theories']))
            theory_sets[theory_set].append(paper['paper_id'])
        
        # Find papers with identical theory sets
        identical_sets = {k: v for k, v in theory_sets.items() if len(v) > 1}
        
        return identical_sets
    
    def print_report(self):
        """Print comprehensive diagnostic report"""
        print("=" * 80)
        print("THEORY DISTRIBUTION DIAGNOSTIC REPORT")
        print("=" * 80)
        
        # Get total counts
        with self.driver.session() as session:
            total_papers = session.run("MATCH (p:Paper) RETURN count(p) as count").single()['count']
            total_theories = session.run("MATCH (t:Theory) RETURN count(t) as count").single()['count']
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Papers: {total_papers}")
        print(f"   Total Theories: {total_theories}")
        
        # Most common theories
        print(f"\n🔝 TOP 20 MOST COMMON THEORIES:")
        common = self.get_most_common_theories(20)
        for i, theory in enumerate(common, 1):
            percentage = (theory['paper_count'] / total_papers * 100) if total_papers > 0 else 0
            print(f"   {i:2d}. {theory['theory_name']:<40} {theory['paper_count']:3d} papers ({percentage:.1f}%)")
        
        # Check for duplicate normalization
        print(f"\n🔄 NORMALIZATION CHECK:")
        duplicates = self.check_duplicate_theories()
        if duplicates:
            print(f"   Found {len(duplicates)} theories with multiple original names:")
            for dup in duplicates[:10]:  # Show first 10
                print(f"   - '{dup['canonical_name']}' from:")
                for orig in dup['original_names'][:5]:  # Show first 5 originals
                    print(f"     • {orig}")
                if len(dup['original_names']) > 5:
                    print(f"     ... and {len(dup['original_names']) - 5} more")
        else:
            print("   ✓ No duplicate normalization detected")
        
        # Theory overlap analysis
        print(f"\n📋 THEORY SET OVERLAP:")
        identical_sets = self.analyze_theory_overlap()
        if identical_sets:
            print(f"   ⚠️  Found {len(identical_sets)} theory sets shared by multiple papers:")
            for theory_set, paper_ids in list(identical_sets.items())[:10]:  # Show first 10
                if len(theory_set) > 0:
                    print(f"   - {len(paper_ids)} papers share these {len(theory_set)} theories:")
                    for theory in theory_set[:5]:
                        print(f"     • {theory}")
                    if len(theory_set) > 5:
                        print(f"     ... and {len(theory_set) - 5} more")
                    print(f"     Papers: {', '.join(paper_ids[:5])}")
                    if len(paper_ids) > 5:
                        print(f"     ... and {len(paper_ids) - 5} more papers")
        else:
            print("   ✓ No identical theory sets found")
        
        # Paper-level distribution
        print(f"\n📄 PAPER-LEVEL DISTRIBUTION:")
        papers = self.get_paper_theory_distribution()
        theory_counts = [p['theory_count'] for p in papers]
        if theory_counts:
            avg_theories = sum(theory_counts) / len(theory_counts)
            max_theories = max(theory_counts)
            min_theories = min(theory_counts)
            print(f"   Average theories per paper: {avg_theories:.1f}")
            print(f"   Min theories: {min_theories}, Max theories: {max_theories}")
            
            # Show papers with most/least theories
            papers_sorted = sorted(papers, key=lambda x: x['theory_count'], reverse=True)
            print(f"\n   Papers with most theories:")
            for p in papers_sorted[:5]:
                print(f"   - {p['paper_id']}: {p['theory_count']} theories")
                for theory in p['theories'][:3]:
                    print(f"     • {theory}")
                if len(p['theories']) > 3:
                    print(f"     ... and {len(p['theories']) - 3} more")
            
            print(f"\n   Papers with fewest theories:")
            for p in papers_sorted[-5:]:
                print(f"   - {p['paper_id']}: {p['theory_count']} theories")
                if p['theories']:
                    for theory in p['theories']:
                        print(f"     • {theory}")
        
        print("\n" + "=" * 80)

if __name__ == "__main__":
    try:
        diagnostic = TheoryDiagnostic()
        diagnostic.print_report()
        diagnostic.close()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

