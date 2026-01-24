# Architecture Flow Documentation
## How New Components Fit Into the System

This document explains how the recently enhanced components work together in the complete system architecture.

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    PDF Papers (836 papers)                       │
└───────────────────────────┬─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              BATCH PROCESSING LAYER                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │ batch_process_       │  │ async_pipeline.py           │    │
│  │ complete_extraction  │  │ (Alternative async pipeline)│    │
│  │ .py                  │  │                              │    │
│  └──────────┬───────────┘  └──────────────┬───────────────┘    │
│             │                              │                    │
│             └──────────┬───────────────────┘                    │
│                        │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              EXTRACTION LAYER                                    │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │ RedesignedMethodology│  │ EnhancedGPT4Extractor        │    │
│  │ Processor            │  │ (Alternative GPT-4 extractor)│    │
│  │                      │  │                              │    │
│  │ Uses:                │  │ Uses:                        │    │
│  │ - RedesignedOllama   │  │ - GPT-4 Turbo                │    │
│  │   Extractor          │  │ - JSON mode                  │    │
│  │ - RedesignedPDF      │  │ - Structured schemas         │    │
│  │   Processor          │  │                              │    │
│  └──────────┬───────────┘  └──────────────┬───────────────┘    │
│             │                              │                    │
│             └──────────┬───────────────────┘                    │
│                        │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              NORMALIZATION LAYER                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │ EntityNormalizer     │  │ EmbeddingNormalizer          │    │
│  │ (String-based)       │  │ (Semantic similarity)        │    │
│  │                      │  │                              │    │
│  │ - Dictionary lookup  │  │ - Embedding-based matching  │    │
│  │ - String similarity  │  │ - Continuous learning        │    │
│  │ - Rule-based         │  │ - Higher accuracy            │    │
│  └──────────┬───────────┘  └──────────────┬───────────────┘    │
│             │                              │                    │
│             └──────────┬───────────────────┘                    │
│                        │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              INGESTION LAYER                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ RedesignedNeo4jIngester                                  │   │
│  │                                                           │   │
│  │ - Entity normalization (via EntityNormalizer)            │   │
│  │ - Data validation (via DataValidator)                    │   │
│  │ - Transaction management                                 │   │
│  │ - Batch writes                                           │   │
│  │ - Relationship creation                                  │   │
│  └───────────────────────┬───────────────────────────────────┘   │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NEO4J DATABASE                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Nodes: Paper, Theory, Method, Phenomenon, Author, etc.    │   │
│  │ Relationships: USES_THEORY, USES_METHOD, etc.           │   │
│  └───────────────────────┬───────────────────────────────────┘   │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              API LAYER (FastAPI)                                 │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │ api_server.py        │  │ research_analytics_         │    │
│  │ (Main API)           │  │ endpoints.py                 │    │
│  │                      │  │ (Analytics endpoints)        │    │
│  │ - Query endpoints    │  │                              │    │
│  │ - Metrics endpoints  │  │ - Fragmentation analysis     │    │
│  │ - Theory comparison  │  │ - Methodology evolution      │    │
│  │ - Trend analysis     │  │ - Author metrics            │    │
│  │ - Uses EntityNormalizer│ │ - Descriptive statistics    │    │
│  └──────────────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Detailed Component Flow

### 1. **Batch Processing Layer**

#### `batch_process_complete_extraction.py`
**Purpose**: Orchestrates batch processing of multiple PDF papers

**Flow**:
```
1. Discovers PDF files in specified folder
2. Loads progress file (resume capability)
3. For each PDF:
   a. Checks if already processed (skip if yes)
   b. Calls RedesignedMethodologyProcessor.process_paper()
   c. Validates extraction results
   d. Saves progress after each paper
   e. Computes paper-to-paper relationships
4. Generates final statistics and saves results
```

**Key Features**:
- Progress tracking (resume from where it left off)
- Error handling and retry logic
- Relationship computation after ingestion
- Paper embedding generation

**Dependencies**:
- `RedesignedMethodologyProcessor` (from `redesigned_methodology_extractor.py`)
- Neo4j driver (for relationship computation)
- SentenceTransformer (for embeddings)

---

#### `async_pipeline.py` (Alternative)
**Purpose**: High-performance async processing pipeline

