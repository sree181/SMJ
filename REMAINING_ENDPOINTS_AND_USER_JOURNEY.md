# Remaining Endpoints & End-to-End User Journey

## 🔍 Remaining 5 Endpoints

### 1. `GET /api/connections/theory-phenomenon/{theory_name}`
**Purpose**: Get all phenomena explained by a specific theory

**Why Needed**:
- When user clicks on a theory in Paper Detail → Show what phenomena it explains
- Theory Explorer screen → Show all phenomena for a theory
- Research question: "What phenomena does Resource-Based View explain?"

**Priority**: 🟡 **HIGH** - Core exploration feature

**Use Cases**:
- User viewing a theory wants to see what it explains
- Building theory-phenomenon network visualization
- Theory comparison (which theories explain same phenomena)

---

### 2. `GET /api/connections/phenomenon-theory/{phenomenon_name}`
**Purpose**: Get all theories explaining a specific phenomenon

**Why Needed**:
- When user clicks on a phenomenon → Show which theories explain it
- Phenomenon Explorer screen → Show all theories for a phenomenon
- Research question: "What theories explain resource allocation patterns?"

**Priority**: 🟡 **HIGH** - Core exploration feature

**Use Cases**:
- User viewing a phenomenon wants to see explaining theories
- Building phenomenon-theory network visualization
- Theory comparison (which theories explain same phenomenon)

---

### 3. `GET /api/phenomena/{phenomenon_name}`
**Purpose**: Get detailed information about a phenomenon

**Why Needed**:
- Phenomenon detail page → Full information about a phenomenon
- Show all papers studying it, all theories explaining it
- Statistics and metadata

**Priority**: 🟡 **MEDIUM** - Detail view feature

**Use Cases**:
- Deep dive into a specific phenomenon
- Understanding phenomenon context and domain
- Finding all related research

---

### 4. `GET /api/analytics/connection-strength-distribution`
**Purpose**: Get distribution of connection strengths

**Why Needed**:
- Analytics Dashboard → Show distribution chart
- Understanding overall connection quality
- Research insights: "Most connections are moderate strength"

**Priority**: 🟢 **LOW** - Analytics feature

**Use Cases**:
- Analytics dashboard visualization
- Quality assessment of connections
- Research insights

---

### 5. `GET /api/connections/{connection_id}/factors`
**Purpose**: Get detailed factor breakdown for a connection

**Why Needed**:
- Connection detail view → Show why connection got its strength
- Transparency: "Why is this connection 0.85?"
- Factor analysis and debugging

**Priority**: 🟢 **LOW** - Detail/transparency feature

**Use Cases**:
- Understanding connection strength calculation
- Debugging why connections are strong/weak
- Research transparency

---

## 🗺️ End-to-End User Journey

### Complete User Journey Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY FLOW                            │
└─────────────────────────────────────────────────────────────────┘

1. LANDING (Dashboard)
   ↓
2. EXPLORATION (Search/Query)
   ↓
3. DISCOVERY (Paper Detail)
   ↓
4. DEEP DIVE (Connections/Phenomena)
   ↓
5. ANALYSIS (Analytics/Temporal)
   ↓
6. INSIGHTS (Graph Explorer)
```

---

## 📱 Screen-by-Screen API Integration

### Screen 1: Dashboard (`/`)

**User Goal**: Get overview and quick access

**APIs Used**:
1. `GET /api/stats` ✅
   - **Purpose**: Show overview statistics
   - **Data**: Papers, theories, methods, authors counts
   - **UI**: Stats cards at top

2. `GET /api/analytics/top-connections?n=5&type=aggregated` ✅
   - **Purpose**: Show top 5 strongest connections
   - **Data**: Theory-Phenomenon connections with strength
   - **UI**: "Top Connections" card
   - **New Feature**: Highlights strongest research connections

3. `GET /api/phenomena?limit=5` ✅
   - **Purpose**: Show recent/trending phenomena
   - **Data**: List of phenomena with counts
   - **UI**: "Recent Phenomena" card
   - **New Feature**: Quick access to phenomena

**User Actions**:
- View stats → See overview
- Click "Top Connections" → Navigate to Connections Explorer
- Click "Recent Phenomena" → Navigate to Phenomena Explorer
- Enter search query → Navigate to Search Results

**API Flow**:
```
Dashboard Load
  ↓
GET /api/stats (parallel)
GET /api/analytics/top-connections (parallel)
GET /api/phenomena (parallel)
  ↓
