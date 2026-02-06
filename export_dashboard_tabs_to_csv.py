#!/usr/bin/env python3
"""
Export Dashboard Tabs to CSV
Exports data for each tab in the Advanced Analytics Dashboard to separate CSV files.
Each tab gets its own CSV file for easy sharing with coauthors.
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

class DashboardTabExporter:
    def __init__(self, api_base_url: str = None):
        """Initialize Neo4j connection and optionally API base URL"""
        self.uri = os.getenv("NEO4J_URI", "").strip()
        self.user = os.getenv("NEO4J_USER", "").strip()
        self.password = os.getenv("NEO4J_PASSWORD", "").strip()
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError("Missing Neo4j credentials. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.api_base_url = api_base_url or os.getenv("API_BASE_URL", "http://localhost:5000/api")
        print(f"✓ Connected to Neo4j at {self.uri}")
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def export_tab_1_papers_by_timeframe(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Tab: Papers by Timeframe (Basic Charts)"""
        print(f"\n📊 Exporting Tab 1: Papers by Timeframe...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_1_papers_by_timeframe_{timestamp}.csv"
        
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
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if intervals:
                writer = csv.DictWriter(f, fieldnames=intervals[0].keys())
                writer.writeheader()
                writer.writerows(intervals)
        
        print(f"✓ Exported {len(intervals)} intervals to {output_file}")
        return output_file
    
    def export_tab_2_authors_by_period(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Tab: Authors by Period"""
        print(f"\n👥 Exporting Tab 2: Authors by Period...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_2_authors_by_period_{timestamp}.csv"
        
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                # Get top authors
                result = session.run("""
                    MATCH (p:Paper)<-[:AUTHORED]-(a:Author)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year
                      AND p.year > 0
                    WITH a, count(DISTINCT p) as paper_count, collect(DISTINCT p.paper_id) as paper_ids
                    RETURN a.author_id as author_id,
                           a.full_name as full_name,
                           a.given_name as given_name,
                           a.family_name as family_name,
                           paper_count,
                           paper_ids
                    ORDER BY paper_count DESC, a.family_name, a.given_name
                """, start_year=current_start, end_year=current_end).data()
                
                # Get total unique authors
                total_authors_result = session.run("""
                    MATCH (p:Paper)<-[:AUTHORED]-(a:Author)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    RETURN count(DISTINCT a) as total_unique_authors
                """, start_year=current_start, end_year=current_end).single()
                unique_author_count = total_authors_result['total_unique_authors'] if total_authors_result else 0
                
                # Get total papers
                papers_result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year AND p.year < $end_year AND p.year > 0
                    RETURN count(p) as paper_count
                """, start_year=current_start, end_year=current_end).single()
                total_papers = papers_result['paper_count'] if papers_result else 0
                
                # Flatten for CSV
                for author in result:
                    intervals.append({
                        'Interval': interval_str,
                        'Start Year': current_start,
                        'End Year': current_end - 1,
                        'Author ID': author.get('author_id', ''),
                        'Author Name': author.get('full_name') or f"{author.get('given_name', '')} {author.get('family_name', '')}".strip(),
                        'Given Name': author.get('given_name', ''),
                        'Family Name': author.get('family_name', ''),
                        'Papers Authored': author.get('paper_count', 0),
                        'Total Unique Authors in Interval': unique_author_count,
                        'Total Papers in Interval': total_papers
                    })
                
                current_start = current_end
        
        # Write to CSV
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        if intervals:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Interval', 'Start Year', 'End Year', 'Author ID', 'Author Name', 
                            'Given Name', 'Family Name', 'Papers Authored', 
                            'Total Unique Authors in Interval', 'Total Papers in Interval']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(intervals)
            
            print(f"✓ Exported {len(intervals)} author records to {output_file}")
        else:
            print(f"⚠ No author data found")
        
        return output_file
    
    def export_tab_3_topics_by_period(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Tab: Topics by Period (with LLM-generated names)"""
        print(f"\n📚 Exporting Tab 3: Topics by Period...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_3_topics_by_period_{timestamp}.csv"
        
        # Get topics from Neo4j Topic nodes
        intervals_data = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                # Get topics for this interval from Neo4j
                result = session.run("""
                    MATCH (t:Topic)
                    WHERE t.interval = $interval
                    OPTIONAL MATCH (t)-[:REPRESENTED_BY]->(rep:Paper)
                    OPTIONAL MATCH (p:Paper)-[:BELONGS_TO_TOPIC]->(t)
                    WITH t, rep, count(DISTINCT p) as paper_count
                    RETURN t.topic_id as topic_id,
                           t.name as topic_name,
                           t.cluster_id as cluster_id,
                           t.coherence as coherence,
                           t.paper_count as stored_paper_count,
                           paper_count as actual_paper_count,
                           rep.paper_id as representative_paper_id,
                           rep.title as representative_paper_title
                    ORDER BY t.cluster_id
                """, interval=interval_str).data()
                
                # Get total topics and papers for interval
                totals_result = session.run("""
                    MATCH (t:Topic)
                    WHERE t.interval = $interval
                    WITH count(DISTINCT t) as total_topics
                    MATCH (p:Paper)-[:BELONGS_TO_TOPIC]->(t:Topic)
                    WHERE t.interval = $interval
                    RETURN total_topics, count(DISTINCT p) as total_papers
                """, interval=interval_str).single()
                
                total_topics = totals_result['total_topics'] if totals_result else 0
                total_papers = totals_result['total_papers'] if totals_result else 0
                
                for topic in result:
                    intervals_data.append({
                        'Interval': interval_str,
                        'Start Year': current_start,
                        'End Year': current_end - 1,
                        'Topic ID': topic.get('topic_id', ''),
                        'Topic Name': topic.get('topic_name') or topic.get('representative_paper_title', 'N/A'),
                        'Cluster ID': topic.get('cluster_id', ''),
                        'Paper Count': topic.get('actual_paper_count') or topic.get('stored_paper_count', 0),
                        'Coherence': round(topic.get('coherence', 0.0), 4) if topic.get('coherence') else 0.0,
                        'Representative Paper ID': topic.get('representative_paper_id', ''),
                        'Representative Paper Title': topic.get('representative_paper_title', '')[:200],  # Truncate
                        'Total Topics in Interval': total_topics,
                        'Total Papers in Interval': total_papers
                    })
                
                current_start = current_end
        
        # Write to CSV
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        if intervals_data:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['Interval', 'Start Year', 'End Year', 'Topic ID', 'Topic Name', 'Cluster ID',
                            'Paper Count', 'Coherence', 'Representative Paper ID', 'Representative Paper Title',
                            'Total Topics in Interval', 'Total Papers in Interval']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(intervals_data)
            
            print(f"✓ Exported {len(intervals_data)} topic records to {output_file}")
        else:
            print(f"⚠ No topic data found")
        
        return output_file
    
    def export_tab_4_phenomena_by_period(self, start_year: int = 1985, end_year: int = 2025, top_n: int = 20, output_file: str = None):
        """Tab: Phenomenon Evolution by Period"""
        print(f"\n🔬 Exporting Tab 4: Phenomena by Period...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_4_phenomena_by_period_{timestamp}.csv"
        
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                # Get top phenomena
                result = session.run("""
                    MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    WITH ph, count(DISTINCT p) as papers_studying_phenomenon, collect(DISTINCT p.paper_id) as paper_ids
                    RETURN ph.phenomenon_name as phenomenon_name,
                           papers_studying_phenomenon,
                           paper_ids
                    ORDER BY papers_studying_phenomenon DESC
                    LIMIT $top_n
                """, start_year=current_start, end_year=current_end, top_n=top_n).data()
                
                # Get total unique phenomena
                total_phenomena_result = session.run("""
                    MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    RETURN count(DISTINCT ph) as total_unique_phenomena
                """, start_year=current_start, end_year=current_end).single()
                unique_phenomena_count = total_phenomena_result['total_unique_phenomena'] if total_phenomena_result else 0
                
                # Get total papers
                papers_result = session.run("""
                    MATCH (p:Paper)
                    WHERE p.year >= $start_year AND p.year < $end_year AND p.year > 0
                    RETURN count(p) as paper_count
                """, start_year=current_start, end_year=current_end).single()
                total_papers = papers_result['paper_count'] if papers_result else 0
                
                # Flatten for CSV
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
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
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
        
        return output_file
    
    def export_tab_5_theory_evolution(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Tab: Theory Evolution (Theory Proportions)"""
        print(f"\n📈 Exporting Tab 5: Theory Evolution...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_5_theory_evolution_{timestamp}.csv"
        
        # Call API endpoint for theory evolution
        try:
            url = f"{self.api_base_url}/analytics/theories/evolution-divergence"
            params = {"start_year": start_year, "end_year": end_year}
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            intervals_data = []
            for interval_data in data.get('intervals', []):
                interval = interval_data.get('interval', '')
                start_yr = interval_data.get('start_year', 0)
                end_yr = interval_data.get('end_year', 0)
                
                for theory in interval_data.get('theories', []):
                    intervals_data.append({
                        'Interval': interval,
                        'Start Year': start_yr,
                        'End Year': end_yr,
                        'Theory Name': theory.get('theory_name', ''),
                        'Paper Count': theory.get('paper_count', 0),
                        'Proportion': round(theory.get('proportion', 0.0), 4),
                        'Cumulative Count': theory.get('cumulative_count', 0),
                        'Is New': theory.get('is_new', False),
                        'Is Persistent': theory.get('is_persistent', False)
                    })
            
            # Write to CSV
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            if intervals_data:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['Interval', 'Start Year', 'End Year', 'Theory Name', 'Paper Count',
                                'Proportion', 'Cumulative Count', 'Is New', 'Is Persistent']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(intervals_data)
                
                print(f"✓ Exported {len(intervals_data)} theory evolution records to {output_file}")
            else:
                print(f"⚠ No theory evolution data found")
            
            return output_file
        except Exception as e:
            print(f"⚠ Error exporting theory evolution: {e}")
            return None
    
    def export_tab_6_theory_betweenness(self, min_phenomena: int = 2, output_file: str = None):
        """Tab: Theory Betweenness"""
        print(f"\n🔗 Exporting Tab 6: Theory Betweenness...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_6_theory_betweenness_{timestamp}.csv"
        
        # Call API endpoint
        try:
            url = f"{self.api_base_url}/analytics/theories/betweenness"
            params = {"min_phenomena": min_phenomena}
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            records = []
            for theory_name, theory_data in data.get('theory_betweenness', {}).items():
                records.append({
                    'Theory Name': theory_name,
                    'Betweenness Score': round(theory_data.get('betweenness_score', 0.0), 4),
                    'Phenomena Count': theory_data.get('phenomena_count', 0),
                    'Papers Count': theory_data.get('papers_count', 0),
                    'Cross Topic Reach': round(theory_data.get('cross_topic_reach', 0.0), 4)
                })
            
            # Write to CSV
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            if records:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['Theory Name', 'Betweenness Score', 'Phenomena Count', 
                                'Papers Count', 'Cross Topic Reach']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                
                print(f"✓ Exported {len(records)} theory betweenness records to {output_file}")
            else:
                print(f"⚠ No theory betweenness data found")
            
            return output_file
        except Exception as e:
            print(f"⚠ Error exporting theory betweenness: {e}")
            return None
    
    def export_tab_7_opportunity_gaps(self, max_theories: int = 2, output_file: str = None):
        """Tab: Opportunity Gaps"""
        print(f"\n💡 Exporting Tab 7: Opportunity Gaps...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_7_opportunity_gaps_{timestamp}.csv"
        
        # Call API endpoint
        try:
            url = f"{self.api_base_url}/analytics/phenomena/opportunity-gaps"
            params = {"max_theories": max_theories}
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            records = []
            for gap in data.get('opportunity_gaps', []):
                records.append({
                    'Phenomenon Name': gap.get('phenomenon_name', ''),
                    'Opportunity Score': round(gap.get('opportunity_score', 0.0), 4),
                    'Theories Count': gap.get('theories_count', 0),
                    'Papers Count': gap.get('papers_count', 0),
                    'Theories': ', '.join(gap.get('theories', []))
                })
            
            # Write to CSV
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            if records:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['Phenomenon Name', 'Opportunity Score', 'Theories Count', 
                                'Papers Count', 'Theories']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                
                print(f"✓ Exported {len(records)} opportunity gap records to {output_file}")
            else:
                print(f"⚠ No opportunity gap data found")
            
            return output_file
        except Exception as e:
            print(f"⚠ Error exporting opportunity gaps: {e}")
            return None
    
    def export_tab_8_integration_mechanism(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Tab: Integration Mechanism"""
        print(f"\n🔀 Exporting Tab 8: Integration Mechanism...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"analytics_exports/tab_8_integration_mechanism_{timestamp}.csv"
        
        # Call API endpoint
        try:
            url = f"{self.api_base_url}/analytics/integration/mechanism"
            params = {"start_year": start_year, "end_year": end_year}
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            records = []
            for pair in data.get('theory_pairs', []):
                records.append({
                    'Theory 1': pair.get('theory1', ''),
                    'Theory 2': pair.get('theory2', ''),
                    'Co-usage Count': pair.get('co_usage_count', 0),
                    'Integration Score': round(pair.get('integration_score', 0.0), 4),
                    'Papers': ', '.join(pair.get('papers', [])[:10])  # Limit to first 10 paper IDs
                })
            
            # Write to CSV
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            if records:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['Theory 1', 'Theory 2', 'Co-usage Count', 'Integration Score', 'Papers']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(records)
                
                print(f"✓ Exported {len(records)} integration mechanism records to {output_file}")
            else:
                print(f"⚠ No integration mechanism data found")
            
            return output_file
        except Exception as e:
            print(f"⚠ Error exporting integration mechanism: {e}")
            return None
    
    def export_all_tabs(self, start_year: int = 1985, end_year: int = 2025, output_dir: str = "analytics_exports"):
        """Export all dashboard tabs to separate CSV files"""
        print(f"\n{'='*70}")
        print(f"📊 EXPORTING ALL DASHBOARD TABS TO CSV")
        print(f"{'='*70}")
        print(f"Time Range: {start_year}-{end_year}")
        print(f"Output Directory: {output_dir}")
        print(f"{'='*70}\n")
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_files = {}
        
        # Export each tab
        try:
            exported_files['tab_1_papers'] = self.export_tab_1_papers_by_timeframe(
                start_year, end_year, 
                os.path.join(output_dir, f"tab_1_papers_by_timeframe_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 1: {e}")
        
        try:
            exported_files['tab_2_authors'] = self.export_tab_2_authors_by_period(
                start_year, end_year,
                os.path.join(output_dir, f"tab_2_authors_by_period_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 2: {e}")
        
        try:
            exported_files['tab_3_topics'] = self.export_tab_3_topics_by_period(
                start_year, end_year,
                os.path.join(output_dir, f"tab_3_topics_by_period_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 3: {e}")
        
        try:
            exported_files['tab_4_phenomena'] = self.export_tab_4_phenomena_by_period(
                start_year, end_year, top_n=20,
                output_file=os.path.join(output_dir, f"tab_4_phenomena_by_period_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 4: {e}")
        
        try:
            exported_files['tab_5_theory_evolution'] = self.export_tab_5_theory_evolution(
                start_year, end_year,
                os.path.join(output_dir, f"tab_5_theory_evolution_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 5: {e}")
        
        try:
            exported_files['tab_6_theory_betweenness'] = self.export_tab_6_theory_betweenness(
                min_phenomena=2,
                output_file=os.path.join(output_dir, f"tab_6_theory_betweenness_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 6: {e}")
        
        try:
            exported_files['tab_7_opportunity_gaps'] = self.export_tab_7_opportunity_gaps(
                max_theories=2,
                output_file=os.path.join(output_dir, f"tab_7_opportunity_gaps_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 7: {e}")
        
        try:
            exported_files['tab_8_integration_mechanism'] = self.export_tab_8_integration_mechanism(
                start_year, end_year,
                os.path.join(output_dir, f"tab_8_integration_mechanism_{timestamp}.csv")
            )
        except Exception as e:
            print(f"❌ Error exporting Tab 8: {e}")
        
        # Create summary
        summary_file = os.path.join(output_dir, f"export_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Dashboard Tabs Export Summary\n")
            f.write(f"{'='*70}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Time Range: {start_year}-{end_year}\n")
            f.write(f"{'='*70}\n\n")
            
            f.write("Exported Files:\n")
            f.write("-" * 70 + "\n")
            for tab_name, file_path in exported_files.items():
                if file_path:
                    f.write(f"{tab_name}: {file_path}\n")
                else:
                    f.write(f"{tab_name}: FAILED\n")
        
        print(f"\n{'='*70}")
        print(f"✅ EXPORT COMPLETE")
        print(f"{'='*70}")
        print(f"All CSV files exported to: {output_dir}/")
        print(f"Summary saved to: {summary_file}")
        print(f"{'='*70}\n")
        
        return exported_files


def main():
    """Main execution function"""
    exporter = None
    try:
        # You can specify API base URL if different from default
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:5000/api")
        exporter = DashboardTabExporter(api_base_url=api_base_url)
        
        # Export all tabs
        exported_files = exporter.export_all_tabs(
            start_year=1985,
            end_year=2025
        )
        
        print("\n✅ All exports completed successfully!")
        print("\nExported files:")
        for tab_name, file_path in exported_files.items():
            if file_path:
                print(f"  ✓ {tab_name}: {file_path}")
            else:
                print(f"  ✗ {tab_name}: FAILED")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if exporter:
            exporter.close()


if __name__ == "__main__":
    main()
