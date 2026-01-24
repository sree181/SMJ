# API Endpoints Quick Reference

## Complete Endpoint List (14 Total)

### Existing Endpoints (5)
1. `GET /api/health` - Health check
2. `POST /api/query` - Natural language query
3. `GET /api/graph` - Full graph data
4. `GET /api/stats` - Statistics
5. `POST /api/search` - Search papers
6. `GET /api/papers/{paper_id}` - Paper details

### New Connection Strength Endpoints (9)

#### Core Endpoints (4) - ✅ Implemented
7. `GET /api/connections/theory-phenomenon` - List connections with filters
8. `GET /api/connections/aggregated` - Aggregated statistics
9. `GET /api/phenomena` - List phenomena
10. `GET /api/analytics/top-connections` - Top N connections

#### Exploration Endpoints (2) - ✅ **NEW**
11. `GET /api/connections/theory-phenomenon/{theory_name}` - Phenomena for theory
12. `GET /api/connections/phenomenon-theory/{phenomenon_name}` - Theories for phenomenon

#### Detail Endpoints (2) - ✅ **NEW**
13. `GET /api/phenomena/{phenomenon_name}` - Phenomenon details
14. `GET /api/connections/{connection_id}/factors` - Factor breakdown

#### Analytics Endpoints (1) - ✅ **NEW**
15. `GET /api/analytics/connection-strength-distribution` - Distribution stats

---

## Quick Test Commands

```bash
# 1. Get phenomena for a theory
curl "http://localhost:5000/api/connections/theory-phenomenon/Resource-Based View"

# 2. Get theories for a phenomenon
curl "http://localhost:5000/api/connections/phenomenon-theory/Resource allocation patterns"

# 3. Get phenomenon detail
curl "http://localhost:5000/api/phenomena/Resource allocation patterns"

# 4. Get distribution
curl "http://localhost:5000/api/analytics/connection-strength-distribution"

# 5. Get factor breakdown
curl "http://localhost:5000/api/connections/Resource-Based View::Resource allocation patterns/factors"
```

---

## Status

✅ **ALL ENDPOINTS IMPLEMENTED** - Ready for frontend integration!

