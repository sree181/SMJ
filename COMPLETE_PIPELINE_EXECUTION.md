# Complete Pipeline Execution Plan

## Current Neo4j Status

### Node Types (10)
1. **Author**: 0 nodes ❌
2. **Contribution**: 807 nodes ✅
3. **Finding**: 946 nodes ✅
4. **Method**: 154 nodes ✅
5. **Paper**: 1,029 nodes ✅
6. **Phenomenon**: 1,407 nodes ✅
7. **ResearchQuestion**: 1,221 nodes ✅
8. **Software**: 10 nodes ✅
9. **Theory**: 1,019 nodes ✅
10. **Variable**: 4 nodes ✅

### Relationship Types (10)
1. **ADDRESSES**: 1,221 relationships (Paper → ResearchQuestion) ✅
2. **EXPLAINS_PHENOMENON**: 3,640 relationships (Theory → Phenomenon) ✅
3. **EXPLAINS_PHENOMENON_AGGREGATED**: 3,635 relationships ✅
4. **MAKES**: 749 relationships (Paper → Contribution) ✅
5. **REPORTS**: 892 relationships (Paper → Finding) ✅
6. **STUDIES_PHENOMENON**: 1,474 relationships (Paper → Phenomenon) ✅
7. **USES_METHOD**: 401 relationships (Paper → Method) ✅
8. **USES_SOFTWARE**: 10 relationships ✅
9. **USES_THEORY**: 1,550 relationships (Paper → Theory) ✅
10. **USES_VARIABLE**: 4 relationships ✅

### Missing Data Analysis

**Total Papers**: 1,029

**Missing Fields**:
- **Titles**: 433 papers (42.1%) ❌
- **Authors**: 1,029 papers (100.0%) ❌ CRITICAL
- **Theories**: 451 papers (43.8%) ⚠️
- **Methods**: 733 papers (71.2%) ⚠️
- **Phenomena**: 555 papers (53.9%) ⚠️
- **Research Questions**: 490 papers (47.6%) ⚠️
- **Findings**: 1,029 papers (100.0%) ❌ (but Finding nodes exist - relationship issue)
- **Contributions**: 1,029 papers (100.0%) ❌ (but Contribution nodes exist - relationship issue)

## Issues Identified

### Critical Issues
1. **Authors**: 0 nodes, 0 relationships - Complete absence
2. **Titles**: 433 papers missing titles
3. **Findings/Contributions**: Nodes exist but relationships missing (REPORTS/MAKES exist but queries look for HAS_FINDING/HAS_CONTRIBUTION)

### High Priority
4. **Theories**: 43.8% papers missing
5. **Methods**: 71.2% papers missing
6. **Phenomena**: 53.9% papers missing
7. **Research Questions**: 47.6% papers missing

## Solution

### Script Created: `run_missing_fields_pipeline.py`

**Features**:
1. Finds all papers with missing data
2. Locates PDF files for those papers
3. Creates temporary directory with symlinks to PDFs
4. Runs high-performance pipeline on those papers
5. Cleans up temporary directory

**Usage**:
```bash
# Process all papers with missing data
python run_missing_fields_pipeline.py

# Process first 10 papers (for testing)
python run_missing_fields_pipeline.py 10
```

### What It Will Fix

1. **Authors**: Will extract and ingest authors (fix already applied)
2. **Titles**: Will re-extract titles for papers missing them
3. **Theories**: Will extract theories for papers missing them
4. **Methods**: Will extract methods for papers missing them
5. **Phenomena**: Will extract phenomena for papers missing them
6. **Research Questions**: Will extract research questions for papers missing them
7. **Findings**: Will create relationships (nodes already exist)
8. **Contributions**: Will create relationships (nodes already exist)

## Execution Plan

### Step 1: Run Inventory
```bash
python neo4j_inventory.py > neo4j_inventory_output.txt
```

### Step 2: Run Pipeline (Test with Small Batch First)
```bash
# Test with 10 papers
python run_missing_fields_pipeline.py 10
```

### Step 3: Verify Results
```bash
# Check if authors were created
python -c "from neo4j import GraphDatabase; import os; from dotenv import load_dotenv; load_dotenv(); driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD'))); session = driver.session(); result = session.run('MATCH (a:Author) RETURN count(a) as count'); print(f'Authors: {result.single()[\"count\"]}'); driver.close()"
```

### Step 4: Run Full Pipeline
```bash
# Process all papers
python run_missing_fields_pipeline.py
```

## Expected Outcomes

After running the pipeline:
- ✅ Authors: Should have ~1,000+ author nodes
- ✅ Titles: Should have 0 papers missing titles
- ✅ Theories: Should have <10% papers missing theories
- ✅ Methods: Should have <20% papers missing methods
- ✅ Phenomena: Should have <10% papers missing phenomena
- ✅ Research Questions: Should have <10% papers missing research questions
- ✅ Findings: Relationships should be created
- ✅ Contributions: Relationships should be created

## Files Created

1. **`neo4j_inventory.py`** - Comprehensive database inventory
2. **`run_missing_fields_pipeline.py`** - Pipeline execution script
3. **`COMPLETE_PIPELINE_EXECUTION.md`** - This document