**Flow**:
```
1. Discovers papers
2. Creates PaperTask objects
3. Distributes tasks to worker pool (async)
4. Each worker:
   a. Extracts paper data
   b. Normalizes entities
   c. Ingests to Neo4j
5. Monitors progress and handles failures
```

**Key Features**:
- Async/await for concurrent processing
- Worker pool (configurable workers)
- Redis support for distributed processing
- Better performance for large batches

**Dependencies**:
- `RedesignedMethodologyProcessor`
- Async Neo4j operations
- Optional Redis for distributed processing

---

### 2. **Extraction Layer**

#### `RedesignedMethodologyProcessor` (from `redesigned_methodology_extractor.py`)
**Purpose**: Main orchestrator for paper extraction

**Flow**:
```
1. Extract text from PDF (RedesignedPDFProcessor)
2. Extract metadata (RedesignedOllamaExtractor)
3. Identify methodology section
4. Extract primary methods
5. Extract detailed method information
6. Extract theories, phenomena, variables, findings, etc.
7. Call RedesignedNeo4jIngester to ingest all data
```

**Components Used**:
- `RedesignedOllamaExtractor`: LLM-based extraction
- `RedesignedPDFProcessor`: PDF text extraction
- `RedesignedNeo4jIngester`: Data ingestion

**Key Features**:
- Multi-stage extraction (section → methods → details)
- Retry logic with exponential backoff
- Caching of LLM responses
- Fallback mechanisms

---

#### `RedesignedOllamaExtractor` (from `redesigned_methodology_extractor.py`)
**Purpose**: LLM-based entity extraction using OLLAMA

**Flow**:
```
1. Receives text and extraction type
2. Builds prompt with few-shot examples
3. Calls OLLAMA API with retry logic
4. Parses JSON response
5. Validates extracted entities
6. Returns structured data
```

**Key Features**:
- Connection testing
- Retry with exponential backoff
- Response caching
- Timeout handling
- Fallback extraction methods

---

#### `EnhancedGPT4Extractor` (from `enhanced_gpt4_extractor.py`)
**Purpose**: Alternative extractor using GPT-4 Turbo

**Flow**:
```
1. Extract text from PDF
2. Build structured JSON schema
3. Call GPT-4 Turbo with JSON mode
4. Parse and validate response
5. Normalize entities
6. Return ExtractionResult
```

**Key Features**:
- GPT-4 Turbo with JSON mode
- Comprehensive schemas
- Async support
- Batch processing
- Entity normalization integration

**When to Use**:
- Higher accuracy needed
- OpenAI API available
- Budget allows for GPT-4 costs

---

### 3. **Normalization Layer**

#### `EntityNormalizer` (from `entity_normalizer.py`)
**Purpose**: String-based entity normalization

**Flow**:
```
1. Receives entity name and type
2. Cleans name (whitespace, punctuation)
3. Checks dictionary mappings:
   - Exact match → return canonical name
   - Partial match → return canonical name
4. If no match, uses string similarity (SequenceMatcher)
5. Returns normalized canonical name
```

**Normalization Rules**:
- **Theories**: "RBV" → "Resource-Based View", "Dynamic Capabilities Theory" → "Dynamic Capabilities Theory"
- **Methods**: "OLS" → "Ordinary Least Squares", "Fixed Effects" → "Fixed Effects Regression"
- **Software**: "stata" → "Stata", "r studio" → "R"
- **Phenomena**: Conservative normalization (preserves specificity)

**Key Features**:
- Comprehensive dictionary mappings
- String similarity matching
- Title case normalization
- Acronym preservation
- Optional embedding support

**Usage**:
```python
from entity_normalizer import get_normalizer
normalizer = get_normalizer()
canonical = normalizer.normalize_theory("RBV")  # → "Resource-Based View"
```

---

#### `EmbeddingNormalizer` (from `embedding_normalizer.py`)
**Purpose**: Semantic similarity-based normalization using embeddings

**Flow**:
```
1. Builds canonical entity database with embeddings
2. Receives entity name
3. Generates embedding for input
4. Computes cosine similarity with all canonical entities
5. If similarity > threshold → return canonical name
6. Otherwise → return cleaned original (new entity)
```

**Key Features**:
- Embedding-based similarity (semantic matching)
- Continuous learning (can add new canonical entities)
- Higher accuracy for unknown variations
- Caching of embeddings
- Export/import canonical database

