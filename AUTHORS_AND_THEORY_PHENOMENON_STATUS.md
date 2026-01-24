# Authors and Theory-Phenomenon Relationships Status

## Summary

### ✅ **Authors**
- **Storage**: Authors are stored in Neo4j with `Author` nodes
- **Relationships**: `(Paper)-[:AUTHORED_BY]->(Author)` or `(Author)-[:AUTHORED]->(Paper)`
- **Endpoints Available**:
  - `/api/research/authors/top` - Top authors with metrics
  - `/api/research/authors/collaboration-network` - Author collaboration network
  - Authors are included in paper detail endpoints (`/api/papers/{paper_id}`)

### ✅ **Multiple Theories → Single Phenomenon**
- **Endpoint**: `/api/research/phenomena-theories` (in `research_analytics_endpoints.py`)
- **Also**: `/api/connections/phenomenon-theory/{phenomenon_name}` (in `api_server.py`)
- **Purpose**: Find phenomena explained by multiple theories (theoretical pluralism)
- **Status**: ✅ Implemented and working

### ✅ **Single Theory → Multiple Phenomena**
- **Endpoint**: `/api/research/theory-phenomena` (in `research_analytics_endpoints.py`)
- **Also**: `/api/connections/theory-phenomenon/{theory_name}` (in `api_server.py`)
- **Purpose**: Find theories that explain multiple phenomena
- **Status**: ✅ Implemented and working

## Detailed Information

### 1. Authors

**Storage in Neo4j**:
```cypher
(:Author {
  author_id: string,
  full_name: string,
  given_name: string,
  family_name: string,
  email: string,
  orcid: string,
  position: int,
  corresponding_author: boolean
})

(:Paper)-[:AUTHORED_BY {position: int}]->(:Author)
```

**Current Status**:
- Authors are extracted and stored during ingestion
- However, the `/api/stats` endpoint shows `"authors": 0`, which suggests authors may not have been fully ingested
- Author endpoints exist but may return empty results if no authors are in the database

**Endpoints**:
1. `GET /api/research/authors/top?limit=50&min_papers=3`
   - Returns top authors with:
     - Paper count
     - Career span (first to last publication)
     - Primary theories used
     - Primary methods used
     - Top collaborators
     - Collaboration count

2. `GET /api/research/authors/collaboration-network?min_collaborations=2&limit=200`
   - Returns network data for visualization:
     - Nodes: authors with paper counts
     - Edges: collaborations with weights

### 2. Multiple Theories Addressing Same Phenomenon

**Endpoint**: `GET /api/research/phenomena-theories?min_papers=2`

**Returns**:
```json
{
  "phenomenon_name": "Resource allocation patterns",
  "theories_count": 3,
  "theories": [
    {"name": "Resource-Based View", "count": 15},
    {"name": "Agency Theory", "count": 8},
    {"name": "Transaction Cost Economics", "count": 5}
  ],
  "theoretical_pluralism": 0.6,
  "dominant_theory": "Resource-Based View"
}
```

**Use Cases**:
- Identify phenomena with theoretical pluralism
- Compare how different theories explain the same phenomenon
- Find research opportunities (theories that could be applied to a phenomenon)

**Also Available**:
- `GET /api/connections/phenomenon-theory/{phenomenon_name}?min_strength=0.3`
  - More detailed endpoint with connection strengths
  - Includes paper IDs and relationship metadata

### 3. Single Theory Addressing Multiple Phenomena

**Endpoint**: `GET /api/research/theory-phenomena?min_papers=2`

**Returns**:
```json
{
  "theory_name": "Resource-Based View",
  "phenomena_count": 12,
  "phenomena": [
    {"name": "Resource allocation patterns", "count": 15},
    {"name": "Competitive advantage", "count": 22},
    {"name": "Firm performance", "count": 18}
  ],
  "coverage_breadth": 1.0,
  "primary_phenomenon": "Competitive advantage"
}
```

**Use Cases**:
- Identify theories with broad applicability
- Understand theory scope and coverage
- Find theories that could be applied to new phenomena

**Also Available**:
- `GET /api/connections/theory-phenomenon/{theory_name}?min_strength=0.3`
  - More detailed endpoint with connection strengths
  - Includes paper IDs and relationship metadata

## Testing

### Test Authors Endpoint:
```bash
curl "http://localhost:5000/api/research/authors/top?limit=5"
```

### Test Multiple Theories → Phenomenon:
```bash
curl "http://localhost:5000/api/research/phenomena-theories?min_papers=2&limit=5"
# Or with specific phenomenon:
curl "http://localhost:5000/api/connections/phenomenon-theory/Resource%20allocation%20patterns"
```

### Test Single Theory → Multiple Phenomena:
```bash
curl "http://localhost:5000/api/research/theory-phenomena?min_papers=2&limit=5"
# Or with specific theory:
curl "http://localhost:5000/api/connections/theory-phenomenon/Resource-Based%20View"
```

## Issues & Recommendations

### Authors Issue
**Problem**: `/api/stats` shows `"authors": 0`, suggesting authors may not have been fully ingested.

**Recommendation**:
1. Check if authors are actually in Neo4j:
   ```cypher
   MATCH (a:Author) RETURN count(a)
   MATCH (p:Paper)-[:AUTHORED_BY]->(a:Author) RETURN count(*)
   ```

2. If authors are missing, they may need to be re-ingested or the ingestion process needs to be checked.

### Endpoint Access
The research analytics endpoints are included in the main app via:
```python
from research_analytics_endpoints import router as research_router
app.include_router(research_router)
```

The router has prefix `/api/research`, so endpoints should be accessible at:
- `/api/research/authors/top`
- `/api/research/phenomena-theories`
- `/api/research/theory-phenomena`
- `/api/research/fragmentation/{period}`

## Conclusion

✅ **Theory-Phenomenon Relationships**: Fully implemented and working
- Multiple theories → single phenomenon: ✅ Working
- Single theory → multiple phenomena: ✅ Working

⚠️ **Authors**: Endpoints exist but may need data verification
- Author storage structure is correct
- Endpoints are implemented
- Need to verify if authors were actually ingested
