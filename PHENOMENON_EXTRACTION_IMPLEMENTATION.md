# Phenomenon Extraction & Theory-Phenomenon Connections - Implementation Complete ✅

## Overview

Successfully implemented:
1. **Phenomenon Extraction**: LLM-based extraction of observable events, patterns, behaviors, or trends
2. **Theory-Phenomenon Connections**: Automatic linking of theories to phenomena they explain

---

## 1. Phenomenon Extraction

### Implementation

**File**: `redesigned_methodology_extractor.py`
**Method**: `extract_phenomena(text: str, paper_id: str) -> List[Dict[str, Any]]`
**Lines**: 508-581

### How It Works

1. **Input**: First 25,000 characters (Introduction + Literature Review + Methodology)
2. **LLM Extraction**: Uses standardized prompt template with few-shot examples
3. **Output**: List of phenomena with:
   - `phenomenon_name`: Exact name as written
   - `phenomenon_type`: behavior, pattern, event, trend, or process
   - `domain`: strategic_management, organizational_behavior, or other
   - `description`: Brief description
   - `section`: Where it appears (introduction, literature_review, methodology)
   - `context`: How the phenomenon is studied

### Extraction Rules

```python
rules = [
    "Extract EXACT phenomenon names as they appear - do NOT summarize or rewrite",
    "Phenomena are observable events, patterns, behaviors, or trends that are being studied",
    "Extract ONLY phenomena that are explicitly stated as the focus of the research",
    "DO NOT extract generic concepts or theories - only concrete phenomena",
    "Be conservative - extract only clearly identified phenomena",
    "Include context about how the phenomenon is studied"
]
```

### Examples

**Example 1**: Single phenomenon
```
Input: "This study examines the phenomenon of economic nationalism in court 
       rulings against foreign firms."
Output: {
    "phenomenon_name": "Economic nationalism in court rulings",
    "phenomenon_type": "behavior",
    "description": "Systematic favoritism of domestic firms over foreign firms"
}
```

**Example 2**: Multiple phenomena
```
Input: "We study two phenomena: (1) resource allocation patterns during 
       financial crises, and (2) strategic responses to market disruptions."
Output: [
    {"phenomenon_name": "Resource allocation patterns during financial crises", ...},
    {"phenomenon_name": "Strategic responses to market disruptions", ...}
]
```

---

## 2. Data Validation

### PhenomenonData Model

**File**: `data_validator.py`
**Class**: `PhenomenonData`
**Lines**: 143-150

```python
class PhenomenonData(BaseModel):
    phenomenon_name: str = Field(..., min_length=1, max_length=200)
    phenomenon_type: Optional[str] = Field(None, max_length=50)
    domain: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=2000)
    section: Optional[str] = Field(None, max_length=50)
    context: Optional[str] = Field(None, max_length=1000)
```

### Validation Method

```python
@staticmethod
def validate_phenomenon(data: Dict[str, Any]) -> Optional[PhenomenonData]:
    """Validate phenomenon data"""
    try:
        return PhenomenonData(**data)
    except ValidationError as e:
        logger.warning(f"Phenomenon validation failed: {e}")
        return None
```

---

## 3. Neo4j Ingestion

### Phenomenon Node Creation

**File**: `redesigned_methodology_extractor.py`
**Method**: `ingest_paper_with_methods()`
**Lines**: 2153-2175

```cypher
MERGE (ph:Phenomenon {phenomenon_name: $phenomenon_name})
SET ph.phenomenon_type = $phenomenon_type,
    ph.domain = $domain,
    ph.description = $description,
    ph.context = $context
```

### Paper-Phenomenon Relationship

**Relationship**: `(Paper)-[:STUDIES_PHENOMENON]->(Phenomenon)`

**Properties**:
- `section`: Where phenomenon appears
- `context`: How phenomenon is studied

```cypher
MERGE (p)-[r:STUDIES_PHENOMENON {
    section: $section,
    context: $context
}]->(ph)
```

---

## 4. Theory-Phenomenon Connections

### Connection Logic

**File**: `redesigned_methodology_extractor.py`
**Lines**: 2176-2220

### How Theories Connect to Phenomena

The system automatically creates `EXPLAINS_PHENOMENON` relationships when:

1. **Primary Theory + Same Section**:
   - Theory has `role: "primary"`
   - Phenomenon appears in same section as theory
   - → **Connection Strength**: 0.7

