# API Endpoints Design for Connection Strength Features

## Current API Status

### ✅ Existing Endpoints
1. `GET /api/health` - Health check
2. `POST /api/query` - LLM-powered natural language queries
3. `GET /api/graph` - Full knowledge graph data
4. `GET /api/stats` - Graph statistics
5. `POST /api/search` - Search papers
6. `GET /api/papers/{paper_id}` - Get paper details

### ❌ Missing Endpoints for Connection Strength
- Theory-Phenomenon connections
- Connection strength queries
- Aggregated statistics
- Factor breakdowns
- Phenomena exploration

---

## Proposed API Design

### RESTful Structure
```
/api/connections/          - Connection strength endpoints
/api/theories/            - Theory-related endpoints
/api/phenomena/           - Phenomenon-related endpoints
/api/analytics/           - Analytics and aggregation endpoints
```

---

## New Endpoints to Add

### 1. Theory-Phenomenon Connections

#### `GET /api/connections/theory-phenomenon`
**Purpose**: Get all Theory-Phenomenon connections with strength

**Query Parameters**:
- `theory_name` (optional): Filter by theory
- `phenomenon_name` (optional): Filter by phenomenon
- `min_strength` (optional, default: 0.3): Minimum connection strength
- `max_strength` (optional, default: 1.0): Maximum connection strength
- `paper_id` (optional): Filter by specific paper
- `limit` (optional, default: 50): Max results
- `offset` (optional, default: 0): Pagination offset

