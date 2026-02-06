#!/usr/bin/env python3
"""
Export Dashboard Charts to PNG using Plotly
Exports all dashboard charts as black and white PNG files with:
- 1200 DPI
- 4080 pixels wide
- Professional black and white styling using Plotly
"""

import os
import sys
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests

# Load environment variables
load_dotenv()

# Black and white color scheme for Plotly
BW_COLORS = {
    'black': '#000000',
    'dark_gray': '#333333',
    'medium_gray': '#666666',
    'light_gray': '#999999',
    'very_light_gray': '#CCCCCC',
    'white': '#FFFFFF'
}

# Line styles and markers for distinguishing series
LINE_STYLES = ['solid', 'dash', 'dot', 'dashdot']
MARKER_SYMBOLS = ['circle', 'square', 'diamond', 'triangle-up', 'triangle-down', 'x', 'cross']

class ChartExporter:
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
    
    def get_bw_layout(self, title: str, xaxis_title: str, yaxis_title: str, width: int = 4080, height: int = 2448):
        """Get a black and white layout template for Plotly charts with large, readable fonts"""
        layout = go.Layout(
            title=dict(
                text=title,
                font=dict(size=48, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
                x=0.5,
                xanchor='center',
                pad=dict(t=40, b=50)
            ),
            xaxis=dict(
                title=dict(text=xaxis_title, font=dict(size=40, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold')),
                tickfont=dict(size=30, color=BW_COLORS['black'], family='Arial, sans-serif'),
                gridcolor=BW_COLORS['very_light_gray'],
                gridwidth=1,
                showgrid=True,
                linecolor=BW_COLORS['black'],
                linewidth=3,
                mirror=True,
                tickangle=-45,
                tickmode='linear'
            ),
            yaxis=dict(
                title=dict(text=yaxis_title, font=dict(size=40, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold')),
                tickfont=dict(size=30, color=BW_COLORS['black'], family='Arial, sans-serif'),
                gridcolor=BW_COLORS['very_light_gray'],
                gridwidth=1,
                showgrid=True,
                linecolor=BW_COLORS['black'],
                linewidth=3,
                mirror=True
            ),
            plot_bgcolor=BW_COLORS['white'],
            paper_bgcolor=BW_COLORS['white'],
            width=width,
            height=height,
            margin=dict(l=200, r=120, t=150, b=250),
            legend=dict(
                font=dict(size=26, color=BW_COLORS['black'], family='Arial, sans-serif'),
                bgcolor=BW_COLORS['white'],
                bordercolor=BW_COLORS['black'],
                borderwidth=2,
                x=1.02,
                y=1,
                xanchor='left',
                yanchor='top'
            )
        )
        return layout
    
    def export_chart_1_paper_counts(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Chart 1: Research Volume Evolution (Bar Chart)"""
        print(f"\n📊 Exporting Chart 1: Research Volume Evolution...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chart_exports/chart_1_paper_counts_{timestamp}.png"
        
        # Get data from Neo4j
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
                intervals.append({'interval': interval_str, 'count': paper_count})
                current_start = current_end
        
        if not intervals:
            print("⚠ No data found")
            return None
        
        # Prepare data
        intervals_list = [i['interval'] for i in intervals]
        counts = [i['count'] for i in intervals]
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=intervals_list,
            y=counts,
            marker=dict(
                color=BW_COLORS['dark_gray'],
                line=dict(color=BW_COLORS['black'], width=3)
            ),
            text=counts,
            textposition='outside',
            textfont=dict(size=32, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
            name='Papers'
        ))
        
        # Apply layout
        layout = self.get_bw_layout(
            title='Research Volume Evolution',
            xaxis_title='Time Period',
            yaxis_title='Number of Papers'
        )
        fig.update_layout(layout)
        
        # Export
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        fig.write_image(output_file, width=4080, height=2448, scale=1, format='png')
        
        print(f"✓ Exported to {output_file}")
        return output_file
    
    def export_chart_2_topic_evolution(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Chart 2: Topic Landscape Evolution (Area Chart)"""
        print(f"\n📈 Exporting Chart 2: Topic Landscape Evolution...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chart_exports/chart_2_topic_evolution_{timestamp}.png"
        
        # Get data from API
        try:
            url = f"{self.api_base_url}/analytics/topics/evolution"
            params = {"start_year": start_year, "end_year": end_year}
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            intervals_data = data.get('intervals', [])
            if not intervals_data:
                print("⚠ No data found")
                return None
            
            # Prepare data
            intervals = [i['interval'] for i in intervals_data]
            topic_counts = [i.get('topic_count', 0) for i in intervals_data]
            coherence = [i.get('coherence', 0) * 100 for i in intervals_data]
            diversity = [i.get('diversity', 0) * 100 for i in intervals_data]
            
            # Create figure with secondary y-axis
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # Primary y-axis: Topic Count
            fig.add_trace(
                go.Scatter(
                    x=intervals,
                    y=topic_counts,
                    mode='lines+markers',
                    name='Topic Count',
                    line=dict(color=BW_COLORS['black'], width=4),
                    marker=dict(size=12, color=BW_COLORS['black'], symbol='circle',
                              line=dict(width=2, color=BW_COLORS['black'])),
                    fill='tozeroy',
                    fillcolor=f"rgba(0, 0, 0, 0.1)"
                ),
                secondary_y=False
            )
            
            # Secondary y-axis: Coherence and Diversity
            fig.add_trace(
                go.Scatter(
                    x=intervals,
                    y=coherence,
                    mode='lines+markers',
                    name='Coherence (%)',
                    line=dict(color=BW_COLORS['medium_gray'], width=3, dash='dash'),
                    marker=dict(size=12, color=BW_COLORS['medium_gray'], symbol='square',
                              line=dict(width=2, color=BW_COLORS['medium_gray']))
                ),
                secondary_y=True
            )
            
            fig.add_trace(
                go.Scatter(
                    x=intervals,
                    y=diversity,
                    mode='lines+markers',
                    name='Diversity (%)',
                    line=dict(color=BW_COLORS['light_gray'], width=3, dash='dot'),
                    marker=dict(size=12, color=BW_COLORS['light_gray'], symbol='diamond',
                              line=dict(width=2, color=BW_COLORS['light_gray']))
                ),
                secondary_y=True
            )
            
            # Update layout
            fig.update_layout(
                title=dict(
                    text='Topic Landscape Evolution',
                    font=dict(size=48, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
                    x=0.5,
                    xanchor='center',
                    pad=dict(t=40, b=50)
                ),
                plot_bgcolor=BW_COLORS['white'],
                paper_bgcolor=BW_COLORS['white'],
                width=4080,
                height=2448,
                margin=dict(l=200, r=200, t=150, b=250),
                legend=dict(
                    font=dict(size=26, color=BW_COLORS['black'], family='Arial, sans-serif'),
                    bgcolor=BW_COLORS['white'],
                    bordercolor=BW_COLORS['black'],
                    borderwidth=2,
                    x=1.02,
                    y=1,
                    xanchor='left',
                    yanchor='top'
                )
            )
            
            # Update axes
            fig.update_xaxes(
                title_text='Time Period',
                title_font=dict(size=40, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
                tickfont=dict(size=30, color=BW_COLORS['black'], family='Arial, sans-serif'),
                gridcolor=BW_COLORS['very_light_gray'],
                gridwidth=1,
                linecolor=BW_COLORS['black'],
                linewidth=3,
                mirror=True,
                tickangle=-45
            )
            
            fig.update_yaxes(
                title_text='Number of Topics',
                title_font=dict(size=40, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
                tickfont=dict(size=30, color=BW_COLORS['black'], family='Arial, sans-serif'),
                gridcolor=BW_COLORS['very_light_gray'],
                gridwidth=1,
                linecolor=BW_COLORS['black'],
                linewidth=3,
                mirror=True,
                secondary_y=False
            )
            
            fig.update_yaxes(
                title_text='Percentage (%)',
                title_font=dict(size=40, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
                tickfont=dict(size=30, color=BW_COLORS['black'], family='Arial, sans-serif'),
                gridcolor=BW_COLORS['very_light_gray'],
                gridwidth=1,
                linecolor=BW_COLORS['black'],
                linewidth=3,
                mirror=True,
                secondary_y=True
            )
            
            # Export
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            fig.write_image(output_file, width=4080, height=2448, scale=1, format='png')
            
            print(f"✓ Exported to {output_file}")
            return output_file
        except Exception as e:
            print(f"⚠ Error: {e}")
            return None
    
    def export_chart_3_authors_by_period(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Chart 3: Authors by Period (Bar Chart)"""
        print(f"\n👥 Exporting Chart 3: Authors by Period...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chart_exports/chart_3_authors_by_period_{timestamp}.png"
        
        # Get data from Neo4j
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                result = session.run("""
                    MATCH (p:Paper)<-[:AUTHORED]-(a:Author)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year
                      AND p.year > 0
                    RETURN count(DISTINCT a) as unique_authors
                """, start_year=current_start, end_year=current_end).single()
                
                unique_authors = result['unique_authors'] if result else 0
                intervals.append({'interval': interval_str, 'count': unique_authors})
                current_start = current_end
        
        if not intervals:
            print("⚠ No data found")
            return None
        
        # Prepare data
        intervals_list = [i['interval'] for i in intervals]
        counts = [i['count'] for i in intervals]
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=intervals_list,
            y=counts,
            marker=dict(
                color=BW_COLORS['medium_gray'],
                line=dict(color=BW_COLORS['black'], width=3)
            ),
            text=counts,
            textposition='outside',
            textfont=dict(size=32, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
            name='Authors'
        ))
        
        # Apply layout
        layout = self.get_bw_layout(
            title='Authors by Period',
            xaxis_title='Time Period',
            yaxis_title='Number of Unique Authors'
        )
        fig.update_layout(layout)
        
        # Export
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        fig.write_image(output_file, width=4080, height=2448, scale=1, format='png')
        
        print(f"✓ Exported to {output_file}")
        return output_file
    
    def export_chart_4_phenomena_by_period(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Chart 4: Phenomena by Period (Bar Chart)"""
        print(f"\n🔬 Exporting Chart 4: Phenomena by Period...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chart_exports/chart_4_phenomena_by_period_{timestamp}.png"
        
        # Get data from Neo4j
        intervals = []
        current_start = start_year
        
        with self.driver.session() as session:
            while current_start < end_year:
                current_end = min(current_start + 5, end_year)
                interval_str = f"{current_start}-{current_end-1}"
                
                result = session.run("""
                    MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                    WHERE p.year >= $start_year 
                      AND p.year < $end_year 
                      AND p.year > 0
                    RETURN count(DISTINCT ph) as unique_phenomena
                """, start_year=current_start, end_year=current_end).single()
                
                unique_phenomena = result['unique_phenomena'] if result else 0
                intervals.append({'interval': interval_str, 'count': unique_phenomena})
                current_start = current_end
        
        if not intervals:
            print("⚠ No data found")
            return None
        
        # Prepare data
        intervals_list = [i['interval'] for i in intervals]
        counts = [i['count'] for i in intervals]
        
        # Create bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=intervals_list,
            y=counts,
            marker=dict(
                color=BW_COLORS['light_gray'],
                line=dict(color=BW_COLORS['black'], width=3)
            ),
            text=counts,
            textposition='outside',
            textfont=dict(size=32, color=BW_COLORS['black'], family='Arial, sans-serif', weight='bold'),
            name='Phenomena'
        ))
        
        # Apply layout
        layout = self.get_bw_layout(
            title='Phenomena by Period',
            xaxis_title='Time Period',
            yaxis_title='Number of Unique Phenomena'
        )
        fig.update_layout(layout)
        
        # Export
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        fig.write_image(output_file, width=4080, height=2448, scale=1, format='png')
        
        print(f"✓ Exported to {output_file}")
        return output_file
    
    def export_chart_5_theory_evolution(self, start_year: int = 1985, end_year: int = 2025, output_file: str = None):
        """Chart 5: Theory Evolution (Line Chart)"""
        print(f"\n📊 Exporting Chart 5: Theory Evolution...")
        
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"chart_exports/chart_5_theory_evolution_{timestamp}.png"
        
        # Get data from API
        try:
            url = f"{self.api_base_url}/analytics/theories/evolution-divergence"
            params = {"start_year": start_year, "end_year": end_year}
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            data = response.json()
            
            intervals_data = data.get('intervals', [])
            if not intervals_data:
                print("⚠ No data found")
                return None
            
            # Get top 5 theories across all intervals
            # Note: theories is a DICT where keys are theory names, not a list
            theory_counts = {}
            for interval in intervals_data:
                if not isinstance(interval, dict):
                    continue
                
                theories = interval.get('theories', {})
                if not isinstance(theories, dict):
                    continue
                
                # theories is a dict: {theory_name: {usage_count, paper_count, ...}}
                for theory_name, theory_data in theories.items():
                    if isinstance(theory_data, dict):
                        paper_count = theory_data.get('paper_count', 0) or theory_data.get('usage_count', 0)
                    else:
                        paper_count = 0
                    
                    if theory_name:
                        theory_counts[theory_name] = theory_counts.get(theory_name, 0) + paper_count
            
            top_theories = sorted(theory_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_theory_names = [t[0] for t in top_theories]
            
            # Create figure
            fig = go.Figure()
            
            # Prepare data for each top theory
            intervals = []
            for i in intervals_data:
                if isinstance(i, dict):
                    intervals.append(i.get('interval', ''))
                else:
                    intervals.append(str(i))
            
            colors = [BW_COLORS['black'], BW_COLORS['dark_gray'], BW_COLORS['medium_gray'], 
                     BW_COLORS['light_gray'], BW_COLORS['very_light_gray']]
            
            for idx, theory_name in enumerate(top_theory_names):
                proportions = []
                for interval in intervals_data:
                    if not isinstance(interval, dict):
                        proportions.append(0)
                        continue
                    
                    # theories is a dict: {theory_name: {usage_count, paper_count, ...}}
                    theories = interval.get('theories', {})
                    if not isinstance(theories, dict):
                        proportions.append(0)
                        continue
                    
                    theory_data = theories.get(theory_name)
                    if theory_data and isinstance(theory_data, dict):
                        # Calculate proportion: paper_count / total_papers
                        paper_count = theory_data.get('paper_count', 0) or theory_data.get('usage_count', 0)
                        total_papers = interval.get('total_papers', 1)
                        prop = (paper_count / total_papers * 100) if total_papers > 0 else 0
                    else:
                        prop = 0
                    
                    proportions.append(prop)
                
                fig.add_trace(go.Scatter(
                    x=intervals,
                    y=proportions,
                    mode='lines+markers',
                    name=theory_name[:40],  # Truncate long names
                    line=dict(color=colors[idx % len(colors)], width=4, 
                             dash=LINE_STYLES[idx % len(LINE_STYLES)]),
                    marker=dict(size=12, symbol=MARKER_SYMBOLS[idx % len(MARKER_SYMBOLS)],
                              line=dict(width=2, color=colors[idx % len(colors)]))
                ))
            
            # Apply layout
            layout = self.get_bw_layout(
                title='Theory Evolution (Top 5 Theories)',
                xaxis_title='Time Period',
                yaxis_title='Proportion (%)'
            )
            fig.update_layout(layout)
            
            # Export
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
            fig.write_image(output_file, width=4080, height=2448, scale=1, format='png')
            
            print(f"✓ Exported to {output_file}")
            return output_file
        except Exception as e:
            print(f"⚠ Error: {e}")
            return None
    
    def export_all_charts(self, start_year: int = 1985, end_year: int = 2025, output_dir: str = "chart_exports"):
        """Export all charts to PNG files"""
        print(f"\n{'='*70}")
        print(f"📊 EXPORTING ALL CHARTS TO PNG (PLOTLY)")
        print(f"{'='*70}")
        print(f"Time Range: {start_year}-{end_year}")
        print(f"Output Directory: {output_dir}")
        print(f"Resolution: 4080px wide, 1200 DPI, Black & White")
        print(f"{'='*70}\n")
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_files = {}
        
        # Export each chart (charts that don't require API)
        try:
            exported_files['chart_1_paper_counts'] = self.export_chart_1_paper_counts(
                start_year, end_year, 
                os.path.join(output_dir, f"chart_1_paper_counts_{timestamp}.png")
            )
        except Exception as e:
            print(f"❌ Error exporting Chart 1: {e}")
            exported_files['chart_1_paper_counts'] = None
        
        try:
            exported_files['chart_3_authors'] = self.export_chart_3_authors_by_period(
                start_year, end_year,
                os.path.join(output_dir, f"chart_3_authors_by_period_{timestamp}.png")
            )
        except Exception as e:
            print(f"❌ Error exporting Chart 3: {e}")
            exported_files['chart_3_authors'] = None
        
        try:
            exported_files['chart_4_phenomena'] = self.export_chart_4_phenomena_by_period(
                start_year, end_year,
                os.path.join(output_dir, f"chart_4_phenomena_by_period_{timestamp}.png")
            )
        except Exception as e:
            print(f"❌ Error exporting Chart 4: {e}")
            exported_files['chart_4_phenomena'] = None
        
        # Charts that require API (may fail if API not available)
        try:
            exported_files['chart_2_topic_evolution'] = self.export_chart_2_topic_evolution(
                start_year, end_year,
                os.path.join(output_dir, f"chart_2_topic_evolution_{timestamp}.png")
            )
            if not exported_files['chart_2_topic_evolution']:
                print("⚠ Chart 2: No data returned from API")
        except requests.exceptions.RequestException as e:
            print(f"⚠ Chart 2 requires API server (may not be running): {e}")
            exported_files['chart_2_topic_evolution'] = None
        except Exception as e:
            print(f"❌ Error exporting Chart 2: {e}")
            import traceback
            traceback.print_exc()
            exported_files['chart_2_topic_evolution'] = None
        
        try:
            exported_files['chart_5_theory_evolution'] = self.export_chart_5_theory_evolution(
                start_year, end_year,
                os.path.join(output_dir, f"chart_5_theory_evolution_{timestamp}.png")
            )
            if not exported_files['chart_5_theory_evolution']:
                print("⚠ Chart 5: No data returned from API")
        except requests.exceptions.RequestException as e:
            print(f"⚠ Chart 5 requires API server (may not be running): {e}")
            exported_files['chart_5_theory_evolution'] = None
        except Exception as e:
            print(f"❌ Error exporting Chart 5: {e}")
            import traceback
            traceback.print_exc()
            exported_files['chart_5_theory_evolution'] = None
        
        # Create summary
        summary_file = os.path.join(output_dir, f"export_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Chart Export Summary (Plotly)\n")
            f.write(f"{'='*70}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Time Range: {start_year}-{end_year}\n")
            f.write(f"Resolution: 4080px wide, 1200 DPI\n")
            f.write(f"Color: Black & White (Grayscale)\n")
            f.write(f"Library: Plotly\n")
            f.write(f"{'='*70}\n\n")
            
            f.write("Exported Files:\n")
            f.write("-" * 70 + "\n")
            for chart_name, file_path in exported_files.items():
                if file_path:
                    f.write(f"{chart_name}: {file_path}\n")
                else:
                    f.write(f"{chart_name}: FAILED\n")
        
        print(f"\n{'='*70}")
        print(f"✅ EXPORT COMPLETE")
        print(f"{'='*70}")
        print(f"All PNG files exported to: {output_dir}/")
        print(f"Summary saved to: {summary_file}")
        print(f"{'='*70}\n")
        
        return exported_files


def main():
    """Main execution function"""
    exporter = None
    try:
        # Check if kaleido is available (required for Plotly image export)
        try:
            import kaleido
        except ImportError:
            print("\n⚠ WARNING: 'kaleido' package not found!")
            print("   Plotly requires 'kaleido' to export images.")
            print("   Install it with: pip install kaleido")
            print("   Or use: pip install plotly[kaleido]")
            sys.exit(1)
        
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:5000/api")
        exporter = ChartExporter(api_base_url=api_base_url)
        
        # Export all charts
        exported_files = exporter.export_all_charts(
            start_year=1985,
            end_year=2025
        )
        
        print("\n✅ All chart exports completed successfully!")
        print("\nExported files:")
        for chart_name, file_path in exported_files.items():
            if file_path:
                print(f"  ✓ {chart_name}: {file_path}")
            else:
                print(f"  ✗ {chart_name}: FAILED")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if exporter:
            exporter.close()


if __name__ == "__main__":
    main()