Display cards
```

---

### Screen 2: Search Results (`/search?q=...`)

**User Goal**: Find papers, theories, methods, phenomena

**APIs Used**:
1. `POST /api/search` ✅
   - **Purpose**: Search papers by query
   - **Data**: Papers matching search term
   - **UI**: Paper cards in results list

2. `POST /api/query` ✅ (if question detected)
   - **Purpose**: Natural language query
   - **Data**: LLM-generated answer + source papers
   - **UI**: Query results with answer

3. `GET /api/connections/theory-phenomenon?search={query}&limit=5` ✅
   - **Purpose**: Show connections related to search
   - **Data**: Theory-Phenomenon connections
   - **UI**: "Related Connections" section
   - **New Feature**: Show connections in search context

**User Actions**:
- View search results → See papers
- Click paper → Navigate to Paper Detail
- View related connections → See Theory-Phenomenon links
- Click connection → Navigate to Connection Detail

**API Flow**:
```
User enters search query
  ↓
Detect if question or search term
  ↓
If question:
  POST /api/query → Show answer + sources
If search:
  POST /api/search → Show papers
  GET /api/connections/theory-phenomenon → Show related connections
  ↓
Display results
```

---

### Screen 3: Paper Detail (`/paper/:id`)

**User Goal**: Understand a specific paper in detail

**APIs Used**:
1. `GET /api/papers/{paper_id}` ✅
   - **Purpose**: Get full paper information
   - **Data**: Paper metadata, authors, theories, methods, etc.
   - **UI**: Paper detail tabs

2. `GET /api/connections/theory-phenomenon?paper_id={paper_id}` ✅
   - **Purpose**: Get Theory-Phenomenon connections for this paper
   - **Data**: Connections with strength and factor scores
   - **UI**: New tab "Theory-Phenomenon Connections"
   - **New Feature**: Show how theories explain phenomena in this paper

3. `GET /api/connections/theory-phenomenon/{theory_name}` ⏳
   - **Purpose**: When user clicks theory → Show all phenomena it explains
   - **Data**: All phenomena for this theory (across all papers)
   - **UI**: Modal or side panel
   - **New Feature**: Theory exploration

4. `GET /api/phenomena/{phenomenon_name}` ⏳
   - **Purpose**: When user clicks phenomenon → Show full details
   - **Data**: Phenomenon details, all explaining theories, all papers
   - **UI**: Modal or side panel
   - **New Feature**: Phenomenon exploration

**User Actions**:
- View paper details → See all information
- Click theory → See all phenomena it explains (across all papers)
- Click phenomenon → See all theories explaining it
- View connection strength → See factor breakdown
- Navigate to related papers → Explore further

**API Flow**:
```
Paper Detail Load
  ↓
GET /api/papers/{paper_id} (parallel)
GET /api/connections/theory-phenomenon?paper_id={paper_id} (parallel)
  ↓
Display paper info + connections tab
  ↓
User clicks theory:
  GET /api/connections/theory-phenomenon/{theory_name}
  ↓
Show phenomena modal
  ↓
User clicks phenomenon:
  GET /api/phenomena/{phenomenon_name}
  ↓
Show phenomenon detail modal
```

---

### Screen 4: Connections Explorer (`/connections`) - NEW

**User Goal**: Explore all Theory-Phenomenon connections

**APIs Used**:
1. `GET /api/connections/theory-phenomenon` ✅
   - **Purpose**: List all connections with filters
   - **Data**: Connections with strength, factors, papers
   - **UI**: Filterable table/list

2. `GET /api/connections/aggregated` ✅
   - **Purpose**: Show aggregated statistics
   - **Data**: Average strength, paper counts, etc.
   - **UI**: Aggregated view toggle

3. `GET /api/connections/{connection_id}/factors` ⏳
   - **Purpose**: Show factor breakdown when user clicks connection
   - **Data**: Detailed factor scores and explanations
   - **UI**: Detail panel or modal

4. `GET /api/analytics/connection-strength-distribution` ⏳
   - **Purpose**: Show distribution chart
   - **Data**: Distribution buckets and statistics
   - **UI**: Chart visualization

**User Actions**:
- Filter by theory → See connections for theory
- Filter by phenomenon → See connections for phenomenon
- Filter by strength range → See connections in range
- Sort by strength → See strongest/weakest
- Click connection → See factor breakdown
- View aggregated → See cross-paper statistics

**API Flow**:
```
Connections Explorer Load
  ↓
GET /api/connections/theory-phenomenon?limit=50
GET /api/analytics/connection-strength-distribution (parallel)
  ↓
Display connections list + distribution chart
  ↓
User applies filters:
  GET /api/connections/theory-phenomenon?{filters}
  ↓
