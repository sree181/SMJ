# Export Charts to PNG (Plotly)

This script exports all dashboard charts as high-resolution black and white PNG files using Plotly for professional-quality visualizations.

## Specifications

- **Width**: 4080 pixels
- **Height**: 2448 pixels (3:5 aspect ratio)
- **DPI**: 1200 (publication quality)
- **Color**: Black and white (grayscale)
- **Format**: PNG
- **Library**: Plotly (professional charting)

## Usage

```bash
python3 export_charts_to_png.py
```

## Charts Exported

1. **Chart 1: Research Volume Evolution** - Bar chart showing paper counts by 5-year intervals
2. **Chart 2: Topic Landscape Evolution** - Area chart with dual y-axis showing topic metrics over time
3. **Chart 3: Authors by Period** - Bar chart showing unique authors by interval
4. **Chart 4: Phenomena by Period** - Bar chart showing unique phenomena by interval
5. **Chart 5: Theory Evolution** - Line chart showing top 5 theories over time with different line styles

## Output Location

All PNG files are saved to the `chart_exports/` directory with timestamps:
- `chart_1_paper_counts_YYYYMMDD_HHMMSS.png`
- `chart_2_topic_evolution_YYYYMMDD_HHMMSS.png`
- `chart_3_authors_by_period_YYYYMMDD_HHMMSS.png`
- `chart_4_phenomena_by_period_YYYYMMDD_HHMMSS.png`
- `chart_5_theory_evolution_YYYYMMDD_HHMMSS.png`

A summary file is also created: `export_summary_YYYYMMDD_HHMMSS.txt`

## Requirements

- Neo4j connection (via `.env` file with `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`)
- Backend API server running (for charts 2 and 5 that use API endpoints)
- Python packages: `neo4j`, `python-dotenv`, `requests`, `plotly`, `kaleido`, `numpy`

## Installation

Install required packages:
```bash
pip install plotly kaleido numpy
```

Or install with plotly extras:
```bash
pip install plotly[kaleido] numpy
```

**Note**: `kaleido` is required for Plotly to export images. The script will check for it and provide installation instructions if missing.

## Features

- **Professional Styling**: Clean, publication-ready black and white charts
- **High Quality**: 1200 DPI resolution for crisp text and lines
- **Grayscale Colors**: Uses black, dark gray, medium gray, light gray for distinction
- **Line Styles**: Different dash patterns and markers to distinguish series
- **Clear Labels**: Large, readable fonts with proper spacing
- **Grid Lines**: Subtle grid lines for easy value reading
- **Value Labels**: Bar charts show values above bars

## Notes

- Charts use grayscale colors (black, dark gray, medium gray, light gray) for publication-ready output
- Different line styles (solid, dash, dot, dashdot) and markers (circle, square, diamond, etc.) distinguish series in line charts
- All charts include grid lines, axis labels, and titles
- Charts are optimized for academic publication (high DPI, clear labels, professional styling)
- Plotly provides better rendering quality than matplotlib for complex charts
