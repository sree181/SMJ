# Neo4j User Guide - Literature Review Knowledge Graph

## Table of Contents
1. [Getting Started](#getting-started)
2. [Understanding the Graph](#understanding-the-graph)
3. [Basic Navigation](#basic-navigation)
4. [Node Types Explained](#node-types-explained)
5. [Relationship Types Explained](#relationship-types-explained)
6. [Common Queries](#common-queries)
7. [Tips and Best Practices](#tips-and-best-practices)

---

## Getting Started

### Step 1: Access Neo4j Browser

1. **Open Neo4j Browser**: Go to your Neo4j Aura instance URL
   - Your URL: `https://console.neo4j.io/` or your specific Aura instance
   - Or use Neo4j Desktop if installed locally

2. **Login**:
   - Enter your **Username**: `neo4j` (or your custom username)
   - Enter your **Password**: (your Neo4j password from `.env` file)
   - Click **Connect**

### Step 2: Understanding the Interface

The Neo4j Browser has three main areas:
- **Top Bar**: Where you type queries (Cypher language)
- **Graph View**: Visual representation of nodes and relationships
- **Table View**: Tabular data view (click "Table" button)

---

## Understanding the Graph

### What is a Knowledge Graph?

Think of it like a **network map** where:
- **Nodes** = Things (papers, authors, methods, theories, etc.)
- **Relationships** = Connections between things (papers use methods, authors write papers, etc.)

### Visual Example

```
Paper (2025_4359)
  ├─[:AUTHORED]→ Author (Daniel B. Sands)
  ├─[:USES_METHOD]→ Method (OLS Regression)
  ├─[:USES_THEORY]→ Theory (Resource-Based View)
  ├─[:ADDRESSES]→ ResearchQuestion ("How do firms...?")
  └─[:USES_VARIABLE]→ Variable (Firm Performance)
```

---

## Basic Navigation

### 1. View All Nodes

**Query**:
```cypher
MATCH (n)
RETURN n
LIMIT 50
```

**What it does**: Shows up to 50 nodes in the graph

**How to use**:
1. Type the query in the top bar
2. Press `Enter` or click the play button (▶)
3. Nodes appear as colored circles

### 2. Count Nodes by Type

**Query**:
```cypher
MATCH (n)
RETURN labels(n)[0] as NodeType, count(n) as Count
ORDER BY Count DESC
```

**What it does**: Shows how many of each node type exist

**Result**: Table showing:
- NodeType: Paper, Method, Theory, etc.
- Count: Number of each type

### 3. View a Specific Paper

**Query**:
```cypher
MATCH (p:Paper {paper_id: "2025_4359"})
RETURN p
```

**What it does**: Shows one specific paper and its properties

**To see properties**: Click on the node in the graph view, or use:
```cypher
MATCH (p:Paper {paper_id: "2025_4359"})
RETURN p.title, p.abstract, p.publication_year
```

### 4. Explore Connections from a Paper

**Query**:
```cypher
MATCH (p:Paper {paper_id: "2025_4359"})-[r]->(connected)
RETURN p, r, connected
LIMIT 50
```

**What it does**: Shows the paper and everything connected to it

**Visual**: You'll see the paper in the center with lines (relationships) connecting to other nodes

---

## Node Types Explained

### 1. **Paper** Node
**What it is**: A research paper/article

**Properties**:
- `paper_id`: Unique identifier (e.g., "2025_4359")
- `title`: Paper title
- `abstract`: Paper abstract
- `publication_year`: Year published (e.g., 2025)
- `doi`: Digital Object Identifier
- `keywords`: List of keywords

**Color**: Usually blue or purple

**Example Query**:
```cypher
MATCH (p:Paper)
RETURN p.title, p.publication_year
ORDER BY p.publication_year DESC
LIMIT 10
```

---

### 2. **Author** Node
**What it is**: A person who wrote a paper

**Properties**:
- `author_id`: Unique identifier (e.g., "smith_john")
- `full_name`: Full name (e.g., "John A. Smith")
- `given_name`: First name
- `family_name`: Last name
- `email`: Email address
- `orcid`: ORCID identifier (if available)

**Color**: Usually green

**Example Query**:
```cypher
MATCH (a:Author)
RETURN a.full_name, a.email
LIMIT 10
```

---

### 3. **Method** Node
**What it is**: A research method used in papers

**Properties**:
- `name`: Method name (e.g., "OLS Regression", "Case Study")
- `type`: Method type (e.g., "quantitative", "qualitative")
- `confidence`: How confident we are this method is used (0.0-1.0)

**Color**: Usually orange

**Example Query**:
```cypher
MATCH (m:Method)
RETURN m.name, m.type
ORDER BY m.name
```

---

### 4. **Theory** Node
**What it is**: A theoretical framework or concept

**Properties**:
- `name`: Theory name (e.g., "Resource-Based View", "Agency Theory")
- `domain`: Research domain (e.g., "strategic_management")
- `theory_type`: Type (e.g., "framework", "concept")
- `description`: Brief description

**Color**: Usually yellow

**Example Query**:
```cypher
MATCH (t:Theory)
RETURN t.name, t.domain
ORDER BY t.name
```

---

### 5. **ResearchQuestion** Node
**What it is**: A research question addressed by a paper

**Properties**:
- `question_id`: Unique identifier
- `question`: Full question text (e.g., "How do firms achieve competitive advantage?")
- `question_type`: Type (e.g., "explanatory", "descriptive", "predictive")
- `domain`: Research domain
- `section`: Where it appears (e.g., "introduction", "abstract")

**Color**: Usually pink

**Example Query**:
```cypher
MATCH (rq:ResearchQuestion)
RETURN rq.question, rq.question_type
LIMIT 5
```

---

### 6. **Variable** Node
**What it is**: A variable used in research (dependent, independent, control, etc.)

**Properties**:
- `variable_id`: Unique identifier
- `variable_name`: Variable name (e.g., "Firm Performance", "CEO Tenure")
- `variable_type`: Type (e.g., "dependent", "independent", "control", "moderator", "mediator")
- `measurement`: How it's measured (e.g., "ROA", "Tobin's Q")
- `operationalization`: How it's operationalized
- `domain`: Variable domain (e.g., "organizational", "financial")

**Color**: Usually cyan

**Example Query**:
```cypher
MATCH (v:Variable {variable_type: "dependent"})
RETURN v.variable_name, v.measurement
LIMIT 10
```

---

### 7. **Finding** Node
**What it is**: A research finding or result from a paper

**Properties**:
- `finding_id`: Unique identifier
- `finding_text`: Description of the finding
- `finding_type`: Type (e.g., "positive", "negative", "null", "mixed")
- `significance`: Statistical significance (if mentioned)
- `effect_size`: Effect size (if mentioned)
- `section`: Where it appears (e.g., "results", "discussion")

**Color**: Usually red

**Example Query**:
```cypher
MATCH (f:Finding)
RETURN f.finding_text, f.finding_type
LIMIT 5
```

---

### 8. **Contribution** Node
**What it is**: A research contribution made by a paper

**Properties**:
- `contribution_id`: Unique identifier
- `contribution_text`: Description of the contribution
- `contribution_type`: Type (e.g., "theoretical", "empirical", "methodological", "practical")
- `section`: Where it appears (e.g., "discussion", "conclusion")

**Color**: Usually magenta

**Example Query**:
```cypher
MATCH (c:Contribution {contribution_type: "theoretical"})
RETURN c.contribution_text
LIMIT 5
```

---

### 9. **Software** Node
**What it is**: Software or tool used for analysis

**Properties**:
- `software_name`: Software name (e.g., "Stata", "R", "Python")
- `version`: Version number (if mentioned)
- `software_type`: Type (e.g., "statistical", "programming", "qualitative")
- `usage`: How it's used

**Color**: Usually teal

**Example Query**:
```cypher
MATCH (s:Software)
RETURN s.software_name, s.version
ORDER BY s.software_name
```

---

### 10. **Dataset** Node
**What it is**: A dataset or data source used in research

**Properties**:
- `dataset_name`: Dataset name (e.g., "Compustat", "CRSP", "Survey Data")
- `dataset_type`: Type (e.g., "archival", "survey", "experimental")
- `time_period`: Time period covered (e.g., "2000-2020")
- `sample_size`: Sample size (if mentioned)
- `access`: How data was accessed

**Color**: Usually brown

**Example Query**:
```cypher
MATCH (d:Dataset)
RETURN d.dataset_name, d.dataset_type
ORDER BY d.dataset_name
```

---

### 11. **Institution** Node
**What it is**: A university or organization where authors work

**Properties**:
- `institution_id`: Unique identifier
- `institution_name`: Institution name (e.g., "Stanford University")
- `city`: City location
- `country`: Country
- `department`: Department name (if mentioned)

**Color**: Usually gray

**Example Query**:
```cypher
MATCH (i:Institution)
RETURN i.institution_name, i.country
ORDER BY i.institution_name
```

---

## Relationship Types Explained

### Paper → Entity Relationships

#### 1. **AUTHORED**
**What it means**: An author wrote a paper

**Direction**: `(Author)-[:AUTHORED]->(Paper)`

**Properties**:
- `position`: Author position (1 = first author, 2 = second, etc.)

**Example Query**:
```cypher
MATCH (a:Author)-[r:AUTHORED]->(p:Paper)
RETURN a.full_name, p.title, r.position
ORDER BY r.position
LIMIT 10
```

---

#### 2. **USES_METHOD**
**What it means**: A paper uses a specific research method

**Direction**: `(Paper)-[:USES_METHOD]->(Method)`

**Properties**:
- `confidence`: How confident we are (0.0-1.0)

**Example Query**:
```cypher
MATCH (p:Paper)-[r:USES_METHOD]->(m:Method)
RETURN p.title, m.name, r.confidence
ORDER BY r.confidence DESC
LIMIT 10
```

---

#### 3. **USES_THEORY**
**What it means**: A paper uses a theoretical framework

**Direction**: `(Paper)-[:USES_THEORY]->(Theory)`

**Properties**:
- `role`: "primary" (main theory) or "supporting" (supporting theory)
- `section`: Where theory appears (e.g., "introduction", "literature_review")
- `usage_context`: How theory is used

**Example Query**:
```cypher
MATCH (p:Paper)-[r:USES_THEORY {role: "primary"}]->(t:Theory)
RETURN p.title, t.name, r.role
LIMIT 10
```

---

#### 4. **ADDRESSES**
**What it means**: A paper addresses a research question

**Direction**: `(Paper)-[:ADDRESSES]->(ResearchQuestion)`

**Example Query**:
```cypher
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
RETURN p.title, rq.question
LIMIT 10
```

---

#### 5. **USES_VARIABLE**
**What it means**: A paper uses a variable in its analysis

**Direction**: `(Paper)-[:USES_VARIABLE]->(Variable)`

**Properties**:
- `variable_type`: Role of variable ("dependent", "independent", "control", etc.)

**Example Query**:
```cypher
MATCH (p:Paper)-[r:USES_VARIABLE]->(v:Variable {variable_type: "dependent"})
RETURN p.title, v.variable_name
LIMIT 10
```

---

#### 6. **REPORTS**
**What it means**: A paper reports a research finding

**Direction**: `(Paper)-[:REPORTS]->(Finding)`

**Example Query**:
```cypher
MATCH (p:Paper)-[:REPORTS]->(f:Finding)
RETURN p.title, f.finding_text, f.finding_type
LIMIT 5
```

---

#### 7. **MAKES**
**What it means**: A paper makes a research contribution

**Direction**: `(Paper)-[:MAKES]->(Contribution)`

**Example Query**:
```cypher
MATCH (p:Paper)-[:MAKES]->(c:Contribution)
RETURN p.title, c.contribution_text, c.contribution_type
LIMIT 5
```

---

#### 8. **USES_SOFTWARE**
**What it means**: A paper uses software for analysis

**Direction**: `(Paper)-[:USES_SOFTWARE]->(Software)`

**Example Query**:
```cypher
MATCH (p:Paper)-[:USES_SOFTWARE]->(s:Software)
RETURN p.title, s.software_name
LIMIT 10
```

---

#### 9. **USES_DATASET**
**What it means**: A paper uses a dataset

**Direction**: `(Paper)-[:USES_DATASET]->(Dataset)`

**Example Query**:
```cypher
MATCH (p:Paper)-[:USES_DATASET]->(d:Dataset)
RETURN p.title, d.dataset_name, d.dataset_type
LIMIT 10
```

---

#### 10. **AFFILIATED_WITH**
**What it means**: An author is affiliated with an institution

**Direction**: `(Author)-[:AFFILIATED_WITH]->(Institution)`

**Properties**:
- `affiliation_type`: "primary" or "secondary"
- `position_title`: Author's position (e.g., "Professor", "Assistant Professor")

**Example Query**:
```cypher
MATCH (a:Author)-[r:AFFILIATED_WITH]->(i:Institution)
RETURN a.full_name, i.institution_name, r.position_title
LIMIT 10
```

---

### Paper → Paper Relationships

#### 11. **USES_SAME_THEORY**
**What it means**: Two papers use the same primary theory

**Direction**: `(Paper)-[:USES_SAME_THEORY]->(Paper)`

**Properties**:
- `theory_name`: Name of shared theory
- `temporal_gap`: Years between papers

**Example Query**:
```cypher
MATCH (p1:Paper)-[r:USES_SAME_THEORY]->(p2:Paper)
RETURN p1.title, p2.title, r.theory_name, r.temporal_gap
LIMIT 10
```

---

#### 12. **USES_SAME_METHOD**
**What it means**: Two papers use the same method

**Direction**: `(Paper)-[:USES_SAME_METHOD]->(Paper)`

**Properties**:
- `method_name`: Name of shared method
- `temporal_gap`: Years between papers

**Example Query**:
```cypher
MATCH (p1:Paper)-[r:USES_SAME_METHOD]->(p2:Paper)
RETURN p1.title, p2.title, r.method_name
LIMIT 10
```

---

#### 13. **USES_SAME_VARIABLES**
**What it means**: Two papers use the same variables (2+ shared)

**Direction**: `(Paper)-[:USES_SAME_VARIABLES]->(Paper)`

**Properties**:
- `variable_overlap`: Number of shared variables
- `variable_types`: List of shared variable names
- `temporal_gap`: Years between papers

**Example Query**:
```cypher
MATCH (p1:Paper)-[r:USES_SAME_VARIABLES]->(p2:Paper)
RETURN p1.title, p2.title, r.variable_overlap, r.variable_types
LIMIT 10
```

---

#### 14. **TEMPORAL_SEQUENCE**
**What it means**: Two papers are in the same topic area, ordered by time

**Direction**: `(Paper)-[:TEMPORAL_SEQUENCE]->(Paper)`

**Properties**:
- `time_gap`: Years between papers
- `sequence`: "before" or "after"
- `context`: "same_theory" or "same_method"

**Example Query**:
```cypher
MATCH (p1:Paper)-[r:TEMPORAL_SEQUENCE]->(p2:Paper)
WHERE r.sequence = "after"
RETURN p1.title, p2.title, r.time_gap, r.context
LIMIT 10
```

---

## Common Queries

### 1. Find All Papers Using a Specific Theory

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title, p.publication_year
ORDER BY p.publication_year
```

**What it does**: Lists all papers using Resource-Based View theory

---

### 2. Find Papers Using a Specific Method

```cypher
MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: "OLS Regression"})
RETURN p.title, p.publication_year
ORDER BY p.publication_year DESC
```

**What it does**: Lists all papers using OLS Regression

---

### 3. Find Research Questions with Few Papers (Research Gaps)

```cypher
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
WITH rq, count(p) as paper_count
WHERE paper_count < 3
RETURN rq.question, paper_count
ORDER BY paper_count
```

**What it does**: Finds research questions that have been addressed by fewer than 3 papers (potential research gaps)

---

### 4. Find Papers by an Author

```cypher
MATCH (a:Author {full_name: "Daniel B. Sands"})-[:AUTHORED]->(p:Paper)
RETURN p.title, p.publication_year
ORDER BY p.publication_year DESC
```

**What it does**: Lists all papers by a specific author

---

### 5. Find Papers Using Same Variables

```cypher
MATCH (p1:Paper)-[:USES_SAME_VARIABLES]->(p2:Paper)
WHERE p1.paper_id = "2025_4359"
RETURN p2.title, p2.publication_year
```

**What it does**: Finds papers that use similar variables to a specific paper

---

### 6. Find Contradictory Findings

```cypher
MATCH (p1:Paper)-[:REPORTS]->(f1:Finding {finding_type: "positive"})
MATCH (p2:Paper)-[:REPORTS]->(f2:Finding {finding_type: "negative"})
WHERE p1 <> p2
RETURN p1.title, f1.finding_text, p2.title, f2.finding_text
LIMIT 10
```

**What it does**: Finds papers with contradictory findings (positive vs negative)

---

### 7. Find Most Used Methods

```cypher
MATCH (p:Paper)-[:USES_METHOD]->(m:Method)
WITH m, count(p) as usage_count
RETURN m.name, m.type, usage_count
ORDER BY usage_count DESC
LIMIT 10
```

**What it does**: Lists methods by how many papers use them

---

### 8. Find Most Used Theories

```cypher
MATCH (p:Paper)-[:USES_THEORY {role: "primary"}]->(t:Theory)
WITH t, count(p) as usage_count
RETURN t.name, usage_count
ORDER BY usage_count DESC
LIMIT 10
```

**What it does**: Lists theories by how many papers use them as primary theory

---

### 9. Explore a Paper's Complete Network

```cypher
MATCH path = (p:Paper {paper_id: "2025_4359"})-[*1..2]-(connected)
RETURN path
LIMIT 50
```

**What it does**: Shows a paper and everything connected to it (2 levels deep)

**Visual**: You'll see the paper in the center with all its connections

---

### 10. Find Papers Similar to a Given Paper

```cypher
MATCH (p1:Paper {paper_id: "2025_4359"})-[:USES_SAME_THEORY]->(p2:Paper)
RETURN p2.title, p2.publication_year
UNION
MATCH (p1:Paper {paper_id: "2025_4359"})-[:USES_SAME_METHOD]->(p2:Paper)
RETURN p2.title, p2.publication_year
```

**What it does**: Finds papers that share theories or methods with a specific paper

---

## Tips and Best Practices

### 1. Start Simple
- Begin with simple queries (like counting nodes)
- Gradually add complexity
- Use `LIMIT` to avoid overwhelming results

### 2. Use Graph View for Exploration
- Click on nodes to see their properties
- Click on relationships to see relationship properties
- Drag nodes to rearrange the graph

### 3. Use Table View for Data
- Click "Table" button to see data in tabular format
- Better for reading text properties (abstracts, questions, etc.)

### 4. Save Useful Queries
- Neo4j Browser has a "Favorites" feature
- Save queries you use frequently
- Create a collection of useful queries

### 5. Understand the Graph Structure
- Papers are the **central hub**
- Everything connects to papers
- Paper-to-paper relationships show connections between papers

### 6. Use Filters
- Add `WHERE` clauses to filter results
- Use properties to find specific nodes
- Combine multiple conditions with `AND`

### 7. Explore Relationships
- Follow relationships to discover connections
- Use `[*1..2]` to explore 1-2 levels deep
- Use `[*]` to explore all connections (be careful - can be slow!)

### 8. Count Before Exploring
- Use `count()` to see how many results you'll get
- Add `LIMIT` to large result sets
- Use `ORDER BY` to sort results

---

## Visual Guide to Node Colors

Neo4j Browser automatically assigns colors to different node types. Here's a typical color scheme:

- 🔵 **Blue**: Papers
- 🟢 **Green**: Authors
- 🟠 **Orange**: Methods
- 🟡 **Yellow**: Theories
- 🩷 **Pink**: Research Questions
- 🔵 **Cyan**: Variables
- 🔴 **Red**: Findings
- 🟣 **Magenta**: Contributions
- 🔵 **Teal**: Software
- 🟤 **Brown**: Datasets
- ⚪ **Gray**: Institutions

**Note**: Colors may vary depending on your Neo4j Browser theme

---

## Common Patterns

### Pattern 1: Find Papers Using Theory X and Method Y

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
MATCH (p)-[:USES_METHOD]->(m:Method {name: "OLS Regression"})
RETURN p.title, p.publication_year
```

### Pattern 2: Find Authors Who Work Together

```cypher
MATCH (a1:Author)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(a2:Author)
WHERE a1 <> a2
RETURN a1.full_name, a2.full_name, p.title
LIMIT 10
```

### Pattern 3: Find Papers Building on Previous Work

```cypher
MATCH (p1:Paper)-[:TEMPORAL_SEQUENCE {sequence: "before"}]->(p2:Paper)
MATCH (p1)-[:USES_THEORY]->(t:Theory)<-[:USES_THEORY]-(p2)
RETURN p1.title, p2.title, t.name
LIMIT 10
```

---

## Troubleshooting

### Problem: Query returns no results
**Solution**: 
- Check spelling of node labels (case-sensitive: `Paper` not `paper`)
- Check property names (use exact property names)
- Try a simpler query first

### Problem: Graph view is cluttered
**Solution**:
- Use `LIMIT` to reduce results
- Use `WHERE` to filter
- Click and drag nodes to rearrange
- Use table view instead

### Problem: Query is slow
**Solution**:
- Add `LIMIT` clause
- Be more specific with `WHERE` conditions
- Avoid `[*]` (all paths) - use specific relationship types

### Problem: Can't find a specific paper
**Solution**:
- Check the `paper_id` format (e.g., "2025_4359")
- Try searching by title:
  ```cypher
  MATCH (p:Paper)
  WHERE p.title CONTAINS "your search term"
  RETURN p
  ```

---

## Quick Reference Card

### Basic Commands
- `MATCH (n)` - Find nodes
- `RETURN n` - Return results
- `WHERE` - Filter conditions
- `LIMIT 10` - Limit results
- `ORDER BY` - Sort results

### Node Labels
- `:Paper` - Research papers
- `:Author` - Authors
- `:Method` - Research methods
- `:Theory` - Theoretical frameworks
- `:ResearchQuestion` - Research questions
- `:Variable` - Variables
- `:Finding` - Research findings
- `:Contribution` - Research contributions
- `:Software` - Software tools
- `:Dataset` - Datasets
- `:Institution` - Institutions

### Common Relationships
- `[:AUTHORED]` - Author wrote paper
- `[:USES_METHOD]` - Paper uses method
- `[:USES_THEORY]` - Paper uses theory
- `[:ADDRESSES]` - Paper addresses question
- `[:USES_VARIABLE]` - Paper uses variable
- `[:REPORTS]` - Paper reports finding
- `[:MAKES]` - Paper makes contribution
- `[:USES_SAME_THEORY]` - Papers share theory
- `[:USES_SAME_METHOD]` - Papers share method

---

## Next Steps

1. **Start Exploring**: Try the basic queries above
2. **Modify Queries**: Change parameters to find what you need
3. **Build Complex Queries**: Combine patterns to answer research questions
4. **Save Favorites**: Save useful queries for later
5. **Experiment**: The graph is read-only for queries - explore freely!

---

## Need Help?

- **Neo4j Documentation**: https://neo4j.com/docs/
- **Cypher Query Language**: https://neo4j.com/developer/cypher/
- **Neo4j Browser Guide**: https://neo4j.com/developer/neo4j-browser/

Happy exploring! 🚀