Update list
  ↓
User clicks connection:
  GET /api/connections/{connection_id}/factors
  ↓
Show factor breakdown
```

---

### Screen 5: Phenomena Explorer (`/phenomena`) - NEW

**User Goal**: Explore all phenomena and their theories

**APIs Used**:
1. `GET /api/phenomena` ✅
   - **Purpose**: List all phenomena
   - **Data**: Phenomena with counts
   - **UI**: Phenomena list/grid

2. `GET /api/phenomena/{phenomenon_name}` ⏳
   - **Purpose**: Get detailed information about a phenomenon
   - **Data**: Phenomenon details, theories, papers, statistics
   - **UI**: Detail view

3. `GET /api/connections/phenomenon-theory/{phenomenon_name}` ⏳
   - **Purpose**: Get all theories explaining a phenomenon
   - **Data**: Theories with connection strengths
   - **UI**: Theories list with strengths

**User Actions**:
- Browse phenomena → See all phenomena
- Search phenomena → Filter by name/domain/type
- Click phenomenon → See details
- View explaining theories → See which theories explain it
- Click theory → Navigate to theory detail
- View papers → See all papers studying this phenomenon

**API Flow**:
```
Phenomena Explorer Load
  ↓
GET /api/phenomena?limit=100
  ↓
Display phenomena list
  ↓
User clicks phenomenon:
  GET /api/phenomena/{phenomenon_name} (parallel)
  GET /api/connections/phenomenon-theory/{phenomenon_name} (parallel)
  ↓
Show detail view with theories
```

---

### Screen 6: Query Results (`/query`)

**User Goal**: Ask natural language questions

**APIs Used**:
1. `POST /api/query` ✅
   - **Purpose**: Natural language query processing
   - **Data**: LLM-generated answer + source papers
   - **UI**: Answer display + source papers

2. `GET /api/connections/theory-phenomenon?theory_name={theory}` ✅
   - **Purpose**: If query mentions theory → Show connections
   - **Data**: Connections for that theory
   - **UI**: Related connections section
   - **New Feature**: Context-aware connections

**User Actions**:
- Enter question → Get answer
- View source papers → Navigate to papers
- View related connections → Explore connections
- Refine query → Ask follow-up

**API Flow**:
```
User enters question
  ↓
POST /api/query
  ↓
Extract entities (theories, phenomena) from answer
  ↓
GET /api/connections/theory-phenomenon?theory_name={extracted}
  ↓
Display answer + sources + related connections
```

---

### Screen 7: Analytics Dashboard (`/analytics`) - PLACEHOLDER

**User Goal**: Understand overall research landscape

**APIs Used**:
1. `GET /api/stats` ✅
   - **Purpose**: Overall statistics
   - **Data**: Counts of all entities

2. `GET /api/analytics/connection-strength-distribution` ⏳
   - **Purpose**: Connection strength distribution
   - **Data**: Distribution buckets and statistics
   - **UI**: Distribution chart

3. `GET /api/analytics/top-connections?n=20` ✅
   - **Purpose**: Top connections
   - **Data**: Top 20 connections
   - **UI**: Top connections list

4. `GET /api/connections/aggregated?sort_by=paper_count&limit=10` ✅
   - **Purpose**: Most studied connections
   - **Data**: Connections with most papers
   - **UI**: Most studied list

**User Actions**:
- View overall stats → See big picture
- View distribution → Understand connection quality
- View top connections → See strongest links
- View most studied → See popular connections

---

### Screen 8: Graph Explorer (`/graph`) - PLACEHOLDER

**User Goal**: Visualize knowledge graph

**APIs Used**:
1. `GET /api/graph` ✅
   - **Purpose**: Full graph data
   - **Data**: Nodes and edges

2. `GET /api/connections/theory-phenomenon` ✅
   - **Purpose**: Theory-Phenomenon connections for graph
   - **Data**: Connections as edges
   - **UI**: Graph edges with strength as weight
   - **New Feature**: Connection strength as edge thickness

3. `GET /api/connections/aggregated` ✅
   - **Purpose**: Aggregated connections for graph
   - **Data**: Aggregated edges
   - **UI**: Aggregated edges (thicker = more papers)

**User Actions**:
- View graph → See network
- Filter by strength → Show only strong connections
- Click node → See details
- Click edge → See connection details

---

## 🔄 Complete User Journey Examples

### Journey 1: "I want to understand Resource-Based View"

```
1. Dashboard
   User: Clicks "Top Connections" card
   API: GET /api/analytics/top-connections
   UI: Shows top connections

