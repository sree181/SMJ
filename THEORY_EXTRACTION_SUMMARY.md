# Theory Extraction - Complete Summary

## ✅ Implementation Complete

Theory extraction has been successfully implemented and tested. Here's what was extracted from paper `2025_4359`:

### Extracted Theories (7 total):
1. **Value-Based Strategy** (primary framework)
2. **Value-Based View (VBV)** (primary framework)
3. **Status Quo Configuration** (supporting model)
4. **Reactivity** (supporting concept)
5. **Resource-Based View (RBV)** (challenging framework)
6. **Institutional Theory** (supporting perspective)
7. **Upper Echelons Theory** (supporting perspective)

## Prompt Explanation

### Prompt Structure

The extraction prompt is designed to:

1. **Focus on Introduction + Literature Review** (first 20,000 characters)
   - These sections contain the most theory discussion
   - Avoids slower processing of full paper

2. **Extract Exact Theory Names**
   - Uses exact names as written (e.g., "Resource-Based View" not "resource based view")
   - Handles abbreviations (e.g., "RBV" and "Resource-Based View")

3. **Classify Theory Role**
   - `primary`: Main theoretical framework
   - `supporting`: Used to support arguments
   - `challenging`: Theories critiqued
   - `extending`: Theories built upon

4. **Capture Usage Context**
   - Brief description of how theory is used
   - Helps understand theory application

5. **Identify Section Location**
   - Where theory appears (introduction, literature_review, discussion)

### Key Prompt Features

- **Common Theories Reference**: Includes list of common SMJ theories to help LLM recognize them
- **Strict Extraction Rules**: Only extract explicitly mentioned theories
- **JSON Schema**: Structured output for easy parsing
- **Validation**: Filters out empty or invalid theory names

## Nodes Created

### Theory Node
```cypher
(:Theory {
  name: "Resource-Based View",
  domain: "strategic_management",
  theory_type: "framework",
  description: "Brief description if provided"
})
```

**Properties**:
- `name` (string): Theory name (unique identifier)
- `domain` (string): Research domain (default: "strategic_management")
- `theory_type` (string): "framework", "concept", "model", "perspective"
- `description` (string): Brief description if provided in paper

## Relationships Created

### 1. Paper → Theory
**Relationship**: `(Paper)-[:USES_THEORY]->(Theory)`

**Properties**:
- `role` (string): "primary", "supporting", "challenging", "extending"
- `section` (string): "introduction", "literature_review", "discussion"
- `usage_context` (string): How theory is used in the paper

**Example**:
```cypher
(Paper {paper_id: "2025_4359"})-[:USES_THEORY {
  role: "primary",
  section: "literature_review",
  usage_context: "begins with the idea that value creation and capture extend from free-form bargaining among actors in a value network"
}]->(Theory {name: "Value-Based Strategy"})
```

### 2. Theory → Theory (Future)
These relationships will be created in a separate step:
- `(Theory)-[:RELATED_TO {relationship_type, strength}]->(Theory)`
- `(Theory)-[:EXTENDS {extension_type, year}]->(Theory)`

## Extraction Flow

```
1. Extract text (first 20k chars)
   ↓
2. Send to LLM with theory extraction prompt
   ↓
3. LLM identifies theories and their roles
   ↓
4. Parse JSON response
   ↓
5. Validate theory names (not empty)
   ↓
6. Create Theory nodes in Neo4j (MERGE by name)
   ↓
7. Create USES_THEORY relationships
```

## Example Neo4j Queries

### 1. Find All Papers Using a Theory
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.title, p.year, t.name
ORDER BY p.year
```

### 2. Find Primary Theories
```cypher
MATCH (p:Paper)-[r:USES_THEORY {role: "primary"}]->(t:Theory)
RETURN t.name, count(p) as paper_count
ORDER BY paper_count DESC
```

### 3. Theory Evolution Over Time
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory {name: "Resource-Based View"})
RETURN p.year, count(p) as count
ORDER BY p.year
```

### 4. Papers Using Multiple Theories
```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)
WITH p, collect(t.name) as theories
WHERE size(theories) > 2
RETURN p.title, theories
```

### 5. Theory Usage by Role
```cypher
MATCH (p:Paper)-[r:USES_THEORY]->(t:Theory)
RETURN t.name, r.role, count(p) as count
ORDER BY t.name, count DESC
```

## Benefits

1. **Theoretical Gap Identification**: Find theories with few papers
2. **Theory Evolution**: Track how theories are used over time
3. **Theory Relationships**: Identify complementary or competing theories
4. **Research Streams**: Find papers using similar theoretical frameworks
5. **Literature Review**: Quickly identify theoretical foundations

## Integration Status

- ✅ Theory extraction method created (`extract_theories`)
- ✅ Prompt designed and optimized (20k chars, 2500 tokens)
- ✅ Neo4j ingestion logic added (Theory nodes + USES_THEORY relationships)
- ✅ Tested on sample paper (7 theories extracted)
- ✅ Integrated into main processing pipeline

## Next Steps

1. **Theory Relationship Extraction**: Create relationships between theories
2. **Theory Validation**: Filter out hallucinated theories (e.g., "not explicitly mentioned")
3. **Theory Normalization**: Merge similar theory names (e.g., "RBV" and "Resource-Based View")
4. **Batch Processing**: Test on multiple papers to validate consistency

