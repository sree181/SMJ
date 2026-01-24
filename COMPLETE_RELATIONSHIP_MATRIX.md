# Complete Relationship Matrix for Literature Review Graph

## Overview

This document defines ALL relationships between the 10 node types in our knowledge graph. Each relationship is designed to support specific research queries and enable comprehensive literature analysis.

## Node Types

1. **Paper** - Research papers (core entity)
2. **Method** - Research methods (quantitative/qualitative/mixed)
3. **Theory** - Theoretical frameworks
4. **ResearchQuestion** - Research questions
5. **Variable** - Variables (dependent/independent/control/moderator/mediator)
6. **Finding** - Research findings/results
7. **Contribution** - Research contributions
8. **Software** - Analysis tools/software
9. **Dataset** - Data sources
10. **Author** - Authors (optional)

---

## Complete Relationship Matrix

### Paper → Entity Relationships

#### 1. Paper → Method
**Relationship**: `(Paper)-[:USES_METHOD]->(Method)`
**Properties**:
- `confidence` (0.0-1.0): How confident we are this paper uses this method
- `primary` (boolean): Is this a primary method or secondary?
- `context` (string): How the method is used in this paper

**Purpose**: 
- Find all papers using a specific method
- Track method evolution over time
- Compare papers by methodology

**Example Query**:
```cypher
// Find all papers using OLS Regression
MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: "OLS Regression"})
RETURN p.title, p.year, m.name
ORDER BY p.year
```

---

#### 2. Paper → Theory
**Relationship**: `(Paper)-[:USES_THEORY]->(Theory)`
**Properties**:
- `role` (string): "primary", "supporting", "challenging"
- `section` (string): Where theory is mentioned ("introduction", "discussion")

**Purpose**:
- Find papers using same theoretical framework
- Track theory evolution
- Identify theoretical gaps

**Example Query**:
```cypher
// Papers using Resource-Based View
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title, p.year, t.name
```

---

#### 3. Paper → ResearchQuestion
**Relationship**: `(Paper)-[:ADDRESSES]->(ResearchQuestion)`
**Properties**:
- `primary` (boolean): Is this the main research question?
- `section` (string): Where question appears ("abstract", "introduction")

**Purpose**:
- Find papers addressing similar questions
- Identify research gaps (questions with few papers)
- Track question evolution

**Example Query**:
```cypher
// Research questions with few papers (gaps)
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
WITH rq, count(p) as paper_count
WHERE paper_count < 3
RETURN rq.question, paper_count
ORDER BY paper_count
```

---

#### 4. Paper → Variable
**Relationship**: `(Paper)-[:USES_VARIABLE]->(Variable)`
**Properties**:
- `role` (string): "dependent", "independent", "control", "moderator", "mediator"
- `measurement` (string): How variable is measured
- `operationalization` (string): How variable is operationalized

**Purpose**:
- Find papers using same variables
- Track variable usage patterns
- Identify variable relationships

**Example Query**:
```cypher
// Papers using "Firm Performance" as dependent variable
MATCH (p:Paper)-[:USES_VARIABLE {role: "dependent"}]->(v:Variable {name: "Firm Performance"})
RETURN p.title, v.name, v.measurement
```

---

#### 5. Paper → Finding
**Relationship**: `(Paper)-[:REPORTS_FINDING]->(Finding)`
**Properties**:
- `significance` (string): Statistical significance if applicable
- `effect_size` (float): Effect size if applicable
- `section` (string): Where finding is reported ("results", "discussion")

**Purpose**:
- Track research findings
- Compare findings across papers
- Identify contradictory findings

**Example Query**:
```cypher
// Findings from papers using OLS
MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: "OLS Regression"})
MATCH (p)-[:REPORTS_FINDING]->(f:Finding)
RETURN p.title, f.finding_text, f.significance
```

---

#### 6. Paper → Contribution
**Relationship**: `(Paper)-[:MAKES_CONTRIBUTION]->(Contribution)`
**Properties**:
- `novelty_level` (string): "incremental", "moderate", "significant"
- `validated` (boolean): Has contribution been validated by other papers?

**Purpose**:
- Track research contributions
- Identify contribution gaps
- Find papers building on contributions

**Example Query**:
```cypher
// Significant contributions
MATCH (p:Paper)-[:MAKES_CONTRIBUTION]->(c:Contribution)
WHERE c.novelty_level = "significant"
RETURN p.title, c.contribution_text
```

---

