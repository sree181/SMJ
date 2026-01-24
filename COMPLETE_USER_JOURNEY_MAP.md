# Complete User Journey Map - End-to-End Integration

## 🎯 Product Vision

A comprehensive research assistant that helps researchers:
1. **Discover** relevant papers and connections
2. **Explore** theories, phenomena, and their relationships
3. **Analyze** patterns and trends
4. **Understand** how theories explain phenomena

---

## 🗺️ Complete User Journey Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLETE USER JOURNEY                             │
└─────────────────────────────────────────────────────────────────────┘

START: User opens application
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 1: DASHBOARD (/)                                              │
│ Goal: Get overview and quick access                                  │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: GET /api/stats
  │   └─> Shows: Papers, Theories, Methods, Authors counts
  │
  ├─ API: GET /api/analytics/top-connections?n=5
  │   └─> Shows: Top 5 strongest Theory-Phenomenon connections
  │
  └─ API: GET /api/phenomena?limit=5
      └─> Shows: Recent/Trending phenomena
  │
  ↓ User Action: Enters search query OR clicks a card
  │
  ├─> Navigate to Search Results (/search)
  ├─> Navigate to Connections Explorer (/connections)
  ├─> Navigate to Phenomena Explorer (/phenomena)
  └─> Navigate to Analytics (/analytics)
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 2: SEARCH RESULTS (/search?q=...)                             │
│ Goal: Find papers, theories, methods, phenomena                     │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: POST /api/search?query={query}
  │   └─> Returns: Papers matching search
  │   └─> UI: Paper cards with theories, methods
  │
  ├─ API: POST /api/query?query={question} (if question detected)
  │   └─> Returns: LLM answer + source papers
  │   └─> UI: Answer display + source papers
  │
  └─ API: GET /api/connections/theory-phenomenon?search={query}
      └─> Returns: Related Theory-Phenomenon connections
      └─> UI: "Related Connections" section
  │
  ↓ User Action: Clicks on paper OR connection
  │
  ├─> Navigate to Paper Detail (/paper/:id)
  └─> Navigate to Connection Detail (modal)
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 3: PAPER DETAIL (/paper/:id)                                  │
│ Goal: Understand a specific paper in detail                         │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: GET /api/papers/{paper_id}
  │   └─> Returns: Full paper information
  │   └─> UI: Overview, Theories, Methods, Questions tabs
  │
  ├─ API: GET /api/connections/theory-phenomenon?paper_id={paper_id}
  │   └─> Returns: Theory-Phenomenon connections for this paper
  │   └─> UI: New "Connections" tab with strength scores
  │
  ├─ API: GET /api/connections/theory-phenomenon/{theory_name} ⏳
  │   └─> Trigger: User clicks on a theory
  │   └─> Returns: All phenomena explained by this theory (all papers)
  │   └─> UI: Modal showing theory's phenomena
  │
  └─ API: GET /api/phenomena/{phenomenon_name} ⏳
      └─> Trigger: User clicks on a phenomenon
      └─> Returns: Full phenomenon details + all explaining theories
      └─> UI: Modal showing phenomenon details
  │
  ↓ User Action: Clicks theory/phenomenon OR navigates
  │
  ├─> Show theory modal (all phenomena)
  ├─> Show phenomenon modal (all theories)
  ├─> Navigate to Connections Explorer
  └─> Navigate to Phenomena Explorer
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 4: CONNECTIONS EXPLORER (/connections) - NEW                 │
│ Goal: Explore all Theory-Phenomenon connections                     │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: GET /api/connections/theory-phenomenon?{filters}
  │   └─> Returns: Filtered connections list
  │   └─> UI: Filterable table with strength, factors, papers
  │
  ├─ API: GET /api/connections/aggregated?{filters}
  │   └─> Returns: Aggregated statistics
  │   └─> UI: Aggregated view toggle
  │
  ├─ API: GET /api/analytics/connection-strength-distribution ⏳
  │   └─> Returns: Distribution statistics
  │   └─> UI: Distribution chart
  │
  └─ API: GET /api/connections/{connection_id}/factors ⏳
      └─> Trigger: User clicks connection
      └─> Returns: Factor breakdown
      └─> UI: Detail panel showing why strength is X
  │
  ↓ User Action: Applies filters OR clicks connection
  │
  ├─> Update list with filters
  ├─> Show connection detail
  └─> Navigate to Paper Detail
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 5: PHENOMENA EXPLORER (/phenomena) - NEW                     │
│ Goal: Explore all phenomena and their theories                      │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: GET /api/phenomena?{filters}
  │   └─> Returns: Filtered phenomena list
  │   └─> UI: Phenomena grid/list with counts
  │
  ├─ API: GET /api/phenomena/{phenomenon_name} ⏳
  │   └─> Trigger: User clicks phenomenon
  │   └─> Returns: Full phenomenon details
  │   └─> UI: Detail view
  │
  └─ API: GET /api/connections/phenomenon-theory/{phenomenon_name} ⏳
      └─> Trigger: User clicks phenomenon
      └─> Returns: All theories explaining this phenomenon
      └─> UI: Theories list with connection strengths
  │
  ↓ User Action: Clicks phenomenon OR theory
  │
  ├─> Show phenomenon detail
  ├─> Show explaining theories
  └─> Navigate to Connections Explorer
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 6: QUERY RESULTS (/query)                                     │
│ Goal: Ask natural language questions                                │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: POST /api/query?query={question}
  │   └─> Returns: LLM-generated answer + sources
  │   └─> UI: Answer display + source papers
  │
  └─ API: GET /api/connections/theory-phenomenon?theory_name={extracted}
      └─> Trigger: Extract theory from answer
      └─> Returns: Connections for mentioned theory
      └─> UI: "Related Connections" section
  │
  ↓ User Action: Clicks source paper OR connection
  │
  ├─> Navigate to Paper Detail
  └─> Navigate to Connections Explorer
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 7: ANALYTICS DASHBOARD (/analytics) - PLACEHOLDER            │
│ Goal: Understand overall research landscape                         │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: GET /api/stats
  │   └─> Returns: Overall statistics
  │   └─> UI: Stats cards
  │
  ├─ API: GET /api/analytics/connection-strength-distribution ⏳
  │   └─> Returns: Distribution statistics
  │   └─> UI: Distribution chart
  │
  ├─ API: GET /api/analytics/top-connections?n=20
  │   └─> Returns: Top 20 connections
  │   └─> UI: Top connections list
  │
  └─ API: GET /api/connections/aggregated?sort_by=paper_count
      └─> Returns: Most studied connections
      └─> UI: Most studied list
  │
  ↓
