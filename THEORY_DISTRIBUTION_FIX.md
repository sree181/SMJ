# Theory Distribution Analysis and Fixes

## Problem Identified

You reported seeing the same set of theories across all nodes in the graph. After analysis, we found:

### Issues Found:

1. **Duplicate Theories Not Normalized**:
   - "Dynamic Capabilities Theory" (38 papers) vs "Dynamic Capabilities" (4 papers) - **FIXED**
   - "Resource-Based View" (113 papers) vs "Resource-Based View (RBV)" (4 papers) vs "RBV (Resource-Based View)" (2 papers) - **FIXED**

2. **High Theory Overlap**:
   - 83.5% of papers use "Resource-Based View"
   - 77.0% use "Upper Echelons Theory"
   - 68.3% use "Organizational Learning Theory"
   
   **Note**: These are genuinely common theories in Strategic Management, but the percentages seem high, suggesting extraction may be too permissive.

3. **Identical Theory Sets**:
   - 13 papers share the exact same 10 theories
   - Multiple groups of papers with identical theory sets

## Fixes Implemented

### 1. Improved Normalization Logic (`entity_normalizer.py`)

**Changes**:
- Enhanced `normalize_theory()` to handle variations more precisely
- Added logic to remove common suffixes ("theory", "framework", "perspective") for matching
- Improved substring matching to only match direct variations (e.g., "Resource-Based View (RBV)") not longer specific names (e.g., "Adner's Resource-Based View")
- Added special handling for RBV and Dynamic Capabilities variations
- Prevents over-normalization of distinct theories

**Example**:
- Before: "Dynamic Capabilities" and "Dynamic Capabilities Theory" were separate
- After: Both normalize to "Dynamic Capabilities Theory"

### 2. Stricter Extraction Prompt (`redesigned_methodology_extractor.py`)

**Changes**:
- Made extraction rules more conservative
- Emphasized that theories must be **actively used**, not just mentioned
- Added explicit instructions to skip theories only mentioned in passing
- Clarified that theories must be **discussed**, not just named
- Added quality-over-quantity guidance

**Key Improvements**:
- "Extract ONLY theories that are EXPLICITLY USED in the paper's analysis or framework"
- "If a theory appears only once or twice without discussion, SKIP it"
- "Be EXTREMELY conservative - it's better to miss a theory than to extract one that's not actually used"

### 3. Database Cleanup (`fix_duplicate_theories.py`)

**Created script to**:
- Identify duplicate theories that should be merged
- Merge relationships from duplicates to canonical forms
- Preserve original names in `original_name` property
- Choose most common name as canonical (based on paper count)

**Merged**:
- "Dynamic Capabilities" → "Dynamic Capabilities Theory" (4 papers merged)
- "RBV (Resource-Based View)" → "Resource-Based View" (2 papers merged)
- "Resource-Based View (RBV)" → "Resource-Based View" (4 papers merged)

## Current Status

### After Fixes:
- **Total Papers**: 139
- **Total Theories**: 229 (down from 232)
- **No duplicate normalization detected** ✓
- **Average theories per paper**: 6.6

### Top Theories (After Merge):
1. Resource-Based View: 116 papers (83.5%)
2. Upper Echelons Theory: 107 papers (77.0%)
3. Organizational Learning Theory: 95 papers (68.3%)
4. Institutional Theory: 78 papers (56.1%)
5. Agency Theory: 75 papers (54.0%)

## Remaining Concerns

### High Theory Overlap

The high percentages (83.5% for RBV, 77.0% for Upper Echelons) could indicate:

1. **These are genuinely common theories** in Strategic Management Journal papers
2. **Extraction is still too permissive** - extracting theories mentioned in literature reviews rather than actively used

### Recommendations

1. **For Future Papers**: The updated extraction prompt should be more conservative
2. **For Existing Papers**: Consider re-extracting theories with the stricter prompt, but this would require:
   - Re-processing all papers
   - Significant time investment
   - May reduce theory counts (which could be good if current counts are inflated)

3. **Manual Review**: Sample a few papers to verify if the extracted theories are actually used or just mentioned

## Tools Created

1. **`diagnose_theory_distribution.py`**: 
   - Analyzes theory distribution across papers
   - Identifies duplicate normalization issues
   - Shows theory overlap and paper-level distribution

2. **`fix_duplicate_theories.py`**:
   - Finds duplicate theories that should be merged
   - Merges relationships and preserves data
   - Can run in dry-run mode to preview changes

## Usage

### Check Theory Distribution:
```bash
python3 diagnose_theory_distribution.py
```

### Fix Duplicate Theories:
```bash
# Dry run (preview changes)
python3 fix_duplicate_theories.py

# Actually merge duplicates
python3 fix_duplicate_theories.py --execute
```

## Next Steps

1. ✅ **Completed**: Fixed normalization to prevent over-merging
2. ✅ **Completed**: Made extraction prompt more conservative
3. ✅ **Completed**: Merged existing duplicate theories in database
4. ⚠️ **Optional**: Re-extract theories for existing papers with stricter prompt (time-intensive)
5. ⚠️ **Optional**: Manual review of sample papers to validate extraction quality

## Conclusion

The main issues have been addressed:
- Duplicate theories are now properly normalized
- Extraction prompt is more conservative for future papers
- Existing duplicates in the database have been merged

The high overlap percentages may reflect genuine commonality of these theories in Strategic Management research, but the stricter extraction rules should help ensure only actively-used theories are extracted going forward.