#### 7. Paper → Software
**Relationship**: `(Paper)-[:USES_SOFTWARE]->(Software)`
**Properties**:
- `version` (string): Software version if specified
- `primary` (boolean): Primary software or secondary?

**Purpose**:
- Track software usage trends
- Find papers using same tools
- Enable reproducibility

**Example Query**:
```cypher
// Papers using Stata
MATCH (p:Paper)-[:USES_SOFTWARE]->(s:Software {name: "Stata"})
RETURN p.title, s.version, p.year
ORDER BY p.year
```

---

#### 8. Paper → Dataset
**Relationship**: `(Paper)-[:USES_DATASET]->(Dataset)`
**Properties**:
- `time_period` (string): Time period of data used
- `geography` (string): Geographic scope

**Purpose**:
- Track data source usage
- Find papers using same datasets
- Enable replication studies

**Example Query**:
```cypher
// Papers using Compustat dataset
MATCH (p:Paper)-[:USES_DATASET]->(d:Dataset {name: "Compustat"})
RETURN p.title, d.time_period, d.geography
```

---

#### 9. Paper → Author
**Relationship**: `(Author)-[:AUTHORED]->(Paper)`
**Properties**:
- `order` (integer): Author order (1 = first author)
- `corresponding` (boolean): Is this the corresponding author?

**Purpose**:
- Author collaboration networks
- Track author research focus
- Find co-authors

**Example Query**:
```cypher
// Papers by an author
MATCH (a:Author {name: "John Smith"})-[:AUTHORED]->(p:Paper)
RETURN p.title, p.year
ORDER BY p.year DESC
```

---

#### 10. Paper → Paper Relationships

##### 10a. Citation
**Relationship**: `(Paper)-[:CITES]->(Paper)`
**Properties**:
- `citation_type` (string): "direct", "indirect", "background"
- `section` (string): Where citation appears

**Purpose**:
- Citation network analysis
- Find influential papers
- Track paper impact

**Example Query**:
```cypher
// Most cited papers
MATCH (p1:Paper)<-[:CITES]-(p2:Paper)
WITH p1, count(p2) as citation_count
RETURN p1.title, citation_count
ORDER BY citation_count DESC
LIMIT 10
```

##### 10b. Similarity
**Relationship**: `(Paper)-[:SIMILAR_TO]->(Paper)`
**Properties**:
- `similarity_score` (0.0-1.0): Overall similarity score
- `similarity_dimensions` (array): ["methodological", "theoretical", "topical", "temporal"]
- `methodological_similarity` (float): Method similarity
- `theoretical_similarity` (float): Theory similarity
- `topical_similarity` (float): Topic similarity

**Purpose**:
- Find similar papers
- Multi-dimensional similarity
- Research gap identification

**Example Query**:
```cypher
// Papers similar to a given paper
MATCH (p1:Paper {paper_id: "2025_4359"})-[:SIMILAR_TO {methodological_similarity: 0.8}]->(p2:Paper)
RETURN p2.title, p2.year
```

##### 10c. Extension
**Relationship**: `(Paper)-[:EXTENDS]->(Paper)`
**Properties**:
- `extension_type` (string): "theoretical", "empirical", "methodological"
- `builds_on` (string): What aspect it builds on

**Purpose**:
- Track paper evolution
- Find papers building on others
- Identify research streams

**Example Query**:
```cypher
// Papers extending a given paper
MATCH (p1:Paper {paper_id: "2025_4359"})<-[:EXTENDS]-(p2:Paper)
RETURN p2.title, p2.year, p2.extension_type
```

##### 10d. Replication
**Relationship**: `(Paper)-[:REPLICATES]->(Paper)`
**Properties**:
- `replication_type` (string): "exact", "conceptual", "methodological"
- `success` (boolean): Was replication successful?

**Purpose**:
- Track replication studies
- Validate findings
- Enable reproducibility

**Example Query**:
```cypher
// Replication studies
MATCH (p1:Paper)<-[:REPLICATES]-(p2:Paper)
RETURN p1.title, p2.title, p2.replication_type, p2.success
```

---

### Entity → Entity Relationships

#### 11. Method → Method

##### 11a. Similarity
**Relationship**: `(Method)-[:SIMILAR_TO]->(Method)`
**Properties**:
- `similarity_score` (0.0-1.0): How similar are the methods
- `similarity_type` (string): "conceptual", "statistical", "application"

