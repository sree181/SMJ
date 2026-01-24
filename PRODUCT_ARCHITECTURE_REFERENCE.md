# Product Architecture Reference
## Theory-Centric Research Intelligence System

---

## 🎯 Product Positioning

**NOT**: Generic LLM search tool  
**IS**: Theory-Aware Cognitive Research Intelligence System

**Core Differentiation**: Theoretical strength and reasoning, not generic Q&A

---

## 🏗️ Existing Backend Architecture (DO NOT REDESIGN)

### Core Components (Already Implemented)

#### Database Layer
- **Neo4j Graph Database** with comprehensive schema:
  - **Nodes**: Paper, Author, Theory, Method, Phenomenon, ResearchQuestion, Variable, Finding, Contribution, Software, Dataset, TimePeriod
  - **Relationships**: 
    - Paper-level: AUTHORED, USES_THEORY, USES_METHOD, STUDIES_PHENOMENON, HAS_FINDING, HAS_CONTRIBUTION, USES_SOFTWARE, USES_DATASET, CITES, BELONGS_TO_PERIOD
    - Theory-Phenomenon: EXPLAINS_PHENOMENON, EXPLAINS_PHENOMENON_AGGREGATED (with connection_strength and factor breakdown)
    - Similarity/co-usage: SEMANTIC_SIMILARITY, COMMONLY_USED_WITH, USES_SAME_THEORY, USES_SAME_METHOD

#### Extraction Pipeline (Already Implemented)
- `RedesignedPDFProcessor` - PDF text extraction
- `RedesignedOllamaExtractor` - Multi-stage LLM extraction
- `RedesignedNeo4jIngester` - Graph ingestion
- `EntityNormalizer` - Entity name normalization
- `DataValidator` - Pydantic validation
- `ConnectionStrengthCalculator` - Theory-Phenomenon strength calculation
- `ConflictResolver` - Conflict resolution
- `BatchProcessor` - Batch processing
- `LLMCache` - Response caching
- `StandardizedPromptTemplate` - Prompt management

#### API Layer (Already Implemented)
- FastAPI backend at `http://localhost:5000`
- `Neo4jService` - Database connection management
- `LLMClient` - LLM integration (OLLAMA/OpenAI)

#### Existing Endpoints (DO NOT BREAK)
**Health & General**:
- `GET /api/health`
- `POST /api/query`
- `GET /api/graph`
- `GET /api/stats`

**Search & Details**:
- `POST /api/search` - Paper-centric search
- `GET /api/papers/{paper_id}` - Paper detail

**Connection & Analytics**:
- `GET /api/connections/theory-phenomenon`
- `GET /api/connections/aggregated`
- `GET /api/phenomena`
- `GET /api/analytics/top-connections`
- `GET /api/connections/theory-phenomenon/{theory_name}`
- `GET /api/connections/phenomenon-theory/{phenomenon_name}`
- `GET /api/phenomena/{phenomenon_name}`
- `GET /api/analytics/connection-strength-distribution`
- `GET /api/connections/{connection_id}/factors`

---

## 🚀 High-End Features to Implement

### 1. Theory Reasoning Engine

**Purpose**: Compare theories, identify compatibility/tension, suggest integrative frameworks

**Key Capabilities**:
- Compare theories (assumptions, constructs, typical phenomena, methods, levels of analysis)
- Identify compatibility vs tension between theories
- Suggest possible integrative conceptual frameworks
- Use graph data + LLM to explain "why" (co-usage patterns, semantic similarity, conflicting roles)

**Implementation Approach**:
- Backend: New endpoint `POST /api/theories/compare`
- Frontend: Theory comparison UI with side-by-side view
- LLM: Reasoning layer to explain compatibility/tension based on graph evidence

---

### 2. Contribution-Synthesis Engine

**Purpose**: Detect white spaces and contribution opportunities

**Key Capabilities**:
- Detect underexplored Theory–Phenomenon or Theory–Method combinations
- Identify rare or emerging constructs
- Generate potential contributions, gap statements, integration angles
- Use graph statistics (counts, co-occurrence, strength, sparsity) + LLM

**Implementation Approach**:
- Backend: New endpoint `GET /api/contributions/opportunities?query=...`
- Frontend: Contribution opportunity explorer
- LLM: Synthesize gap statements from graph statistics

