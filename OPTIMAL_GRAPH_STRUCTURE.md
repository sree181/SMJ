# Optimal Graph Structure for Literature Review System

## Design Principles

1. **Query-Optimized**: Enable fast, intuitive queries for research questions
2. **Research-Focused**: Support literature review, gap analysis, and temporal evolution
3. **Semantic Richness**: Capture relationships between concepts, methods, theories
4. **Scalability**: Efficient for large-scale paper collections

## Node Types

### 1. **Paper** (Core Entity)
**Properties**:
- `paper_id` (unique identifier)
- `title`
- `abstract`
- `year`
- `journal`
- `doi`
- `keywords` (array)
- `citation_count` (optional)
- `impact_factor` (optional)

**Purpose**: Central entity connecting all research elements

### 2. **Method** (Quantitative/Qualitative/Mixed)
**Properties**:
- `name` (e.g., "OLS Regression", "Case Study", "Grounded Theory")
- `type` ("quantitative", "qualitative", "mixed")
- `category` (e.g., "regression", "machine_learning", "qualitative_analysis")
- `description` (brief description)
- `first_used_year` (temporal tracking)

**Purpose**: 
- Enable method evolution queries
- Find papers using specific methods
- Compare method effectiveness

**Relationships**:
- `(Paper)-[:USES_METHOD {confidence, context}]->(Method)`
- `(Method)-[:SIMILAR_TO {similarity_score}]->(Method)`
- `(Method)-[:EVOLVED_FROM]->(Method)` (temporal)

### 3. **Theory** (Theoretical Framework)
**Properties**:
- `name` (e.g., "Resource-Based View", "Agency Theory")
- `domain` (e.g., "strategic_management", "organizational_behavior")
- `description`

**Purpose**:
- Track theoretical foundations
- Find papers using same theories
- Identify theoretical gaps

**Relationships**:
- `(Paper)-[:USES_THEORY]->(Theory)`
- `(Theory)-[:RELATED_TO {relationship_type}]->(Theory)`
- `(Theory)-[:EXTENDS]->(Theory)`

### 4. **ResearchQuestion**
**Properties**:
- `question` (full text)
- `question_type` ("descriptive", "explanatory", "predictive", "prescriptive")
- `domain`
- `section` (where extracted from: "introduction", "abstract")

**Purpose**:
- Identify research gaps
- Find papers addressing similar questions
- Track question evolution

**Relationships**:
- `(Paper)-[:ADDRESSES]->(ResearchQuestion)`
- `(ResearchQuestion)-[:RELATED_TO]->(ResearchQuestion)`
- `(ResearchQuestion)-[:ANSWERS]->(ResearchQuestion)` (if one answers another)