2. **Context Overlap**:
   - Theory usage context and phenomenon context share ≥2 keywords
   - → **Connection Strength**: 0.5

### Relationship Structure

**Relationship**: `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)`

**Properties**:
- `paper_id`: Which paper establishes this connection
- `theory_role`: primary, supporting, challenging, or extending
- `section`: Where connection is made
- `connection_strength`: 0.5 (supporting) or 0.7 (primary)

```cypher
MERGE (t)-[r:EXPLAINS_PHENOMENON {
    paper_id: $paper_id,
    theory_role: $theory_role,
    section: $section,
    connection_strength: $connection_strength
}]->(ph)
```

### Example Connection

```
Paper: "Strategic management during financial crisis"
Theory: "Resource-Based View" (primary)
Phenomenon: "Resource allocation patterns during financial crises"

Connection:
(Theory {name: "Resource-Based View"})-[:EXPLAINS_PHENOMENON {
    paper_id: "2021_4327",
    theory_role: "primary",
    section: "introduction",
    connection_strength: 0.7
}]->(Phenomenon {phenomenon_name: "Resource allocation patterns during financial crises"})
```

---

## 5. Processing Pipeline Integration

### Updated Flow

```
1. Extract text from PDF
   ↓
2. Extract theories
   ↓
3. Extract phenomena (NEW)
   ↓
4. Ingest to Neo4j:
   - Create Theory nodes
   - Create Phenomenon nodes
   - Create Paper-Phenomenon relationships
   - Create Theory-Phenomenon relationships (NEW)
```

### Code Changes

**File**: `redesigned_methodology_extractor.py`
**Method**: `process_paper()`
**Lines**: 2369-2376 (phenomenon extraction)
**Lines**: 2434-2436 (ingestion with phenomena)

---

## 6. Prompt Template Integration

### ExtractionType Enum

**File**: `prompt_template.py`
**Line**: 23

```python
PHENOMENON = "phenomenon"
```

### Few-Shot Examples

**File**: `prompt_template.py`
**Lines**: 208-260

Three examples provided:
1. Single phenomenon extraction
2. Multiple phenomena with theory connection
3. Focused phenomenon extraction

---

## 7. Usage Examples

### Query: Find Phenomena Studied in Papers

```cypher
MATCH (p:Paper)-[:STUDIES_PHENOMENON]->(ph:Phenomenon)
RETURN p.title, ph.phenomenon_name, ph.phenomenon_type
LIMIT 10
```

### Query: Find Theories Explaining Phenomena

```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
RETURN t.name as theory, ph.phenomenon_name as phenomenon, 
       r.connection_strength as strength, r.theory_role as role
ORDER BY r.connection_strength DESC
```

### Query: Find Papers Using Theory to Explain Phenomenon

```cypher
MATCH (p:Paper)-[:USES_THEORY]->(t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
WHERE t.name = "Resource-Based View"
RETURN p.title, ph.phenomenon_name, r.connection_strength
```

### Query: Most Common Theory-Phenomenon Connections

```cypher
MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
RETURN t.name as theory, ph.phenomenon_name as phenomenon, 
       count(r) as connection_count
ORDER BY connection_count DESC
LIMIT 10
```

---

## 8. Future Enhancements

### Potential Improvements

1. **LLM-Based Connection**: Use LLM to determine if theory explains phenomenon (more accurate than keyword matching)
2. **Connection Confidence**: Calculate confidence based on:
   - Theory role (primary > supporting)
   - Section overlap
   - Context similarity (using embeddings)
3. **Phenomenon Normalization**: Normalize phenomenon names (similar to theory normalization)
4. **Phenomenon Relationships**: Create relationships between related phenomena
5. **Temporal Analysis**: Track how theories explain phenomena over time

---

## Summary

✅ **Phenomenon Extraction**: Implemented with LLM-based extraction
✅ **Data Validation**: PhenomenonData model added
✅ **Neo4j Ingestion**: Phenomenon nodes and STUDIES_PHENOMENON relationships
✅ **Theory-Phenomenon Connections**: EXPLAINS_PHENOMENON relationships with connection strength
✅ **Pipeline Integration**: Full integration into processing pipeline
✅ **Prompt Template**: Few-shot examples added

**Status**: Complete and ready to use! 🎉