**Purpose**:
- Find similar methods
- Method clustering
- Alternative method suggestions

**Example Query**:
```cypher
// Methods similar to OLS
MATCH (m1:Method {name: "OLS Regression"})-[:SIMILAR_TO]->(m2:Method)
RETURN m2.name, m2.similarity_score
ORDER BY m2.similarity_score DESC
```

##### 11b. Evolution
**Relationship**: `(Method)-[:EVOLVED_FROM]->(Method)`
**Properties**:
- `evolution_type` (string): "extension", "refinement", "combination"
- `year` (integer): When evolution occurred

**Purpose**:
- Track method evolution
- Understand method development
- Historical method analysis

**Example Query**:
```cypher
// Methods that evolved from OLS
MATCH (m1:Method {name: "OLS Regression"})<-[:EVOLVED_FROM]-(m2:Method)
RETURN m2.name, m2.evolution_type
```

---

#### 12. Theory → Theory

##### 12a. Related
**Relationship**: `(Theory)-[:RELATED_TO]->(Theory)`
**Properties**:
- `relationship_type` (string): "complementary", "competing", "extending", "challenging"
- `strength` (float): Strength of relationship (0.0-1.0)

**Purpose**:
- Understand theory relationships
- Find complementary theories
- Identify theoretical debates

**Example Query**:
```cypher
// Theories related to RBV
MATCH (t1:Theory {name: "Resource-Based View"})-[:RELATED_TO]->(t2:Theory)
RETURN t2.name, t2.relationship_type, t2.strength
```

##### 12b. Extension
**Relationship**: `(Theory)-[:EXTENDS]->(Theory)`
**Properties**:
- `extension_type` (string): "theoretical", "empirical", "boundary"
- `year` (integer): When extension was proposed

**Purpose**:
- Track theory development
- Find theory extensions
- Understand theory evolution

**Example Query**:
```cypher
// Theories extending RBV
MATCH (t1:Theory {name: "Resource-Based View"})<-[:EXTENDS]-(t2:Theory)
RETURN t2.name, t2.extension_type
```

---

#### 13. Variable → Variable

##### 13a. Related
**Relationship**: `(Variable)-[:RELATED_TO]->(Variable)`
**Properties**:
- `relationship_type` (string): "correlated", "causal", "conceptual"
- `strength` (float): Relationship strength

**Purpose**:
- Understand variable relationships
- Find related variables
- Variable network analysis

**Example Query**:
```cypher
// Variables related to Firm Performance
MATCH (v1:Variable {name: "Firm Performance"})-[:RELATED_TO]->(v2:Variable)
RETURN v2.name, v2.relationship_type
```

##### 13b. Moderation
**Relationship**: `(Variable)-[:MODERATES]->(Variable)`
**Properties**:
- `moderation_type` (string): "strengthening", "weakening", "reversing"
- `direction` (string): "positive", "negative", "curvilinear"

**Purpose**:
- Track moderation effects
- Find moderating variables
- Understand conditional relationships

**Example Query**:
```cypher
// Variables that moderate Firm Performance
MATCH (v1:Variable {name: "Firm Performance"})<-[:MODERATES]-(v2:Variable)
RETURN v2.name, v2.moderation_type
```

##### 13c. Mediation
**Relationship**: `(Variable)-[:MEDIATES]->(Variable)`
**Properties**:
- `mediation_type` (string): "full", "partial", "indirect"
- `effect_size` (float): Mediation effect size

**Purpose**:
- Track mediation effects
- Find mediating variables
- Understand indirect relationships

**Example Query**:
```cypher
// Variables that mediate between X and Y
MATCH (v1:Variable)-[:MEDIATES]->(v2:Variable)
RETURN v1.name, v2.name, v2.mediation_type
```

---

#### 14. Finding → Finding

##### 14a. Related
**Relationship**: `(Finding)-[:RELATED_TO]->(Finding)`
**Properties**:
- `relationship_type` (string): "supporting", "extending", "contextual"
- `strength` (float): Relationship strength

**Purpose**:
- Find related findings
- Build cumulative knowledge
- Identify finding patterns

**Example Query**:
```cypher
// Findings related to a specific finding
MATCH (f1:Finding)-[:RELATED_TO]->(f2:Finding)
RETURN f2.finding_text, f2.relationship_type
```

##### 14b. Contradiction
**Relationship**: `(Finding)-[:CONTRADICTS]->(Finding)`
**Properties**:
- `contradiction_type` (string): "direct", "partial", "contextual"
- `explanation` (string): Why findings contradict