### 5. **Variable** (Dependent/Independent/Control/Moderator/Mediator)
**Properties**:
- `name` (e.g., "Firm Performance", "CEO Tenure")
- `type` ("dependent", "independent", "control", "moderator", "mediator")
- `domain` (e.g., "organizational", "financial", "strategic")
- `measurement` (how it's measured)
- `operationalization` (how it's operationalized)

**Purpose**:
- Track variable usage across papers
- Find papers using same variables
- Identify variable relationships

**Relationships**:
- `(Paper)-[:USES_VARIABLE {role: "dependent/independent/etc"}]->(Variable)`
- `(Variable)-[:RELATED_TO]->(Variable)`
- `(Variable)-[:MODERATES]->(Variable)`
- `(Variable)-[:MEDIATES]->(Variable)`

### 6. **Finding** (Research Findings/Results)
**Properties**:
- `finding_text` (summary of finding)
- `finding_type` ("positive", "negative", "null", "mixed")
- `significance` (statistical significance if applicable)
- `effect_size` (if applicable)
- `section` (where extracted from)

**Purpose**:
- Track research findings
- Compare findings across papers
- Identify contradictory findings

**Relationships**:
- `(Paper)-[:REPORTS_FINDING]->(Finding)`
- `(Finding)-[:SUPPORTS]->(Theory)`
- `(Finding)-[:CONTRADICTS]->(Finding)`
- `(Finding)-[:RELATED_TO]->(Finding)`

### 7. **Contribution**
**Properties**:
- `contribution_text` (description)
- `contribution_type` ("theoretical", "empirical", "methodological", "practical")
- `novelty_level` ("incremental", "moderate", "significant")

**Purpose**:
- Track research contributions
- Identify contribution gaps
- Find papers with similar contributions

**Relationships**:
- `(Paper)-[:MAKES_CONTRIBUTION]->(Contribution)`
- `(Contribution)-[:BUILDS_ON]->(Contribution)`

### 8. **Software** (Analysis Tools)
**Properties**:
- `name` (e.g., "Stata 17", "R 4.2", "Python 3.10")
- `version` (if specified)
- `category` ("statistical", "programming", "qualitative")

**Purpose**:
- Track software usage trends
- Find papers using same tools
- Enable reproducibility queries

**Relationships**:
- `(Paper)-[:USES_SOFTWARE]->(Software)`
- `(Method)-[:IMPLEMENTED_IN]->(Software)`

### 9. **Dataset** (Data Sources)
**Properties**:
- `name` (e.g., "Compustat", "CRSP", "Survey Data")
- `type` ("archival", "survey", "experimental", "interview")
- `time_period` (e.g., "2000-2020")
- `geography` (e.g., "US", "Global")

**Purpose**:
- Track data source usage
- Find papers using same datasets
- Enable replication studies

**Relationships**:
- `(Paper)-[:USES_DATASET]->(Dataset)`

### 10. **Author** (Optional - for author networks)
**Properties**:
- `name`
- `affiliation`
- `email`
- `orcid` (if available)

**Purpose**:
- Author collaboration networks
- Track author research focus

**Relationships**:
- `(Author)-[:AUTHORED]->(Paper)`
- `(Author)-[:COLLABORATED_WITH]->(Author)`

## Relationship Types

### Paper-to-Entity Relationships
- `(Paper)-[:USES_METHOD {confidence, context, primary: true/false}]->(Method)`
- `(Paper)-[:USES_THEORY]->(Theory)`
- `(Paper)-[:ADDRESSES]->(ResearchQuestion)`
- `(Paper)-[:USES_VARIABLE {role}]->(Variable)`
- `(Paper)-[:REPORTS_FINDING]->(Finding)`
- `(Paper)-[:MAKES_CONTRIBUTION]->(Contribution)`
- `(Paper)-[:USES_SOFTWARE]->(Software)`
- `(Paper)-[:USES_DATASET]->(Dataset)`

### Entity-to-Entity Relationships
- `(Method)-[:SIMILAR_TO {similarity_score, similarity_type}]->(Method)`
- `(Method)-[:EVOLVED_FROM]->(Method)` (temporal evolution)
- `(Theory)-[:RELATED_TO {relationship_type}]->(Theory)`
- `(Theory)-[:EXTENDS]->(Theory)`
- `(Variable)-[:RELATED_TO]->(Variable)`
- `(Variable)-[:MODERATES]->(Variable)`
- `(Variable)-[:MEDIATES]->(Variable)`
- `(Finding)-[:SUPPORTS]->(Theory)`
- `(Finding)-[:CONTRADICTS]->(Finding)`
- `(Finding)-[:RELATED_TO]->(Finding)`
- `(ResearchQuestion)-[:RELATED_TO]->(ResearchQuestion)`
- `(ResearchQuestion)-[:ANSWERS]->(ResearchQuestion)`

### Paper-to-Paper Relationships
- `(Paper)-[:CITES]->(Paper)` (citation network)
- `(Paper)-[:SIMILAR_TO {similarity_score, similarity_dimensions: []}]->(Paper)`
  - Similarity dimensions: ["methodological", "theoretical", "topical", "temporal"]
- `(Paper)-[:EXTENDS]->(Paper)` (builds on)
- `(Paper)-[:REPLICATES]->(Paper)` (replication study)

## Query Examples

### 1. Method Evolution
```cypher
// How has OLS usage evolved over time?
MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: "OLS Regression"})
RETURN p.year, count(p) as count
ORDER BY p.year
```

### 2. Research Gaps
```cypher
// Find research questions with few papers
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
WITH rq, count(p) as paper_count
WHERE paper_count < 3
RETURN rq.question, paper_count
ORDER BY paper_count
```

### 3. Method Comparison
```cypher
// Papers using similar methods
MATCH (p1:Paper)-[:USES_METHOD]->(m1:Method)
MATCH (p2:Paper)-[:USES_METHOD]->(m2:Method)
WHERE (m1)-[:SIMILAR_TO]-(m2) AND p1 <> p2
RETURN p1.title, p2.title, m1.name, m2.name
```

### 4. Theoretical Gaps
```cypher
// Theories with few empirical studies
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WITH t, count(p) as paper_count
WHERE paper_count < 5
RETURN t.name, paper_count
ORDER BY paper_count
```

### 5. Variable Relationships
```cypher
// Papers using same variables
MATCH (p1:Paper)-[:USES_VARIABLE]->(v:Variable)<-[:USES_VARIABLE]-(p2:Paper)
WHERE p1 <> p2
RETURN v.name, collect(DISTINCT p1.title) as papers
```

### 6. Contradictory Findings
```cypher
// Papers with contradictory findings on same topic
MATCH (p1:Paper)-[:REPORTS_FINDING]->(f1:Finding)
MATCH (p2:Paper)-[:REPORTS_FINDING]->(f2:Finding)
WHERE (f1)-[:CONTRADICTS]-(f2)
RETURN p1.title, p2.title, f1.finding_text, f2.finding_text
```

### 7. Temporal Evolution
```cypher
// How has a theory been used over time?
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.year, count(p) as count, collect(p.title) as papers
ORDER BY p.year
```

### 8. Similar Papers (Multi-dimensional)
```cypher
// Find papers similar across multiple dimensions
MATCH (p1:Paper)-[:SIMILAR_TO {similarity_dimensions: ["methodological", "theoretical"]}]->(p2:Paper)
WHERE p1.year > 2020
RETURN p1.title, p2.title, p1.year, p2.year
```

## Implementation Priority

### Phase 1: Core Structure (Current Focus)
- Paper, Method, Software nodes
- `USES_METHOD`, `USES_SOFTWARE` relationships
- Method similarity relationships

### Phase 2: Research Elements
- ResearchQuestion, Theory, Variable nodes
- Related relationships

### Phase 3: Findings & Contributions
- Finding, Contribution nodes
- Support/contradict relationships

### Phase 4: Advanced Features
- Author networks
- Citation networks
- Dataset tracking

## Benefits of This Structure

1. **Query Efficiency**: Direct node relationships enable fast queries
2. **Research Insights**: Multi-dimensional connections reveal patterns
3. **Gap Identification**: Sparse connections indicate research gaps
4. **Temporal Analysis**: Year-based queries show evolution
5. **Semantic Richness**: Relationships capture research context
6. **Scalability**: Graph structure scales to thousands of papers

