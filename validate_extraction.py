#!/usr/bin/env python3
"""
Data Quality Validation for Batch Processing
Validates extracted entities and relationships for completeness and accuracy
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class ExtractionValidator:
    """Validates the quality and completeness of extracted data"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USER")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.driver = None
        self.connect()
    
    def connect(self):
        """Connect to Neo4j"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            print("✓ Connected to Neo4j for validation")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def validate_paper_completeness(self) -> Dict[str, Any]:
        """Validate that papers have complete entity extractions"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Get all papers with their entity counts
                result = session.run("""
                    MATCH (p:Paper)
                    OPTIONAL MATCH (p)-[:HAS_QUESTION]->(q:ResearchQuestion)
                    OPTIONAL MATCH (p)-[:HAS_METHODOLOGY]->(m:Methodology)
                    OPTIONAL MATCH (p)-[:HAS_FINDING]->(f:Finding)
                    OPTIONAL MATCH (p)-[:HAS_ENTITY]->(e:Entity)
                    RETURN p.paper_id as paper_id, p.year as year,
                           count(DISTINCT q) as questions,
                           count(DISTINCT m) as methodologies,
                           count(DISTINCT f) as findings,
                           count(DISTINCT e) as entities
                """)
                
                papers = []
                for record in result:
                    papers.append({
                        'paper_id': record['paper_id'],
                        'year': record['year'],
                        'questions': record['questions'],
                        'methodologies': record['methodologies'],
                        'findings': record['findings'],
                        'entities': record['entities'],
                        'total_entities': record['questions'] + record['methodologies'] + record['findings'] + record['entities']
                    })
                
                return {
                    'total_papers': len(papers),
                    'papers_with_questions': len([p for p in papers if p['questions'] > 0]),
                    'papers_with_methodologies': len([p for p in papers if p['methodologies'] > 0]),
                    'papers_with_findings': len([p for p in papers if p['findings'] > 0]),
                    'papers_with_entities': len([p for p in papers if p['entities'] > 0]),
                    'papers_with_minimal_entities': len([p for p in papers if p['total_entities'] >= 5]),
                    'average_entities_per_paper': sum(p['total_entities'] for p in papers) / len(papers) if papers else 0,
                    'paper_details': papers
                }
        except Exception as e:
            print(f"Error validating paper completeness: {e}")
            return {}
    
    def validate_entity_quality(self) -> Dict[str, Any]:
        """Validate the quality of extracted entities"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Check for empty or very short entities
                result = session.run("""
                    MATCH (q:ResearchQuestion)
                    WHERE size(q.question) < 10
                    RETURN count(q) as short_questions
                """)
                short_questions = result.single()['short_questions']
                
                result = session.run("""
                    MATCH (m:Methodology)
                    WHERE size(m.methodology) < 5
                    RETURN count(m) as short_methodologies
                """)
                short_methodologies = result.single()['short_methodologies']
                
                result = session.run("""
                    MATCH (f:Finding)
                    WHERE size(f.finding) < 10
                    RETURN count(f) as short_findings
                """)
                short_findings = result.single()['short_findings']
                
                # Check for duplicate entities
                result = session.run("""
                    MATCH (e:Entity)
                    WITH e.name as name, count(e) as count
                    WHERE count > 1
                    RETURN count as duplicate_entities
                """)
                duplicate_entities = sum(record['duplicate_entities'] for record in result)
                
                return {
                    'short_questions': short_questions,
                    'short_methodologies': short_methodologies,
                    'short_findings': short_findings,
                    'duplicate_entities': duplicate_entities
                }
        except Exception as e:
            print(f"Error validating entity quality: {e}")
            return {}
    
    def validate_relationships(self) -> Dict[str, Any]:
        """Validate the quality of relationships"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Get relationship statistics
                result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                """)
                
                relationships = {record['rel_type']: record['count'] for record in result}
                
                # Check for orphaned entities (entities without relationships)
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE NOT (e)-[]-()
                    RETURN count(e) as orphaned_entities
                """)
                orphaned_entities = result.single()['orphaned_entities']
                
                return {
                    'relationship_types': relationships,
                    'orphaned_entities': orphaned_entities,
                    'total_relationships': sum(relationships.values())
                }
        except Exception as e:
            print(f"Error validating relationships: {e}")
            return {}
    
    def validate_temporal_consistency(self) -> Dict[str, Any]:
        """Validate temporal consistency of the data"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                # Get year distribution
                result = session.run("""
                    MATCH (p:Paper)
                    RETURN p.year as year, count(p) as count
                    ORDER BY year
                """)
                
                year_distribution = {record['year']: record['count'] for record in result}
                
                # Check for papers with missing years
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year IS NULL OR p.year = 0
                    RETURN count(p) as missing_years
                """)
                missing_years = result.single()['missing_years']
                
                return {
                    'year_distribution': year_distribution,
                    'missing_years': missing_years,
                    'year_range': {
                        'min': min(year_distribution.keys()) if year_distribution else None,
                        'max': max(year_distribution.keys()) if year_distribution else None
                    }
                }
        except Exception as e:
            print(f"Error validating temporal consistency: {e}")
            return {}
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        print("🔍 Generating validation report...")
        
        report = {
            'timestamp': str(datetime.now()),
            'paper_completeness': self.validate_paper_completeness(),
            'entity_quality': self.validate_entity_quality(),
            'relationships': self.validate_relationships(),
            'temporal_consistency': self.validate_temporal_consistency()
        }
        
        # Calculate overall quality score
        completeness = report['paper_completeness']
        if completeness:
            total_papers = completeness['total_papers']
            if total_papers > 0:
                quality_score = (
                    completeness['papers_with_questions'] / total_papers * 0.3 +
                    completeness['papers_with_methodologies'] / total_papers * 0.2 +
                    completeness['papers_with_findings'] / total_papers * 0.3 +
                    completeness['papers_with_entities'] / total_papers * 0.2
                ) * 100
                report['overall_quality_score'] = quality_score
        
        return report
    
    def print_validation_summary(self, report: Dict[str, Any]):
        """Print a summary of validation results"""
        print("\n" + "="*60)
        print("📊 EXTRACTION VALIDATION REPORT")
        print("="*60)
        
        # Paper completeness
        completeness = report.get('paper_completeness', {})
        if completeness:
            print(f"📄 Total Papers: {completeness.get('total_papers', 0)}")
            print(f"❓ Papers with Questions: {completeness.get('papers_with_questions', 0)}")
            print(f"🔬 Papers with Methodologies: {completeness.get('papers_with_methodologies', 0)}")
            print(f"📈 Papers with Findings: {completeness.get('papers_with_findings', 0)}")
            print(f"🏷️  Papers with Entities: {completeness.get('papers_with_entities', 0)}")
            print(f"✅ Papers with Minimal Entities (≥5): {completeness.get('papers_with_minimal_entities', 0)}")
            print(f"📊 Average Entities per Paper: {completeness.get('average_entities_per_paper', 0):.2f}")
            print()
        
        # Entity quality
        quality = report.get('entity_quality', {})
        if quality:
            print("🔍 Entity Quality Issues:")
            print(f"  Short Questions (<10 chars): {quality.get('short_questions', 0)}")
            print(f"  Short Methodologies (<5 chars): {quality.get('short_methodologies', 0)}")
            print(f"  Short Findings (<10 chars): {quality.get('short_findings', 0)}")
            print(f"  Duplicate Entities: {quality.get('duplicate_entities', 0)}")
            print()
        
        # Relationships
        relationships = report.get('relationships', {})
        if relationships:
            print("🔗 Relationship Statistics:")
            for rel_type, count in relationships.get('relationship_types', {}).items():
                print(f"  {rel_type}: {count}")
            print(f"  Orphaned Entities: {relationships.get('orphaned_entities', 0)}")
            print()
        
        # Overall quality score
        if 'overall_quality_score' in report:
            score = report['overall_quality_score']
            print(f"🎯 Overall Quality Score: {score:.1f}/100")
            if score >= 80:
                print("✅ Excellent extraction quality!")
            elif score >= 60:
                print("⚠️  Good extraction quality, some improvements needed")
            else:
                print("❌ Poor extraction quality, review extraction process")
        
        print("="*60)
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()

def main():
    """Main validation function"""
    validator = ExtractionValidator()
    
    try:
        report = validator.generate_validation_report()
        validator.print_validation_summary(report)
        
        # Save detailed report
        with open('validation_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print("\n📄 Detailed report saved to: validation_report.json")
        
    finally:
        validator.close()

if __name__ == "__main__":
    main()
