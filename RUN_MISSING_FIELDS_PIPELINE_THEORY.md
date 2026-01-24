# Consolidated Theory: `run_missing_fields_pipeline.py`

## Overview

The `run_missing_fields_pipeline.py` script is a **data completeness orchestration system** that identifies papers with missing critical data, re-extracts information from PDFs, and updates Neo4j with comprehensive research metadata.

## Core Purpose

**Problem**: Papers in Neo4j may be missing:
- Titles (433 papers)
- Authors (0 authors currently)
- Theories (451 papers)
- Methods (733 papers)
- Phenomena (555 papers)
- Research Questions (490 papers)
- Years (extracted from filenames)

**Solution**: Automated pipeline that:
1. Identifies gaps
2. Locates source PDFs
3. Re-extracts missing data using GPT-4
4. Updates Neo4j with complete information

---

## Architecture & Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DATA GAP IDENTIFICATION                                   │
│    - Query Neo4j for papers missing:                        │
│      • Titles (NULL or empty)                               │
│      • Authors (no AUTHORED_BY relationships)              │
│      • Theories (no USES_THEORY relationships)             │
│      • Methods (no USES_METHOD relationships)              │
│      • Phenomena (no STUDIES_PHENOMENON relationships)     │
│      • Research Questions (no ADDRESSES relationships)      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PDF LOCATION & YEAR EXTRACTION                           │
│    - Find PDF files matching paper_id                       │
│    - Extract year from filename (e.g., 2010_353.pdf → 2010) │
│    - Update Neo4j with years BEFORE extraction              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. TEMPORARY DIRECTORY CREATION                             │
│    - Create temp_missing_fields_pdfs/                       │
│    - Create symlinks to source PDFs                        │
│    - Maintain paper_id → PDF_path mapping                   │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. HIGH-PERFORMANCE PIPELINE EXECUTION                      │
│    - Initialize HighPerformancePipeline                    │
│    - Process PDFs with GPT-4 extraction                     │
│    - Entity normalization (embedding-based)                  │
│    - Neo4j ingestion (batched operations)                  │
│    - Progress tracking & resume capability                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. DATA INGESTION                                           │
│    - Paper metadata (title, abstract, year, DOI)            │
│    - Authors (with affiliations → Institution nodes)        │
│    - Theories (with roles, domains, constructs)            │
│    - Methods (with types, sample sizes, software)           │
│    - Phenomena (with types, descriptions, context)          │
│    - Research Questions (with types, sections)             │
│    - Findings, Contributions, Variables, Citations         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. CLEANUP                                                  │
│    - Remove temporary directory                             │
│    - Close database connections                             │
│    - Report statistics                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. `MissingFieldsPipelineRunner` Class

**Responsibilities:**
- Database connection management
- Gap identification logic
- PDF location and year extraction
- Pipeline orchestration

**Key Methods:**

#### `find_papers_missing_data() -> Set[str]`
- Queries Neo4j for papers missing each data type
- Returns unique set of `paper_id`s to process
- Logs counts for each missing field type

#### `find_pdf_path(paper_id: str) -> Path`
- Searches for PDF using multiple patterns:
  - `{paper_id}.pdf`
  - `**/{paper_id}.pdf`
  - `**/*{paper_id}*.pdf`
- Returns first match or `None`

#### `extract_year_from_filename(pdf_path: Path) -> Optional[int]`
- Extracts year from filename pattern: `YYYY_XXXX.pdf` or `YYYY-XXXX.pdf`
- Validates year range (1900-2100)
- Returns `None` if pattern not found

#### `update_paper_years(paper_pdf_mapping: dict)`
- Updates Neo4j `year` property from filenames
- Only updates if `year` is NULL or 0
- Executes BEFORE pipeline to ensure temporal context

#### `create_temp_directory(paper_ids: Set[str]) -> Tuple[Path, Dict]`
- Creates `temp_missing_fields_pdfs/` directory
- Creates symlinks to source PDFs (preserves original files)
- Returns directory path and `paper_id → PDF_path` mapping

#### `run_pipeline(limit: int = None)`
- Main orchestration method
- Supports limiting number of papers (for testing)
- Initializes `HighPerformancePipeline` with:
  - `max_workers=10` (reduced for stability)
  - Progress tracking file
- Executes async pipeline
- Cleans up temporary directory

---

## Integration with High-Performance Pipeline

The script delegates actual extraction and ingestion to `HighPerformancePipeline`:

```python
pipeline = HighPerformancePipeline(
    max_workers=10,
    progress_file=Path("missing_fields_progress.json")
)

stats = await pipeline.run(
    base_dir=temp_dir,
    year_range=None,
    resume=False  # Don't skip already processed
)
```