---

### 3. Research Trajectory & Trend Forecasting

**Purpose**: Show past/current trends, forecast future directions

**Key Capabilities**:
- Show past and current trends using TimePeriod and EVOLVED_TO relationships
- Summarize shifts in theories, methods, and phenomena usage over time
- Use LLM to narrate: "Where the field has been" and "Where the field seems to be going"

**Implementation Approach**:
- Backend: New endpoint `GET /api/trends/{entity_type}/{entity_name}?period=...`
- Frontend: Trend timeline visualization
- LLM: Narrative generation from temporal patterns

---

### 4. Reasoning Personas

**Purpose**: Support different reasoning "modes" for LLM responses

**Key Capabilities**:
- Historian: Tracing theoretical genealogy and debates
- Reviewer #2: Critical, gap-finding, skeptical
- Advisor/Mentor: Constructive suggestions and next steps
- Industry Strategist: Translating research to practice
- Implement via LLM prompt conditioning; selectable in UI

**Implementation Approach**:
- Backend: Extend `/api/query` with `persona` parameter
- Frontend: Persona selector component
- LLM: Persona-specific system prompts

---

### 5. Conceptual Graph Simulation / Model Sandbox

**Purpose**: Let users build/edit conceptual models and check graph support

**Key Capabilities**:
- UI to build/edit conceptual model (Theories, Phenomena, Variables, directional relationships)
- Backend checks graph support (papers, findings) for each link
- Compute plausibility scores (based on existing connections and strength)
- LLM explains whether model is well-supported, under-supported, or contradictory
- Suggest moderators/mediators or missing constructs

**Implementation Approach**:
- Backend: New endpoint `POST /api/sandbox/validate`
- Frontend: Model editor with graph visualization
- LLM: Model validation and suggestion generation

---

### 6. Multi-Agent Debate (Optional Advanced)

**Purpose**: Simulate agents representing different theories or personas

**Key Capabilities**:
- Simulate "agents" representing different theories or personas
- Each uses graph-based evidence + LLM to argue
- System synthesizes convergence/divergence in final summary

**Implementation Approach**:
- Backend: New endpoint `POST /api/debate/start`
- Frontend: Debate visualization
- LLM: Multi-agent reasoning with graph grounding

---

### 7. Instant Research Blueprint

**Purpose**: Generate research blueprint from topic query

**Key Capabilities**:
- Given topic query (e.g., "psychological safety in AI-enabled teams")
- Output blueprint: candidate theories, common methods, typical variables, hypothesis patterns, potential contribution claims
- All grounded in Neo4j evidence; LLM used to structure and narrate

**Implementation Approach**:
- Backend: New endpoint `POST /api/research/blueprint`
- Frontend: Blueprint visualization UI
- LLM: Structure and narrate blueprint from graph data

---

### 8. Knowledge Reputation & Strength Metrics

**Purpose**: Compute and visualize knowledge metrics

**Key Capabilities**:
- Theory momentum (usage over time)
- Method obsolescence or adoption rate
- Phenomenon "hotness" (recent study volume and diversity)
- Evidence strength (average connection_strength, number of papers)
- Visualize and summarize for users

**Implementation Approach**:
- Backend: New endpoint `GET /api/metrics/{entity_type}/{entity_name}`
- Frontend: Metrics dashboard
- LLM: Summarize metrics in narrative form

---

## 🎨 Frontend Architecture

### Tech Stack
- **Framework**: React + TypeScript
- **Build Tool**: Next.js or Vite
- **Base URL**: `http://localhost:3000`

### Pages/Routes

```
/                          - Search landing (topic & question search)
/discover?query=...        - Search results + theory/phenomena/paper summary
/theory/:name              - Theory detail & reasoning engine
/phenomenon/:name          - Phenomenon detail
/compare                   - Theory comparison view
/sandbox                   - Conceptual model sandbox
/blueprint                 - Instant research blueprint UI
/trends                    - Trend analysis dashboard
/metrics                   - Knowledge reputation metrics
/debate                    - Multi-agent debate (optional)
```

### Core Components

**Search & Discovery**:
- `SearchBar` - Unified search input
- `SearchSummaryPanel` - Summary of search results
- `TheoryRankList` - Ranked list of theories
- `PhenomenonList` - List of phenomena
- `PaperList` - List of papers

