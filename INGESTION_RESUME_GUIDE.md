# Ingestion Resume Guide

## Current Status

### Analysis Summary
- **Total PDFs found**: 836 papers across all year folders
- **Papers in Neo4j**: Unable to verify (connection issue), but progress file suggests some papers were processed
- **Papers marked as processed**: 0 (cleaned - all removed for retry)
- **Papers marked as failed**: 0 (cleaned - all removed for retry)
- **Papers needing processing**: ~790 papers

### What Was Done
1. ✅ Analyzed ingestion status using `analyze_ingestion_status.py`
2. ✅ Cleaned progress file to remove duplicates and prepare for resume
3. ✅ Created resume list with 790 papers to process

## Resume Instructions

### Option 1: Process by Year Folder (Recommended)

Process papers folder by folder, starting with the most recent:

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate

# Process 2025-2029 papers (10 papers)
python batch_process_complete_extraction.py 2025-2029

# Process 2020-2024 papers (158 papers)
python batch_process_complete_extraction.py 2020-2024

# Process 2015-2019 papers
python batch_process_complete_extraction.py 2015-2019

# Continue with earlier years...
```

### Option 2: Process in Background

Run the batch processor in the background so it continues even if you disconnect:

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate

# Process 2020-2024 in background
nohup python batch_process_complete_extraction.py 2020-2024 > batch_extraction_output.log 2>&1 &
```

### Monitor Progress

While processing, monitor progress:

```bash
# View live log
tail -f batch_extraction_output.log

# Check progress file
cat batch_extraction_progress.json | python -m json.tool

# Check how many papers processed
python -c "
import json
with open('batch_extraction_progress.json') as f:
    data = json.load(f)
    print(f\"Processed: {len(data['processed_papers'])}\")
    print(f\"Failed: {len(data['failed_papers'])}\")
"
```

## Important Notes

### Progress Tracking
- The batch processor automatically skips papers already in `processed_papers` list
- Progress is saved after each paper
- If the process stops, you can restart and it will resume from where it left off

### Failed Papers
- Papers that fail will be added to `failed_papers` list
- You can retry failed papers by removing them from `failed_papers` in the progress file
- Common failure reasons:
  - OLLAMA connection timeout (increase timeout or check OLLAMA is running)
  - Neo4j connection issues (check network/credentials)
  - PDF parsing errors (corrupted files)

### Performance
- Expected processing time: ~3 minutes per paper
- For 790 papers: ~40 hours total
- Consider processing in smaller batches (e.g., 50-100 papers at a time)

## Troubleshooting

### Neo4j Connection Issues
If you see connection errors:
1. Check your `.env` file has correct Neo4j credentials
2. Verify Neo4j database is accessible
3. Check network connectivity

### OLLAMA Timeout Issues
If papers fail with OLLAMA timeouts:
1. Ensure OLLAMA is running: `ollama serve`
2. Check OLLAMA model is available: `ollama list`
3. Consider increasing timeout in the extraction code
4. Or switch to OpenAI API if available

### Resume After Cleanup
The progress file has been cleaned:
- Original backed up to: `batch_extraction_progress.json.backup`
- All papers removed from processed/failed lists
- Ready for fresh start or selective processing

## Next Steps

1. **Start with a small batch** to verify everything works:
   ```bash
   python batch_process_complete_extraction.py 2025-2029
   ```

2. **Monitor the first batch** to ensure no errors

3. **Scale up** to larger batches once confirmed working

4. **Check Neo4j** periodically to verify papers are being ingested

## Files Created

- `analyze_ingestion_status.py` - Analysis script
- `clean_progress_file.py` - Progress file cleanup script
- `resume_ingestion_list.json` - List of papers to process
- `batch_extraction_progress.json.backup` - Backup of original progress file
- `INGESTION_RESUME_GUIDE.md` - This guide
