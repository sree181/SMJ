# Batch Processing Monitoring Guide

## Current Status

The batch processor is **currently running** in the background. Here's how to monitor it:

---

## Quick Status Check

### Option 1: Use the Monitoring Script (Recommended)

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python monitor_batch_status.py
```

This shows:
- ✅ Progress (processed/failed papers)
- ✅ Neo4j database status
- ✅ Recent papers
- ✅ Node and relationship counts
- ✅ Log file status

### Option 2: Continuous Monitoring (Auto-refresh)

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python monitor_batch_status.py --loop 30
```

This updates every 30 seconds. Press `Ctrl+C` to stop.

---

## Check Progress File

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
cat batch_extraction_progress.json | python -m json.tool
```

Shows:
- `processed_papers`: List of successfully processed papers
- `failed_papers`: List of papers that failed

---

## Check Log Files

### Main Log File (if process was started with redirection):
```bash
tail -f batch_extraction_output.log
```

### Standard Log File:
```bash
tail -f batch_extraction.log
```

**Note**: If the log file is empty, the process might be running without output redirection.

---

## Check if Process is Running

```bash
ps aux | grep batch_process_complete_extraction | grep -v grep
```

If you see a process, it's running!

---

## Check Neo4j Status

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python -c "
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
load_dotenv()
driver = GraphDatabase.driver(os.getenv('NEO4J_URI'), auth=(os.getenv('NEO4J_USER'), os.getenv('NEO4J_PASSWORD')))
with driver.session() as session:
    result = session.run('MATCH (p:Paper) RETURN count(p) as count').single()
    print(f'Papers in Neo4j: {result[\"count\"]}')
driver.close()
"
```

---

## Restart with Proper Logging

If you want to restart the process with proper logging:

### 1. Stop the current process:
```bash
pkill -f batch_process_complete_extraction
```

### 2. Start with output redirection:
```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
nohup python batch_process_complete_extraction.py "2020-2024" > batch_extraction_output.log 2>&1 &
```

### 3. Monitor the output:
```bash
tail -f batch_extraction_output.log
```

---

## Current Process Status

Based on the monitoring script:

- ✅ **Process is running** (PID: 48005)
- ✅ **10 papers processed**
- ❌ **6 papers failed**
- ✅ **8 papers in Neo4j**

### Recent Processed Papers:
- 2025_4431
- 2025_4478
- 2025_4488
- 2025_4533
- 2025_4573

### Failed Papers:
- 2025_4260
- 2025_4346
- 2025_4431
- 2025_4478
- 2025_4573

**Note**: Some papers appear in both lists, which might indicate partial processing or retry attempts.

---

## Troubleshooting

### If log file is empty:
The process might be running without output redirection. Use the monitoring script instead:
```bash
python monitor_batch_status.py
```

### If you can't see progress:
1. Check if process is running: `ps aux | grep batch_process`
2. Check progress file: `cat batch_extraction_progress.json`
3. Use monitoring script: `python monitor_batch_status.py`

### If process seems stuck:
1. Check Neo4j connection
2. Check OLLAMA is running: `curl http://localhost:11434/api/tags`
3. Check for errors in `batch_extraction_results.json`

---

## Best Practice: Use the Monitoring Script

Instead of `tail -f`, use the monitoring script which provides:
- ✅ Real-time progress
- ✅ Neo4j statistics
- ✅ Recent papers
- ✅ Error summary
- ✅ Auto-refresh option

```bash
python monitor_batch_status.py --loop 30
```

This is more informative than just watching log files!

