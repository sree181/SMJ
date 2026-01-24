# Strict Theory Re-Extraction - Running

## Status: ✅ IN PROGRESS

The re-extraction process has been started with a **much stricter prompt** that will only extract theories that are **actively used**, not just mentioned.

## Changes Made

### 1. Stricter Extraction Prompt

Updated `redesigned_methodology_extractor.py` with maximum strictness:

**Key Changes:**
- **PRIMARY theories ONLY**: Must be explicitly stated as main framework AND used in analysis
- **SUPPORTING theories**: Only if explicitly used to support arguments (not just mentioned)
- **Skip if context says**: "mentioned in literature review without being used", "only mentioned", "not central"
- **Common theories**: RBV, Upper Echelons, etc. - only extract if actually used, not just mentioned
- **Quality over quantity**: Prefer 0-3 accurate theories over 5-10 generic ones

### 2. Process Started

```bash
python3 re_extract_theories_all_papers.py
```

Running in background, processing all 139 papers.

## Expected Results

### Before (Current State):
- Paper `2021_4373`: 10 theories (7 just mentioned in literature review)
- Average: 6.6 theories per paper
- Many papers with 5-10 "supporting" theories from literature reviews

### After (Strict Re-Extraction):
- Paper `2021_4373`: ~2-4 theories (only actively used)
- Average: ~3-4 theories per paper (more accurate)
- Only theories that are actually used in analysis

## Monitoring

### Check Progress:
```bash
tail -f theory_re_extraction_full.log
```

### Check Progress File:
```bash
cat theory_re_extraction_progress.json
```

### Check if Running:
```bash
ps aux | grep re_extract_theories_all_papers
```

## Time Estimate

- **Per paper**: ~30-60 seconds
- **139 papers**: ~2-3 hours total
- **Started**: Check log file for start time

## What Gets Changed

- **Theory relationships**: Old ones deleted, new ones created
- **Theory nodes**: Preserved (only relationships change)
- **Other entities**: Methods, variables, findings, etc. unchanged

## After Completion

Run diagnostics to see improvements:

```bash
# Check overall distribution
python3 diagnose_theory_distribution.py

# Check specific paper
python3 analyze_paper_theories.py 2021_4373

# Check for over-extraction
python3 identify_over_extracted_theories.py
```

## Key Improvements

1. **Stricter prompt**: Only extracts actively-used theories
2. **Better normalization**: Duplicates already merged
3. **Quality focus**: Fewer, more accurate theories
4. **Cleaner graph**: Less clutter, more signal

## Notes

- Process can be interrupted (Ctrl+C) and resumed
- Progress saved every 10 papers
- Failed papers are logged and skipped
- Can resume from specific paper if needed



