# Commented Out API Endpoints

## Endpoints Commented Out Due to 404 Errors

The following endpoints have been commented out in `advanced_analytics_endpoints.py` because they were causing 404 errors:

### 1. ❌ `/api/analytics/theories/concentration-index`
- **Status**: Commented out
- **Method**: `GET`
- **Description**: Theoretical Concentration Index (HHI - Herfindahl-Hirschman Index)
- **Location**: Line ~1450 in `advanced_analytics_endpoints.py`
- **Reason**: Returning 404 Not Found

### 2. ❌ `/api/analytics/theories/problem-alignment`
- **Status**: Commented out
- **Method**: `GET`
- **Description**: Theory-Problem Alignment Score
- **Location**: Line ~1461 in `advanced_analytics_endpoints.py`
- **Reason**: Returning 404 Not Found

### 3. ❌ `/api/analytics/theories/integrative-centrality`
- **Status**: Commented out
- **Method**: `GET`
- **Description**: Integrative Theory Centrality (betweenness of papers using each theory)
- **Location**: Line ~1472 in `advanced_analytics_endpoints.py`
- **Reason**: Returning 404 Not Found

### 4. ❌ `/api/analytics/canonical/coverage`
- **Status**: Commented out
- **Method**: `GET`
- **Description**: Canonical Coverage Ratio by year
- **Location**: Line ~1428 in `advanced_analytics_endpoints.py`
- **Reason**: Returning 404 Not Found

### 5. ❌ `/api/analytics/canonical/centrality`
- **Status**: Commented out
- **Method**: `GET`
- **Description**: Canonical Centrality (eigenvector and PageRank)
- **Location**: Line ~1439 in `advanced_analytics_endpoints.py`
- **Reason**: Returning 404 Not Found

### 6. ❌ `/api/analytics/theories/cumulative`
- **Status**: Commented out
- **Method**: `GET`
- **Description**: Cumulative Theory metrics (knowledge accumulation, theory persistence)
- **Location**: Line ~1417 in `advanced_analytics_endpoints.py`
- **Reason**: Returning 404 Not Found

---

## ✅ Active Endpoints (Still Working)

The following endpoints remain active and functional:

### 1. ✓ `/api/analytics/papers/by-interval`
- **Method**: `GET`
- **Description**: Paper counts by 5-year intervals
- **Parameters**: `start_year`, `end_year`

### 2. ✓ `/api/analytics/topics/evolution`
- **Method**: `GET`
- **Description**: Topic evolution metrics
- **Parameters**: `start_year`, `end_year`

### 3. ✓ `/api/analytics/theories/evolution-divergence`
- **Method**: `GET`
- **Description**: Theoretical evolution and divergence metrics
- **Parameters**: `start_year`, `end_year`

### 4. ✓ `/api/analytics/theories/betweenness`
- **Method**: `GET`
- **Description**: Theory betweenness and cross-topic reach
- **Parameters**: `min_phenomena`

### 5. ✓ `/api/analytics/phenomena/opportunity-gaps`
- **Method**: `GET`
- **Description**: Opportunity gap scores for under-theorized phenomena
- **Parameters**: `max_theories`

### 6. ✓ `/api/analytics/integration/mechanism`
- **Method**: `GET`
- **Description**: Integration mechanism metrics (theory co-usage, integration scores)
- **Parameters**: `start_year`, `end_year`

---

## Next Steps

To re-enable the commented endpoints:

1. **Investigate the root cause**: The 404 errors suggest the router may not be properly registering these endpoints, or there may be a routing conflict.

2. **Check router registration**: Verify that `advanced_analytics_endpoints.py` router is properly included in `api_server.py`:
   ```python
   from advanced_analytics_endpoints import router as advanced_analytics_router
   app.include_router(advanced_analytics_router)
   ```

3. **Check for route conflicts**: Ensure no other router is using the same paths.

4. **Test individually**: Uncomment one endpoint at a time and test to identify which specific endpoints are problematic.

5. **Check FastAPI docs**: Visit `http://localhost:5000/docs` to see which endpoints are actually registered.

---

## Date
2026-01-23