**Theory Features**:
- `TheoryDetailView` - Theory detail page
- `TheoryComparisonView` - Side-by-side comparison
- `TheoryReasoningPanel` - LLM reasoning output

**Contribution & Gaps**:
- `ContributionOpportunityList` - List of opportunities
- `GapAnalysisPanel` - Gap visualization

**Trends & Metrics**:
- `TrendTimeline` - Temporal trend visualization
- `MetricsDashboard` - Knowledge metrics

**Advanced Features**:
- `PersonaSelector` - Select reasoning persona
- `ModelEditor` - Conceptual model builder
- `DebateView` - Multi-agent debate visualization
- `BlueprintView` - Research blueprint display

---

## 📡 API Design Patterns

### New Endpoint Pattern

**Aggregation Endpoints** (Pure Neo4j):
```python
@app.get("/api/discovery/search-summary")
async def get_search_summary(query: str):
    """
    Returns: summary counts, top theories, top phenomena, representative papers
    Uses: Neo4jService only, no LLM
    """
```

**LLM-Enhanced Endpoints**:
```python
@app.post("/api/research/blueprint")
async def generate_blueprint(request: BlueprintRequest):
    """
    Step 1: Query Neo4j for relevant entities
    Step 2: Build structured context object
    Step 3: Call LLM with context + task
    Returns: {reasoningText: str, supportingData: dict}
    """
```

### Response Structure

**Standard Response Format**:
```typescript
interface APIResponse<T> {
  data: T;
  reasoningText?: string;  // LLM narrative (if applicable)
  supportingData?: any;     // Graph-derived data used
  metadata?: {
    query?: string;
    timestamp: string;
    source: "neo4j" | "llm" | "both";
  };
}
```

---

## 🤖 LLM Usage Pattern

### Workflow Pattern

1. **Step 1**: Query Neo4j for all relevant entities, counts, and relationships
2. **Step 2**: Build a compact, structured context object
3. **Step 3**: Call LLM with:
   - **System prompt**: Define persona/mode + constraints
   - **Context**: JSON or text summary of Neo4j results
   - **User question**: Specific task (e.g., "compare these theories", "generate blueprint")
4. **Return**: Both `reasoningText` (LLM narrative) and `supportingData` (graph data)

### LLM Principles

- ✅ **DO**: Use LLM as reasoning + narrative layer
- ✅ **DO**: Ground all facts in Neo4j graph
- ✅ **DO**: Return both LLM output and source data
- ❌ **DON'T**: Let LLM hallucinate sources
- ❌ **DON'T**: Use LLM for raw data retrieval

---

## 📋 Implementation Protocol

### When Asked to Implement Feature X

1. **Restate the scope clearly**
   > "Implementing: Theory Reasoning Engine MVP – comparison endpoint + frontend comparison UI."

2. **Identify existing data & endpoints**
   - Which existing endpoints will be used?
   - Do we need a new aggregator endpoint?

3. **Outline the solution**
   - **Backend**: New FastAPI route(s), Cypher queries, LLM calls
   - **Frontend**: Pages, components, hooks

4. **Write concrete code**
   - Complete, compilable snippets (backend + frontend)
   - TypeScript interfaces for responses
   - Docstrings and inline comments
   - Explain: aggregation logic, LLM calls, custom metrics

5. **Keep product vision in mind**
   - Every feature should make the user **more theoretically intelligent**:
     - Better at picking theories
     - Better at framing phenomena
     - Better at designing contributions
     - Better at understanding trends and gaps

---

## 🎯 Product Vision Checklist

Every feature should:

