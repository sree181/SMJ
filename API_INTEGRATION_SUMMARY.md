# API Integration Summary - Quick Reference

## 🔍 Remaining 5 Endpoints

### High Priority (Implement First)

#### 1. `GET /api/connections/theory-phenomenon/{theory_name}`
**Purpose**: Get all phenomena explained by a theory  
**Used In**: Paper Detail (theory click), Theory Explorer  
**Example**: `GET /api/connections/theory-phenomenon/Resource-Based View`  
**Returns**: List of phenomena with connection strengths

#### 2. `GET /api/connections/phenomenon-theory/{phenomenon_name}`
**Purpose**: Get all theories explaining a phenomenon  
**Used In**: Paper Detail (phenomenon click), Phenomena Explorer  
**Example**: `GET /api/connections/phenomenon-theory/Resource allocation patterns`  
**Returns**: List of theories with connection strengths

### Medium Priority

#### 3. `GET /api/phenomena/{phenomenon_name}`
**Purpose**: Get detailed information about a phenomenon  
**Used In**: Phenomena Explorer, Paper Detail  
**Example**: `GET /api/phenomena/Resource allocation patterns`  
**Returns**: Phenomenon details, theories, papers, statistics

### Low Priority (Nice to Have)

#### 4. `GET /api/analytics/connection-strength-distribution`
**Purpose**: Get distribution statistics  
**Used In**: Analytics Dashboard  
**Returns**: Distribution buckets (very_strong, strong, moderate, weak)

#### 5. `GET /api/connections/{connection_id}/factors`
**Purpose**: Get detailed factor breakdown  
**Used In**: Connection Detail, Paper Detail  
**Example**: `GET /api/connections/Resource-Based View::Resource allocation::paper_001/factors`  
**Returns**: Factor scores with explanations

---

## 🗺️ End-to-End User Journey

### Journey Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER JOURNEY MAP                          │
└─────────────────────────────────────────────────────────────┘

1. DASHBOARD (/)
   ├─> GET /api/stats ✅
   ├─> GET /api/analytics/top-connections ✅
   └─> GET /api/phenomena ✅
   │
   ↓ User searches or clicks
   │
2. SEARCH RESULTS (/search)
   ├─> POST /api/search ✅
   ├─> POST /api/query ✅ (if question)
   └─> GET /api/connections/theory-phenomenon ✅
   │
   ↓ User clicks paper
   │
3. PAPER DETAIL (/paper/:id)
   ├─> GET /api/papers/{id} ✅
   ├─> GET /api/connections/theory-phenomenon?paper_id={id} ✅
   ├─> GET /api/connections/theory-phenomenon/{theory} ⏳ (on theory click)
   └─> GET /api/phenomena/{phenomenon} ⏳ (on phenomenon click)
   │
   ↓ User explores further
   │
4. CONNECTIONS EXPLORER (/connections) - NEW
   ├─> GET /api/connections/theory-phenomenon ✅
   ├─> GET /api/connections/aggregated ✅
   ├─> GET /api/analytics/connection-strength-distribution ⏳
   └─> GET /api/connections/{id}/factors ⏳
   │
5. PHENOMENA EXPLORER (/phenomena) - NEW
   ├─> GET /api/phenomena ✅
   ├─> GET /api/phenomena/{phenomenon} ⏳
   └─> GET /api/connections/phenomenon-theory/{phenomenon} ⏳
```

---

## 📊 API Usage by Screen

| Screen | Existing APIs | New APIs (✅) | Pending APIs (⏳) | Total |
|--------|--------------|---------------|-------------------|-------|
| **Dashboard** | 1 | 2 | 0 | 3 |
| **Search** | 2 | 1 | 0 | 3 |
| **Paper Detail** | 1 | 1 | 2 | 4 |
| **Connections Explorer** | 0 | 2 | 2 | 4 |
| **Phenomena Explorer** | 0 | 1 | 2 | 3 |
| **Query Results** | 1 | 1 | 0 | 2 |
| **Analytics** | 1 | 2 | 1 | 4 |
| **Graph Explorer** | 1 | 2 | 0 | 3 |

**Total**: 10 unique APIs
- **Existing**: 5
- **New (Implemented)**: 4
- **New (Pending)**: 5

---

## 🎯 Complete User Journey Examples

### Example 1: Theory Exploration

```
User Goal: "I want to understand Resource-Based View"

1. Dashboard
   └─> Sees "Top Connections" showing "RBV → Resource allocation (0.95)"
   
2. Connections Explorer
   └─> Filters by theory: "Resource-Based View"
   └─> API: GET /api/connections/theory-phenomenon?theory_name=Resource-Based View ✅
   └─> Sees: 4 phenomena explained by RBV
   
3. Connection Detail
   └─> Clicks on "RBV → Resource allocation"
   └─> API: GET /api/connections/{id}/factors ⏳
   └─> Sees: Why strength is 0.85 (factor breakdown)
   
4. Paper Detail
   └─> Clicks on a paper
   └─> API: GET /api/papers/{id} ✅
   └─> API: GET /api/connections/theory-phenomenon?paper_id={id} ✅
   └─> Sees: Paper's connections tab
   
