# Export Dashboard Tabs to CSV

This script exports data from each dashboard tab to separate CSV files for easy sharing with coauthors.

## Usage

```bash
python3 export_dashboard_tabs_to_csv.py
```

## What Gets Exported

The script exports the following tabs to separate CSV files:

1. **Tab 1: Papers by Timeframe** - Paper counts by 5-year intervals
2. **Tab 2: Authors by Period** - Author counts and top authors by 5-year intervals
3. **Tab 3: Topics by Period** - Topic evolution with LLM-generated names by 5-year intervals
4. **Tab 4: Phenomena by Period** - Top phenomena studied by 5-year intervals
5. **Tab 5: Theory Evolution** - Theory proportions and evolution over time
6. **Tab 6: Theory Betweenness** - Theory betweenness scores and cross-topic reach
7. **Tab 7: Opportunity Gaps** - Under-theorized phenomena with opportunity scores
8. **Tab 8: Integration Mechanism** - Theory co-usage and integration scores

## Output Location

All CSV files are saved to the `analytics_exports/` directory with timestamps:
- `tab_1_papers_by_timeframe_YYYYMMDD_HHMMSS.csv`
- `tab_2_authors_by_period_YYYYMMDD_HHMMSS.csv`
- `tab_3_topics_by_period_YYYYMMDD_HHMMSS.csv`
- `tab_4_phenomena_by_period_YYYYMMDD_HHMMSS.csv`
- `tab_5_theory_evolution_YYYYMMDD_HHMMSS.csv`
- `tab_6_theory_betweenness_YYYYMMDD_HHMMSS.csv`
- `tab_7_opportunity_gaps_YYYYMMDD_HHMMSS.csv`
- `tab_8_integration_mechanism_YYYYMMDD_HHMMSS.csv`

A summary file is also created: `export_summary_YYYYMMDD_HHMMSS.txt`

## Requirements

- Neo4j connection (via `.env` file with `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)
- Backend API server running (for tabs 5-8 that use API endpoints)
- Python packages: `neo4j`, `python-dotenv`, `requests`

## Notes

- Tabs 1-4 query Neo4j directly (faster, no API dependency)
- Tabs 5-8 call the backend API endpoints (requires API server to be running)
- If the API server is not running, tabs 5-8 will fail gracefully with error messages
- All exports include timestamps to avoid overwriting previous exports