┌─────────────────────────────────────────────────────────────────────┐
│ SCREEN 8: GRAPH EXPLORER (/graph) - PLACEHOLDER                     │
│ Goal: Visualize knowledge graph                                     │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─ API: GET /api/graph
  │   └─> Returns: Full graph data
  │   └─> UI: Graph visualization
  │
  ├─ API: GET /api/connections/theory-phenomenon
  │   └─> Returns: Theory-Phenomenon connections
  │   └─> UI: Edges with strength as thickness
  │
  └─ API: GET /api/connections/aggregated
      └─> Returns: Aggregated connections
      └─> UI: Aggregated edges (thicker = more papers)
```

---

## 🔄 Complete User Journey Examples

### Example 1: "I want to understand Resource-Based View"

```
STEP 1: Dashboard
├─ User lands on dashboard
├─ Sees "Top Connections" card showing:
│  └─> "Resource-Based View → Resource allocation patterns (0.95)"
├─ API: GET /api/analytics/top-connections?n=5
└─ User clicks "Top Connections" card

STEP 2: Connections Explorer
├─ User sees all connections
├─ Filters by theory: "Resource-Based View"
├─ API: GET /api/connections/theory-phenomenon?theory_name=Resource-Based View
├─ Sees list:
│  ├─> RBV → Resource allocation (0.85, 5 papers)
│  ├─> RBV → Firm performance (0.72, 3 papers)
│  └─> RBV → Strategic decisions (0.68, 2 papers)
└─ User clicks on "RBV → Resource allocation"

STEP 3: Connection Detail
├─ API: GET /api/connections/{connection_id}/factors
├─ Shows factor breakdown:
│  ├─> Role Weight: 0.40 (47%) - Primary theory
│  ├─> Section Score: 0.20 (24%) - Same section
│  ├─> Keyword Score: 0.20 (24%) - Strong overlap
│  ├─> Semantic Score: 0.15 (18%) - Similar meaning
│  └─> Explicit Bonus: 0.05 (6%) - Key words match
└─ User clicks "View Papers"

STEP 4: Paper List
├─ Shows 5 papers with this connection
├─ User clicks on a paper
└─ Navigate to Paper Detail

STEP 5: Paper Detail
├─ API: GET /api/papers/{paper_id}
├─ API: GET /api/connections/theory-phenomenon?paper_id={paper_id}
├─ Shows paper with "Connections" tab
├─ User sees this paper's connections
└─ User clicks on "Resource allocation patterns" phenomenon

STEP 6: Phenomenon Detail
├─ API: GET /api/phenomena/Resource allocation patterns
├─ API: GET /api/connections/phenomenon-theory/Resource allocation patterns
├─ Shows:
│  ├─> Phenomenon details
│  ├─> All theories explaining it:
│  │   ├─> Resource-Based View (0.85, 5 papers)
│  │   ├─> Agency Theory (0.65, 3 papers)
│  │   └─> Transaction Cost Economics (0.58, 2 papers)
│  └─> All papers studying it
└─ User explores further
```

---

### Example 2: "I'm researching resource allocation patterns"

```
STEP 1: Search
├─ User searches "resource allocation"
├─ API: POST /api/search?query=resource allocation
├─ Shows papers
└─ User clicks "Explore Phenomena" button