**What the pipeline does:**
1. **Extraction**: GPT-4 Turbo with JSON mode (3 combined API calls)
2. **Normalization**: Embedding-based entity normalization
3. **Validation**: Pydantic models ensure data quality
4. **Ingestion**: Batched Neo4j operations (UNWIND clauses)

---

## Data Flow: What Gets Populated

### 1. Year (from filenames)
- **Source**: PDF filename pattern
- **Example**: `2010_353.pdf` → `year = 2010`
- **Update**: Direct Neo4j SET operation
- **Estimated**: 433+ papers

### 2. Authors
- **Extraction**: GPT-4 from PDF metadata
- **Fields**: `full_name`, `given_name`, `family_name`, `position`, `email`, `orcid`
- **Relationships**: `AUTHORED_BY` (Paper → Author)
- **Affiliations**: `Institution` nodes + `AFFILIATED_WITH` relationships
- **Estimated**: ~1,000+ authors for 1,029 papers

### 3. Titles
- **Extraction**: GPT-4 from PDF
- **Update**: `Paper.title` property
- **Estimated**: 433 papers currently missing

### 4. Theories
- **Extraction**: GPT-4 from paper content
- **Fields**: `name`, `role`, `domain`, `usage_context`, `key_constructs`, `assumptions`
- **Relationships**: `USES_THEORY` (Paper → Theory)
- **Estimated**: 451 papers missing

### 5. Methods
- **Extraction**: GPT-4 from methodology sections
- **Fields**: `name`, `type`, `data_sources`, `sample_size`, `time_period`, `software`
- **Relationships**: `USES_METHOD` (Paper → Method)
- **Estimated**: 733 papers missing

### 6. Phenomena
- **Extraction**: GPT-4 from paper content
- **Fields**: `phenomenon_name`, `phenomenon_type`, `domain`, `description`, `context`
- **Relationships**: `STUDIES_PHENOMENON` (Paper → Phenomenon) with `context` property
- **Estimated**: 555 papers missing

### 7. Research Questions
- **Extraction**: GPT-4 from paper content
- **Fields**: `question`, `question_type`, `section`, `domain`
- **Relationships**: `ADDRESSES` (Paper → ResearchQuestion)
- **Estimated**: 490 papers missing

### 8. Additional Entities
- **Findings**: `REPORTS` relationships (if nodes exist)
- **Contributions**: `MAKES` relationships (if nodes exist)
- **Variables**: `USES_VARIABLE` relationships
- **Software**: `USES_SOFTWARE` relationships
- **Datasets**: `USES_DATASET` relationships
- **Citations**: `CITES` relationships

---

## Execution Model

### Command-Line Usage

```bash
# Process all papers with missing data
python run_missing_fields_pipeline.py

# Process first 10 papers (for testing)
python run_missing_fields_pipeline.py 10
```

### Async Execution

The pipeline uses `asyncio` for concurrent processing:
- Multiple workers process PDFs in parallel
- Progress is tracked in `missing_fields_progress.json`
- Supports resume capability (though disabled by default)

---

## Error Handling & Robustness

1. **Missing PDFs**: Logged but doesn't stop pipeline
2. **Extraction Failures**: Individual paper failures don't stop batch
3. **Neo4j Connection**: Retry logic in `HighPerformancePipeline`
4. **Validation Errors**: Nodes created with fallback values
5. **Year Extraction**: Gracefully handles non-standard filenames

---

## Performance Characteristics

- **Batch Processing**: Processes papers in parallel (10 workers)
- **Symlinks**: Fast directory creation (no file copying)
- **Year Updates**: Single transaction per paper
- **Pipeline**: Optimized with batched Neo4j operations

---

## Dependencies

- `high_performance_pipeline.py`: Core extraction & ingestion
- `enhanced_gpt4_extractor.py`: GPT-4 extraction with JSON mode
- `embedding_normalizer.py`: Entity normalization
- `redesigned_methodology_extractor.py`: Neo4j ingestion
- `data_validator.py`: Pydantic validation models

---

## Success Criteria

After execution, the database should have:
- ✅ All papers with titles
- ✅ All papers with authors (and affiliations)
- ✅ All papers with years (from filenames)
- ✅ Increased coverage of theories, methods, phenomena
- ✅ Research questions for most papers
- ✅ Complete relationship graph

---

## Future Enhancements

1. **Incremental Updates**: Only process papers with new missing fields
2. **Priority Queue**: Process high-impact papers first
3. **Validation Reports**: Detailed gap analysis
4. **Progress Visualization**: Real-time dashboard
5. **Rollback Capability**: Undo changes if needed