**When to Use**:
- Unknown entity variations
- Need semantic matching (not just string)
- Higher accuracy requirements
- Can afford embedding computation cost

**Usage**:
```python
from embedding_normalizer import get_embedding_normalizer
normalizer = get_embedding_normalizer()
result = normalizer.normalize("resource based view", "Theory")
# Returns: NormalizationResult with canonical name and confidence
```

---

### 4. **Ingestion Layer**

#### `RedesignedNeo4jIngester` (from `redesigned_methodology_extractor.py`)
**Purpose**: Graph-optimized Neo4j ingestion with normalization and validation

**Flow**:
```
1. Receives extracted data (paper, methods, theories, etc.)
2. For each entity:
   a. Normalize name (EntityNormalizer)
   b. Validate data (DataValidator)
   c. Resolve conflicts (ConflictResolver)
3. Begin Neo4j transaction
4. Create/Merge nodes:
   - Paper node
   - Theory nodes (normalized)
   - Method nodes (normalized)
   - Phenomenon nodes (normalized)
   - Author nodes
   - Variable nodes
   - Finding nodes
   - etc.
5. Create relationships:
   - Paper → Theory (USES_THEORY)
   - Paper → Method (USES_METHOD)
   - Paper → Phenomenon (STUDIES)
   - Paper → Author (AUTHORED)
   - etc.
6. Commit transaction (or rollback on error)
```

**Key Features**:
- **Entity Normalization**: Prevents duplicates
- **Data Validation**: Ensures data quality
- **Transaction Management**: Atomic operations
- **Batch Writes**: Optimized performance
- **Relationship Creation**: Complete graph structure

**Integration Points**:
- Uses `EntityNormalizer` for all entity names
- Uses `DataValidator` for data validation
- Uses `ConflictResolver` for conflict resolution

---

### 5. **API Layer**

#### `api_server.py`
**Purpose**: Main FastAPI server with query and analytics endpoints

**Key Endpoints**:
- `POST /api/query` - Natural language queries with persona support
- `GET /api/metrics/{entity_type}/{entity_name}` - Knowledge metrics
- `POST /api/theories/compare` - Theory comparison
- `GET /api/theories/{theory_name}/context` - Theory context
- `GET /api/contributions/opportunities` - Research opportunities
- `GET /api/trends/{entity_type}/{entity_name}` - Temporal trends

**Entity Normalization Usage**:
```python
# In metrics endpoint
from entity_normalizer import get_normalizer
normalizer = get_normalizer()
normalized_name = normalizer.normalize_theory(theory_name)

# In theory comparison
normalized_theories = [normalizer.normalize_theory(t) for t in theories]

# In trend analysis
normalized_name = normalizer.normalize_method(method_name)
```

**Flow**:
```
1. Receives API request
2. Normalizes entity names (if needed)
3. Queries Neo4j
4. Processes results
5. Generates LLM narratives (if needed)
6. Returns JSON response
```

---

#### `research_analytics_endpoints.py`
**Purpose**: Advanced analytics endpoints

**Key Endpoints**:
- `GET /api/analytics/fragmentation/{period}` - Topical fragmentation
- `GET /api/analytics/theory-phenomena` - Theory-phenomenon mappings
- `GET /api/analytics/methodology-evolution/{period}` - Method evolution
- `GET /api/analytics/authors/top` - Top authors
- `GET /api/analytics/statistics/{period}` - Descriptive statistics

**Flow**:
```
1. Receives analytics request
2. Queries Neo4j with complex Cypher queries
3. Computes metrics (Gini coefficients, ratios, etc.)
4. Aggregates data by period
5. Returns structured analytics
```

---

## 🔄 Complete Data Flow Example

### Example: Processing a Single Paper