5. Phenomenon Exploration
   └─> Clicks on "Resource allocation patterns"
   └─> API: GET /api/phenomena/Resource allocation patterns ⏳
   └─> API: GET /api/connections/phenomenon-theory/Resource allocation patterns ⏳
   └─> Sees: All theories explaining this phenomenon
```

---

### Example 2: Phenomenon Research

```
User Goal: "I'm researching resource allocation patterns"

1. Search
   └─> Searches "resource allocation"
   └─> API: POST /api/search ✅
   └─> Sees: Papers
   
2. Phenomena Explorer
   └─> Clicks "Explore Phenomena"
   └─> API: GET /api/phenomena?search=resource allocation ✅
   └─> Sees: Matching phenomena
   
3. Phenomenon Detail
   └─> Clicks "Resource allocation patterns"
   └─> API: GET /api/phenomena/Resource allocation patterns ⏳
   └─> API: GET /api/connections/phenomenon-theory/Resource allocation patterns ⏳
   └─> Sees: 3 theories explaining it (RBV, Agency, TCE)
   
4. Theory Comparison
   └─> Compares theories
   └─> API: GET /api/connections/theory-phenomenon/Resource-Based View ⏳
   └─> API: GET /api/connections/theory-phenomenon/Agency Theory ⏳
   └─> Sees: Side-by-side comparison
```

---

## 🔗 API Integration Patterns

### Pattern 1: Parallel Loading
```javascript
// Dashboard loads 3 APIs in parallel
const [stats, topConnections, phenomena] = await Promise.all([
  api.getStats(),
  api.getTopConnections(5),
  api.getPhenomena(5)
]);
```

### Pattern 2: Sequential with Context
```javascript
// Paper Detail: Load paper, then connections
const paper = await api.getPaper(paperId);
const connections = await api.getConnections({ paper_id: paperId });
```

### Pattern 3: Lazy Loading
```javascript
// Connections tab: Load on tab click
const handleTabClick = async () => {
  if (tab === 'connections' && !connectionsLoaded) {
    const data = await api.getConnections({ paper_id: paperId });
    setConnections(data);
  }
};
```

### Pattern 4: Progressive Enhancement
```javascript
// Search: Load connections after papers
const papers = await api.searchPapers(query);
const connections = await api.getConnections({ search: query }); // Optional
```

---

## 📈 Scalability Strategy

### Current Implementation
- ✅ Pagination on all list endpoints
- ✅ Filtering to reduce result sets
- ✅ Indexed queries (Neo4j indexes)
- ✅ Parallel API calls where possible

### Future Enhancements
- ⏳ Caching layer (Redis)
- ⏳ Response compression
- ⏳ Batch queries
- ⏳ GraphQL for flexible queries

---

## ✅ Implementation Checklist

### Phase 1: Core Exploration (Week 1)
- [x] `/api/connections/theory-phenomenon` ✅
- [x] `/api/connections/aggregated` ✅
- [ ] `/api/connections/theory-phenomenon/{theory_name}` ⏳
- [ ] `/api/connections/phenomenon-theory/{phenomenon_name}` ⏳

### Phase 2: Detail Views (Week 2)
- [x] `/api/phenomena` ✅
- [ ] `/api/phenomena/{phenomenon_name}` ⏳

### Phase 3: Analytics (Week 3)
- [x] `/api/analytics/top-connections` ✅
- [ ] `/api/analytics/connection-strength-distribution` ⏳
- [ ] `/api/connections/{connection_id}/factors` ⏳

---

## 🎨 Frontend Integration Points

### Where APIs Appear

1. **Dashboard Cards**:
   - Top Connections → `/api/analytics/top-connections`
   - Recent Phenomena → `/api/phenomena`

2. **Paper Detail Tabs**:
   - Connections Tab → `/api/connections/theory-phenomenon?paper_id={id}`
   - Theory Click → `/api/connections/theory-phenomenon/{theory}`
   - Phenomenon Click → `/api/phenomena/{phenomenon}`

3. **Search Results**:
   - Related Connections → `/api/connections/theory-phenomenon?search={query}`

4. **New Screens**:
   - Connections Explorer → `/api/connections/theory-phenomenon` + filters
   - Phenomena Explorer → `/api/phenomena` + detail endpoints

---

## 📝 Summary

### Remaining 5 Endpoints

1. **Theory → Phenomena** (`/api/connections/theory-phenomenon/{theory_name}`) - HIGH
2. **Phenomenon → Theories** (`/api/connections/phenomenon-theory/{phenomenon_name}`) - HIGH
3. **Phenomenon Detail** (`/api/phenomena/{phenomenon_name}`) - MEDIUM
4. **Distribution Stats** (`/api/analytics/connection-strength-distribution`) - LOW
5. **Factor Breakdown** (`/api/connections/{connection_id}/factors`) - LOW

### End-to-End Integration

**All APIs work together** across 8 screens to create seamless user journeys:
- **Discovery** → Search/Query APIs
- **Exploration** → Connection/Phenomena APIs
- **Analysis** → Aggregated/Analytics APIs
- **Deep Dive** → Detail APIs

**The product enables researchers to navigate from overview to detail, from theory to phenomenon to paper, creating a rich, interconnected research experience.**