STEP 2: Phenomena Explorer
├─ API: GET /api/phenomena?search=resource allocation
├─ Shows matching phenomena:
│  ├─> Resource allocation patterns (3 theories, 8 papers)
│  ├─> Resource allocation during crises (2 theories, 5 papers)
│  └─> Resource allocation in M&A (1 theory, 3 papers)
└─ User clicks "Resource allocation patterns"

STEP 3: Phenomenon Detail
├─ API: GET /api/phenomena/Resource allocation patterns
├─ API: GET /api/connections/phenomenon-theory/Resource allocation patterns
├─ Shows:
│  ├─> Phenomenon: "Resource allocation patterns"
│  ├─> Type: behavior
│  ├─> Domain: strategic_management
│  ├─> Description: "How firms allocate resources..."
│  ├─> Explaining Theories:
│  │   ├─> Resource-Based View (strength: 0.85, 5 papers)
│  │   ├─> Agency Theory (strength: 0.65, 3 papers)
│  │   └─> Transaction Cost Economics (strength: 0.58, 2 papers)
│  └─> Papers: 8 papers studying this phenomenon
└─ User clicks "Resource-Based View" theory

STEP 4: Theory Detail
├─ API: GET /api/connections/theory-phenomenon/Resource-Based View
├─ Shows all phenomena explained by RBV:
│  ├─> Resource allocation patterns (0.85, 5 papers)
│  ├─> Firm performance (0.72, 3 papers)
│  ├─> Strategic decisions (0.68, 2 papers)
│  └─> Competitive advantage (0.75, 4 papers)
└─ User compares theories

STEP 5: Theory Comparison
├─ User views side-by-side:
│  ├─> RBV explains: 4 phenomena
│  └─> Agency Theory explains: 2 phenomena (overlap: 1)
└─ User explores connections
```

---

### Example 3: "What are the strongest research connections?"

```
STEP 1: Dashboard
├─ User sees "Top Connections" card
├─ API: GET /api/analytics/top-connections?n=5&type=aggregated
├─ Shows:
│  ├─> RBV → Resource allocation (0.95, 8 papers)
│  ├─> Institutional Theory → Legitimacy (0.92, 6 papers)
│  ├─> Agency Theory → Governance (0.88, 7 papers)
│  └─> ...
└─ User clicks "View All"

STEP 2: Connections Explorer
├─ API: GET /api/connections/theory-phenomenon?min_strength=0.8
├─ Shows only very strong connections (>= 0.8)
├─ User toggles to "Aggregated View"
├─ API: GET /api/connections/aggregated?min_paper_count=3
├─ Shows aggregated statistics:
│  ├─> RBV → Resource allocation:
│  │   ├─> Avg Strength: 0.82
│  │   ├─> Papers: 8
│  │   ├─> Max: 0.95, Min: 0.65
│  │   └─> Std Dev: 0.095
└─ User clicks on connection

STEP 3: Connection Detail
├─ API: GET /api/connections/{connection_id}/factors
├─ Shows why it's strong:
│  ├─> Role Weight: 0.40 (Primary theory)
│  ├─> Section Score: 0.20 (Same section)
│  ├─> Keyword Score: 0.20 (Strong overlap)
│  ├─> Semantic Score: 0.15 (Similar meaning)
│  └─> Explicit Bonus: 0.05 (Explicit mention)
└─ User explores papers

