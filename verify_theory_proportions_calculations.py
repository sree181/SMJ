#!/usr/bin/env python3
"""
Detailed Verification Report for Theory Proportions Tab
Queries Neo4j database directly and verifies all calculations
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from typing import Dict, List, Any
from collections import defaultdict

load_dotenv()

class TheoryProportionsVerifier:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def get_paper_counts_by_interval(self, start_year: int = 1985, end_year: int = 2025) -> List[Dict]:
        """Get paper counts by 5-year intervals"""
        intervals = []
        current_start = start_year
        
        while current_start < end_year:
            current_end = min(current_start + 5, end_year)
            
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year
                      AND p.year > 0
                    RETURN count(p) as count,
                           collect(p.paper_id) as paper_ids
                """, start_year=current_start, end_year=current_end)
                
                record = result.single()
                count = record['count'] if record else 0
                paper_ids = record['paper_ids'] if record else []
                
                intervals.append({
                    'interval': f"{current_start}-{current_end-1}",
                    'start_year': current_start,
                    'end_year': current_end - 1,
                    'count': count,
                    'paper_ids': paper_ids
                })
            
            current_start = current_end
        
        return intervals
    
    def get_theory_usage_by_interval(self, paper_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get theory usage counts for a set of papers with detailed info"""
        if not paper_ids:
            return {}
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.paper_id IN $paper_ids
                RETURN t.name as theory_name, 
                       count(DISTINCT p) as usage_count,
                       collect(DISTINCT p.paper_id) as paper_ids
            """, paper_ids=paper_ids)
            
            return {
                r['theory_name']: {
                    'count': r['usage_count'],
                    'paper_ids': r['paper_ids']
                } for r in result
            }
    
    def calculate_proportions(self, theory_usage: Dict[str, Dict[str, Any]], top_n: int = 20) -> List[Dict[str, Any]]:
        """Calculate proportions for top N theories"""
        if not theory_usage:
            return []
        
        # Sort by usage count (descending)
        sorted_theories = sorted(
            theory_usage.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        # Get top N
        top_theories = sorted_theories[:top_n]
        
        # Calculate total usage for top N
        total_usage = sum(t[1]['count'] for t in top_theories)
        
        # Calculate proportions
        proportions = []
        for theory_name, data in top_theories:
            usage_count = data['count']
            percentage = (usage_count / total_usage * 100) if total_usage > 0 else 0
            
            proportions.append({
                'theory_name': theory_name,
                'usage_count': usage_count,
                'percentage': percentage,
                'paper_ids': data['paper_ids']
            })
        
        return proportions
    
    def verify_interval_proportions(self, intervals: List[Dict], top_n: int = 20) -> List[Dict[str, Any]]:
        """Verify theory proportions for all intervals"""
        results = []
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            theory_usage = self.get_theory_usage_by_interval(paper_ids)
            proportions = self.calculate_proportions(theory_usage, top_n)
            
            total_theories = len(theory_usage)
            total_usage_all = sum(t['count'] for t in theory_usage.values())
            total_usage_top_n = sum(p['usage_count'] for p in proportions)
            coverage = (total_usage_top_n / total_usage_all * 100) if total_usage_all > 0 else 0
            
            results.append({
                'interval': interval,
                'paper_count': len(paper_ids),
                'total_theories': total_theories,
                'total_usage_all': total_usage_all,
                'total_usage_top_n': total_usage_top_n,
                'coverage': coverage,
                'top_theories': proportions
            })
        
        return results
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("THEORY PROPORTIONS TAB - DETAILED CALCULATION VERIFICATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("OVERVIEW")
        report.append("-" * 80)
        report.append("")
        report.append("The Theory Proportions tab displays pie charts showing the distribution")
        report.append("of theory usage across 5-year intervals. Each pie chart shows:")
        report.append("  - Top 20 theories by usage count")
        report.append("  - Percentage of total usage for each theory")
        report.append("  - Total usage count for the top 20 theories")
        report.append("")
        report.append("Data Source: Same as Theory Evolution tab")
        report.append("Endpoint: /api/analytics/theories/evolution-divergence")
        report.append("")
        
        # Get intervals
        intervals = self.get_paper_counts_by_interval(1985, 2025)
        
        report.append("SECTION 1: CALCULATION LOGIC")
        report.append("-" * 80)
        report.append("")
        report.append("1.1 Database Query:")
        report.append("  Query: MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)")
        report.append("         WHERE p.paper_id IN $paper_ids")
        report.append("         RETURN t.name, count(DISTINCT p) as usage_count")
        report.append("")
        report.append("1.2 Proportion Calculation:")
        report.append("  Step 1: Get all theories and their usage counts for the interval")
        report.append("  Step 2: Sort theories by usage count (descending)")
        report.append("  Step 3: Select top 20 theories")
        report.append("  Step 4: Calculate total usage for top 20: sum(usage_count)")
        report.append("  Step 5: Calculate percentage for each theory:")
        report.append("          percentage = (theory_usage_count / total_usage_top_20) * 100")
        report.append("")
        report.append("1.3 Display Logic:")
        report.append("  - Pie chart shows top 20 theories")
        report.append("  - Each slice size = theory percentage")
        report.append("  - Tooltip shows: 'X uses (Y%)'")
        report.append("  - List below shows top 10 theories with counts and percentages")
        report.append("")
        
        # Verify proportions
        results = self.verify_interval_proportions(intervals, top_n=20)
        
        report.append("SECTION 2: VERIFIED CALCULATIONS BY INTERVAL")
        report.append("-" * 80)
        report.append("")
        
        for result in results:
            report.append(f"Interval: {result['interval']}")
            report.append(f"  Papers: {result['paper_count']}")
            report.append(f"  Total Theories: {result['total_theories']}")
            report.append(f"  Total Theory Usage (All): {result['total_usage_all']}")
            report.append(f"  Total Theory Usage (Top 20): {result['total_usage_top_n']}")
            report.append(f"  Coverage (Top 20 / All): {result['coverage']:.1f}%")
            report.append("")
            report.append("  Top 20 Theories (for pie chart):")
            report.append("")
            
            for i, theory in enumerate(result['top_theories'], 1):
                report.append(f"    {i:2d}. {theory['theory_name']}")
                report.append(f"        Usage: {theory['usage_count']} papers")
                report.append(f"        Percentage: {theory['percentage']:.2f}%")
                report.append(f"        Calculation: ({theory['usage_count']} / {result['total_usage_top_n']}) * 100 = {theory['percentage']:.2f}%")
                report.append("")
            
            report.append("  Top 10 Theories (displayed in list below chart):")
            report.append("")
            for i, theory in enumerate(result['top_theories'][:10], 1):
                report.append(f"    {i:2d}. {theory['theory_name']}: {theory['usage_count']} uses ({theory['percentage']:.1f}%)")
            
            report.append("")
            report.append("  Verification:")
            report.append(f"    Sum of top 20 percentages: {sum(t['percentage'] for t in result['top_theories']):.2f}%")
            report.append(f"    Expected: 100.00%")
            report.append("")
            report.append("-" * 80)
            report.append("")
        
        # Summary statistics
        report.append("SECTION 3: SUMMARY STATISTICS")
        report.append("-" * 80)
        report.append("")
        
        total_theories = sum(r['total_theories'] for r in results)
        avg_theories_per_interval = total_theories / len(results) if results else 0
        avg_coverage = sum(r['coverage'] for r in results) / len(results) if results else 0
        
        report.append(f"Total Intervals: {len(results)}")
        report.append(f"Total Unique Theories (across all intervals): {total_theories}")
        report.append(f"Average Theories per Interval: {avg_theories_per_interval:.1f}")
        report.append(f"Average Coverage (Top 20 / All): {avg_coverage:.1f}%")
        report.append("")
        
        # Most common theories across intervals
        report.append("SECTION 4: MOST COMMON THEORIES ACROSS INTERVALS")
        report.append("-" * 80)
        report.append("")
        
        theory_appearances = defaultdict(int)
        theory_total_usage = defaultdict(int)
        
        for result in results:
            for theory in result['top_theories']:
                theory_appearances[theory['theory_name']] += 1
                theory_total_usage[theory['theory_name']] += theory['usage_count']
        
        most_common = sorted(
            theory_appearances.items(),
            key=lambda x: (x[1], theory_total_usage[x[0]]),
            reverse=True
        )[:20]
        
        report.append("Theories appearing in top 20 across multiple intervals:")
        report.append("")
        for theory_name, appearances in most_common:
            total_usage = theory_total_usage[theory_name]
            report.append(f"  {theory_name}:")
            report.append(f"    Appears in {appearances} intervals")
            report.append(f"    Total usage across intervals: {total_usage} papers")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF VERIFICATION REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    verifier = TheoryProportionsVerifier()
    try:
        report = verifier.generate_report()
        print(report)
        
        # Also save to file
        with open("THEORY_PROPORTIONS_VERIFICATION_REPORT.txt", "w") as f:
            f.write(report)
        print("\n✅ Report saved to THEORY_PROPORTIONS_VERIFICATION_REPORT.txt")
        
    finally:
        verifier.close()

if __name__ == "__main__":
    main()