2. Connections Explorer
   User: Filters by theory "Resource-Based View"
   API: GET /api/connections/theory-phenomenon?theory_name=Resource-Based View
   UI: Shows all phenomena explained by RBV

3. Connection Detail
   User: Clicks on "RBV → Resource allocation" connection
   API: GET /api/connections/{connection_id}/factors
   UI: Shows factor breakdown (why strength is 0.85)

4. Paper Detail
   User: Clicks on a paper in connection
   API: GET /api/papers/{paper_id}
   API: GET /api/connections/theory-phenomenon?paper_id={paper_id}
   UI: Shows paper with connections tab

5. Phenomenon Detail
   User: Clicks on "Resource allocation patterns" phenomenon
   API: GET /api/phenomena/Resource allocation patterns
   API: GET /api/connections/phenomenon-theory/Resource allocation patterns
   UI: Shows all theories explaining this phenomenon
```

---

### Journey 2: "I'm researching resource allocation patterns"

```
1. Search
   User: Searches "resource allocation"
   API: POST /api/search?query=resource allocation
   UI: Shows papers

2. Phenomena Explorer
   User: Clicks "Explore Phenomena" button
   API: GET /api/phenomena?search=resource allocation
   UI: Shows matching phenomena

3. Phenomenon Detail
   User: Clicks "Resource allocation patterns"
   API: GET /api/phenomena/Resource allocation patterns
   API: GET /api/connections/phenomenon-theory/Resource allocation patterns
   UI: Shows all theories explaining it

4. Theory Comparison
   User: Compares theories (RBV vs Agency Theory)
   API: GET /api/connections/theory-phenomenon?theory_name=Resource-Based View
   API: GET /api/connections/theory-phenomenon?theory_name=Agency Theory
   UI: Side-by-side comparison

5. Paper Detail
   User: Clicks paper studying this phenomenon
   API: GET /api/papers/{paper_id}
   UI: Shows paper details
```

---

### Journey 3: "What are the strongest research connections?"

```
1. Dashboard
   User: Views "Top Connections" card
   API: GET /api/analytics/top-connections?n=5&type=aggregated
   UI: Shows top 5 connections

2. Analytics Dashboard
   User: Navigates to Analytics
   API: GET /api/analytics/connection-strength-distribution
   API: GET /api/analytics/top-connections?n=20
   UI: Shows distribution chart + top 20 list

3. Connections Explorer
   User: Filters by strength >= 0.8
   API: GET /api/connections/theory-phenomenon?min_strength=0.8
   UI: Shows only very strong connections

4. Connection Detail
   User: Clicks on connection
   API: GET /api/connections/{connection_id}/factors
   UI: Shows why it's strong (factor breakdown)

5. Aggregated View
   User: Toggles to aggregated view
   API: GET /api/connections/aggregated?min_paper_count=3
   UI: Shows cross-paper statistics
