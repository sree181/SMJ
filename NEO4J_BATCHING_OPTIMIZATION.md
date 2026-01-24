# Neo4j Batching Optimization - Implementation Plan

## Current Performance Issue

**Current**: 10-15 separate `tx.run()` calls per paper
- Each call is a separate database operation
- High transaction overhead
- ~2.0s per paper ingestion time

**Target**: Batch operations using UNWIND to reduce to 3-5 queries
- Expected: 1.3-1.5x speedup (2.0s → 1.3s)

## Optimization Strategy

### Phase 1: Simple Batching (Immediate Impact)
1. ✅ Batch delete operations (already done - 8 queries → 1 query)
2. ⏭️ Batch Variables + Findings + Contributions + Research Questions using UNWIND
3. ⏭️ Batch Author creation using UNWIND

### Phase 2: Complex Batching (Future)
4. Batch Theory creation (complex due to conflict resolution)
5. Batch Method creation (complex due to validation)

## Implementation Approach

### Pre-processing Pattern
1. **Normalize & Validate** all entities in Python (before transaction)
2. **Collect** processed data into arrays
3. **Batch** create nodes using UNWIND
4. **Batch** create relationships using UNWIND

### Example: Batched Variable Creation

**Before** (N queries):
```python
for var in variables_data:
    validated_var = self.validator.validate_variable(var)
    tx.run("MERGE (v:Variable ...)", ...)
    tx.run("MATCH (p:Paper ...) MERGE (p)-[:USES_VARIABLE]->(v)", ...)
```

**After** (1 query):
```python
# Pre-process all variables
validated_variables = []
for var in variables_data:
    validated_var = self.validator.validate_variable(var)
    if validated_var:
        validated_variables.append({
            "var_id": f"{paper_id}_var_{hash(validated_var.variable_name) % 10000}",
            "var_name": validated_var.variable_name,
            "variable_type": validated_var.variable_type,
            ...
        })

# Batch create in single query
if validated_variables:
    tx.run("""
        MATCH (p:Paper {paper_id: $paper_id})
        UNWIND $variables AS var
        MERGE (v:Variable {variable_id: var.var_id})
        SET v.variable_name = var.var_name,
            v.variable_type = var.variable_type,
            ...
        MERGE (p)-[r:USES_VARIABLE {variable_type: var.variable_type}]->(v)
    """, paper_id=paper_id, variables=validated_variables)
```

## Expected Performance

- **Delete operations**: 8 queries → 1 query (already done)
- **Variables**: N queries → 1 query
- **Findings**: N queries → 1 query
- **Contributions**: N queries → 1 query
- **Research Questions**: N queries → 1 query

**Total reduction**: ~15 queries → ~5 queries per paper

## Files to Modify

1. `redesigned_methodology_extractor.py`
   - Lines 1853-1927: Research Questions (batch)
   - Lines 1928-1963: Variables (batch)
   - Lines 1964-2000: Findings (batch)
   - Lines 2001-2030: Contributions (batch)
