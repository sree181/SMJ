# Batch Processing Restart Instructions

## How It Works

The batch processor **automatically resumes** from where it paused:

1. **Progress Tracking**: Saves progress to `batch_extraction_progress.json`
2. **Skip Processed**: Automatically skips papers already processed
3. **Continue Processing**: Picks up with remaining papers

## Current Status

**Papers Processed**: 3/10
- ✅ 2025_2079
- ✅ 2025_4098  
- ✅ 2025_4359

**Remaining**: 7 papers to process

## Restart Command

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python batch_process_complete_extraction.py 2025-2029
```

Or run in background:
```bash
nohup python batch_process_complete_extraction.py 2025-2029 > batch_extraction_output.log 2>&1 &
```

## What Happens on Restart

1. Loads `batch_extraction_progress.json`
2. Skips papers in "processed_papers" list
3. Continues with remaining papers
4. Updates progress file after each paper

## Monitor Progress

```bash
# View live log
tail -f batch_extraction_output.log

# Check progress file
cat batch_extraction_progress.json | python -m json.tool

# Check Neo4j status
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

## If You Want to Reprocess a Paper

Edit `batch_extraction_progress.json` and remove the paper_id from "processed_papers" array.

## Expected Completion

- **Remaining papers**: 7
- **Estimated time**: ~5-10 minutes (depending on paper complexity)
- **Final result**: All 10 papers processed and ingested

