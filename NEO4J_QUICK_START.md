# Neo4j Quick Start Guide - 5 Minute Tutorial

## Step 1: Login (1 minute)

1. Go to: `https://console.neo4j.io/` (or your Neo4j Aura URL)
2. Enter username: `neo4j`
3. Enter password: (from your `.env` file)
4. Click **Connect**

---

## Step 2: Your First Query (2 minutes)

### Count All Papers
```cypher
MATCH (p:Paper)
RETURN count(p) as TotalPapers
```

**What to do**:
1. Type the query in the top bar
2. Press `Enter`
3. See the result: "TotalPapers: 3" (or however many papers you have)

---

### See All Papers
```cypher
MATCH (p:Paper)
RETURN p.title, p.publication_year
ORDER BY p.publication_year DESC
```

**What you'll see**: A table with paper titles and years

---

## Step 3: Explore One Paper (2 minutes)

### Pick a Paper ID
First, get a paper ID:
```cypher
MATCH (p:Paper)
RETURN p.paper_id
LIMIT 1
```

### See Everything Connected to That Paper
Replace `"2025_4359"` with your paper ID:
```cypher
MATCH (p:Paper {paper_id: "2025_4359"})-[r]->(connected)
RETURN p, r, connected
LIMIT 50
```

**What you'll see**: 
- The paper in the center
- Lines connecting to:
  - Authors (who wrote it)
  - Methods (what methods were used)
  - Theories (what theories were used)
  - Research Questions (what questions it addresses)
  - Variables (what variables were used)
  - Findings (what was found)
  - And more!

**Try this**: Click on any node to see its properties

---

## What Each Node Type Means

| Node Type | What It Is | Example |
|-----------|-----------|---------|
| **Paper** | A research paper | "Double-edged stars: Michelin stars..." |
| **Author** | Person who wrote paper | "Daniel B. Sands" |
| **Method** | Research method used | "OLS Regression", "Case Study" |
| **Theory** | Theoretical framework | "Resource-Based View" |
| **ResearchQuestion** | Question paper addresses | "How do firms achieve competitive advantage?" |
| **Variable** | Variable in analysis | "Firm Performance", "CEO Tenure" |
| **Finding** | Research result | "Firms with X perform better" |
| **Contribution** | What paper contributes | "Extends RBV to include..." |
| **Software** | Tool used | "Stata", "R", "Python" |
| **Dataset** | Data source | "Compustat", "CRSP" |

---

## What Each Relationship Means

| Relationship | What It Means | Example |
|--------------|---------------|---------|
| **AUTHORED** | Author wrote paper | Author → Paper |
| **USES_METHOD** | Paper uses method | Paper → Method |
| **USES_THEORY** | Paper uses theory | Paper → Theory |
| **ADDRESSES** | Paper addresses question | Paper → ResearchQuestion |
| **USES_VARIABLE** | Paper uses variable | Paper → Variable |
| **REPORTS** | Paper reports finding | Paper → Finding |
| **USES_SAME_THEORY** | Papers share theory | Paper → Paper |
| **USES_SAME_METHOD** | Papers share method | Paper → Paper |

---

## Useful Queries to Try

### 1. Find Papers Using a Theory
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title
```

### 2. Find Papers Using a Method
```cypher
MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
RETURN m.name, count(p) as paper_count
ORDER BY paper_count DESC
```

### 3. Find All Authors
```cypher
MATCH (a:Author)
RETURN a.full_name, a.email
```

### 4. Find Research Questions
```cypher
MATCH (rq:ResearchQuestion)
RETURN rq.question
LIMIT 10
```

---

## Tips

1. **Always use LIMIT** when exploring (prevents slow queries)
2. **Click nodes** to see their properties
3. **Use Table view** for reading text (click "Table" button)
4. **Start simple** - build up to complex queries

---

## Common Questions

**Q: How do I find papers similar to one I'm reading?**
```cypher
MATCH (p1:Paper {paper_id: "2025_4359"})-[:USES_SAME_THEORY]->(p2:Paper)
RETURN p2.title
```

**Q: What methods are most commonly used?**
```cypher
MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
RETURN m.name, count(p) as count
ORDER BY count DESC
LIMIT 10
```

**Q: What theories are used in papers?**
```cypher
MATCH (p:Paper)-[:USES_THEORY {role: "primary"}]->(t:Theory)
RETURN t.name, count(p) as count
ORDER BY count DESC
```

---

That's it! You're ready to explore! 🎉