**Purpose**:
- Identify contradictory findings
- Understand research debates
- Find research gaps

**Example Query**:
```cypher
// Contradictory findings
MATCH (f1:Finding)-[:CONTRADICTS]->(f2:Finding)
RETURN f1.finding_text, f2.finding_text, f2.contradiction_type
```

##### 14c. Support
**Relationship**: `(Finding)-[:SUPPORTS]->(Theory)`
**Properties**:
- `support_type` (string): "strong", "moderate", "weak"
- `evidence_type` (string): "empirical", "theoretical", "mixed"

**Purpose**:
- Link findings to theories
- Validate theories
- Build theoretical evidence

**Example Query**:
```cypher
// Findings supporting a theory
MATCH (f:Finding)-[:SUPPORTS]->(t:Theory {name: "Resource-Based View"})
RETURN f.finding_text, f.support_type
```

---

#### 15. ResearchQuestion → ResearchQuestion

##### 15a. Related
**Relationship**: `(ResearchQuestion)-[:RELATED_TO]->(ResearchQuestion)`
**Properties**:
- `relationship_type` (string): "similar", "extending", "narrowing", "broadening"
- `strength` (float): Relationship strength

**Purpose**:
- Find related research questions
- Track question evolution
- Identify question clusters

**Example Query**:
```cypher
// Research questions related to a question
MATCH (rq1:ResearchQuestion)-[:RELATED_TO]->(rq2:ResearchQuestion)
RETURN rq2.question, rq2.relationship_type
```

##### 15b. Answers
**Relationship**: `(ResearchQuestion)-[:ANSWERS]->(ResearchQuestion)`
**Properties**:
- `answer_type` (string): "partial", "complete", "refutes"
- `confidence` (float): How confident is the answer

**Purpose**:
- Link questions to answers
- Track question resolution
- Identify unanswered questions

**Example Query**:
```cypher
// Questions that answer a research question
MATCH (rq1:ResearchQuestion)<-[:ANSWERS]-(rq2:ResearchQuestion)
RETURN rq2.question, rq2.answer_type
```

---

#### 16. Contribution → Contribution

##### 16a. Builds On
**Relationship**: `(Contribution)-[:BUILDS_ON]->(Contribution)`
**Properties**:
- `build_type` (string): "extends", "refines", "applies", "challenges"
- `year` (integer): When contribution was made

**Purpose**:
- Track contribution evolution
- Find building blocks
- Understand contribution chains

**Example Query**:
```cypher
// Contributions building on a contribution
MATCH (c1:Contribution)<-[:BUILDS_ON]-(c2:Contribution)
RETURN c2.contribution_text, c2.build_type
```

---

#### 17. Method → Software

##### 17a. Implementation
**Relationship**: `(Method)-[:IMPLEMENTED_IN]->(Software)`
**Properties**:
- `package` (string): Specific package/library
- `version` (string): Software version

**Purpose**:
- Link methods to software
- Find implementation details
- Enable reproducibility

**Example Query**:
```cypher
// Software implementing OLS
MATCH (m:Method {name: "OLS Regression"})-[:IMPLEMENTED_IN]->(s:Software)
RETURN s.name, s.package, s.version
```

---

## Relationship Summary Table

| From Node | Relationship | To Node | Purpose |
|-----------|-------------|---------|---------|
| Paper | USES_METHOD | Method | Track method usage |
| Paper | USES_THEORY | Theory | Track theory usage |
| Paper | ADDRESSES | ResearchQuestion | Link papers to questions |
| Paper | USES_VARIABLE | Variable | Track variable usage |
| Paper | REPORTS_FINDING | Finding | Link papers to findings |
| Paper | MAKES_CONTRIBUTION | Contribution | Link papers to contributions |
| Paper | USES_SOFTWARE | Software | Track software usage |
| Paper | USES_DATASET | Dataset | Track dataset usage |
| Author | AUTHORED | Paper | Author-paper links |
| Paper | CITES | Paper | Citation network |
| Paper | SIMILAR_TO | Paper | Paper similarity |
| Paper | EXTENDS | Paper | Paper extensions |
| Paper | REPLICATES | Paper | Replication studies |
| Method | SIMILAR_TO | Method | Method similarity |
| Method | EVOLVED_FROM | Method | Method evolution |
| Theory | RELATED_TO | Theory | Theory relationships |
| Theory | EXTENDS | Theory | Theory extensions |
| Variable | RELATED_TO | Variable | Variable relationships |
| Variable | MODERATES | Variable | Moderation effects |
| Variable | MEDIATES | Variable | Mediation effects |
| Finding | RELATED_TO | Finding | Finding relationships |
| Finding | CONTRADICTS | Finding | Contradictory findings |
| Finding | SUPPORTS | Theory | Theory support |
| ResearchQuestion | RELATED_TO | ResearchQuestion | Question relationships |
| ResearchQuestion | ANSWERS | ResearchQuestion | Question answers |
| Contribution | BUILDS_ON | Contribution | Contribution chains |
| Method | IMPLEMENTED_IN | Software | Method implementation |

