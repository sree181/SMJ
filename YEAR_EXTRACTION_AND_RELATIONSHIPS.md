# Year Extraction and Relationship Types - Summary

## ✅ Changes Made

### 1. Year Extraction from Filenames

**Modified**: `run_missing_fields_pipeline.py`

**New Features**:
- `extract_year_from_filename()`: Extracts year from PDF filename
  - Pattern: `YYYY_XXXX.pdf` or `YYYY-XXXX.pdf` → extracts `YYYY`
  - Example: `2010_353.pdf` → `2010`
  - Validates year is between 1900-2100
- `update_paper_years()`: Updates Neo4j papers with extracted years
  - Only updates papers with missing or zero year values
  - Runs automatically before pipeline execution

**How It Works**:
1. When pipeline finds PDFs, it extracts year from filename
2. Before running extraction, it updates all papers with missing years
3. Year is extracted using regex pattern: `^(\d{4})[_-]`

**Example**:
```python
# Filename: 2010-2014/2010_353.pdf
# Extracted: 2010
# Updates: Paper node with paper_id="2010_353" → year=2010
```

---

## 2. Relationship Types Explanation

Created comprehensive documentation: `RELATIONSHIP_TYPES_EXPLANATION.md`

### Summary of Three Relationship Types

#### 1. STUDIES_PHENOMENON
- **Pattern**: `(Paper)-[:STUDIES_PHENOMENON]->(Phenomenon)`
- **Purpose**: Direct link - paper studies a phenomenon
- **Count**: 1,474 relationships
- **Granularity**: Paper level (one per paper-phenomenon pair)

#### 2. EXPLAINS_PHENOMENON
- **Pattern**: `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)`
- **Purpose**: Theory explains phenomenon (established by specific papers)
- **Count**: 3,640 relationships
- **Granularity**: Paper level (multiple can exist for same theory-phenomenon pair)
- **Properties**: `paper_id`, `connection_strength`, `theory_role`, `section`, etc.

#### 3. EXPLAINS_PHENOMENON_AGGREGATED
- **Pattern**: `(Theory)-[:EXPLAINS_PHENOMENON_AGGREGATED]->(Phenomenon)`
- **Purpose**: Aggregated summary of all EXPLAINS_PHENOMENON relationships
- **Count**: 3,635 relationships
- **Granularity**: Theory-Phenomenon pair level (one per unique pair)
- **Properties**: `avg_strength`, `paper_count`, `paper_ids` (combined list)

### Key Differences

| Aspect | STUDIES_PHENOMENON | EXPLAINS_PHENOMENON | EXPLAINS_PHENOMENON_AGGREGATED |
|--------|-------------------|---------------------|-------------------------------|
| **Direction** | Paper → Phenomenon | Theory → Phenomenon | Theory → Phenomenon |
| **Created When** | Paper mentions phenomenon | Paper uses theory AND studies phenomenon | Aggregated from EXPLAINS_PHENOMENON |
| **Granularity** | Per paper | Per paper | Per theory-phenomenon pair |
| **Use Case** | Find papers studying phenomena | Find theories explaining phenomena (with paper detail) | Fast aggregated queries |
| **Count** | 1,474 | 3,640 | 3,635 |

### Relationship Hierarchy

```
Paper "2010_353"
  ├─[:USES_THEORY]-> Theory "Resource-Based View"
  └─[:STUDIES_PHENOMENON]-> Phenomenon "Resource allocation patterns"

Theory "Resource-Based View"
  └─[:EXPLAINS_PHENOMENON {paper_id: "2010_353"}]-> Phenomenon "Resource allocation patterns"
     (Individual relationship from this paper)

Theory "Resource-Based View"
  └─[:EXPLAINS_PHENOMENON_AGGREGATED {paper_count: 5}]-> Phenomenon "Resource allocation patterns"
     (Aggregated summary of all 5 papers)
```

---

## Usage

### Running Pipeline with Year Extraction

```bash
# Process 10 papers (will extract years from filenames)
python run_missing_fields_pipeline.py 10

# Process all papers
python run_missing_fields_pipeline.py
```

**What Happens**:
1. Finds papers with missing data
2. Locates PDF files
3. **Extracts years from filenames and updates Neo4j** ← NEW
4. Runs extraction pipeline
5. Ingests all missing fields

---

## Files Modified/Created

1. **`run_missing_fields_pipeline.py`** - Modified
   - Added `extract_year_from_filename()` method
   - Added `update_paper_years()` method
   - Modified `create_temp_directory()` to return paper-pdf mapping
   - Integrated year extraction into pipeline flow

2. **`RELATIONSHIP_TYPES_EXPLANATION.md`** - Created
   - Comprehensive explanation of all three relationship types
   - Examples, use cases, and differences

3. **`YEAR_EXTRACTION_AND_RELATIONSHIPS.md`** - Created (this file)
   - Summary of changes

---

## Next Steps

1. **Test Year Extraction**: Run pipeline on a small batch to verify year extraction works
2. **Verify Relationships**: Check Neo4j to confirm all three relationship types are present
3. **Run Full Pipeline**: Once OpenAI quota is available, run full pipeline for all missing fields
