# Analytics Export to CSV

This script exports comprehensive analytics reports from Neo4j to CSV files.

## Features

Exports the following reports:

1. **Papers by Timeframe** - Paper counts for each 5-year interval
2. **Authors by Timeline** - Top authors and their paper counts per interval
3. **Topics by Timeline** - Topic clusters identified via K-means clustering on paper embeddings
4. **Phenomena by Timeline** - Top phenomena and their paper counts per interval

## Usage

### Basic Usage

```bash
cd "Strategic Management Journal"
python3 export_analytics_to_csv.py
```

### Custom Time Range

Edit the script and modify the `main()` function:

```python
reports = exporter.export_all_reports(
    start_year=1990,  # Custom start year
    end_year=2020     # Custom end year
)
```

### Export Individual Reports

You can also export individual reports:

```python
from export_analytics_to_csv import AnalyticsExporter

exporter = AnalyticsExporter()

# Export only papers
exporter.export_papers_by_timeframe(
    start_year=1985,
    end_year=2025,
    output_file="papers.csv"
)

# Export only authors
exporter.export_authors_by_timeline(
    start_year=1985,
    end_year=2025,
    top_n=100,  # Top 100 authors per interval
    output_file="authors.csv"
)

exporter.close()
```

## Output Files

All CSV files are saved to the `analytics_exports/` directory with timestamps:

- `papers_by_timeframe_YYYYMMDD_HHMMSS.csv`
- `authors_by_timeline_YYYYMMDD_HHMMSS.csv`
- `topics_by_timeline_YYYYMMDD_HHMMSS.csv`
- `phenomena_by_timeline_YYYYMMDD_HHMMSS.csv`
- `export_summary_YYYYMMDD_HHMMSS.txt`

## CSV File Structure

### Papers by Timeframe
- Interval (e.g., "1985-1989")
- Start Year
- End Year
- Paper Count

### Authors by Timeline
- Interval
- Start Year
- End Year
- Author Name
- Given Name
- Family Name
- Papers Authored
- Total Unique Authors in Interval
- Total Papers in Interval

### Topics by Timeline
- Interval
- Start Year
- End Year
- Topic Number (cluster ID)
- Topic Paper Count
- Topic Coherence (similarity score)
- Representative Paper ID
- Representative Paper Title
- Total Topics in Interval
- Total Papers in Interval

### Phenomena by Timeline
- Interval
- Start Year
- End Year
- Phenomenon Name
- Papers Studying Phenomenon
- Total Unique Phenomena in Interval
- Total Papers in Interval

## Requirements

- Neo4j connection (via environment variables)
- Python packages: `neo4j`, `numpy`, `scikit-learn`, `python-dotenv`

## Environment Variables

Set these in your `.env` file or environment:

```bash
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

## Notes

- **Topics Export**: Uses K-means clustering on paper embeddings. This can take several minutes for large datasets.
- **Top N Limits**: Authors and Phenomena exports are limited to top 50 per interval by default (configurable).
- **Time Intervals**: All reports use 5-year intervals (e.g., 1985-1989, 1990-1994, etc.)