```

---

## 📊 API Usage Matrix

| Screen | Existing APIs | New APIs | Total APIs |
|--------|---------------|----------|------------|
| **Dashboard** | `/api/stats` | `/api/analytics/top-connections`, `/api/phenomena` | 3 |
| **Search Results** | `/api/search`, `/api/query` | `/api/connections/theory-phenomenon` | 3 |
| **Paper Detail** | `/api/papers/{id}` | `/api/connections/theory-phenomenon`, `/api/connections/theory-phenomenon/{theory}`, `/api/phenomena/{phenomenon}` | 4 |
| **Connections Explorer** | - | `/api/connections/theory-phenomenon`, `/api/connections/aggregated`, `/api/connections/{id}/factors`, `/api/analytics/connection-strength-distribution` | 4 |
| **Phenomena Explorer** | - | `/api/phenomena`, `/api/phenomena/{phenomenon}`, `/api/connections/phenomenon-theory/{phenomenon}` | 3 |
| **Query Results** | `/api/query` | `/api/connections/theory-phenomenon` | 2 |
| **Analytics** | `/api/stats` | `/api/analytics/connection-strength-distribution`, `/api/analytics/top-connections`, `/api/connections/aggregated` | 4 |
| **Graph Explorer** | `/api/graph` | `/api/connections/theory-phenomenon`, `/api/connections/aggregated` | 3 |

**Total Unique APIs**: 10
- **Existing**: 5 (`/api/stats`, `/api/search`, `/api/query`, `/api/papers/{id}`, `/api/graph`)
- **New (Implemented)**: 4 (`/api/connections/theory-phenomenon`, `/api/connections/aggregated`, `/api/phenomena`, `/api/analytics/top-connections`)
- **New (Pending)**: 5 (listed above)

---

## 🎯 Implementation Priority

### Phase 1: Core Exploration (HIGH Priority)
1. ✅ `GET /api/connections/theory-phenomenon` - DONE
2. ✅ `GET /api/connections/aggregated` - DONE
3. ⏳ `GET /api/connections/theory-phenomenon/{theory_name}` - NEEDED
4. ⏳ `GET /api/connections/phenomenon-theory/{phenomenon_name}` - NEEDED

**Why**: These enable core exploration features (theory → phenomena, phenomenon → theories)

---

### Phase 2: Detail Views (MEDIUM Priority)
5. ✅ `GET /api/phenomena` - DONE
6. ⏳ `GET /api/phenomena/{phenomenon_name}` - NEEDED

**Why**: Enables deep dive into specific phenomena

---

### Phase 3: Analytics & Transparency (LOW Priority)
7. ✅ `GET /api/analytics/top-connections` - DONE
8. ⏳ `GET /api/analytics/connection-strength-distribution` - NICE TO HAVE
9. ⏳ `GET /api/connections/{connection_id}/factors` - NICE TO HAVE

**Why**: Analytics and transparency features, not critical for core functionality

---

## 🔗 API Dependencies

### Critical Path APIs (Must Have)
```
Dashboard → /api/stats ✅
Search → /api/search ✅
Paper Detail → /api/papers/{id} ✅
Connections Explorer → /api/connections/theory-phenomenon ✅
Phenomena Explorer → /api/phenomena ✅
```

### Enhancement APIs (Nice to Have)
```
Paper Detail → /api/connections/theory-phenomenon/{theory} ⏳
Phenomena Explorer → /api/phenomena/{phenomenon} ⏳
Analytics → /api/analytics/connection-strength-distribution ⏳
Connection Detail → /api/connections/{id}/factors ⏳
```

---

## 📈 Scalability Considerations

### API Call Patterns

**Heavy Load Scenarios**:
1. Dashboard loads 3 APIs in parallel ✅ (handled)
2. Search loads 2 APIs in parallel ✅ (handled)
3. Paper Detail loads 2-4 APIs ⚠️ (needs optimization)

**Optimization Strategies**:
1. **Caching**: Cache aggregated data (1 hour TTL)
2. **Batching**: Combine related queries
3. **Lazy Loading**: Load connections on tab click
4. **Pagination**: All list endpoints paginated ✅

---

## 🎨 UI Integration Points

### Where New APIs Appear in UI

1. **Dashboard**:
   - Top Connections card → `/api/analytics/top-connections`
   - Recent Phenomena card → `/api/phenomena`

2. **Paper Detail**:
   - New tab "Connections" → `/api/connections/theory-phenomenon?paper_id={id}`
   - Theory click → `/api/connections/theory-phenomenon/{theory}`
   - Phenomenon click → `/api/phenomena/{phenomenon}`

3. **Search Results**:
   - Related Connections section → `/api/connections/theory-phenomenon?search={query}`

4. **New Screens**:
   - Connections Explorer → `/api/connections/theory-phenomenon` + filters
   - Phenomena Explorer → `/api/phenomena` + `/api/phenomena/{phenomenon}`

---

## ✅ Summary

### Remaining 5 Endpoints

1. **`GET /api/connections/theory-phenomenon/{theory_name}`** - HIGH Priority
   - Enables: Theory → Phenomena exploration
   - Used in: Paper Detail, Theory Explorer

2. **`GET /api/connections/phenomenon-theory/{phenomenon_name}`** - HIGH Priority
   - Enables: Phenomenon → Theories exploration
   - Used in: Paper Detail, Phenomena Explorer

3. **`GET /api/phenomena/{phenomenon_name}`** - MEDIUM Priority
   - Enables: Phenomenon detail view
   - Used in: Phenomena Explorer, Paper Detail

4. **`GET /api/analytics/connection-strength-distribution`** - LOW Priority
   - Enables: Distribution visualization
   - Used in: Analytics Dashboard

5. **`GET /api/connections/{connection_id}/factors`** - LOW Priority
   - Enables: Factor breakdown transparency
   - Used in: Connection Detail, Paper Detail

### End-to-End Integration

**All APIs work together** to create a seamless research journey:
- **Discovery** → Search/Query APIs
- **Exploration** → Connection/Phenomena APIs
- **Analysis** → Aggregated/Analytics APIs
- **Deep Dive** → Detail APIs

**User flows** are supported by multiple APIs working in parallel and sequence, creating a rich, interconnected research experience.

