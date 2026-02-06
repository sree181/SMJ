#!/usr/bin/env python3
"""
Export Knowledge Graph Visualizations using Graphviz
Generates clear, non-overlapping graph visualizations directly from Neo4j
using Graphviz for publication-quality output.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Try to import graphviz
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False
    print("⚠ WARNING: graphviz not installed. Install with: pip install graphviz")
    print("   Also install system package: brew install graphviz (macOS) or apt-get install graphviz (Linux)")

# Load environment variables
load_dotenv()

class KnowledgeGraphGraphvizExporter:
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
    
    def get_paper_theory_graph(self, limit: int = 20) -> Dict[str, Any]:
        """Extract Paper-Theory relationships from Neo4j"""
        print(f"  Extracting Paper-Theory relationships (limit: {limit})...")
        
        nodes = {}
        edges = []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                WHERE p.year > 0 AND p.paper_id IS NOT NULL AND t.name IS NOT NULL
                WITH p, t, count(*) as strength
                ORDER BY p.year DESC, strength DESC
                LIMIT $limit
                RETURN DISTINCT p.paper_id as paper_id,
                       p.title as paper_title,
                       p.year as year,
                       t.name as theory_name
            """, limit=limit)
            
            for record in result:
                paper_id = record['paper_id']
                paper_title = record['paper_title'] or f"Paper {paper_id}"
                year = record['year'] or 0
                theory_name = record['theory_name']
                
                if not paper_id or not theory_name:
                    continue
                
                # Add paper node
                if paper_id not in nodes:
                    label = f"{year}\n{paper_title[:40]}{'...' if len(paper_title) > 40 else ''}"
                    nodes[paper_id] = {'type': 'Paper', 'label': label, 'year': year}
                
                # Add theory node
                if theory_name not in nodes:
                    nodes[theory_name] = {'type': 'Theory', 'label': theory_name}
                
                # Add edge
                edges.append((paper_id, theory_name))
        
        print(f"  ✓ Extracted {len(nodes)} nodes, {len(edges)} edges")
        return {'nodes': nodes, 'edges': edges}
    
    def get_theory_phenomenon_graph(self, limit: int = 25) -> Dict[str, Any]:
        """Extract Theory-Phenomenon relationships from Neo4j"""
        print(f"  Extracting Theory-Phenomenon relationships (limit: {limit})...")
        
        nodes = {}
        edges = []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
                MATCH (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
                WHERE t.name IS NOT NULL AND ph.phenomenon_name IS NOT NULL
                WITH t, ph, count(DISTINCT p) as paper_count
                ORDER BY paper_count DESC
                LIMIT $limit
                RETURN t.name as theory_name,
                       ph.phenomenon_name as phenomenon_name,
                       paper_count
            """, limit=limit)
            
            for record in result:
                theory_name = record['theory_name']
                phenomenon_name = record['phenomenon_name']
                paper_count = record['paper_count'] or 1
                
                if not theory_name or not phenomenon_name:
                    continue
                
                # Add theory node
                if theory_name not in nodes:
                    nodes[theory_name] = {'type': 'Theory', 'label': theory_name}
                
                # Add phenomenon node
                if phenomenon_name not in nodes:
                    label = phenomenon_name[:50] + ('...' if len(phenomenon_name) > 50 else '')
                    nodes[phenomenon_name] = {'type': 'Phenomenon', 'label': label}
                
                # Add edge
                edges.append((theory_name, phenomenon_name, paper_count))
        
        print(f"  ✓ Extracted {len(nodes)} nodes, {len(edges)} edges")
        return {'nodes': nodes, 'edges': edges}
    
    def visualize_graph(self, graph_data: Dict[str, Any], title: str, output_file: str):
        """Visualize graph using Graphviz"""
        if not GRAPHVIZ_AVAILABLE:
            print("  ❌ Graphviz not available. Please install graphviz.")
            return None
        
        nodes = graph_data['nodes']
        edges = graph_data['edges']
        
        if len(nodes) == 0:
            print("  ⚠ No nodes to visualize")
            return None
        
        print(f"  Visualizing graph: {len(nodes)} nodes, {len(edges)} edges...")
        
        # Create Graphviz graph
        dot = graphviz.Digraph(comment=title, format='png')
        dot.attr(rankdir='LR', size='40,24', dpi='1200')
        dot.attr('node', shape='box', style='rounded,filled', fontname='Arial', fontsize='14')
        dot.attr('edge', color='gray50', penwidth='2')
        
        # Add title as a label
        dot.attr(label=title, fontsize='24', fontname='Arial Bold')
        dot.attr(labelloc='t', labeljust='c')
        
        # Separate nodes by type
        paper_nodes = {k: v for k, v in nodes.items() if v['type'] == 'Paper'}
        theory_nodes = {k: v for k, v in nodes.items() if v['type'] == 'Theory'}
        phenomenon_nodes = {k: v for k, v in nodes.items() if v['type'] == 'Phenomenon'}
        author_nodes = {k: v for k, v in nodes.items() if v['type'] == 'Author'}
        
        # Add nodes with different colors and shapes
        # Papers - dark gray, rectangle
        for node_id, node_data in paper_nodes.items():
            dot.node(node_id, node_data['label'], 
                    fillcolor='#333333', fontcolor='white',
                    shape='box', style='rounded,filled')
        
        # Theories - medium gray, ellipse
        for node_id, node_data in theory_nodes.items():
            dot.node(node_id, node_data['label'],
                    fillcolor='#666666', fontcolor='white',
                    shape='ellipse', style='filled')
        
        # Phenomena - light gray, diamond
        for node_id, node_data in phenomenon_nodes.items():
            dot.node(node_id, node_data['label'],
                    fillcolor='#999999', fontcolor='black',
                    shape='diamond', style='filled')
        
        # Authors - very light gray, triangle
        for node_id, node_data in author_nodes.items():
            dot.node(node_id, node_data['label'],
                    fillcolor='#CCCCCC', fontcolor='black',
                    shape='triangle', style='filled')
        
        # Add edges
        for edge in edges:
            if len(edge) == 2:
                source, target = edge
                dot.edge(source, target)
            elif len(edge) == 3:
                source, target, weight = edge
                # Use thicker edge for higher weight
                penwidth = str(min(5, max(1, weight / 2)))
                dot.edge(source, target, penwidth=penwidth)
        
        # Add footer with Neo4j info
        footer = f'Data Source: Neo4j Knowledge Graph | {len(nodes)} nodes, {len(edges)} relationships'
        dot.attr(fontsize='16', fontname='Arial Italic')
        
        # Render graph
        try:
            # Save source file
            source_file = output_file.replace('.png', '.gv')
            dot.save(source_file)
            
            # Render to PNG
            dot.render(output_file.replace('.png', ''), format='png', cleanup=True)
            
            # Rename to desired output file
            rendered_file = output_file.replace('.png', '.png')
            if os.path.exists(output_file.replace('.png', '.png')):
                os.rename(output_file.replace('.png', '.png'), output_file)
            
            print(f"  ✓ Saved to {output_file}")
            return output_file
        except Exception as e:
            print(f"  ❌ Error rendering graph: {e}")
            print(f"     Make sure graphviz is installed: brew install graphviz (macOS)")
            return None
    
    def export_all_graphs(self, output_dir: str = "knowledge_graph_exports"):
        """Export all knowledge graph visualizations"""
        print(f"\n{'='*70}")
        print(f"📊 EXPORTING KNOWLEDGE GRAPH VISUALIZATIONS (GRAPHVIZ)")
        print(f"{'='*70}")
        print(f"Output Directory: {output_dir}")
        print(f"Resolution: High DPI, Clear Layout, No Overlaps")
        print(f"{'='*70}\n")
        
        if not GRAPHVIZ_AVAILABLE:
            print("❌ Graphviz not available. Please install:")
            print("   1. System package: brew install graphviz (macOS) or apt-get install graphviz (Linux)")
            print("   2. Python package: pip install graphviz")
            return {}
        
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        exported_files = {}
        
        # Graph 1: Paper-Theory relationships
        try:
            print(f"\n📄 Graph 1: Paper-Theory Relationships")
            graph_data = self.get_paper_theory_graph(limit=20)
            if len(graph_data['nodes']) > 0:
                output_file = os.path.join(output_dir, f"graph_1_paper_theory_{timestamp}.png")
                exported_files['graph_1_paper_theory'] = self.visualize_graph(
                    graph_data,
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
            graph_data = self.get_theory_phenomenon_graph(limit=25)
            if len(graph_data['nodes']) > 0:
                output_file = os.path.join(output_dir, f"graph_2_theory_phenomenon_{timestamp}.png")
                exported_files['graph_2_theory_phenomenon'] = self.visualize_graph(
                    graph_data,
                    "Knowledge Graph: Theories and Phenomena",
                    output_file
                )
            else:
                print("  ⚠ No data found")
                exported_files['graph_2_theory_phenomenon'] = None
        except Exception as e:
            print(f"  ❌ Error: {e}")
            exported_files['graph_2_theory_phenomenon'] = None
        
        # Create summary
        summary_file = os.path.join(output_dir, f"export_summary_{timestamp}.txt")
        with open(summary_file, 'w') as f:
            f.write(f"Knowledge Graph Export Summary (Graphviz)\n")
            f.write(f"{'='*70}\n")
            f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Source: Neo4j Knowledge Graph\n")
            f.write(f"Visualization: Graphviz (Clear, Non-Overlapping Layout)\n")
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
        exporter = KnowledgeGraphGraphvizExporter()
        
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