```
1. User runs: python batch_process_complete_extraction.py 2020-2024

2. BatchProcessor discovers PDF: "2020_1103.pdf"

3. BatchProcessor calls:
   processor = RedesignedMethodologyProcessor()
   result = processor.process_paper(pdf_path)

4. RedesignedMethodologyProcessor:
   a. Extracts text: pdf_processor.extract_text_from_pdf()
   b. Extracts metadata: extractor.extract_paper_metadata()
   c. Extracts theories: extractor.extract_theories()
   d. Extracts methods: extractor.extract_primary_methods()
   e. Extracts phenomena: extractor.extract_phenomena()
   f. Calls ingester: ingester.ingest_paper_with_methods(...)

5. RedesignedNeo4jIngester:
   a. Normalizes theory "RBV" → "Resource-Based View" (EntityNormalizer)
   b. Normalizes method "OLS" → "Ordinary Least Squares" (EntityNormalizer)
   c. Validates data (DataValidator)
   d. Creates Paper node
   e. Creates/Merges Theory node ("Resource-Based View")
   f. Creates/Merges Method node ("Ordinary Least Squares")
   g. Creates relationships:
      - (Paper)-[:USES_THEORY]->(Theory)
      - (Paper)-[:USES_METHOD]->(Method)
   h. Commits transaction

6. BatchProcessor:
   a. Validates extraction results
   b. Computes paper-to-paper relationships
   c. Saves progress to batch_extraction_progress.json
   d. Moves to next paper

7. User queries API:
   GET /api/metrics/theory/Resource-Based View
   
8. API Server:
   a. Normalizes input (if needed)
   b. Queries Neo4j for metrics
   c. Generates LLM narrative
   d. Returns response
```

---

## 🔗 Component Dependencies

```
batch_process_complete_extraction.py
    └──> RedesignedMethodologyProcessor
            ├──> RedesignedOllamaExtractor
            ├──> RedesignedPDFProcessor
            └──> RedesignedNeo4jIngester
                    ├──> EntityNormalizer
                    ├──> DataValidator
                    └──> ConflictResolver

async_pipeline.py
    └──> RedesignedMethodologyProcessor
            (same as above)

api_server.py
    ├──> EntityNormalizer (for normalization)
    ├──> Neo4jService (for queries)
    └──> LLMClient (for narratives)

research_analytics_endpoints.py
    └──> Neo4jService (for complex queries)

EnhancedGPT4Extractor
    └──> EntityNormalizer (for normalization)
```

---

## 🎯 Key Design Decisions

### 1. **Why Two Normalizers?**
- **EntityNormalizer**: Fast, dictionary-based, good for known entities
- **EmbeddingNormalizer**: Slower but more accurate, handles unknown variations
- **Hybrid Approach**: Use EntityNormalizer first, EmbeddingNormalizer for unknowns

### 2. **Why Two Extractors?**
- **RedesignedOllamaExtractor**: Free, local, good for batch processing
- **EnhancedGPT4Extractor**: Paid, cloud-based, higher accuracy
- **Choice**: Based on budget, accuracy needs, and availability

### 3. **Why Two Batch Processors?**
- **batch_process_complete_extraction.py**: Simple, synchronous, easy to debug
- **async_pipeline.py**: Fast, concurrent, better for large batches
- **Choice**: Use async for large batches, sync for small/test batches

### 4. **Normalization Strategy**
- **During Ingestion**: All entities normalized before MERGE
- **During Queries**: Input normalized before querying
- **Result**: Consistent canonical names throughout system

---

## 📝 Integration Checklist

When adding new features:

- [ ] Use `EntityNormalizer` for all entity names
- [ ] Validate data before ingestion
- [ ] Use transactions for atomic operations
- [ ] Normalize API inputs
- [ ] Handle errors gracefully
- [ ] Log important operations
- [ ] Update progress tracking

---

## 🚀 Next Steps for Ingestion

Based on the current architecture:

1. **Start Batch Processing**:
   ```bash
   python batch_process_complete_extraction.py 2025-2029
   ```

2. **Monitor Progress**:
   - Check `batch_extraction_progress.json`
   - View `batch_extraction.log`
   - Query Neo4j to verify ingestion

3. **Scale Up**:
   - Process larger folders
   - Use `async_pipeline.py` for better performance
   - Consider `EnhancedGPT4Extractor` for higher accuracy

4. **Verify Normalization**:
   - Check Neo4j for duplicate entities
   - Verify canonical names are used
   - Test API endpoints with various entity name formats

---

## 📚 Related Documentation

- `INGESTION_RESUME_GUIDE.md` - How to resume ingestion
- `BACKEND_ARCHITECTURE_COMPLETE.md` - Detailed backend architecture
- `CRITICAL_FIXES_COMPLETE.md` - Normalization implementation details
- `API_DESIGN_SCALABILITY.md` - API design with normalization
