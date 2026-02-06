# Neo4j Browser Queries for Graph Visualization

Run these queries one by one in Neo4j Aura Browser to visualize and export knowledge graphs as PNG images.

## How to Use

1. Open Neo4j Aura Browser (or Neo4j Desktop Browser)
2. Copy and paste each query below
3. Click "Run" to visualize the graph
4. Click the **Export** button (download icon) in the browser to save as PNG
5. Repeat for each query

---

## Query 1: Papers and Theories (Top 10)

**Description**: Shows papers connected to the theories they use.

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WHERE p.year > 0 AND p.paper_id IS NOT NULL AND t.name IS NOT NULL
WITH p, t, count(*) as strength
ORDER BY p.year DESC, strength DESC
LIMIT 10
RETURN p, t
```

**What you'll see**: Papers (rectangles) connected to Theories (ellipses)

---

## Query 2: Theories and Phenomena (Top 10)

**Description**: Shows theories that explain phenomena through papers.

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
MATCH (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
WHERE t.name IS NOT NULL AND ph.phenomenon_name IS NOT NULL
WITH t, ph, count(DISTINCT p) as paper_count
ORDER BY paper_count DESC
LIMIT 10
RETURN t, ph
```

**What you'll see**: Theories (ellipses) connected to Phenomena (diamonds)

---

## Query 3: Papers, Theories, and Phenomena (Top 10)

**Description**: Shows papers with both theories and phenomena they study.

```cypher
MATCH (p:Paper)
WHERE p.year > 0 AND p.paper_id IS NOT NULL
OPTIONAL MATCH (p)-[:USES_THEORY]->(t:Theory)
WHERE t.name IS NOT NULL
OPTIONAL MATCH (p)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
WHERE ph.phenomenon_name IS NOT NULL
WITH p, collect(DISTINCT t)[..3] as theories, 
     collect(DISTINCT ph)[..3] as phenomena
WHERE size(theories) > 0 OR size(phenomena) > 0
RETURN p, theories, phenomena
LIMIT 10
```

**What you'll see**: Papers connected to both Theories and Phenomena

---

## Query 4: Top Theories by Usage (Top 10)

**Description**: Shows the most frequently used theories.

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WHERE t.name IS NOT NULL
WITH t, count(DISTINCT p) as paper_count
ORDER BY paper_count DESC
LIMIT 10
RETURN t
```

**What you'll see**: Top 10 theories as nodes

---

## Query 5: Top Phenomena by Study Count (Top 10)

**Description**: Shows the most frequently studied phenomena.

```cypher
MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
WHERE ph.phenomenon_name IS NOT NULL
WITH ph, count(DISTINCT p) as paper_count
ORDER BY paper_count DESC
LIMIT 10
RETURN ph
```

**What you'll see**: Top 10 phenomena as nodes

---

## Query 6: Theory-Phenomenon Connections (Top 10 Strongest)

**Description**: Shows the strongest theory-phenomenon connections.

```cypher
MATCH (t:Theory)-[:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE t.name IS NOT NULL AND ph.phenomenon_name IS NOT NULL
WITH t, ph, count(*) as connection_strength
ORDER BY connection_strength DESC
LIMIT 10
RETURN t, ph
```

**What you'll see**: Theories directly connected to Phenomena via EXPLAINS_PHENOMENON relationships

---

## Query 7: Recent Papers with Theories (Top 10)

**Description**: Shows the 10 most recent papers and their theories.

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WHERE p.year > 0 AND p.year >= 2015 AND t.name IS NOT NULL
WITH p, collect(DISTINCT t)[..3] as theories
ORDER BY p.year DESC
LIMIT 10
RETURN p, theories
```

**What you'll see**: Recent papers (2015+) with their theories

---

## Query 8: Papers by Time Period (Top 10 per Period)

**Description**: Shows papers from a specific time period with their theories.

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WHERE p.year >= 2010 AND p.year < 2015 
  AND p.paper_id IS NOT NULL 
  AND t.name IS NOT NULL
WITH p, collect(DISTINCT t)[..2] as theories
ORDER BY p.year DESC
LIMIT 10
RETURN p, theories
```

**What you'll see**: Papers from 2010-2014 with their theories

---

## Export Tips in Neo4j Browser

1. **After running a query**, the graph will appear in the visualization panel
2. **Click the Export button** (download icon) in the top toolbar
3. **Select "PNG"** format
4. **Adjust zoom** if needed before exporting (use mouse wheel or zoom controls)
5. **For better quality**: 
   - Zoom in to focus on the graph
   - Use browser's full-screen mode if available
   - Export at maximum zoom for higher resolution

---

## Customization

You can modify the `LIMIT 10` in any query to show more or fewer nodes:
- `LIMIT 5` - Show only 5 nodes (very focused)
- `LIMIT 15` - Show 15 nodes (more comprehensive)
- `LIMIT 20` - Show 20 nodes (detailed view)

---

## Notes

- All queries use `LIMIT 10` to keep visualizations clear and non-overlapping
- Queries filter out NULL values to ensure clean results
- Results are ordered by relevance (usage count, year, etc.)
- Neo4j Browser will automatically layout the graph to prevent overlaps
