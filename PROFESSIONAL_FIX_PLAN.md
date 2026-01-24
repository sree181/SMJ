# Professional Fix Plan - Prioritized Issues

## 🔴 CRITICAL ISSUES (Fix Immediately)

### 1. Authors Not Ingested
**Issue**: 0 authors, 0 AUTHORED_BY relationships
**Impact**: Author network analysis, collaboration features, paper attribution all broken
**Fix**: Verify author extraction in ingestion pipeline, re-ingest if needed

### 2. Missing EXPLAINS_PHENOMENON Relationships
**Issue**: Only 8 relationships exist, but 3,632 should exist based on paper connections
**Impact**: Theory-phenomenon analysis completely broken
**Fix**: Create script to compute EXPLAINS_PHENOMENON from Paper-Theory-Phenomenon paths

### 3. Papers Missing Titles
**Issue**: 433 papers (42%) missing titles
**Impact**: Search, display, and user experience severely degraded
**Fix**: Check ingestion pipeline, ensure title extraction is working

## ⚠️ HIGH PRIORITY (Fix Soon)

### 4. Data Completeness Issues
**Issue**: 
- 43.8% papers missing theories
- 71.2% papers missing methods
**Impact**: Incomplete data for analysis
**Fix**: Review extraction quality, improve LLM prompts if needed

### 5. Missing Database Indexes
**Issue**: No indexes on paper_id, theory_name, method_name, phenomenon_name
**Impact**: Slow queries, poor performance at scale
**Fix**: Create indexes for all frequently queried properties

### 6. Schema Inconsistency
**Issue**: Some queries use `year`, others use `publication_year`
**Impact**: Inconsistent behavior, potential bugs
**Fix**: Standardize on one field name across all queries

## 💡 MEDIUM PRIORITY

### 7. Orphaned Nodes
**Issue**: 1 orphaned theory, 1 orphaned method
**Impact**: Minor data quality issue
**Fix**: Clean up or connect orphaned nodes

### 8. API Error Handling
**Issue**: Inconsistent error handling across endpoints
**Impact**: Poor user experience, difficult debugging
**Fix**: Standardize error responses, add proper error codes

### 9. Missing Relationship Properties
**Issue**: Some USES_THEORY relationships missing 'role' property
**Impact**: Can't distinguish primary vs supporting theories
**Fix**: Ensure all relationships have required properties

## Implementation Priority

1. **Fix #2**: Create EXPLAINS_PHENOMENON relationships (enables core functionality)
2. **Fix #5**: Create database indexes (performance critical)
3. **Fix #3**: Fix missing titles (user experience)
4. **Fix #1**: Investigate author ingestion (if authors were extracted)
5. **Fix #6**: Standardize schema (prevent future bugs)
6. **Fix #4**: Improve extraction quality (long-term)