STEP 4: Paper List
├─ Shows all 8 papers with this connection
├─ User can see strength varies:
│  ├─> Paper 1: 0.95 (very strong)
│  ├─> Paper 2: 0.88 (strong)
│  ├─> Paper 3: 0.82 (strong)
│  └─> ...
└─ User analyzes patterns
```

---

## 📊 API Integration Matrix

### All APIs by Screen

| Screen | API Endpoints | Purpose |
|--------|---------------|---------|
| **Dashboard** | `/api/stats`<br>`/api/analytics/top-connections`<br>`/api/phenomena` | Overview, highlights |
| **Search** | `/api/search`<br>`/api/query`<br>`/api/connections/theory-phenomenon` | Find papers, answer questions, show connections |
| **Paper Detail** | `/api/papers/{id}`<br>`/api/connections/theory-phenomenon?paper_id={id}`<br>`/api/connections/theory-phenomenon/{theory}` ⏳<br>`/api/phenomena/{phenomenon}` ⏳ | Full paper info, connections, exploration |
| **Connections Explorer** | `/api/connections/theory-phenomenon`<br>`/api/connections/aggregated`<br>`/api/analytics/connection-strength-distribution` ⏳<br>`/api/connections/{id}/factors` ⏳ | Explore all connections |
| **Phenomena Explorer** | `/api/phenomena`<br>`/api/phenomena/{phenomenon}` ⏳<br>`/api/connections/phenomenon-theory/{phenomenon}` ⏳ | Explore all phenomena |
| **Query Results** | `/api/query`<br>`/api/connections/theory-phenomenon` | Answer questions, show connections |
| **Analytics** | `/api/stats`<br>`/api/analytics/connection-strength-distribution` ⏳<br>`/api/analytics/top-connections`<br>`/api/connections/aggregated` | Overall statistics |
| **Graph Explorer** | `/api/graph`<br>`/api/connections/theory-phenomenon`<br>`/api/connections/aggregated` | Visualize graph |

---

## 🔗 API Dependency Graph

```
Dashboard
  ├─> /api/stats ✅
  ├─> /api/analytics/top-connections ✅
  └─> /api/phenomena ✅

Search
  ├─> /api/search ✅
  ├─> /api/query ✅
  └─> /api/connections/theory-phenomenon ✅

Paper Detail
  ├─> /api/papers/{id} ✅
  ├─> /api/connections/theory-phenomenon?paper_id={id} ✅
  ├─> /api/connections/theory-phenomenon/{theory} ⏳
  └─> /api/phenomena/{phenomenon} ⏳

Connections Explorer
  ├─> /api/connections/theory-phenomenon ✅
  ├─> /api/connections/aggregated ✅
  ├─> /api/analytics/connection-strength-distribution ⏳
  └─> /api/connections/{id}/factors ⏳

Phenomena Explorer
  ├─> /api/phenomena ✅
  ├─> /api/phenomena/{phenomenon} ⏳
  └─> /api/connections/phenomenon-theory/{phenomenon} ⏳
```

---

## 🎯 Implementation Roadmap

### Phase 1: Core Exploration (Week 1)
**Priority**: 🔴 CRITICAL
- ✅ `/api/connections/theory-phenomenon` - DONE
- ✅ `/api/connections/aggregated` - DONE
- ⏳ `/api/connections/theory-phenomenon/{theory_name}` - IMPLEMENT
- ⏳ `/api/connections/phenomenon-theory/{phenomenon_name}` - IMPLEMENT

**Impact**: Enables core exploration features

---

### Phase 2: Detail Views (Week 2)
**Priority**: 🟡 HIGH
- ✅ `/api/phenomena` - DONE
- ⏳ `/api/phenomena/{phenomenon_name}` - IMPLEMENT

**Impact**: Enables deep dive into phenomena

---

### Phase 3: Analytics & Transparency (Week 3)
**Priority**: 🟢 LOW
- ✅ `/api/analytics/top-connections` - DONE
- ⏳ `/api/analytics/connection-strength-distribution` - IMPLEMENT
- ⏳ `/api/connections/{connection_id}/factors` - IMPLEMENT

**Impact**: Analytics and transparency features

---

## 📈 User Value Proposition

### What Users Can Do

1. **Discover**: Find papers, theories, phenomena quickly
2. **Explore**: Navigate from theory → phenomena → papers seamlessly
3. **Understand**: See why connections are strong (factor breakdown)
4. **Analyze**: View aggregated statistics across papers
5. **Compare**: Compare theories, phenomena, connections
6. **Visualize**: See connections in graph format

### Research Questions Answered

- ✅ "What phenomena does Theory X explain?"
- ✅ "What theories explain Phenomenon Y?"
- ✅ "How strong is the connection between Theory X and Phenomenon Y?"
- ✅ "Why is this connection strong?" (factor breakdown)
- ✅ "Which connections are strongest across all research?"
- ✅ "How many papers connect Theory X to Phenomenon Y?"

---

## ✅ Summary

### Remaining 5 Endpoints

1. **`GET /api/connections/theory-phenomenon/{theory_name}`** - HIGH Priority
2. **`GET /api/connections/phenomenon-theory/{phenomenon_name}`** - HIGH Priority
3. **`GET /api/phenomena/{phenomenon_name}`** - MEDIUM Priority
4. **`GET /api/analytics/connection-strength-distribution`** - LOW Priority
5. **`GET /api/connections/{connection_id}/factors`** - LOW Priority

### End-to-End Integration

**All APIs work together** to create seamless user journeys:
- **8 screens** with integrated API calls
- **10 unique APIs** (5 existing, 4 new, 5 pending)
- **Multiple user journeys** supported
- **Progressive disclosure** from overview to detail

**The product enables researchers to discover, explore, analyze, and understand research connections in a comprehensive, interconnected way.**

