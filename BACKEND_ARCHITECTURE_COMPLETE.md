# Backend Architecture & End-to-End System Overview

## 📋 Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Component Breakdown](#component-breakdown)
3. [Data Flow (End-to-End)](#data-flow-end-to-end)
4. [Extraction Pipeline](#extraction-pipeline)
5. [Neo4j Graph Structure](#neo4j-graph-structure)
6. [API Layer](#api-layer)
7. [LLM Integration](#llm-integration)
8. [Caching & Optimization](#caching--optimization)
9. [Error Handling & Resilience](#error-handling--resilience)
10. [Deployment & Operations](#deployment--operations)

---

## 🏗️ System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
│                    http://localhost:3000                         │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTP/REST API
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                    API SERVER (FastAPI)                           │
│                    http://localhost:5000                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  • REST Endpoints (14 endpoints)                          │   │
│  │  • Request Validation (Pydantic)                          │   │
│  │  • CORS Middleware                                         │   │
│  │  • Error Handling                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────┬──────────────────────────┬───────────────────────┘
               │                           │
               │                           │
    ┌──────────▼──────────┐    ┌──────────▼──────────┐
    │   Neo4j Database    │    │   OLLAMA LLM        │
    │   (Graph Database)   │    │   (Local LLM)        │
    │                      │    │                      │
    │  • Papers            │    │  • llama3.1:8b        │
    │  • Theories         │    │  • Extraction        │
    │  • Methods          │    │  • Query Answering   │
    │  • Phenomena        │    │                      │
    │  • Authors          │    │                      │
    │  • Relationships    │    │                      │
    └─────────────────────┘    └──────────────────────┘
```

### Technology Stack

**Backend Framework**: FastAPI (Python 3.9+)
**Database**: Neo4j (Graph Database)
**LLM**: OLLAMA (Local LLM - llama3.1:8b)
**PDF Processing**: PyMuPDF (fitz)
**Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
**Validation**: Pydantic v2
**Caching**: File-based LLM cache
**Connection Pooling**: Neo4j driver with connection pooling

---

## 🔧 Component Breakdown

### 1. API Server (`api_server.py`)

**Purpose**: Main FastAPI application serving REST endpoints

**Key Components**:

#### 1.1 Neo4jService Class
```python
class Neo4jService:
    - uri: Neo4j connection URI
    - user: Neo4j username
    - password: Neo4j password
    - driver: Neo4j driver instance
    
    Methods:
    - connect(): Establishes Neo4j connection
    - is_connected(): Health check
    - get_all_research_data(): Retrieves all data for LLM
    - get_graph_data_for_query(): Gets graph data for queries
    - close(): Closes connection
```

**Connection Management**:
- Initialized at startup
- Connection pooling (max 50 connections)
- Connection lifetime: 30 minutes
- Automatic reconnection on failure

#### 1.2 LLMClient Class
```python
class LLMClient:
    - api_key: OpenAI API key (optional)
    
    Methods:
    - generate_answer(): Generates LLM answer
    - _generate_fallback_answer(): Fallback if no API key
```

**LLM Integration**:
- Primary: OpenAI API (if key available)
- Fallback: Rule-based answers
- Used for `/api/query` endpoint

#### 1.3 API Endpoints (14 Total)

**Core Endpoints**:
1. `GET /api/health` - Health check
2. `POST /api/query` - Natural language query (LLM)
3. `GET /api/graph` - Full graph data
4. `GET /api/stats` - Statistics
5. `POST /api/search` - Search papers
6. `GET /api/papers/{paper_id}` - Paper details

**Connection Strength Endpoints**:
7. `GET /api/connections/theory-phenomenon` - List connections
8. `GET /api/connections/aggregated` - Aggregated statistics
9. `GET /api/phenomena` - List phenomena
10. `GET /api/analytics/top-connections` - Top connections
11. `GET /api/connections/theory-phenomenon/{theory_name}` - Phenomena for theory
12. `GET /api/connections/phenomenon-theory/{phenomenon_name}` - Theories for phenomenon
13. `GET /api/phenomena/{phenomenon_name}` - Phenomenon details
14. `GET /api/analytics/connection-strength-distribution` - Distribution stats
15. `GET /api/connections/{connection_id}/factors` - Factor breakdown

### 2. Extraction Pipeline (`redesigned_methodology_extractor.py`)

**Purpose**: Multi-stage extraction from PDFs to Neo4j

**Key Classes**:

#### 2.1 RedesignedOllamaExtractor
```python
class RedesignedOllamaExtractor:
    - base_url: OLLAMA server URL (default: http://localhost:11434)
    - model: LLM model (default: llama3.1:8b)
    - max_retries: 5
    - retry_delay: 5 seconds
    - timeout: 300 seconds
    
    Methods:
    - extract_paper_metadata(): Extract paper metadata
    - identify_methodology_section(): Find methodology section
    - extract_primary_methods(): Extract primary methods
    - extract_method_details(): Extract detailed method info
    - extract_theories(): Extract theories
    - extract_phenomena(): Extract phenomena
    - extract_with_retry(): Robust retry with caching
```

**Features**:
- **Caching**: LLM responses cached to avoid redundant calls
- **Retry Logic**: Exponential backoff for timeouts
- **Fallback Mechanisms**: Rule-based extraction if LLM fails
- **Prompt Standardization**: Uses `prompt_template.py`
- **Few-shot Examples**: Included in prompts

#### 2.2 RedesignedPDFProcessor
```python
class RedesignedPDFProcessor:
    Methods:
    - extract_text_from_pdf(): Extract text from PDF using PyMuPDF
```

**PDF Processing**:
- Uses PyMuPDF (fitz) for text extraction
- Handles multi-page PDFs
- Preserves text structure

#### 2.3 RedesignedNeo4jIngester
```python
class RedesignedNeo4jIngester:
    - driver: Neo4j driver
    - normalizer: EntityNormalizer instance
    - validator: DataValidator instance
    - conflict_resolver: ConflictResolver instance
    
    Methods:
    - ingest_paper_with_methods(): Main ingestion method
```

**Ingestion Features**:
- **Entity Normalization**: Prevents duplicate nodes
- **Data Validation**: Pydantic validation before ingestion
- **Transaction Management**: Atomic operations
- **Batch Writes**: Optimized performance
- **Relationship Creation**: Creates all relationships

### 3. Entity Normalization (`entity_normalizer.py`)

**Purpose**: Normalize entity names to canonical forms

**Key Class**:
```python
class EntityNormalizer:
    - theory_mappings: Dict of theory name variations
    - method_mappings: Dict of method name variations
    - software_mappings: Dict of software name variations
    
    Methods:
    - normalize_theory(): Normalize theory names
    - normalize_method(): Normalize method names
    - normalize_software(): Normalize software names
    - normalize_phenomenon(): Normalize phenomenon names
    - normalize_with_embeddings(): Hybrid normalization (string + embeddings)
```

**Normalization Strategy**:
1. **Exact Match**: Check mappings dictionary
2. **Fuzzy Match**: String similarity (SequenceMatcher)
3. **Embedding Match**: Semantic similarity (if enabled)
4. **Fallback**: Return cleaned name

### 4. Data Validation (`data_validator.py`)

**Purpose**: Validate extracted data using Pydantic models

**Key Models**:
```python
- TheoryData: Validates theory extraction
- MethodData: Validates method extraction
- VariableData: Validates variable extraction
- PhenomenonData: Validates phenomenon extraction
- ResearchQuestionData: Validates research question extraction
- FindingData: Validates finding extraction
- ContributionData: Validates contribution extraction
- SoftwareData: Validates software extraction
- DatasetData: Validates dataset extraction
```

**Validation Features**:
- Field type checking
- Range validation (e.g., confidence 0.0-1.0)
- Pattern matching (e.g., theory roles)
- Required vs optional fields

### 5. Connection Strength Calculator (`connection_strength_calculator.py`)

**Purpose**: Calculate connection strength between theories and phenomena

**Key Class**:
```python
class ConnectionStrengthCalculator:
    - use_embeddings: Whether to use semantic embeddings
    - embedding_model: SentenceTransformer model (if enabled)
    
    Methods:
    - calculate_strength(): Calculate connection strength (0.0-1.0)
    - should_create_connection(): Determine if connection should be created
```

**Mathematical Model**:
1. **Role Weight** (0.0-0.4): Theory role importance
2. **Section Score** (0.0-0.2): Section overlap
3. **Keyword Score** (0.0-0.2): Keyword overlap (Jaccard)
4. **Semantic Score** (0.0-0.2): Semantic similarity (cosine)
5. **Explicit Bonus** (0.0-0.1): Explicit mention bonus

**Total**: Sum of all factors (capped at 1.0)

### 6. Prompt Template System (`prompt_template.py`)

**Purpose**: Standardized prompts with few-shot examples

**Key Class**:
```python
class StandardizedPromptTemplate:
    - version: Prompt version (2.0)
    - examples: Few-shot examples per extraction type
    
    Methods:
    - get_prompt(): Get prompt for extraction type
    - _load_examples(): Load few-shot examples
```

**Extraction Types**:
- METADATA
- THEORY
- METHOD
- RESEARCH_QUESTION
- VARIABLE
- FINDING
- CONTRIBUTION
- SOFTWARE
- DATASET
- CITATION
- PHENOMENON

### 7. LLM Cache (`llm_cache.py`)

**Purpose**: Cache LLM responses to avoid redundant calls

**Key Class**:
```python
class LLMCache:
    - cache_dir: Cache directory (llm_cache/)
    
    Methods:
    - get(): Get cached response
    - set(): Cache response
    - _get_cache_key(): Generate cache key
```

**Caching Strategy**:
- Key: `hash(input_text + prompt_type + prompt_version)`
- Storage: JSON files in `llm_cache/` directory
- Invalidation: Based on prompt version

### 8. Conflict Resolver (`conflict_resolver.py`)

**Purpose**: Resolve conflicts in extracted data

**Key Class**:
```python
class ConflictResolver:
    Methods:
    - resolve(): Resolve conflicts
    - _merge_entities(): Merge duplicate entities
    - _prioritize_extraction(): Prioritize based on confidence
```

**Resolution Strategies**:
- MERGE: Merge duplicate entities
- PRIORITIZE: Choose highest confidence
- REJECT: Reject conflicting data

### 9. Batch Processor (`batch_process_complete_extraction.py`)

**Purpose**: Batch process multiple PDFs

**Key Class**:
```python
class BatchProcessor:
    - paper_dir: Directory containing PDFs
    - processor: RedesignedMethodologyProcessor
    - embedding_model: SentenceTransformer model
    - stats: Processing statistics
    
    Methods:
    - process_paper(): Process single paper
    - compute_paper_relationships(): Compute relationships
    - validate_extraction(): Validate extraction quality
    - _generate_paper_embedding(): Generate paper embeddings
```

**Batch Processing Features**:
- Progress tracking (JSON file)
- Error handling per paper
- Statistics collection
- Relationship computation
- Embedding generation

---

## 🔄 Data Flow (End-to-End)

### Flow 1: Paper Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. PDF Input                                                    │
│    /path/to/paper.pdf                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. PDF Text Extraction                                          │
│    RedesignedPDFProcessor.extract_text_from_pdf()               │
│    • PyMuPDF extracts text                                      │
│    • Returns full text string                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Multi-Stage LLM Extraction                                   │
│    RedesignedOllamaExtractor                                    │
│                                                                 │
│    Stage 1: Metadata Extraction                                │
│    ├─ extract_paper_metadata()                                 │
│    ├─ Check cache first                                        │
│    ├─ Call OLLAMA if not cached                                │
│    └─ Cache response                                           │
│                                                                 │
│    Stage 2: Methodology Section Identification                 │
│    ├─ identify_methodology_section()                           │
│    ├─ Fallback to keyword-based if LLM fails                   │
│    └─ Cache response                                           │
│                                                                 │
│    Stage 3: Primary Methods Extraction                         │
│    ├─ extract_primary_methods()                                │
│    └─ Cache response                                           │
│                                                                 │
│    Stage 4: Detailed Method Extraction                         │
│    ├─ extract_method_details()                                 │
│    └─ Cache response                                           │
│                                                                 │
│    Stage 5: Theory Extraction                                  │
│    ├─ extract_theories()                                       │
│    ├─ Stricter prompt with few-shot examples                   │
│    └─ Cache response                                           │
│                                                                 │
│    Stage 6: Phenomenon Extraction                               │
│    ├─ extract_phenomena()                                      │
│    └─ Cache response                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Data Validation                                             │
│    DataValidator                                               │
│    • Validate each extracted entity                            │
│    • Check field types, ranges, patterns                       │
│    • Return validated data or None                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Entity Normalization                                        │
│    EntityNormalizer                                            │
│    • Normalize theory names                                     │
│    • Normalize method names                                     │
│    • Normalize phenomenon names                                │
│    • Prevent duplicate nodes                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Conflict Resolution                                         │
│    ConflictResolver                                            │
│    • Resolve duplicate entities                                │
│    • Merge or prioritize based on strategy                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Connection Strength Calculation                             │
│    ConnectionStrengthCalculator                                │
│    • Calculate Theory-Phenomenon connections                   │
│    • 5-factor model: role, section, keyword, semantic, explicit │
│    • Return strength (0.0-1.0) and factor breakdown           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Neo4j Ingestion                                             │
│    RedesignedNeo4jIngester.ingest_paper_with_methods()         │
│                                                                 │
│    Transaction Start                                           │
│    ├─ Create Paper node                                        │
│    ├─ Create Author nodes + AUTHORED relationships             │
│    ├─ Create Theory nodes + USES_THEORY relationships          │
│    ├─ Create Method nodes + USES_METHOD relationships          │
│    ├─ Create Phenomenon nodes + STUDIES_PHENOMENON             │
│    ├─ Create Theory-Phenomenon connections                     │
│    │  └─ EXPLAINS_PHENOMENON with strength                    │
│    ├─ Create Author-Theory connections                         │
│    │  └─ USES_THEORY relationships                             │
│    ├─ Create Author-Phenomenon connections                    │
│    │  └─ STUDIES_PHENOMENON relationships                     │
│    └─ Transaction Commit                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Post-Ingestion Processing                                  │
│    BatchProcessor.compute_paper_relationships()                │
│    • USES_SAME_THEORY relationships                            │
│    • USES_SAME_METHOD relationships                            │
│    • USES_SAME_VARIABLES relationships                         │
│    • TEMPORAL_SEQUENCE relationships                           │
│                                                                 │
│    BatchProcessor._generate_paper_embedding()                  │
│    • Generate paper embedding                                   │
│    • Store in Paper node                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 2: API Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend Request                                                │
│ POST /api/search                                                │
│ Body: {query: "resource allocation"}                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ FastAPI Middleware                                             │
│ • CORS check                                                    │
│ • Request validation (Pydantic)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ API Endpoint Handler                                           │
│ @app.post("/api/search")                                        │
│ • Parse request                                                 │
│ • Validate query                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Neo4j Query Execution                                          │
│ neo4j_service.driver.session()                                 │
│ • Execute Cypher query                                          │
│ • Search papers, theories, methods                              │
│ • Return results                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Response Formatting                                            │
│ • Format results as JSON                                        │
│ • Add metadata (count, etc.)                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Frontend Response                                              │
│ {papers: [...], count: 10}                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Flow 3: LLM Query Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend Request                                                │
│ POST /api/query                                                 │
│ Body: {query: "What papers use Resource-Based View?"}          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ API Endpoint Handler                                           │
│ @app.post("/api/query")                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Neo4j Data Retrieval                                           │
│ neo4j_service.get_all_research_data()                          │
│ • Get all papers, theories, methods, etc.                      │
│ • Format for LLM context                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ LLM Answer Generation                                          │
│ LLMClient.generate_answer()                                     │
│ • Send query + context to OpenAI/OLLAMA                        │
│ • Generate answer                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ Response Formatting                                            │
│ {answer: "...", sources: [...]}                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Neo4j Graph Structure

### Node Types

#### 1. Paper Node
```cypher
(:Paper {
    paper_id: String (UNIQUE),
    title: String,
    abstract: String,
    publication_year: Integer,
    journal: String,
    keywords: List<String>,
    embedding: List<Float> (384-dim),
    doi: String,
    url: String
})
```

#### 2. Author Node
```cypher
(:Author {
    name: String,
    affiliation: String,
    email: String
})
```

#### 3. Theory Node
```cypher
(:Theory {
    name: String (UNIQUE, normalized),
    domain: String,
    description: String
})
```

#### 4. Method Node
```cypher
(:Method {
    name: String (UNIQUE, normalized),
    type: String (quantitative/qualitative/mixed),
    category: String,
    description: String
})
```

#### 5. Phenomenon Node
```cypher
(:Phenomenon {
    phenomenon_name: String (UNIQUE, normalized),
    phenomenon_type: String,
    domain: String,
    description: String,
    context: String
})
```

#### 6. ResearchQuestion Node
```cypher
(:ResearchQuestion {
    question_id: String (UNIQUE),
    question_text: String,
    type: String,
    section: String
})
```

#### 7. Variable Node
```cypher
(:Variable {
    variable_name: String (UNIQUE),
    variable_type: String,
    measurement: String
})
```

#### 8. Finding Node
```cypher
(:Finding {
    finding_id: String (UNIQUE),
    finding_text: String,
    significance: String,
    section: String
})
```

#### 9. Contribution Node
```cypher
(:Contribution {
    contribution_id: String (UNIQUE),
    contribution_text: String,
    type: String,
    section: String
})
```

#### 10. Software Node
```cypher
(:Software {
    name: String (UNIQUE, normalized),
    version: String,
    type: String
})
```

#### 11. Dataset Node
```cypher
(:Dataset {
    name: String (UNIQUE),
    source: String,
    type: String
})
```

#### 12. TimePeriod Node
```cypher
(:TimePeriod {
    period_id: String (UNIQUE),
    start_year: Integer,
    end_year: Integer,
    period_name: String
})
```

### Relationship Types

#### Paper Relationships
- `(Paper)-[:AUTHORED]->(Author)`
- `(Paper)-[:USES_THEORY {role, section, usage_context}]->(Theory)`
- `(Paper)-[:USES_METHOD {section, description}]->(Method)`
- `(Paper)-[:HAS_RESEARCH_QUESTION]->(ResearchQuestion)`
- `(Paper)-[:USES_VARIABLE]->(Variable)`
- `(Paper)-[:HAS_FINDING]->(Finding)`
- `(Paper)-[:HAS_CONTRIBUTION]->(Contribution)`
- `(Paper)-[:USES_SOFTWARE]->(Software)`
- `(Paper)-[:USES_DATASET]->(Dataset)`
- `(Paper)-[:STUDIES_PHENOMENON {section, context}]->(Phenomenon)`
- `(Paper)-[:CITES]->(Paper)`
- `(Paper)-[:BELONGS_TO_PERIOD]->(TimePeriod)`

#### Theory-Phenomenon Relationships
- `(Theory)-[:EXPLAINS_PHENOMENON {
    paper_id,
    theory_role,
    section,
    connection_strength,
    role_weight,
    section_score,
    keyword_score,
    semantic_score,
    explicit_bonus
}]->(Phenomenon)`

- `(Theory)-[:EXPLAINS_PHENOMENON_AGGREGATED {
    avg_strength,
    min_strength,
    max_strength,
    std_strength,
    paper_count,
    paper_ids,
    avg_role_weight,
    avg_section_score,
    avg_keyword_score,
    avg_semantic_score,
    avg_explicit_bonus
}]->(Phenomenon)`

#### Author Relationships
- `(Author)-[:USES_THEORY {
    paper_id,
    role,
    section,
    first_used_year,
    paper_count
}]->(Theory)`

- `(Author)-[:STUDIES_PHENOMENON {
    paper_id,
    section,
    context,
    first_studied_year,
    paper_count
}]->(Phenomenon)`

#### Paper-Paper Relationships
- `(Paper)-[:USES_SAME_THEORY {
    theory_name,
    temporal_gap
}]->(Paper)`

- `(Paper)-[:USES_SAME_METHOD {
    method_name,
    temporal_gap
}]->(Paper)`

- `(Paper)-[:USES_SAME_VARIABLES {
    variable_count,
    temporal_gap
}]->(Paper)`

- `(Paper)-[:TEMPORAL_SEQUENCE {
    time_gap
}]->(Paper)`

#### Temporal Evolution Relationships
- `(Theory)-[:EVOLVED_TO {
    from_period,
    to_period,
    usage_change,
    strength_change
}]->(Theory)`

- `(Method)-[:EVOLVED_TO {
    from_period,
    to_period,
    usage_change
}]->(Method)`

#### Similarity Relationships
- `(Theory)-[:SEMANTIC_SIMILARITY {
    similarity_score
}]->(Theory)`

- `(Method)-[:OFTEN_USED_WITH {
    co_occurrence_count
}]->(Method)`

- `(Theory)-[:COMMONLY_USED_WITH {
    co_occurrence_count
}]->(Theory)`

### Indexes and Constraints

#### Unique Constraints
```cypher
CREATE CONSTRAINT paper_id_unique IF NOT EXISTS 
FOR (p:Paper) REQUIRE p.paper_id IS UNIQUE;

CREATE CONSTRAINT theory_name_unique IF NOT EXISTS 
FOR (t:Theory) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT method_name_unique IF NOT EXISTS 
FOR (m:Method) REQUIRE m.name IS UNIQUE;

CREATE CONSTRAINT phenomenon_name_unique IF NOT EXISTS 
FOR (ph:Phenomenon) REQUIRE ph.phenomenon_name IS UNIQUE;
```

#### Range Indexes
```cypher
CREATE INDEX paper_year_index IF NOT EXISTS 
FOR (p:Paper) ON (p.publication_year);

CREATE INDEX theory_domain_index IF NOT EXISTS 
FOR (t:Theory) ON (t.domain);

CREATE INDEX method_type_index IF NOT EXISTS 
FOR (m:Method) ON (m.type);
```

#### Full-Text Indexes
```cypher
CREATE FULLTEXT INDEX paper_text_index IF NOT EXISTS 
FOR (p:Paper) ON EACH [p.title, p.abstract];

CREATE FULLTEXT INDEX theory_text_index IF NOT EXISTS 
FOR (t:Theory) ON EACH [t.name, t.description];
```

#### Vector Indexes
```cypher
CREATE VECTOR INDEX paper_embedding_index IF NOT EXISTS 
FOR (p:Paper) ON p.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }
};
```

---

## 🔌 API Layer

### Request/Response Models

#### QueryRequest
```python
class QueryRequest(BaseModel):
    query: str
```

#### QueryResponse
```python
class QueryResponse(BaseModel):
    answer: str
    graphData: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, Any]]] = None
    timestamp: str
```

#### HealthResponse
```python
class HealthResponse(BaseModel):
    status: str
    neo4j_connected: bool
    timestamp: str
```

### Endpoint Details

#### 1. Health Check
```python
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Returns: API status and Neo4j connection status
    """
```

#### 2. Search Papers
```python
@app.post("/api/search")
async def search_papers(request: QueryRequest):
    """
    Search papers by title, abstract, keywords, theory, or method
    Returns: List of matching papers with full details
    """
```

**Query Strategy**:
1. Search papers by theory (via `USES_THEORY` relationship)
2. Search papers by method (via `USES_METHOD` relationship)
3. Search papers by title/abstract/keywords
4. Union all results

#### 3. Natural Language Query
```python
@app.post("/api/query", response_model=QueryResponse)
async def query_graphrag(request: QueryRequest):
    """
    Natural language query using LLM
    Returns: LLM-generated answer + source papers
    """
```

**Process**:
1. Get all research data from Neo4j
2. Format as context for LLM
3. Send query + context to LLM
4. Generate answer
5. Return answer + sources

#### 4. Paper Details
```python
@app.get("/api/papers/{paper_id}")
async def get_paper_detail(paper_id: str):
    """
    Get detailed information about a paper
    Returns: Full paper details with all relationships
    """
```

#### 5. Connection Strength Endpoints
```python
# List connections
@app.get("/api/connections/theory-phenomenon")
async def get_connections(...)

# Aggregated statistics
@app.get("/api/connections/aggregated")
async def get_aggregated_connections(...)

# Phenomena list
@app.get("/api/phenomena")
async def get_phenomena(...)

# Top connections
@app.get("/api/analytics/top-connections")
async def get_top_connections(...)

# Phenomena for theory
@app.get("/api/connections/theory-phenomenon/{theory_name}")
async def get_phenomena_for_theory(...)

# Theories for phenomenon
@app.get("/api/connections/phenomenon-theory/{phenomenon_name}")
async def get_theories_for_phenomenon(...)

# Phenomenon details
@app.get("/api/phenomena/{phenomenon_name}")
async def get_phenomenon_detail(...)

# Connection strength distribution
@app.get("/api/analytics/connection-strength-distribution")
async def get_connection_strength_distribution(...)

# Factor breakdown
@app.get("/api/connections/{connection_id}/factors")
async def get_connection_factors(...)
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🤖 LLM Integration

### OLLAMA Integration

**Configuration**:
- Base URL: `http://localhost:11434`
- Model: `llama3.1:8b`
- Timeout: 300 seconds
- Max Retries: 5
- Retry Delay: 5 seconds (exponential backoff)

**API Calls**:
```python
POST http://localhost:11434/api/generate
Body: {
    "model": "llama3.1:8b",
    "prompt": "...",
    "stream": false,
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "max_tokens": 2000
    }
}
```

**Retry Logic**:
- Exponential backoff for timeouts
- Linear backoff for other errors
- Maximum 5 retries
- Caching to avoid redundant calls

### Prompt Structure

**Standardized Format**:
```
System: [Task description]
Context: [Few-shot examples]
Input: [Text to extract from]
Output: [Expected JSON format]
```

**Few-shot Examples**:
- Included in prompts for each extraction type
- Helps guide LLM behavior
- Reduces hallucinations

### Caching Strategy

**Cache Key Generation**:
```python
cache_key = hash(input_text + prompt_type + prompt_version)
```

**Cache Storage**:
- Directory: `llm_cache/`
- Format: JSON files
- Naming: `{cache_key}.json`

**Cache Invalidation**:
- Based on prompt version
- Manual cache clearing available

---

## ⚡ Caching & Optimization

### LLM Response Caching

**Purpose**: Avoid redundant LLM calls

**Implementation**:
- File-based cache in `llm_cache/` directory
- Key: Hash of input text + prompt type + version
- Storage: JSON files

**Benefits**:
- Faster extraction for repeated papers
- Reduced OLLAMA load
- Cost savings (if using paid LLM)

### Neo4j Connection Pooling

**Configuration**:
```python
GraphDatabase.driver(
    uri,
    auth=(user, password),
    max_connection_lifetime=30 * 60,  # 30 minutes
    max_connection_pool_size=50,
    connection_acquisition_timeout=60,
    connection_timeout=30
)
```

**Benefits**:
- Reuse connections
- Reduced connection overhead
- Better performance

### Batch Operations

**Neo4j Batch Writes**:
- Multiple operations in single transaction
- Atomic commits
- Rollback on error

**PDF Text Caching**:
- Cache extracted PDF text
- Avoid re-extraction for same PDF

### Index Optimization

**Indexes Created**:
- Range indexes on frequently queried fields
- Full-text indexes for search
- Vector indexes for similarity search

**Query Optimization**:
- Use indexes in WHERE clauses
- Limit result sets
- Use aggregation where possible

---

## 🛡️ Error Handling & Resilience

### LLM Error Handling

**Timeout Handling**:
- Exponential backoff retry
- Fallback to rule-based extraction
- Log timeout errors

**API Error Handling**:
- Retry on transient errors
- Fallback mechanisms
- Graceful degradation

### Neo4j Error Handling

**Connection Errors**:
- Automatic reconnection
- Connection health checks
- Graceful error messages

**Transaction Errors**:
- Automatic rollback
- Error logging
- Retry on transient errors

### Data Validation Errors

**Validation Failures**:
- Skip invalid entities
- Log validation errors
- Continue processing

**Normalization Errors**:
- Fallback to cleaned name
- Log normalization issues
- Continue processing

### Extraction Errors

**PDF Extraction Errors**:
- Skip corrupted PDFs
- Log errors
- Continue batch processing

**LLM Extraction Errors**:
- Fallback to rule-based
- Log errors
- Continue processing

---

## 🚀 Deployment & Operations

### Environment Variables

**Required**:
```bash
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
OPENAI_API_KEY=... (optional)
```

**Optional**:
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Startup Sequence

1. **Load Environment Variables**
   - Load from `.env` file
   - Validate required variables

2. **Initialize Neo4j Connection**
   - Create driver
   - Test connection
   - Log connection status

3. **Initialize FastAPI App**
   - Create app instance
   - Add CORS middleware
   - Register endpoints

4. **Start Server**
   - Run with uvicorn
   - Listen on port 5000
   - Enable auto-reload (dev)

### Monitoring

**Logging**:
- File: `batch_extraction.log`
- Console output
- Log levels: INFO, WARNING, ERROR

**Progress Tracking**:
- JSON file: `batch_extraction_progress.json`
- Statistics: `batch_extraction_results.json`

**Health Checks**:
- `/api/health` endpoint
- Neo4j connection status
- LLM availability

### Performance Considerations

**Neo4j**:
- Connection pooling (50 connections)
- Index usage
- Query optimization

**LLM**:
- Response caching
- Batch processing
- Retry logic

**API**:
- Async endpoints
- Connection pooling
- Response compression (if enabled)

---

## 📝 Summary

### Architecture Highlights

1. **Modular Design**: Separate components for extraction, validation, normalization, ingestion
2. **Robust Error Handling**: Retry logic, fallbacks, graceful degradation
3. **Performance Optimization**: Caching, connection pooling, batch operations
4. **Data Quality**: Validation, normalization, conflict resolution
5. **Scalability**: Connection pooling, async operations, batch processing

### Key Technologies

- **FastAPI**: Modern async web framework
- **Neo4j**: Graph database for relationships
- **OLLAMA**: Local LLM for extraction
- **PyMuPDF**: PDF text extraction
- **SentenceTransformers**: Embeddings for similarity
- **Pydantic**: Data validation

### Data Flow Summary

1. **PDF → Text**: PyMuPDF extraction
2. **Text → Entities**: Multi-stage LLM extraction
3. **Entities → Validated**: Pydantic validation
4. **Validated → Normalized**: Entity normalization
5. **Normalized → Graph**: Neo4j ingestion
6. **Graph → API**: REST endpoints
7. **API → Frontend**: JSON responses

### System Capabilities

- **Extraction**: Multi-stage LLM extraction from PDFs
- **Storage**: Neo4j graph database with relationships
- **Query**: Natural language queries with LLM
- **Search**: Multi-strategy search across entities
- **Analytics**: Connection strength, patterns, trends
- **Scalability**: Batch processing, caching, pooling

---

**This architecture provides a robust, scalable, and maintainable system for research paper extraction and knowledge graph construction.**

