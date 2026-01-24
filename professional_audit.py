#!/usr/bin/env python3
"""
Professional System Audit
Comprehensive assessment of data quality, API consistency, and production readiness
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv
from typing import Dict, List, Any
from collections import defaultdict

load_dotenv()

class ProfessionalAudit:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.issues = []
        self.warnings = []
        self.recommendations = []
    
    def run_full_audit(self):
        """Run comprehensive audit"""
        print("=" * 80)
        print("PROFESSIONAL SYSTEM AUDIT")
        print("=" * 80)
        
        with self.driver.session() as session:
            # 1. Data Completeness
            self.audit_data_completeness(session)
            
            # 2. Schema Consistency
            self.audit_schema_consistency(session)
            
            # 3. Relationship Integrity
            self.audit_relationship_integrity(session)
            
            # 4. Data Quality
            self.audit_data_quality(session)
            
            # 5. Performance Indicators
            self.audit_performance(session)
        
        # Print summary
        self.print_summary()
    
    def audit_data_completeness(self, session):
        """Check if all expected data is present"""
        print("\n" + "=" * 80)
        print("1. DATA COMPLETENESS AUDIT")
        print("=" * 80)
        
        # Basic counts
        counts = {}
        entities = ['Paper', 'Theory', 'Method', 'Phenomenon', 'Author', 'ResearchQuestion', 'Variable', 'Finding', 'Contribution']
        
        for entity in entities:
            result = session.run(f'MATCH (n:{entity}) RETURN count(n) as count')
            count = result.single()['count']
            counts[entity] = count
            status = "✓" if count > 0 else "✗"
            print(f"   {status} {entity}: {count}")
        
        # Relationship counts
        print("\n   Relationship Completeness:")
        relationships = [
            ('Paper', 'USES_THEORY', 'Theory'),
            ('Paper', 'USES_METHOD', 'Method'),
            ('Paper', 'STUDIES_PHENOMENON', 'Phenomenon'),
            ('Paper', 'AUTHORED_BY', 'Author'),
            ('Paper', 'ADDRESSES', 'ResearchQuestion'),
            ('Theory', 'EXPLAINS_PHENOMENON', 'Phenomenon')
        ]
        
        for source, rel, target in relationships:
            result = session.run(f'MATCH (a:{source})-[r:{rel}]->(b:{target}) RETURN count(r) as count')
            count = result.single()['count']
            status = "✓" if count > 0 else "✗"
            print(f"   {status} {source}-[{rel}]->{target}: {count}")
            
            if count == 0 and source == 'Paper' and target == 'Author':
                self.issues.append(f"CRITICAL: No {rel} relationships found - Authors not linked to papers")
        
        # Papers missing critical data
        print("\n   Papers Missing Critical Data:")
        result = session.run('''
            MATCH (p:Paper)
            WHERE NOT (p)-[:USES_THEORY]->()
            RETURN count(p) as count
        ''')
        papers_no_theory = result.single()['count']
        if papers_no_theory > 0:
            pct = (papers_no_theory / counts['Paper']) * 100 if counts['Paper'] > 0 else 0
            print(f"   ⚠️  Papers without theories: {papers_no_theory} ({pct:.1f}%)")
            if pct > 10:
                self.warnings.append(f"{pct:.1f}% of papers missing theories")
        
        result = session.run('''
            MATCH (p:Paper)
            WHERE NOT (p)-[:USES_METHOD]->()
            RETURN count(p) as count
        ''')
        papers_no_method = result.single()['count']
        if papers_no_method > 0:
            pct = (papers_no_method / counts['Paper']) * 100 if counts['Paper'] > 0 else 0
            print(f"   ⚠️  Papers without methods: {papers_no_method} ({pct:.1f}%)")
            if pct > 10:
                self.warnings.append(f"{pct:.1f}% of papers missing methods")
    
    def audit_schema_consistency(self, session):
        """Check schema consistency"""
        print("\n" + "=" * 80)
        print("2. SCHEMA CONSISTENCY AUDIT")
        print("=" * 80)
        
        # Check Paper node properties
        result = session.run('''
            MATCH (p:Paper)
            RETURN keys(p) as keys
            LIMIT 1
        ''')
        if result.peek():
            paper_keys = set(result.single()['keys'])
            expected = {'paper_id', 'title', 'year', 'publication_year'}
            
            # Check for inconsistent year fields
            result = session.run('''
                MATCH (p:Paper)
                WHERE p.year IS NULL AND p.publication_year IS NULL
                RETURN count(p) as count
            ''')
            papers_no_year = result.single()['count']
            if papers_no_year > 0:
                self.issues.append(f"Schema inconsistency: {papers_no_year} papers missing both 'year' and 'publication_year'")
                print(f"   ✗ Papers missing year field: {papers_no_year}")
            
            # Check for both year fields existing
            result = session.run('''
                MATCH (p:Paper)
                WHERE p.year IS NOT NULL AND p.publication_year IS NOT NULL
                RETURN count(p) as count
            ''')
            papers_both_year = result.single()['count']
            if papers_both_year > 0:
                self.warnings.append(f"{papers_both_year} papers have both 'year' and 'publication_year' - should standardize")
                print(f"   ⚠️  Papers with both year fields: {papers_both_year}")
        
        # Check relationship property consistency
        print("\n   Relationship Property Consistency:")
        result = session.run('''
            MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
            WHERE r.role IS NULL
            RETURN count(r) as count
        ''')
        theory_rels_no_role = result.single()['count']
        if theory_rels_no_role > 0:
            self.warnings.append(f"{theory_rels_no_role} USES_THEORY relationships missing 'role' property")
            print(f"   ⚠️  USES_THEORY without 'role': {theory_rels_no_role}")
    
    def audit_relationship_integrity(self, session):
        """Check relationship integrity"""
        print("\n" + "=" * 80)
        print("3. RELATIONSHIP INTEGRITY AUDIT")
        print("=" * 80)
        
        # Check for orphaned nodes
        print("\n   Orphaned Nodes:")
        result = session.run('''
            MATCH (t:Theory)
            WHERE NOT (t)<-[:USES_THEORY]-()
            RETURN count(t) as count
        ''')
        orphaned_theories = result.single()['count']
        if orphaned_theories > 0:
            self.warnings.append(f"{orphaned_theories} theories not connected to any papers")
            print(f"   ⚠️  Orphaned theories: {orphaned_theories}")
        
        result = session.run('''
            MATCH (m:Method)
            WHERE NOT (m)<-[:USES_METHOD]-()
            RETURN count(m) as count
        ''')
        orphaned_methods = result.single()['count']
        if orphaned_methods > 0:
            self.warnings.append(f"{orphaned_methods} methods not connected to any papers")
            print(f"   ⚠️  Orphaned methods: {orphaned_methods}")
        
        # Check EXPLAINS_PHENOMENON relationships
        result = session.run('''
            MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
            RETURN count(r) as count
        ''')
        explains_count = result.single()['count']
        print(f"\n   ✓ EXPLAINS_PHENOMENON relationships: {explains_count}")
        
        if explains_count == 0:
            self.issues.append("CRITICAL: No EXPLAINS_PHENOMENON relationships found - Theory-phenomenon connections missing")
        
        # Check for papers that should have EXPLAINS relationships
        result = session.run('''
            MATCH (p:Paper)-[:USES_THEORY]->(t:Theory),
                  (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
            WHERE NOT (t)-[:EXPLAINS_PHENOMENON]->(ph)
            RETURN count(DISTINCT {theory: t.name, phenomenon: ph.phenomenon_name}) as count
        ''')
        missing_explains = result.single()['count']
        if missing_explains > 0:
            self.issues.append(f"Missing {missing_explains} EXPLAINS_PHENOMENON relationships that should exist based on paper connections")
            print(f"   ✗ Missing EXPLAINS relationships: {missing_explains}")
    
    def audit_data_quality(self, session):
        """Check data quality issues"""
        print("\n" + "=" * 80)
        print("4. DATA QUALITY AUDIT")
        print("=" * 80)
        
        # Check for empty/null values
        result = session.run('''
            MATCH (p:Paper)
            WHERE p.title IS NULL OR p.title = ""
            RETURN count(p) as count
        ''')
        papers_no_title = result.single()['count']
        if papers_no_title > 0:
            self.issues.append(f"{papers_no_title} papers missing titles")
            print(f"   ✗ Papers without titles: {papers_no_title}")
        
        # Check for duplicate paper_ids
        result = session.run('''
            MATCH (p:Paper)
            WITH p.paper_id as id, count(p) as count
            WHERE count > 1
            RETURN count(*) as duplicates
        ''')
        duplicates = result.single()['duplicates']
        if duplicates > 0:
            self.issues.append(f"CRITICAL: {duplicates} duplicate paper_ids found")
            print(f"   ✗ Duplicate paper_ids: {duplicates}")
        
        # Check theory name normalization
        result = session.run('''
            MATCH (t:Theory)
            WHERE t.original_name IS NOT NULL AND t.name = t.original_name
            RETURN count(t) as count
        ''')
        normalized_theories = result.single()['count']
        print(f"   ✓ Theories with normalization: {normalized_theories}")
    
    def audit_performance(self, session):
        """Check performance indicators"""
        print("\n" + "=" * 80)
        print("5. PERFORMANCE AUDIT")
        print("=" * 80)
        
        # Check indexes
        result = session.run('SHOW INDEXES')
        indexes = list(result)
        print(f"\n   ✓ Indexes found: {len(indexes)}")
        
        # Check for missing critical indexes
        index_names = [idx.get('name', '') for idx in indexes]
        critical_indexes = [
            'paper_id_index',
            'theory_name_index',
            'method_name_index',
            'phenomenon_name_index'
        ]
        
        for idx_name in critical_indexes:
            if not any(idx_name in name for name in index_names):
                self.recommendations.append(f"Create index for {idx_name}")
                print(f"   ⚠️  Missing index: {idx_name}")
    
    def print_summary(self):
        """Print audit summary"""
        print("\n" + "=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        
        print(f"\n🔴 CRITICAL ISSUES ({len(self.issues)}):")
        for i, issue in enumerate(self.issues, 1):
            print(f"   {i}. {issue}")
        
        print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
        for i, warning in enumerate(self.warnings, 1):
            print(f"   {i}. {warning}")
        
        print(f"\n💡 RECOMMENDATIONS ({len(self.recommendations)}):")
        for i, rec in enumerate(self.recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "=" * 80)
        print("PRIORITY FIXES NEEDED:")
        print("=" * 80)
        
        if self.issues:
            print("\n1. CRITICAL (Fix Immediately):")
            for issue in self.issues:
                if "CRITICAL" in issue:
                    print(f"   - {issue}")
        
        if self.warnings:
            print("\n2. HIGH PRIORITY (Fix Soon):")
            for warning in self.warnings[:5]:
                print(f"   - {warning}")
    
    def close(self):
        self.driver.close()

if __name__ == "__main__":
    audit = ProfessionalAudit()
    try:
        audit.run_full_audit()
    finally:
        audit.close()
