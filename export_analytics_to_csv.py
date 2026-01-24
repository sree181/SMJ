#!/usr/bin/env python3
"""
Export Analytics Reports to CSV
Queries Neo4j and exports summary reports for:
- Paper counts by timeframe
- Authors and counts by timeline
- Topics and counts by timeline
- Phenomena and counts by timeline
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import math

# Load environment variables
load_dotenv()

class AnalyticsExporter:
    def __init__(self):
        """Initialize Neo4j connection"""
        self.uri = os.getenv("NEO4J_URI", "").strip()
        self.user = os.getenv("NEO4J_USER", "").strip()
        self.password = os.getenv("NEO4J_PASSWORD", "").strip()
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError("Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        print(f"✓ Connected to Neo4j at {self.uri}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def export_papers_by_timeframe(self, start_year: int = 1985, end_year: int = 2025, output_file: str = "papers_by_timeframe.csv"):
        """Export paper counts by 5-year intervals"""
        print(f"\n📊 Exporting paper counts by timeframe ({start_year}-{end_year})...")
        
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    RETURN count(p) as paper_count
                """, start_year=current_start, end_year=current_end).single()
                
                paper_count = result['paper_count'] if result else 0
                
                intervals.append({
                    'Interval': interval_str,
                    'Start Year': current_start,
                    'End Year': current_end - 1,
                    'Paper Count': paper_count
                })
                
                current_start = current_end
        
        # Write to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if intervals:
                writer = csv.DictWriter(f, fieldnames=intervals[0].keys())
                writer.writeheader()
                writer.writerows(intervals)
        
        print(f"✓ Exported {len(intervals)} intervals to {output_file}")
        return intervals
    
    def export_authors_by_timeline(self, start_year: int = 1985, end_year: int = 2025, top_n: int = 50, output_file: str = "authors_by_timeline.csv"):
        """Export author counts and top authors by 5-year intervals"""
        print(f"\n👥 Exporting authors by timeline ({start_year}-{end_year})...")
        
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                # Get unique authors and their paper counts
                result = session.run("""
                    MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    WITH a, count(DISTINCT p) as papers_authored
                    RETURN a.full_name as full_name,
                           a.given_name as given_name,
                           a.family_name as family_name,
                           papers_authored
                    ORDER BY papers_authored DESC
                    LIMIT $top_n
                """, start_year=current_start, end_year=current_end, top_n=top_n).data()
                
                unique_author_count = len(result)
                
                # Get total papers in interval
                papers_result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year AND p.year < $end_year AND p.year > 0
                    RETURN count(p) as paper_count
                """, start_year=current_start, end_year=current_end).single()
                total_papers = papers_result['paper_count'] if papers_result else 0
                
                # Flatten for CSV (one row per author per interval)
                for author in result:
                    intervals.append({
                        'Interval': interval_str,
                        'Start Year': current_start,
                        'End Year': current_end - 1,
                        'Author Name': author.get('full_name') or f"{author.get('given_name', '')} {author.get('family_name', '')}".strip(),
                        'Given Name': author.get('given_name', ''),
                        'Family Name': author.get('family_name', ''),
                        'Papers Authored': author.get('papers_authored', 0),
                        'Total Unique Authors in Interval': unique_author_count,
                        'Total Papers in Interval': total_papers
                    })
                
                current_start = current_end
        
        # Write to CSV
        if intervals:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Interval', 'Start Year', 'End Year', 'Author Name', 'Given Name', 
                            'Family Name', 'Papers Authored', 'Total Unique Authors in Interval', 
                            'Total Papers in Interval']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(intervals)
            
            print(f"✓ Exported {len(intervals)} author records to {output_file}")
        else:
            print(f"⚠ No author data found")
        
        return intervals
    
    def export_topics_by_timeline(self, start_year: int = 1985, end_year: int = 2025, output_file: str = "topics_by_timeline.csv"):
        """Export topic evolution with clustering by 5-year intervals"""
        print(f"\n📚 Exporting topics by timeline ({start_year}-{end_year})...")
        print("   This may take a few minutes as it performs clustering analysis...")
        
        intervals_data = []
        current_start = start_year
        
        # Get paper intervals first
        paper_intervals = []
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                      AND p.embedding IS NOT NULL
                    RETURN p.paper_id as paper_id,
                           p.embedding as embedding,
                           p.title as title,
                           p.abstract as abstract
                    ORDER BY p.year
                """, start_year=current_start, end_year=current_end).data()
                
                paper_intervals.append({
                    'interval': interval_str,
                    'start_year': current_start,
                    'end_year': current_end - 1,
                    'papers': result
                })
                
                current_start = current_end
        
        # Perform clustering for each interval
        all_topic_data = []
        for interval_info in paper_intervals:
            interval = interval_info['interval']
            papers = interval_info['papers']
            
            if len(papers) < 3:
                # Not enough papers for clustering
                all_topic_data.append({
                    'Interval': interval,
                    'Start Year': interval_info['start_year'],
                    'End Year': interval_info['end_year'],
                    'Topic Number': 'N/A',
                    'Topic Paper Count': 0,
                    'Topic Coherence': 0.0,
                    'Representative Paper ID': 'N/A',
                    'Representative Paper Title': 'N/A',
                    'Total Topics in Interval': 0,
                    'Total Papers in Interval': len(papers)
                })
                continue
            
            # Extract embeddings
            embeddings = []
            paper_info = []
            for p in papers:
                if p.get('embedding'):
                    embeddings.append(p['embedding'])
                    paper_info.append({
                        'paper_id': p.get('paper_id'),
                        'title': p.get('title', '')
                    })
            
            if len(embeddings) < 3:
                continue
            
            embeddings = np.array(embeddings)
            
            # Determine optimal number of clusters
            max_clusters = min(10, len(embeddings) // 3)
            optimal_k = max(2, max_clusters)
            
            # Perform K-means clustering
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(embeddings)
            
            # Calculate topic metrics
            topics = []
            for cluster_id in range(optimal_k):
                cluster_indices = np.where(cluster_labels == cluster_id)[0]
                cluster_embeddings = embeddings[cluster_indices]
                cluster_papers = [paper_info[i] for i in cluster_indices]
                
                # Calculate coherence (average similarity within cluster)
                if len(cluster_embeddings) > 1:
                    similarities = cosine_similarity(cluster_embeddings)
                    mask = np.ones(similarities.shape, dtype=bool)
                    np.fill_diagonal(mask, False)
                    coherence = similarities[mask].mean()
                else:
                    coherence = 1.0
                
                # Get representative paper (closest to centroid)
                centroid = kmeans.cluster_centers_[cluster_id]
                distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
                representative_idx = cluster_indices[np.argmin(distances)]
                representative_paper = paper_info[representative_idx]
                
                topics.append({
                    'cluster_id': cluster_id,
                    'paper_count': len(cluster_papers),
                    'coherence': float(coherence),
                    'representative_paper': representative_paper
                })
            
            # Add each topic as a row
            for topic in topics:
                all_topic_data.append({
                    'Interval': interval,
                    'Start Year': interval_info['start_year'],
                    'End Year': interval_info['end_year'],
                    'Topic Number': topic['cluster_id'] + 1,
                    'Topic Paper Count': topic['paper_count'],
                    'Topic Coherence': round(topic['coherence'], 4),
                    'Representative Paper ID': topic['representative_paper'].get('paper_id', 'N/A'),
                    'Representative Paper Title': topic['representative_paper'].get('title', 'N/A')[:200],  # Truncate long titles
                    'Total Topics in Interval': len(topics),
                    'Total Papers in Interval': len(embeddings)
                })
        
        # Write to CSV
        if all_topic_data:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Interval', 'Start Year', 'End Year', 'Topic Number', 'Topic Paper Count',
                            'Topic Coherence', 'Representative Paper ID', 'Representative Paper Title',
                            'Total Topics in Interval', 'Total Papers in Interval']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_topic_data)
            
            print(f"✓ Exported {len(all_topic_data)} topic records to {output_file}")
        else:
            print(f"⚠ No topic data found")
        
        return all_topic_data
    
    def export_phenomena_by_timeline(self, start_year: int = 1985, end_year: int = 2025, top_n: int = 50, output_file: str = "phenomena_by_timeline.csv"):
        """Export phenomena counts and top phenomena by 5-year intervals"""
        print(f"\n🔬 Exporting phenomena by timeline ({start_year}-{end_year})...")
        
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                # Get phenomena and their paper counts
                result = session.run("""
                    MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    WITH ph, count(DISTINCT p) as papers_studying_phenomenon
                    RETURN ph.phenomenon_name as phenomenon_name,
                           papers_studying_phenomenon
                    ORDER BY papers_studying_phenomenon DESC
                    LIMIT $top_n
                """, start_year=current_start, end_year=current_end, top_n=top_n).data()
                
                unique_phenomena_count = len(result)
                
                # Get total papers in interval
                papers_result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year AND p.year < $end_year AND p.year > 0
                    RETURN count(p) as paper_count
                """, start_year=current_start, end_year=current_end).single()
                total_papers = papers_result['paper_count'] if papers_result else 0
                
                # Flatten for CSV (one row per phenomenon per interval)
                for phenomenon in result:
                    intervals.append({
                        'Interval': interval_str,
                        'Start Year': current_start,
                        'End Year': current_end - 1,
                        'Phenomenon Name': phenomenon.get('phenomenon_name', ''),
                        'Papers Studying Phenomenon': phenomenon.get('papers_studying_phenomenon', 0),
                        'Total Unique Phenomena in Interval': unique_phenomena_count,
                        'Total Papers in Interval': total_papers
                    })
                
                current_start = current_end
        
        # Write to CSV
        if intervals:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Interval', 'Start Year', 'End Year', 'Phenomenon Name', 
                            'Papers Studying Phenomenon', 'Total Unique Phenomena in Interval', 
                            'Total Papers in Interval']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(intervals)
            
            print(f"✓ Exported {len(intervals)} phenomenon records to {output_file}")
        else:
            print(f"⚠ No phenomenon data found")
        
        return intervals
    
    def export_all_reports(self, start_year: int = 1985, end_year: int = 2025, output_dir: str = "analytics_exports"):
        """Export all reports to CSV files"""
        print(f"\n{'='*60}")
        print(f"📊 EXPORTING ANALYTICS REPORTS TO CSV")
        print(f"{'='*60}")
        print(f"Time Range: {start_year}-{end_year}")
        print(f"Output Directory: {output_dir}")
        print(f"{'='*60}\n")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export all reports
        reports = {
            'papers_by_timeframe': self.export_papers_by_timeframe(
                start_year=start_year, 
                end_year=end_year, 
                output_file=os.path.join(output_dir, f"papers_by_timeframe_{timestamp}.csv")
            ),
            'authors_by_timeline': self.export_authors_by_timeline(
                start_year=start_year, 
                end_year=end_year, 
                top_n=50,
                output_file=os.path.join(output_dir, f"authors_by_timeline_{timestamp}.csv")
            ),
            'topics_by_timeline': self.export_topics_by_timeline(
                start_year=start_year, 
                end_year=end_year,
                output_file=os.path.join(output_dir, f"topics_by_timeline_{timestamp}.csv")
            ),
            'phenomena_by_timeline': self.export_phenomena_by_timeline(
                start_year=start_year, 
                end_year=end_year, 
                top_n=50,
                output_file=os.path.join(output_dir, f"phenomena_by_timeline_{timestamp}.csv")
            )
        }
        
        # Create summary report
        summary_file = os.path.join(output_dir, f"export_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Analytics Export Summary\n")
            f.write(f"{'='*60}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Time Range: {start_year}-{end_year}\n")
            f.write(f"{'='*60}\n\n")
            
            f.write(f"Papers by Timeframe: {len(reports['papers_by_timeframe'])} intervals\n")
            f.write(f"Authors by Timeline: {len(reports['authors_by_timeline'])} records\n")
            f.write(f"Topics by Timeline: {len(reports['topics_by_timeline'])} records\n")
            f.write(f"Phenomena by Timeline: {len(reports['phenomena_by_timeline'])} records\n")
        
        print(f"\n{'='*60}")
        print(f"✅ EXPORT COMPLETE")
        print(f"{'='*60}")
        print(f"All reports exported to: {output_dir}/")
        print(f"Summary saved to: {summary_file}")
        print(f"{'='*60}\n")
        
        return reports


def main():
    """Main execution function"""
    exporter = None
    try:
        exporter = AnalyticsExporter()
        
        # Export all reports
        reports = exporter.export_all_reports(
            start_year=1985,
            end_year=2025
        )
        
        print("\n✅ All exports completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if exporter:
            exporter.close()


if __name__ == "__main__":
    main()
