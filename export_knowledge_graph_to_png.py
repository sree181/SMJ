#!/usr/bin/env python3
"""
Export Knowledge Graph Visualizations to PNG
Generates high-resolution PNG images of the Neo4j knowledge graph
to showcase the data source for journal reviewers.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from neo4j import GraphDatabase
from dotenv import load_dotenv
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Load environment variables
load_dotenv()

# Black and white color scheme
BW_COLORS = {
    'black': '#000000',
    'dark_gray': '#333333',
    'medium_gray': '#666666',
    'light_gray': '#999999',
    'very_light_gray': '#CCCCCC',
    'white': '#FFFFFF'
}

class KnowledgeGraphExporter:
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
    
    def get_paper_theory_graph(self, limit: int = 25) -> nx.Graph:
        """Extract Paper-Theory relationships from Neo4j"""
        print(f"  Extracting Paper-Theory relationships (limit: {limit})...")
        
        G = nx.Graph()
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.year > 0 AND p.paper_id IS NOT NULL AND t.name IS NOT NULL
                RETURN DISTINCT p.paper_id as paper_id,
                       p.title as paper_title,
                       p.year as year,
                       t.name as theory_name
                ORDER BY p.year DESC
                LIMIT $limit
            """, limit=limit)
            
            for record in result:
                paper_id = record['paper_id']
                paper_title = record['paper_title'] or f"Paper {paper_id}"
                year = record['year'] or 0
                theory_name = record['theory_name']
                
                # Skip if any value is None
                if not paper_id or not theory_name:
                    continue
                
                # Add nodes
                if not G.has_node(paper_id):
                    G.add_node(paper_id, 
                              node_type='Paper',
                              label=paper_title[:50] + ('...' if len(paper_title) > 50 else ''),
                              year=year)
                
                if not G.has_node(theory_name):
                    G.add_node(theory_name, 
                              node_type='Theory',
                              label=theory_name)
                
                # Add edge
                if G.has_edge(paper_id, theory_name):
                    G[paper_id][theory_name]['weight'] += 1
                else:
                    G.add_edge(paper_id, theory_name, weight=1)
        
        print(f"  ✓ Extracted {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def get_theory_phenomenon_graph(self, limit: int = 30) -> nx.Graph:
        """Extract Theory-Phenomenon relationships from Neo4j"""
        print(f"  Extracting Theory-Phenomenon relationships (limit: {limit})...")
        
        G = nx.Graph()
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                MATCH (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WHERE t.name IS NOT NULL AND ph.phenomenon_name IS NOT NULL
                WITH t, ph, count(DISTINCT p) as paper_count
                RETURN t.name as theory_name,
                       ph.phenomenon_name as phenomenon_name,
                       paper_count
                ORDER BY paper_count DESC
                LIMIT $limit
            """, limit=limit)
            
            for record in result:
                theory_name = record['theory_name']
                phenomenon_name = record['phenomenon_name']
                paper_count = record['paper_count'] or 1
                
                # Skip if any value is None
                if not theory_name or not phenomenon_name:
                    continue
                
                # Add nodes
                if not G.has_node(theory_name):
                    G.add_node(theory_name, 
                              node_type='Theory',
                              label=theory_name)
                
                if not G.has_node(phenomenon_name):
                    G.add_node(phenomenon_name, 
                              node_type='Phenomenon',
                              label=phenomenon_name)
                
                # Add edge
                G.add_edge(theory_name, phenomenon_name, weight=paper_count)
        
        print(f"  ✓ Extracted {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def get_author_paper_graph(self, limit: int = 25) -> nx.Graph:
        """Extract Author-Paper relationships from Neo4j"""
        print(f"  Extracting Author-Paper relationships (limit: {limit})...")
        
        G = nx.Graph()
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Author)<-[:AUTHORED]-(p:Paper)
                WHERE p.year > 0 AND a.author_id IS NOT NULL AND p.paper_id IS NOT NULL
                RETURN DISTINCT a.author_id as author_id,
                       COALESCE(a.full_name, a.given_name + ' ' + a.family_name, 'Author ' + a.author_id) as author_name,
                       p.paper_id as paper_id,
                       p.title as paper_title,
                       p.year as year
                ORDER BY p.year DESC
                LIMIT $limit
            """, limit=limit)
            
            for record in result:
                author_id = record['author_id']
                author_name = record['author_name'] or f"Author {author_id}"
                paper_id = record['paper_id']
                paper_title = record['paper_title'] or f"Paper {paper_id}"
                year = record['year'] or 0
                
                # Add nodes
                if not G.has_node(author_id):
                    G.add_node(author_id, 
                              node_type='Author',
                              label=author_name[:30] + ('...' if len(author_name) > 30 else ''),
                              name=author_name)
                
                if not G.has_node(paper_id):
                    G.add_node(paper_id, 
                              node_type='Paper',
                              label=paper_title[:30] + ('...' if len(paper_title) > 30 else ''),
                              year=year)
                
                # Add edge
                if G.has_edge(author_id, paper_id):
                    G[author_id][paper_id]['weight'] += 1
                else:
                    G.add_edge(author_id, paper_id, weight=1)
        
        print(f"  ✓ Extracted {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def get_overview_graph(self, limit: int = 20) -> nx.Graph:
        """Extract a high-level overview showing all node types"""
        print(f"  Extracting overview graph (limit: {limit})...")
        
        G = nx.Graph()
        
        with self.driver.session() as session:
            # Get top papers with their theories and phenomena
            result = session.run("""
                MATCH (p:Paper)
                WHERE p.year > 0 AND p.paper_id IS NOT NULL
                OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
                WHERE t.name IS NOT NULL
                OPTIONAL MATCH (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WHERE ph.phenomenon_name IS NOT NULL
                WITH p, collect(DISTINCT t.name)[..3] as theories, 
                     collect(DISTINCT ph.phenomenon_name)[..3] as phenomena
                WHERE size(theories) > 0 OR size(phenomena) > 0
                RETURN p.paper_id as paper_id,
                       p.title as paper_title,
                       p.year as year,
                       theories,
                       phenomena
                ORDER BY p.year DESC
                LIMIT $limit
            """, limit=limit)
            
            for record in result:
                paper_id = record['paper_id']
                paper_title = record['paper_title'] or f"Paper {paper_id}"
                year = record['year'] or 0
                theories = record['theories'] or []
                phenomena = record['phenomena'] or []
                
                # Add paper node
                if not G.has_node(paper_id):
                    G.add_node(paper_id, 
                              node_type='Paper',
                              label=f"P{year}" if year > 0 else "P",
                              year=year)
                
                # Add theory nodes and edges
                for theory_name in (theories or []):
                    if theory_name:
                        if not G.has_node(theory_name):
                            G.add_node(theory_name, 
                                      node_type='Theory',
                                      label=theory_name[:20] + ('...' if len(theory_name) > 20 else ''))
                        G.add_edge(paper_id, theory_name, weight=1)
                
                # Add phenomenon nodes and edges
                for phenomenon_name in (phenomena or []):
                    if phenomenon_name:
                        if not G.has_node(phenomenon_name):
                            G.add_node(phenomenon_name, 
                                      node_type='Phenomenon',
                                      label=phenomenon_name[:20] + ('...' if len(phenomenon_name) > 20 else ''))
                        G.add_edge(paper_id, phenomenon_name, weight=1)
        
        print(f"  ✓ Extracted {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        return G
    
    def visualize_graph(self, G: nx.Graph, title: str, output_file: str, 
                       width: int = 4080, height: int = 2448, dpi: int = 1200):
        """Visualize a NetworkX graph and save as PNG"""
        if G.number_of_nodes() == 0:
            print(f"  ⚠ No nodes to visualize")
            return None
        
        print(f"  Visualizing graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges...")
        
        # If graph is too large, sample the most important nodes
        if G.number_of_nodes() > 30:
            print(f"  Graph too large ({G.number_of_nodes()} nodes), sampling top 30 nodes by degree...")
            # Get nodes with highest degree (most connections)
            node_degrees = dict(G.degree())
            top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:30]
            top_node_ids = [n[0] for n in top_nodes]
            # Create subgraph with top nodes and their neighbors
            G_sub = G.subgraph(top_nodes).copy()
            # Add edges between top nodes if they exist in original graph
            for node in top_node_ids:
                neighbors = list(G.neighbors(node))
                for neighbor in neighbors:
                    if neighbor in top_node_ids:
                        if not G_sub.has_edge(node, neighbor):
                            G_sub.add_edge(node, neighbor, weight=G[node][neighbor].get('weight', 1))
            G = G_sub
            print(f"  Using subgraph with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Create figure
        width_inches = width / dpi
        height_inches = height / dpi
        fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=dpi, facecolor='white')
        
        # Use better layout algorithm based on graph size
        if G.number_of_nodes() <= 15:
            # Use circular layout for small graphs
            pos = nx.circular_layout(G)
        elif G.number_of_nodes() <= 30:
            # Use spring layout with better parameters
            pos = nx.spring_layout(G, k=3, iterations=100, seed=42)
        else:
            # Use force-directed layout
            pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
        
        # Separate nodes by type
        paper_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'Paper']
        theory_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'Theory']
        phenomenon_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'Phenomenon']
        author_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'Author']
        
        # Draw edges with better visibility
        edges = G.edges()
        edge_weights = [G[u][v].get('weight', 1) for u, v in edges]
        if edge_weights and max(edge_weights) > 1:
            max_weight = max(edge_weights)
            edge_widths = [max(1, w / max_weight * 3) for w in edge_weights]
        else:
            edge_widths = [2] * len(edges)
        
        nx.draw_networkx_edges(G, pos, ax=ax, 
                              edge_color=BW_COLORS['medium_gray'],
                              width=edge_widths,
                              alpha=0.7,
                              style='solid')
        
        # Draw nodes by type with different shapes (larger for visibility)
        node_size = 1200
        
        # Papers - circles
        if paper_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=paper_nodes, 
                                  node_color=BW_COLORS['dark_gray'],
                                  node_shape='o',
                                  node_size=node_size,
                                  ax=ax, edgecolors=BW_COLORS['black'], linewidths=2)
        
        # Theories - squares
        if theory_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=theory_nodes, 
                                  node_color=BW_COLORS['medium_gray'],
                                  node_shape='s',
                                  node_size=node_size,
                                  ax=ax, edgecolors=BW_COLORS['black'], linewidths=2)
        
        # Phenomena - diamonds
        if phenomenon_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=phenomenon_nodes, 
                                  node_color=BW_COLORS['light_gray'],
                                  node_shape='D',
                                  node_size=node_size,
                                  ax=ax, edgecolors=BW_COLORS['black'], linewidths=2)
        
        # Authors - triangles
        if author_nodes:
            nx.draw_networkx_nodes(G, pos, nodelist=author_nodes, 
                                  node_color=BW_COLORS['very_light_gray'],
                                  node_shape='^',
                                  node_size=node_size,
                                  ax=ax, edgecolors=BW_COLORS['black'], linewidths=2)
        
        # Draw labels for all nodes (with smart truncation)
        labels = {}
        for n, d in G.nodes(data=True):
            label = d.get('label', str(n))
            # Truncate long labels
            if len(label) > 25:
                label = label[:22] + '...'
            labels[n] = label
        
        # Draw labels with better positioning
        nx.draw_networkx_labels(G, pos, labels, ax=ax,
                               font_size=14,
                               font_color=BW_COLORS['black'],
                               font_weight='bold',
                               font_family='Arial',
                               bbox=dict(boxstyle='round,pad=0.3', 
                                       facecolor='white', 
                                       edgecolor=BW_COLORS['very_light_gray'],
                                       alpha=0.8,
                                       linewidth=1))
        
        # Add title
        ax.set_title(title, fontsize=42, fontweight='bold', color=BW_COLORS['black'],
                    pad=40, family='Arial')
        
        # Create legend
        legend_elements = []
        if paper_nodes:
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                              markerfacecolor=BW_COLORS['dark_gray'],
                                              markersize=20, markeredgecolor=BW_COLORS['black'],
                                              markeredgewidth=2, label='Papers'))
        if theory_nodes:
            legend_elements.append(plt.Line2D([0], [0], marker='s', color='w',
                                              markerfacecolor=BW_COLORS['medium_gray'],
                                              markersize=20, markeredgecolor=BW_COLORS['black'],
                                              markeredgewidth=2, label='Theories'))
        if phenomenon_nodes:
            legend_elements.append(plt.Line2D([0], [0], marker='D', color='w',
                                              markerfacecolor=BW_COLORS['light_gray'],
                                              markersize=20, markeredgecolor=BW_COLORS['black'],
                                              markeredgewidth=2, label='Phenomena'))
        if author_nodes:
            legend_elements.append(plt.Line2D([0], [0], marker='^', color='w',
                                              markerfacecolor=BW_COLORS['very_light_gray'],
                                              markersize=20, markeredgecolor=BW_COLORS['black'],
                                              markeredgewidth=2, label='Authors'))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='upper right', 
                     fontsize=24, frameon=True, fancybox=True,
                     facecolor='white', edgecolor=BW_COLORS['black'],
                     framealpha=1.0, borderpad=1.0)
        
        # Add subtitle with Neo4j info
        subtitle = f"Data Source: Neo4j Knowledge Graph | {G.number_of_nodes()} nodes, {G.number_of_edges()} relationships"
        ax.text(0.5, 0.02, subtitle, transform=ax.transAxes,
               fontsize=22, ha='center', color=BW_COLORS['black'],
               family='Arial', style='italic', weight='bold')
        
        ax.axis('off')
        plt.tight_layout()
        
        # Save
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
        plt.savefig(output_file, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.2)
        plt.close()
        
        print(f"  ✓ Saved to {output_file}")
        return output_file
    
    def export_all_graphs(self, output_dir: str = "knowledge_graph_exports"):
        """Export all knowledge graph visualizations"""
        print(f"\n{'='*70}")
        print(f"📊 EXPORTING KNOWLEDGE GRAPH VISUALIZATIONS")
        print(f"{'='*70}")
        print(f"Output Directory: {output_dir}")
        print(f"Resolution: 4080px wide, 1200 DPI, Black & White")
        print(f"{'='*70}\n")
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_files = {}
        
        # Graph 1: Paper-Theory relationships
        try:
            print(f"\n📄 Graph 1: Paper-Theory Relationships")
            G1 = self.get_paper_theory_graph(limit=50)
            if G1.number_of_nodes() > 0:
                output_file = os.path.join(output_dir, f"graph_1_paper_theory_{timestamp}.png")
                exported_files['graph_1_paper_theory'] = self.visualize_graph(
                    G1, 
                    "Knowledge Graph: Papers and Theories",
                    output_file
                )
            else:
                print("  ⚠ No data found")
                exported_files['graph_1_paper_theory'] = None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            exported_files['graph_1_paper_theory'] = None
        
        # Graph 2: Theory-Phenomenon relationships
        try:
            print(f"\n🔗 Graph 2: Theory-Phenomenon Relationships")
            G2 = self.get_theory_phenomenon_graph(limit=50)
            if G2.number_of_nodes() > 0:
                output_file = os.path.join(output_dir, f"graph_2_theory_phenomenon_{timestamp}.png")
                exported_files['graph_2_theory_phenomenon'] = self.visualize_graph(
                    G2,
                    "Knowledge Graph: Theories and Phenomena",
                    output_file
                )
            else:
                print("  ⚠ No data found")
                exported_files['graph_2_theory_phenomenon'] = None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            exported_files['graph_2_theory_phenomenon'] = None
        
        # Graph 3: Author-Paper relationships
        try:
            print(f"\n👥 Graph 3: Author-Paper Relationships")
            G3 = self.get_author_paper_graph(limit=50)
            if G3.number_of_nodes() > 0:
                output_file = os.path.join(output_dir, f"graph_3_author_paper_{timestamp}.png")
                exported_files['graph_3_author_paper'] = self.visualize_graph(
                    G3,
                    "Knowledge Graph: Authors and Papers",
                    output_file
                )
            else:
                print("  ⚠ No data found")
                exported_files['graph_3_author_paper'] = None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            exported_files['graph_3_author_paper'] = None
        
        # Graph 4: Overview (all node types)
        try:
            print(f"\n🌐 Graph 4: Overview (All Relationships)")
            G4 = self.get_overview_graph(limit=30)
            if G4.number_of_nodes() > 0:
                output_file = os.path.join(output_dir, f"graph_4_overview_{timestamp}.png")
                exported_files['graph_4_overview'] = self.visualize_graph(
                    G4,
                    "Knowledge Graph: Overview (Papers, Theories, Phenomena)",
                    output_file
                )
            else:
                print("  ⚠ No data found")
                exported_files['graph_4_overview'] = None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            exported_files['graph_4_overview'] = None
        
        # Create summary
        summary_file = os.path.join(output_dir, f"export_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Knowledge Graph Export Summary\n")
            f.write(f"{'='*70}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Source: Neo4j Knowledge Graph\n")
            f.write(f"Resolution: 4080px wide, 1200 DPI\n")
            f.write(f"Color: Black & White (Grayscale)\n")
            f.write(f"{'='*70}\n\n")
            
            f.write("Exported Files:\n")
            f.write("-" * 70 + "\n")
            for graph_name, file_path in exported_files.items():
                if file_path:
                    f.write(f"{graph_name}: {file_path}\n")
                else:
                    f.write(f"{graph_name}: FAILED\n")
        
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
        exporter = KnowledgeGraphExporter()
        
        # Export all graphs
        exported_files = exporter.export_all_graphs()
        
        print("\n✅ All knowledge graph exports completed successfully!")
        print("\nExported files:")
        for graph_name, file_path in exported_files.items():
            if file_path:
                print(f"  ✓ {graph_name}: {file_path}")
            else:
                print(f"  ✗ {graph_name}: FAILED")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if exporter:
            exporter.close()


if __name__ == "__main__":
    main()
