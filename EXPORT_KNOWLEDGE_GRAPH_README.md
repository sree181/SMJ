# Export Knowledge Graph Visualizations

This script exports clear, non-overlapping knowledge graph visualizations directly from Neo4j using Graphviz.

## Why Graphviz?

- **No Overlapping Nodes**: Graphviz uses sophisticated layout algorithms (hierarchical, force-directed) that prevent node overlaps
- **Publication Quality**: Designed specifically for clear, readable graph visualizations
- **Automatic Layout**: Handles complex graph layouts automatically
- **High Resolution**: Supports high DPI output

## Installation

### 1. Install Graphviz System Package

**macOS:**
```bash
brew install graphviz
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install graphviz
```

**Windows:**
Download from: https://graphviz.org/download/

### 2. Install Python Package

```bash
pip install graphviz
```

## Usage

```bash
python3 export_knowledge_graph_graphviz.py
```

## Output

All PNG files are saved to `knowledge_graph_exports/`:
- `graph_1_paper_theory_YYYYMMDD_HHMMSS.png` - Papers connected to theories
- `graph_2_theory_phenomenon_YYYYMMDD_HHMMSS.png` - Theories explaining phenomena

## Features

- **Clear Layout**: No overlapping nodes, automatic spacing
- **Node Types**:
  - Papers: Dark gray rectangles
  - Theories: Medium gray ellipses  
  - Phenomena: Light gray diamonds
- **High Resolution**: 1200 DPI output
- **Black & White**: Grayscale colors suitable for publication
- **Labels**: All nodes clearly labeled
- **Data Source**: Each graph shows "Neo4j Knowledge Graph" as data source

## Alternative: Neo4j Browser Export

If you prefer, you can also:
1. Open Neo4j Browser
2. Run a query to visualize the graph
3. Use browser's export feature or screenshot

Example query:
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WHERE p.year > 0
RETURN p, t
LIMIT 20
```

## Troubleshooting

If you get "graphviz not found" error:
1. Make sure system package is installed: `brew install graphviz`
2. Make sure Python package is installed: `pip install graphviz`
3. Restart your terminal after installing
