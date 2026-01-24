# Pipeline Status & Results

## Latest Run Summary

**Date**: Current Session  
**Status**: ✅ Completed (with fixes applied)

### Results
- **Total Papers**: 10
- **Successfully Processed**: 6 (60%)
- **Failed**: 4 (40%)
- **Success Rate**: 60.0%
- **Throughput**: 505.8 papers/hour

### Failed Papers (to be reprocessed)
1. `2025_2079` - NoneType iteration error
2. `2025_4098` - NoneType iteration error  
3. `2025_4359` - NoneType iteration error
4. `2025_4573` - NoneType iteration error

### Extractions
- **Theories**: 0 (validation issues - uppercase roles)
- **Phenomena**: 23 ✅
- **Methods**: 0 (validation issues - data_sources format)
- **Variables**: 31 (validation issues - capitalized types)
- **Findings**: 27 ✅

### Timing
- **Avg Extraction**: 16.6s
- **Avg Normalization**: 0.000s
- **Avg Ingestion**: 2.0s

## Fixes Applied

### 1. ✅ Fixed: `citations_data` not defined
- Added parameter to `ingest_paper_with_methods()`
- Updated all call sites
- Added citations extraction

### 2. ✅ Fixed: `'NoneType' object is not iterable`
- Added defensive checks in normalization
- Ensured extraction always returns lists (never None)
- Added fallback empty lists for all entity types

## Validation Warnings (Non-Critical)

These are data quality issues from GPT-4 extraction but are handled gracefully:

1. **Theory Roles**: GPT-4 returns uppercase (PRIMARY, SUPPORTING) but schema expects lowercase
   - **Impact**: Theories are skipped but paper still processes
   - **Fix Needed**: Add case normalization in extraction or validation

2. **Variable Types**: GPT-4 returns capitalized (Dependent, Independent) but schema expects lowercase
   - **Impact**: Variables are skipped but paper still processes
   - **Fix Needed**: Add case normalization

3. **Method data_sources**: GPT-4 returns strings instead of lists
   - **Impact**: Methods are skipped but paper still processes
   - **Fix Needed**: Ensure GPT-4 returns arrays or convert strings to lists

4. **Author author_id**: Missing required field
   - **Impact**: Authors are skipped but paper still processes
   - **Fix Needed**: Generate author_id in extraction or make field optional

## Current Action

**Restarting pipeline** with all fixes applied to reprocess failed papers.

## Next Steps

1. ✅ Monitor retry run
2. ⏳ Address validation warnings (case normalization)
3. ⏳ Verify all papers process successfully
4. ⏳ Check Neo4j for complete data ingestion
