#!/usr/bin/env python3
"""
Detailed Verification Report for Analytics Charts Tab
Queries Neo4j database directly and verifies all calculations
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import math
from collections import defaultdict
from typing import Dict, List, Any

load_dotenv()

class AnalyticsVerifier:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
    
    def close(self):
        self.driver.close()
    
    def get_paper_counts_by_interval(self, start_year: int = 1985, end_year: int = 2025) -> List[Dict]:
        """Get paper counts by 5-year intervals - VERIFIED"""
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
    
    def verify_summary_metrics(self, intervals: List[Dict]) -> Dict[str, Any]:
        """Calculate and verify summary metrics"""
        total_papers = sum(i['count'] for i in intervals)
        avg_per_interval = total_papers / len(intervals) if intervals else 0
        peak_interval = max(intervals, key=lambda x: x['count']) if intervals else None
        
        return {
            'total_papers': total_papers,
            'avg_per_interval': round(avg_per_interval, 1),
            'peak_interval': peak_interval['interval'] if peak_interval else None,
            'peak_count': peak_interval['count'] if peak_interval else 0,
            'total_intervals': len(intervals)
        }
    
    def get_theory_usage_by_interval(self, paper_ids: List[str]) -> Dict[str, int]:
        """Get theory usage counts for a set of papers"""
        if not paper_ids:
            return {}
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.paper_id IN $paper_ids
                RETURN t.name as theory_name, count(DISTINCT p) as usage_count
            """, paper_ids=paper_ids)
            
            return {r['theory_name']: r['usage_count'] for r in result}
    
    def calculate_diversity(self, theory_usage: Dict[str, int]) -> float:
        """Calculate normalized Shannon entropy (diversity)"""
        if not theory_usage:
            return 0.0
        
        total = sum(theory_usage.values())
        if total == 0:
            return 0.0
        
        proportions = [count / total for count in theory_usage.values()]
        n = len(proportions)
        
        if n <= 1:
            return 0.0
        
        entropy = -sum(p * math.log(p + 1e-10) for p in proportions)
        normalized = entropy / math.log(n + 1e-10)
        
        return normalized
    
    def calculate_gini_coefficient(self, theory_usage: Dict[str, int]) -> float:
        """Calculate Gini coefficient (concentration)"""
        if not theory_usage:
            return 0.0
        
        sorted_counts = sorted([count for count in theory_usage.values()], reverse=True)
        n = len(sorted_counts)
        
        if n <= 1:
            return 0.0
        
        total = sum(sorted_counts)
        if total == 0:
            return 0.0
        
        mean = total / n
        pairwise_diff_sum = sum(abs(xi - xj) 
                               for i, xi in enumerate(sorted_counts) 
                               for j, xj in enumerate(sorted_counts))
        gini = pairwise_diff_sum / (2 * n * n * mean) if mean > 0 else 0.0
        gini = max(0, min(1, gini))
        
        return gini
    
    def calculate_fragmentation(self, gini: float) -> float:
        """Calculate fragmentation index"""
        return 1 - gini
    
    def verify_theory_evolution(self, intervals: List[Dict]) -> List[Dict]:
        """Verify theory evolution calculations for each interval"""
        results = []
        
        for interval_data in intervals:
            interval = interval_data['interval']
            paper_ids = interval_data['paper_ids']
            
            theory_usage = self.get_theory_usage_by_interval(paper_ids)
            
            diversity = self.calculate_diversity(theory_usage)
            gini = self.calculate_gini_coefficient(theory_usage)
            concentration = gini
            fragmentation = self.calculate_fragmentation(gini)
            
            results.append({
                'interval': interval,
                'paper_count': len(paper_ids),
                'theory_count': len(theory_usage),
                'total_theory_usage': sum(theory_usage.values()),
                'diversity': diversity,
                'concentration': concentration,
                'fragmentation': fragmentation,
                'top_theories': sorted(
                    [(name, count) for name, count in theory_usage.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            })
        
        return results
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report = []
        report.append("=" * 80)
        report.append("ANALYTICS CHARTS TAB - DETAILED CALCULATION VERIFICATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # 1. Paper Counts by Interval
        report.append("SECTION 1: RESEARCH VOLUME EVOLUTION (Paper Counts by 5-Year Intervals)")
        report.append("-" * 80)
        report.append("")
        report.append("Calculation Logic:")
        report.append("  Query: MATCH (p:Paper) WHERE p.year >= $start_year AND p.year < $end_year AND p.year > 0")
        report.append("  Returns: count(p) and collect(p.paper_id)")
        report.append("  Intervals: 5-year periods (1985-1989, 1990-1994, etc.)")
        report.append("  Filter: Excludes papers with year = 0 or NULL")
        report.append("")
        
        intervals = self.get_paper_counts_by_interval(1985, 2025)
        
        report.append("Database Results (Verified):")
        report.append("")
        for interval in intervals:
            report.append(f"  {interval['interval']}: {interval['count']} papers")
            report.append(f"    Paper IDs sample (first 5): {', '.join(interval['paper_ids'][:5])}")
        
        report.append("")
        
        # 2. Summary Metrics
        report.append("SECTION 2: SUMMARY METRICS (Top Cards)")
        report.append("-" * 80)
        report.append("")
        
        summary = self.verify_summary_metrics(intervals)
        
        report.append("Calculation Logic:")
        report.append("  1. Total Papers = sum(count) for all intervals")
        report.append("  2. Avg per Interval = Total Papers / Number of Intervals")
        report.append("  3. Peak Period = interval with maximum count")
        report.append("")
        
        report.append("Verified Calculations:")
        report.append(f"  Total Papers: {summary['total_papers']}")
        report.append(f"    Calculation: sum({[i['count'] for i in intervals]}) = {summary['total_papers']}")
        report.append("")
        report.append(f"  Avg per Interval: {summary['avg_per_interval']}")
        report.append(f"    Calculation: {summary['total_papers']} / {summary['total_intervals']} = {summary['avg_per_interval']}")
        report.append("")
        report.append(f"  Peak Period: {summary['peak_interval']} with {summary['peak_count']} papers")
        report.append(f"    Verification: max({[i['count'] for i in intervals]}) = {summary['peak_count']}")
        report.append("")
        
        # 3. Theory Evolution Metrics
        report.append("SECTION 3: THEORETICAL EVOLUTION & DIVERGENCE")
        report.append("-" * 80)
        report.append("")
        
        theory_results = self.verify_theory_evolution(intervals)
        
        report.append("Calculation Logic:")
        report.append("")
        report.append("3.1 Theory Diversity (Normalized Shannon Entropy):")
        report.append("  Formula: Diversity = -Σ(p_i * log(p_i)) / log(n)")
        report.append("  where: p_i = proportion of theory i usage = count_i / total_usage")
        report.append("         n = number of theories")
        report.append("  Range: [0, 1] where 1.0 = perfect diversity, 0.0 = no diversity")
        report.append("")
        
        report.append("3.2 Theory Concentration (Gini Coefficient):")
        report.append("  Formula: Gini = (ΣΣ |x_i - x_j|) / (2 * n² * x̄)")
        report.append("  where: x_i = sorted theory counts (descending)")
        report.append("         n = number of theories")
        report.append("         x̄ = mean of theory counts")
        report.append("  Range: [0, 1] where 0.0 = equal usage, 1.0 = one theory dominates")
        report.append("")
        
        report.append("3.3 Fragmentation Index:")
        report.append("  Formula: Fragmentation = 1 - Gini_Coefficient")
        report.append("  Range: [0, 1] where 1.0 = highly fragmented, 0.0 = concentrated")
        report.append("")
        
        report.append("Verified Calculations by Interval:")
        report.append("")
        
        for result in theory_results:
            report.append(f"  Interval: {result['interval']}")
            report.append(f"    Papers: {result['paper_count']}")
            report.append(f"    Theories: {result['theory_count']}")
            report.append(f"    Total Theory Usage: {result['total_theory_usage']}")
            report.append(f"    Diversity: {result['diversity']:.4f} ({result['diversity']*100:.2f}%)")
            report.append(f"    Concentration: {result['concentration']:.4f} ({result['concentration']*100:.2f}%)")
            report.append(f"    Fragmentation: {result['fragmentation']:.4f} ({result['fragmentation']*100:.2f}%)")
            report.append(f"    Top 5 Theories:")
            for theory, count in result['top_theories']:
                pct = (count / result['total_theory_usage'] * 100) if result['total_theory_usage'] > 0 else 0
                report.append(f"      - {theory}: {count} uses ({pct:.1f}%)")
            report.append("")
        
        # Calculate averages
        avg_diversity = sum(r['diversity'] for r in theory_results) / len(theory_results) if theory_results else 0
        avg_concentration = sum(r['concentration'] for r in theory_results) / len(theory_results) if theory_results else 0
        avg_fragmentation = sum(r['fragmentation'] for r in theory_results) / len(theory_results) if theory_results else 0
        
        report.append("Summary Averages:")
        report.append(f"  Avg Diversity: {avg_diversity:.4f} ({avg_diversity*100:.2f}%)")
        report.append(f"  Avg Concentration: {avg_concentration:.4f} ({avg_concentration*100:.2f}%)")
        report.append(f"  Avg Fragmentation: {avg_fragmentation:.4f} ({avg_fragmentation*100:.2f}%)")
        report.append("")
        
        # 4. Topic Evolution (Note: Requires embeddings, will be simplified)
        report.append("SECTION 4: TOPIC LANDSCAPE EVOLUTION")
        report.append("-" * 80)
        report.append("")
        report.append("Note: Topic evolution uses K-means clustering on paper embeddings.")
        report.append("This requires the 'all-MiniLM-L6-v2' model and paper embeddings.")
        report.append("Full verification requires running the actual clustering algorithm.")
        report.append("")
        report.append("Calculation Logic (from code):")
        report.append("  1. Get paper embeddings for each interval")
        report.append("  2. Perform K-means clustering (optimal_k = min(10, papers/3))")
        report.append("  3. Calculate coherence = average cosine similarity within clusters")
        report.append("  4. Calculate diversity = normalized Shannon entropy of cluster sizes")
        report.append("  5. Calculate stability = similarity of centroids across intervals")
        report.append("")
        report.append("Database Query for Embeddings:")
        report.append("  MATCH (p:Paper) WHERE p.paper_id IN $paper_ids AND p.embedding IS NOT NULL")
        report.append("  RETURN p.paper_id, p.embedding, p.title, p.abstract")
        report.append("")
        
        # Check embedding availability
        with self.driver.session() as session:
            embedding_check = session.run("""
                MATCH (p:Paper)
                WHERE p.embedding IS NOT NULL
                RETURN count(p) as papers_with_embeddings
            """)
            embedding_count = embedding_check.single()['papers_with_embeddings']
            
            total_papers_check = session.run("""
                MATCH (p:Paper)
                WHERE p.year > 0
                RETURN count(p) as total_papers
            """)
            total_papers = total_papers_check.single()['total_papers']
        
        report.append(f"Embedding Availability:")
        report.append(f"  Papers with embeddings: {embedding_count}")
        report.append(f"  Total papers (year > 0): {total_papers}")
        report.append(f"  Coverage: {(embedding_count/total_papers*100):.1f}%")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF VERIFICATION REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    verifier = AnalyticsVerifier()
    try:
        report = verifier.generate_report()
        print(report)
        
        # Also save to file
        with open("ANALYTICS_CHARTS_VERIFICATION_REPORT.txt", "w") as f:
            f.write(report)
        print("\n✅ Report saved to ANALYTICS_CHARTS_VERIFICATION_REPORT.txt")
        
    finally:
        verifier.close()

if __name__ == "__main__":
    main()