## Complex Query Examples

### 1. Multi-Hop: Papers → Methods → Similar Methods → Papers
```cypher
// Find papers using methods similar to methods used in a given paper
MATCH (p1:Paper {paper_id: "2025_4359"})-[:USES_METHOD]->(m1:Method)
MATCH (m1)-[:SIMILAR_TO]->(m2:Method)
MATCH (p2:Paper)-[:USES_METHOD]->(m2)
WHERE p1 <> p2
RETURN DISTINCT p2.title, m2.name
```

### 2. Research Gap: Questions with Few Papers
```cypher
// Research questions with few papers (potential gaps)
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
WITH rq, count(p) as paper_count
WHERE paper_count < 3
MATCH (rq)<-[:ADDRESSES]-(p2:Paper)
RETURN rq.question, paper_count, collect(p2.title) as papers
ORDER BY paper_count
```

### 3. Method Evolution Over Time
```cypher
// How has OLS usage evolved, and what methods evolved from it?
MATCH (p:Paper)-[:USES_METHOD]->(m:Method {name: "OLS Regression"})
WITH p.year as year, count(p) as count
ORDER BY year
MATCH (m2:Method)-[:EVOLVED_FROM]->(m)
RETURN year, count, collect(m2.name) as evolved_methods
```

### 4. Contradictory Findings on Same Topic
```cypher
// Papers with contradictory findings using same methods
MATCH (p1:Paper)-[:USES_METHOD]->(m:Method)
MATCH (p2:Paper)-[:USES_METHOD]->(m)
MATCH (p1)-[:REPORTS_FINDING]->(f1:Finding)
MATCH (p2)-[:REPORTS_FINDING]->(f2:Finding)
WHERE (f1)-[:CONTRADICTS]-(f2) AND p1 <> p2
RETURN p1.title, p2.title, m.name, f1.finding_text, f2.finding_text
```

### 5. Complete Research Stream
```cypher
// Complete research stream: Question → Papers → Methods → Findings → Theory
MATCH (rq:ResearchQuestion {question: "How does X affect Y?"})
MATCH (p:Paper)-[:ADDRESSES]->(rq)
MATCH (p)-[:USES_METHOD]->(m:Method)
MATCH (p)-[:REPORTS_FINDING]->(f:Finding)
MATCH (f)-[:SUPPORTS]->(t:Theory)
RETURN rq.question, p.title, m.name, f.finding_text, t.name
```

## Implementation Priority

### Phase 1: Core (Current)
- Paper → Method
- Paper → Software
- Method → Method (SIMILAR_TO)

### Phase 2: Research Elements
- Paper → Theory
- Paper → ResearchQuestion
- Paper → Variable
- Theory → Theory (RELATED_TO, EXTENDS)

### Phase 3: Findings & Contributions
- Paper → Finding
- Paper → Contribution
- Finding → Finding (RELATED_TO, CONTRADICTS)
- Finding → Theory (SUPPORTS)

### Phase 4: Advanced
- Paper → Paper (CITES, SIMILAR_TO, EXTENDS, REPLICATES)
- Variable → Variable (MODERATES, MEDIATES)
- ResearchQuestion → ResearchQuestion (RELATED_TO, ANSWERS)
- Contribution → Contribution (BUILDS_ON)
- Author → Paper (AUTHORED)
- Paper → Dataset (USES_DATASET)

## Conclusion

This comprehensive relationship matrix enables:
- ✅ **Multi-dimensional queries** across all entity types
- ✅ **Research gap identification** through sparse connections
- ✅ **Temporal evolution** tracking
- ✅ **Semantic relationships** between concepts
- ✅ **Complex research questions** answered through graph traversal

All relationships are designed to support real research queries and enable comprehensive literature analysis.