- ✅ Ground LLM reasoning in structured graph
- ✅ Make users more theoretically intelligent
- ✅ Focus on theoretical strength, not just retrieval
- ✅ Build on existing backend (don't break it)
- ✅ Use LLM for reasoning/narrative, not raw facts
- ✅ Return both LLM output and source data
- ✅ Be composable and predictable

---

## 📚 TypeScript Interfaces (Frontend DTOs)

```typescript
// Theory-related
interface TheorySummary {
  name: string;
  domain: string;
  phenomenonCount: number;
  paperCount: number;
  avgConnectionStrength: number;
}

interface TheoryComparison {
  theories: TheorySummary[];
  compatibility: {
    score: number;
    reasoning: string;
  };
  tensions: Array<{
    theory1: string;
    theory2: string;
    reason: string;
  }>;
  integrativeFrameworks: string[];
}

// Contribution-related
interface ContributionOpportunity {
  type: "theory-phenomenon" | "theory-method" | "construct";
  description: string;
  evidence: {
    paperCount: number;
    connectionStrength?: number;
    sparsity: number;
  };
  potentialContribution: string;
  gapStatement: string;
}

// Trend-related
interface TrendPoint {
  period: string;
  usage: number;
  strength?: number;
  diversity?: number;
}

interface TrendAnalysis {
  entity: string;
  entityType: "theory" | "method" | "phenomenon";
  trends: TrendPoint[];
  narrative: string; // LLM-generated
  forecast: string; // LLM-generated
}

// Blueprint-related
interface ResearchBlueprint {
  topic: string;
  candidateTheories: TheorySummary[];
  commonMethods: Array<{
    name: string;
    usage: number;
  }>;
  typicalVariables: Array<{
    name: string;
    type: string;
  }>;
  hypothesisPatterns: string[];
  contributionClaims: string[];
  narrative: string; // LLM-generated
}

// Metrics-related
interface KnowledgeMetrics {
  entity: string;
  entityType: "theory" | "method" | "phenomenon";
  momentum: number; // Usage over time
  obsolescence?: number; // For methods
  hotness?: number; // For phenomena
  evidenceStrength: {
    avgConnectionStrength: number;
    paperCount: number;
    diversity: number;
  };
  narrative: string; // LLM-generated summary
}

// Persona-related
type PersonaMode = "historian" | "reviewer2" | "advisor" | "strategist";

interface PersonaResponse {
  persona: PersonaMode;
  reasoning: string;
  supportingData: any;
}
```

---

## 🔗 Key Relationships to Leverage

### For Theory Reasoning
- `EXPLAINS_PHENOMENON` - Which phenomena theories explain
- `COMMONLY_USED_WITH` - Theory co-usage patterns
- `SEMANTIC_SIMILARITY` - Similar theories
- `USES_SAME_THEORY` - Papers using same theories

### For Contribution Synthesis
- `EXPLAINS_PHENOMENON` with low `connection_strength` or low `paper_count` - Underexplored
- Missing `EXPLAINS_PHENOMENON` relationships - Gaps
- `USES_SAME_METHOD` - Method co-usage patterns

### For Trend Analysis
- `BELONGS_TO_PERIOD` - Temporal grouping
- `EVOLVED_TO` - Evolution relationships
- `USES_THEORY` with `publication_year` - Temporal usage
- `USES_METHOD` with `publication_year` - Method adoption

### For Metrics
- `EXPLAINS_PHENOMENON_AGGREGATED` - Aggregated strength metrics
- `USES_THEORY` with `paper_count` - Theory momentum
- `STUDIES_PHENOMENON` with `publication_year` - Phenomenon hotness

---

## ✅ Implementation Checklist Template

When implementing a new feature:

- [ ] **Backend**:
  - [ ] New endpoint(s) defined
  - [ ] Cypher queries written and tested
  - [ ] LLM integration (if needed) with proper context
  - [ ] Response models defined
  - [ ] Error handling implemented

- [ ] **Frontend**:
  - [ ] TypeScript interfaces defined
  - [ ] API service methods added
  - [ ] Components created
  - [ ] Pages/routes added
  - [ ] UI/UX polished

- [ ] **Documentation**:
  - [ ] Endpoint documented
  - [ ] Usage examples provided
  - [ ] Architecture notes updated

- [ ] **Testing**:
  - [ ] Backend endpoint tested
  - [ ] Frontend integration tested
  - [ ] LLM output validated (if applicable)

---

## 🎓 Product Intelligence Goals

Every feature should help users become:

1. **Better at picking theories**: Understand compatibility, tension, integration opportunities
2. **Better at framing phenomena**: Know which theories explain which phenomena, identify gaps
3. **Better at designing contributions**: Find white spaces, suggest integrative angles
4. **Better at understanding trends**: See where field has been, where it's going
5. **Better at model building**: Validate conceptual models against graph evidence
6. **Better at research planning**: Generate blueprints grounded in existing knowledge

---

**This document serves as the reference for all future feature implementations.**

