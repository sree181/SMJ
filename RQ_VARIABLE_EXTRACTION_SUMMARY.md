# ResearchQuestion & Variable Extraction - Complete Summary

## ✅ Implementation Complete

ResearchQuestion and Variable extraction have been successfully implemented and tested.

## Test Results

### Paper: `2025_4359`

**Research Questions Extracted**: 3
1. "How third parties affect firms' ability to create and capture value?" (explanatory)
2. "To what extent do third-party evaluations influence the creation and capture of value in markets?" (predictive)
3. "How do firms change their behavior in reaction to being evaluated, observed, or measured?" (explanatory)

**Variables Extracted**: 5
- **Dependent Variables** (4):
  - Restaurant Exits
  - Legitimacy
  - Value Appropriation Challenges
  - Consumer Demand
- **Independent Variables** (1):
  - Michelin Stars

## ResearchQuestion Extraction

### Prompt Design

**Input**: First 15,000 characters (Abstract + Introduction)

**Key Features**:
1. **Exact Question Extraction**: Extracts questions exactly as written (looks for "?")
2. **Question Type Classification**:
   - `descriptive`: What is/are...?
   - `explanatory`: Why/How does...?
   - `predictive`: What will...?
   - `prescriptive`: How should...?
3. **Section Identification**: Where question appears (abstract, introduction, literature_review)
4. **Domain Classification**: Research domain (strategic_management, organizational_behavior, etc.)

### Nodes Created

**ResearchQuestion Node**:
```cypher
(:ResearchQuestion {
  question_id: "2025_4359_rq_1234",
  question: "How third parties affect firms' ability to create and capture value?",
  question_type: "explanatory",
  domain: "strategic_management",
  section: "introduction"
})
```

**Properties**:
- `question_id` (string): Unique identifier (paper_id + hash)
- `question` (string): Full question text
- `question_type` (string): descriptive, explanatory, predictive, prescriptive
- `domain` (string): Research domain
- `section` (string): Where question appears

### Relationships Created

**Paper → ResearchQuestion**: `(Paper)-[:ADDRESSES]->(ResearchQuestion)`

**Example**:
```cypher
(Paper {paper_id: "2025_4359"})-[:ADDRESSES]->(ResearchQuestion {
  question: "How third parties affect firms' ability to create and capture value?"
})
```

## Variable Extraction

### Prompt Design

**Input**: Methodology section (if found) + first 10,000 characters (up to 20k total)

**Key Features**:
1. **Variable Type Classification**:
   - `dependent`: Outcome variable (DV, Y variable)
   - `independent`: Predictor variable (IV, X variable)
   - `control`: Control variable
   - `moderator`: Moderating variable
   - `mediator`: Mediating variable
2. **Measurement Extraction**: How variable is measured (e.g., "ROA", "Tobin's Q")
3. **Operationalization**: How variable is operationalized
4. **Domain Classification**: Variable domain (organizational, financial, strategic, behavioral)

### Nodes Created

**Variable Node**:
```cypher
(:Variable {
  variable_id: "2025_4359_var_5678",
  variable_name: "Restaurant Exits",
  variable_type: "dependent",
  measurement: "rates of exit for Michelin-starred restaurants",
  operationalization: "measured as the likelihood of restaurant exits using a two-decade panel",
  domain: "organizational"
})
```

**Properties**:
- `variable_id` (string): Unique identifier (paper_id + hash)
- `variable_name` (string): Variable name
- `variable_type` (string): dependent, independent, control, moderator, mediator
- `measurement` (string): How variable is measured
- `operationalization` (string): How variable is operationalized
- `domain` (string): Variable domain

### Relationships Created

**Paper → Variable**: `(Paper)-[:USES_VARIABLE]->(Variable)`

**Properties**:
- `variable_type` (string): Role of variable in this paper

**Example**:
```cypher
(Paper {paper_id: "2025_4359"})-[:USES_VARIABLE {
  variable_type: "dependent"
}]->(Variable {
  variable_name: "Restaurant Exits"
})
```

## Extraction Flow

```
1. Extract text
   - ResearchQuestion: First 15k chars (Abstract + Introduction)
   - Variable: Methodology section + first 10k chars (up to 20k)
   ↓
2. Send to LLM with extraction prompt
   ↓
3. LLM identifies questions/variables
   ↓
4. Parse JSON response
   ↓
5. Validate (questions must have "?", variables must have name)
   ↓
6. Create nodes in Neo4j
   ↓
7. Create relationships
```

## Example Neo4j Queries

### 1. Find Papers Addressing a Research Question
```cypher
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
WHERE rq.question CONTAINS "third parties"
RETURN p.title, rq.question
```

### 2. Research Questions by Type
```cypher
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
RETURN rq.question_type, count(rq) as count
ORDER BY count DESC
```

### 3. Variables by Type
```cypher
MATCH (p:Paper)-[r:USES_VARIABLE]->(v:Variable)
RETURN r.variable_type, count(v) as count
ORDER BY count DESC
```

### 4. Papers Using Same Variable
```cypher
MATCH (p1:Paper)-[:USES_VARIABLE]->(v:Variable {variable_name: "Firm Performance"})
MATCH (p2:Paper)-[:USES_VARIABLE]->(v)
WHERE p1 <> p2
RETURN p1.title, p2.title
```

### 5. Research Gaps (Questions with Few Papers)
```cypher
MATCH (p:Paper)-[:ADDRESSES]->(rq:ResearchQuestion)
WITH rq, count(p) as paper_count
WHERE paper_count < 3
RETURN rq.question, paper_count
ORDER BY paper_count
```

## Benefits

1. **Research Gap Identification**: Find questions with few papers
2. **Variable Tracking**: Track variable usage across papers
3. **Question Evolution**: Track how questions evolve over time
4. **Variable Relationships**: Identify moderators and mediators
5. **Literature Review**: Quickly identify research questions and variables

## Integration Status

- ✅ ResearchQuestion extraction method created (`extract_research_questions`)
- ✅ Variable extraction method created (`extract_variables`)
- ✅ Prompts designed and optimized
- ✅ Neo4j ingestion logic added (ResearchQuestion & Variable nodes + relationships)
- ✅ Tested on sample paper (3 questions, 5 variables extracted)
- ✅ Integrated into main processing pipeline

## Next Steps

1. **Test on Multiple Papers**: Validate consistency across papers
2. **Question Relationships**: Create relationships between related questions
3. **Variable Relationships**: Create MODERATES and MEDIATES relationships
4. **Normalization**: Merge similar variable names (e.g., "Firm Performance" vs "Performance")

