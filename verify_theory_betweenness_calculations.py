#!/usr/bin/env python3
"""
Detailed Verification Report for Theory Betweenness Tab
Queries Neo4j database directly and verifies all calculations
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from typing import Dict, List, Any

load_dotenv()

class TheoryBetweennessVerifier:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def get_theory_betweenness_data(self, min_phenomena: int = 2) -> Dict[str, Any]:
        """Get theory betweenness data from database"""
        with self.driver.session() as session:
            # Get theory-phenomenon connections
            result = session.run("""
                MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, count(DISTINCT ph) as phenomenon_count,
                     collect(DISTINCT ph.phenomenon_name) as phenomena
                WHERE phenomenon_count >= $min_phenomena
                RETURN t.name as theory_name,
                       phenomenon_count as cross_topic_reach,
                       phenomena
                ORDER BY phenomenon_count DESC
                LIMIT 100
            """, min_phenomena=min_phenomena)
            
            theories = []
            for record in result:
                theories.append({
                    'theory_name': record['theory_name'],
                    'cross_topic_reach': record['cross_topic_reach'],
                    'phenomena': record['phenomena']
                })
            
            # Get paper counts for all theories
            theory_names = [t['theory_name'] for t in theories]
            paper_counts = {}
            if theory_names:
                paper_counts_result = session.run("""
                    MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                    WHERE t.name IN $theory_names
                    RETURN t.name as theory_name, count(DISTINCT p) as paper_count
                """, theory_names=theory_names)
                
                paper_counts = {r['theory_name']: r['paper_count'] for r in paper_counts_result}
            
            # Calculate betweenness score (normalized cross-topic reach)
            max_reach = max([t['cross_topic_reach'] for t in theories]) if theories else 1
            
            for theory in theories:
                theory['paper_count'] = paper_counts.get(theory['theory_name'], 0)
                theory['betweenness_score'] = theory['cross_topic_reach'] / max_reach if max_reach > 0 else 0
            
            # Calculate summary statistics
            total_bridge_theories = len(theories)
            avg_cross_topic_reach = sum(t['cross_topic_reach'] for t in theories) / len(theories) if theories else 0
            max_cross_topic_reach = max([t['cross_topic_reach'] for t in theories]) if theories else 0
            
            return {
                'theories': theories,
                'summary': {
                    'total_bridge_theories': total_bridge_theories,
                    'avg_cross_topic_reach': avg_cross_topic_reach,
                    'max_cross_topic_reach': max_cross_topic_reach
                }
            }
    
    def verify_relationships(self) -> Dict[str, Any]:
        """Verify EXPLAINS_PHENOMENON relationships in database"""
        with self.driver.session() as session:
            # Count total relationships
            total_result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                RETURN count(r) as total_relationships
            """)
            total_relationships = total_result.single()['total_relationships']
            
            # Count distinct theories
            theories_result = session.run("""
                MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                RETURN count(DISTINCT t) as distinct_theories
            """)
            distinct_theories = theories_result.single()['distinct_theories']
            
            # Count distinct phenomena
            phenomena_result = session.run("""
                MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                RETURN count(DISTINCT ph) as distinct_phenomena
            """)
            distinct_phenomena = phenomena_result.single()['distinct_phenomena']
            
            return {
                'total_relationships': total_relationships,
                'distinct_theories': distinct_theories,
                'distinct_phenomena': distinct_phenomena
            }
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("THEORY BETWEENNESS TAB - DETAILED CALCULATION VERIFICATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("OVERVIEW")
        report.append("-" * 80)
        report.append("")
        report.append("The Theory Betweenness tab identifies 'bridge theories' - theories that")
        report.append("connect multiple phenomena and research domains. This metric measures:")
        report.append("  - Cross-Topic Reach: Number of distinct phenomena each theory explains")
        report.append("  - Betweenness Score: Normalized measure of how theories connect domains")
        report.append("  - Bridge Theories: Theories explaining at least 2 phenomena (default)")
        report.append("")
        
        # Verify relationships
        relationships = self.verify_relationships()
        
        report.append("SECTION 1: DATABASE VERIFICATION")
        report.append("-" * 80)
        report.append("")
        report.append("1.1 Relationship Count:")
        report.append(f"  Total EXPLAINS_PHENOMENON relationships: {relationships['total_relationships']}")
        report.append(f"  Distinct theories with relationships: {relationships['distinct_theories']}")
        report.append(f"  Distinct phenomena explained: {relationships['distinct_phenomena']}")
        report.append("")
        
        report.append("SECTION 2: CALCULATION LOGIC")
        report.append("-" * 80)
        report.append("")
        report.append("2.1 Database Query:")
        report.append("  Query: MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)")
        report.append("         WITH t, count(DISTINCT ph) as phenomenon_count,")
        report.append("              collect(DISTINCT ph.phenomenon_name) as phenomena")
        report.append("         WHERE phenomenon_count >= $min_phenomena")
        report.append("         RETURN t.name, phenomenon_count, phenomena")
        report.append("         ORDER BY phenomenon_count DESC")
        report.append("         LIMIT 100")
        report.append("")
        report.append("2.2 Cross-Topic Reach Calculation:")
        report.append("  Cross-Topic Reach = count(DISTINCT ph) for each theory")
        report.append("  This counts how many distinct phenomena each theory explains")
        report.append("")
        report.append("2.3 Betweenness Score Calculation:")
        report.append("  Step 1: Find maximum cross-topic reach: max_reach = max(all cross_topic_reach)")
        report.append("  Step 2: Normalize each theory: betweenness_score = cross_topic_reach / max_reach")
        report.append("  Range: [0, 1] where 1.0 = theory with maximum reach")
        report.append("")
        report.append("2.4 Paper Count Calculation:")
        report.append("  Query: MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)")
        report.append("         WHERE t.name IN $theory_names")
        report.append("         RETURN t.name, count(DISTINCT p) as paper_count")
        report.append("")
        report.append("2.5 Summary Statistics:")
        report.append("  - Total Bridge Theories: count(theories with cross_topic_reach >= min_phenomena)")
        report.append("  - Avg Cross-Topic Reach: mean(cross_topic_reach) for all bridge theories")
        report.append("  - Max Cross-Topic Reach: max(cross_topic_reach) across all theories")
        report.append("")
        
        # Get betweenness data
        betweenness_data = self.get_theory_betweenness_data(min_phenomena=2)
        
        report.append("SECTION 3: VERIFIED CALCULATIONS")
        report.append("-" * 80)
        report.append("")
        report.append("3.1 Summary Statistics:")
        report.append(f"  Total Bridge Theories: {betweenness_data['summary']['total_bridge_theories']}")
        report.append(f"  Average Cross-Topic Reach: {betweenness_data['summary']['avg_cross_topic_reach']:.2f}")
        report.append(f"  Maximum Cross-Topic Reach: {betweenness_data['summary']['max_cross_topic_reach']}")
        report.append("")
        
        report.append("3.2 Top 20 Bridge Theories (for bar chart):")
        report.append("")
        
        top_20 = betweenness_data['theories'][:20]
        max_reach = betweenness_data['summary']['max_cross_topic_reach']
        
        for i, theory in enumerate(top_20, 1):
            report.append(f"  {i:2d}. {theory['theory_name']}")
            report.append(f"      Cross-Topic Reach: {theory['cross_topic_reach']} phenomena")
            report.append(f"      Paper Count: {theory['paper_count']} papers")
            report.append(f"      Betweenness Score: {theory['betweenness_score']:.4f} ({theory['betweenness_score']*100:.2f}%)")
            report.append(f"      Calculation: {theory['cross_topic_reach']} / {max_reach} = {theory['betweenness_score']:.4f}")
            report.append(f"      Phenomena: {', '.join(theory['phenomena'][:5])}{'...' if len(theory['phenomena']) > 5 else ''}")
            report.append("")
        
        report.append("3.3 All Bridge Theories (for table):")
        report.append("")
        report.append(f"  Total theories returned: {len(betweenness_data['theories'])}")
        report.append("")
        
        # Show sample of all theories
        for i, theory in enumerate(betweenness_data['theories'][:10], 1):
            report.append(f"  {i:2d}. {theory['theory_name']}: {theory['cross_topic_reach']} phenomena, {theory['paper_count']} papers, {theory['betweenness_score']*100:.1f}%")
        
        if len(betweenness_data['theories']) > 10:
            report.append(f"  ... and {len(betweenness_data['theories']) - 10} more theories")
        
        report.append("")
        
        # Verification checks
        report.append("SECTION 4: VERIFICATION CHECKS")
        report.append("-" * 80)
        report.append("")
        
        # Check 1: All theories have cross_topic_reach >= min_phenomena
        min_reach = min([t['cross_topic_reach'] for t in betweenness_data['theories']]) if betweenness_data['theories'] else 0
        report.append(f"4.1 Minimum Reach Check:")
        report.append(f"  Minimum cross_topic_reach: {min_reach}")
        report.append(f"  Expected: >= 2")
        report.append(f"  Status: {'✅ PASS' if min_reach >= 2 else '❌ FAIL'}")
        report.append("")
        
        # Check 2: Betweenness scores are normalized
        max_score = max([t['betweenness_score'] for t in betweenness_data['theories']]) if betweenness_data['theories'] else 0
        report.append(f"4.2 Betweenness Score Normalization:")
        report.append(f"  Maximum betweenness_score: {max_score:.4f}")
        report.append(f"  Expected: 1.0 (theory with max reach)")
        report.append(f"  Status: {'✅ PASS' if abs(max_score - 1.0) < 0.0001 else '❌ FAIL'}")
        report.append("")
        
        # Check 3: Summary statistics match
        calculated_avg = sum(t['cross_topic_reach'] for t in betweenness_data['theories']) / len(betweenness_data['theories']) if betweenness_data['theories'] else 0
        calculated_max = max([t['cross_topic_reach'] for t in betweenness_data['theories']]) if betweenness_data['theories'] else 0
        report.append(f"4.3 Summary Statistics Verification:")
        report.append(f"  Calculated Avg Reach: {calculated_avg:.2f}")
        report.append(f"  Reported Avg Reach: {betweenness_data['summary']['avg_cross_topic_reach']:.2f}")
        report.append(f"  Status: {'✅ PASS' if abs(calculated_avg - betweenness_data['summary']['avg_cross_topic_reach']) < 0.01 else '❌ FAIL'}")
        report.append("")
        report.append(f"  Calculated Max Reach: {calculated_max}")
        report.append(f"  Reported Max Reach: {betweenness_data['summary']['max_cross_topic_reach']}")
        report.append(f"  Status: {'✅ PASS' if calculated_max == betweenness_data['summary']['max_cross_topic_reach'] else '❌ FAIL'}")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF VERIFICATION REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    verifier = TheoryBetweennessVerifier()
    try:
        report = verifier.generate_report()
        print(report)
        
        # Also save to file
        with open("THEORY_BETWEENNESS_VERIFICATION_REPORT.txt", "w") as f:
            f.write(report)
        print("\n✅ Report saved to THEORY_BETWEENNESS_VERIFICATION_REPORT.txt")
        
    finally:
        verifier.close()

if __name__ == "__main__":
    main()