**Response**:
```json
{
  "connections": [
    {
      "theory": {
        "name": "Resource-Based View",
        "domain": "strategic_management"
      },
      "phenomenon": {
        "phenomenon_name": "Resource allocation patterns",
        "phenomenon_type": "behavior",
        "domain": "strategic_management"
      },
      "connection_strength": 0.850,
      "factor_scores": {
        "role_weight": 0.400,
        "section_score": 0.200,
        "keyword_score": 0.200,
        "semantic_score": 0.150,
        "explicit_bonus": 0.050
      },
      "paper_id": "paper_2020_001",
      "theory_role": "primary",
      "section": "introduction"
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

---

#### `GET /api/connections/theory-phenomenon/{theory_name}`
**Purpose**: Get all phenomena explained by a specific theory

**Response**:
```json
{
  "theory": {
    "name": "Resource-Based View",
    "domain": "strategic_management"
  },
  "phenomena": [
    {
      "phenomenon_name": "Resource allocation patterns",
      "connection_strength": 0.850,
      "paper_count": 5,
      "papers": ["paper_2020_001", "paper_2021_005"]
    }
  ],
  "total_phenomena": 12
}
```

---

#### `GET /api/connections/phenomenon-theory/{phenomenon_name}`
**Purpose**: Get all theories explaining a specific phenomenon

**Response**:
```json
{
  "phenomenon": {
    "phenomenon_name": "Resource allocation patterns",
    "phenomenon_type": "behavior"
  },
  "theories": [
    {
      "theory_name": "Resource-Based View",
      "connection_strength": 0.850,
      "paper_count": 5,
      "theory_role": "primary"
    }
  ],
  "total_theories": 3
}
```

---

### 2. Aggregated Connections

#### `GET /api/connections/aggregated`
**Purpose**: Get aggregated connection strength statistics

**Query Parameters**:
- `theory_name` (optional): Filter by theory
- `phenomenon_name` (optional): Filter by phenomenon
- `min_paper_count` (optional, default: 2): Minimum papers for aggregation
- `sort_by` (optional, default: "avg_strength"): Sort by avg_strength, paper_count, max_strength
- `order` (optional, default: "desc"): asc or desc
- `limit` (optional, default: 50)

**Response**:
```json
{
  "aggregated_connections": [
    {
      "theory": {
        "name": "Resource-Based View"
      },
      "phenomenon": {
        "phenomenon_name": "Resource allocation patterns"
      },
      "avg_strength": 0.820,
      "paper_count": 8,
      "max_strength": 0.950,
      "min_strength": 0.650,
      "std_strength": 0.095,
      "avg_factor_scores": {
        "role_weight": 0.380,
        "section_score": 0.190,
        "keyword_score": 0.200,
        "semantic_score": 0.150,
        "explicit_bonus": 0.040
      },
      "paper_ids": ["paper_2020_001", "paper_2021_005", ...]
    }
  ],
  "total": 45
}
```

---

### 3. Connection Analytics

#### `GET /api/analytics/connection-strength-distribution`
**Purpose**: Get distribution of connection strengths

**Response**:
```json
{
  "distribution": {
    "very_strong": {"count": 25, "percentage": 16.7},
    "strong": {"count": 50, "percentage": 33.3},
    "moderate": {"count": 60, "percentage": 40.0},
    "weak": {"count": 15, "percentage": 10.0}
  },
  "statistics": {
    "total_connections": 150,
    "avg_strength": 0.625,
    "median_strength": 0.650,
    "std_strength": 0.185
  }
}
```

---

#### `GET /api/analytics/top-connections`
**Purpose**: Get top N connections by strength

**Query Parameters**:
- `n` (optional, default: 10): Number of top connections
- `type` (optional, default: "all"): "all", "aggregated", "individual"
- `min_paper_count` (optional): For aggregated only

**Response**:
```json
{
  "top_connections": [
    {
      "theory": "Resource-Based View",
      "phenomenon": "Resource allocation patterns",
      "strength": 0.950,
      "paper_count": 8,
      "type": "aggregated"
    }
  ]
}
```

---

### 4. Factor Analysis

#### `GET /api/connections/{connection_id}/factors`
**Purpose**: Get detailed factor breakdown for a connection

**Response**:
```json
{
  "connection": {
    "theory": "Resource-Based View",
    "phenomenon": "Resource allocation patterns",
    "connection_strength": 0.850
  },
  "factors": {
    "role_weight": {
      "value": 0.400,
      "percentage": 47.1,
      "explanation": "Primary theory (40% base weight)"
    },
    "section_score": {
      "value": 0.200,
      "percentage": 23.5,
      "explanation": "Same section (20% boost)"
    },
    "keyword_score": {
      "value": 0.200,
      "percentage": 23.5,
      "explanation": "Strong keyword overlap (Jaccard: 0.65)"
    },
    "semantic_score": {
      "value": 0.150,
      "percentage": 17.6,
      "explanation": "Similar meaning (cosine: 0.68)"
    },
    "explicit_bonus": {
      "value": 0.050,
      "percentage": 5.9,
      "explanation": "Key words match (80% match ratio)"
    }
  }
}
```

---

### 5. Phenomena Exploration

#### `GET /api/phenomena`
**Purpose**: List all phenomena

**Query Parameters**:
- `domain` (optional): Filter by domain
- `phenomenon_type` (optional): Filter by type
- `search` (optional): Search by name
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response**:
```json
{
  "phenomena": [
    {
      "phenomenon_name": "Resource allocation patterns",
      "phenomenon_type": "behavior",
      "domain": "strategic_management",
      "description": "How firms allocate resources",
      "theory_count": 3,
      "paper_count": 8
    }
  ],
  "total": 45
}
```

---

#### `GET /api/phenomena/{phenomenon_name}`
**Purpose**: Get detailed information about a phenomenon

**Response**:
```json
{
  "phenomenon": {
    "phenomenon_name": "Resource allocation patterns",
    "phenomenon_type": "behavior",
    "domain": "strategic_management",
    "description": "How firms allocate resources during financial crises",
    "context": "Studied through firm investment decisions"
  },
  "theories": [
    {
      "theory_name": "Resource-Based View",
      "connection_strength": 0.850,
      "paper_count": 5
    }
  ],
  "papers": [
    {
      "paper_id": "paper_2020_001",
      "title": "...",
      "publication_year": 2020
    }
  ],
  "statistics": {
    "total_theories": 3,
    "total_papers": 8,
    "avg_connection_strength": 0.720
  }
}
```

---

### 6. Theory Exploration

#### `GET /api/theories/{theory_name}/phenomena`
**Purpose**: Get all phenomena explained by a theory

**Response**: Same as `/api/connections/theory-phenomenon/{theory_name}`

---

## Implementation Strategy

### Phase 1: Core Endpoints (Priority 1)
1. ✅ `GET /api/connections/theory-phenomenon` - Main connection query
2. ✅ `GET /api/connections/aggregated` - Aggregated statistics
3. ✅ `GET /api/phenomena` - List phenomena

### Phase 2: Detail Endpoints (Priority 2)
4. ✅ `GET /api/phenomena/{phenomenon_name}` - Phenomenon details
5. ✅ `GET /api/connections/theory-phenomenon/{theory_name}` - Theory's phenomena
6. ✅ `GET /api/analytics/top-connections` - Top connections

### Phase 3: Advanced Analytics (Priority 3)
7. ✅ `GET /api/analytics/connection-strength-distribution` - Distribution
8. ✅ `GET /api/connections/{connection_id}/factors` - Factor breakdown

---

## Scalability Considerations

### 1. Pagination
- All list endpoints support `limit` and `offset`
- Response includes `total` count for UI pagination

### 2. Caching
- Cache aggregated statistics (TTL: 1 hour)
- Cache top connections (TTL: 30 minutes)
- Use Redis or in-memory cache

### 3. Indexing
- Ensure Neo4j indexes exist (✅ Done in Phase 1)
- Use indexed properties in WHERE clauses

### 4. Response Optimization
- Limit default results (50 items)
- Use projection to return only needed fields
- Batch queries where possible

### 5. Error Handling
- Consistent error format
- Proper HTTP status codes
- Detailed error messages

---

## Frontend Integration Points

### Dashboard
- Use `/api/analytics/top-connections` for "Top Connections" card
- Use `/api/analytics/connection-strength-distribution` for chart

### Search Results
- Enhance with connection strength in paper cards
- Show "Explains phenomena" section

### Paper Detail
- Add "Theory-Phenomenon Connections" tab
- Show connection strengths and factor breakdowns

### New Screens
- **Connections Explorer**: Browse all connections
- **Phenomena Explorer**: Browse phenomena and their theories
- **Analytics Dashboard**: Connection strength analytics

---

## API Versioning

### Current: v1
- Base path: `/api/`
- No version prefix (backward compatible)

### Future: v2
- Base path: `/api/v2/`
- Enhanced features, breaking changes

---

## Response Format Standard

### Success Response
```json
{
  "data": {...},
  "meta": {
    "total": 150,
    "limit": 50,
    "offset": 0,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Theory not found",
    "details": {...}
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Next Steps

1. ✅ Design API structure (this document)
2. ⏳ Implement core endpoints
3. ⏳ Add caching layer
4. ⏳ Write API documentation
5. ⏳ Create frontend integration examples
6. ⏳ Add unit tests
7. ⏳ Performance testing

