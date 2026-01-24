# Critical Fixes: Ensure Paper, Theory, Method Nodes Are Created

## Problem Identified

From Neo4j browser, user sees:
- ✅ Contribution nodes (working)
- ✅ Finding nodes (working)  
- ✅ Phenomenon nodes (working)
- ❌ Paper metadata nodes (not visible/complete)
- ❌ Theory nodes (not created - validation failing)
- ❌ Method nodes (not created - validation failing)

## Root Causes

1. **Validation Too Strict**: Case sensitivity (PRIMARY vs primary) causing theories to be skipped
2. **Format Mismatches**: data_sources as string instead of array causing methods to be skipped
3. **Missing author_id**: Authors being skipped
4. **Silent Failures**: Validation failures cause entities to be skipped without creating nodes

## Required Fixes

### Fix 1: Normalize Data Before Validation
- Convert PRIMARY → primary, Dependent → dependent
- Convert string data_sources → array
- Generate author_id automatically

### Fix 2: Create Nodes Even With Partial Data
- If validation fails, create node with available data
- Log warnings but don't skip entirely
- Use fallback values for missing required fields

### Fix 3: Ensure Paper Metadata Always Created
- Paper node should ALWAYS be created
- Even if metadata extraction fails, use fallback
- Ensure title, abstract, year are always set

### Fix 4: Add Research Questions to GPT-4 Schema
- Currently missing from GPT-4 extraction
- Needed for research question analysis

## Implementation Priority

1. **IMMEDIATE**: Fix validation normalization (case, format)
2. **IMMEDIATE**: Ensure Paper/Theory/Method nodes always created
3. **HIGH**: Add Research Questions to GPT-4 schema
4. **HIGH**: Implement missing relationships for research questions
