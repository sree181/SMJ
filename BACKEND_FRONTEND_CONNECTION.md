# Backend-Frontend Connection Guide

## Step-by-Step Connection Status

### ✅ Step 1: Backend API Endpoints Added

**New Endpoints**:
1. `POST /api/search` - Search papers by query
2. `GET /api/papers/{paper_id}` - Get detailed paper information
3. `GET /api/stats` - Updated to include theories, methods, authors

**Status**: ✅ Implemented

---

### ✅ Step 2: Dashboard Stats Connection

**Component**: `src/components/screens/Dashboard.js`

**Connection**:
- Calls `api.getStats()` on mount
- Maps response to stats cards
- Handles errors gracefully

**Test**: 
```bash
curl http://localhost:5000/api/stats
```

**Status**: ✅ Connected

---

### ✅ Step 3: Search Functionality Connection

**Component**: `src/components/screens/SearchResults.js`

**Connection**:
- Calls `api.searchPapers(query)` first
- Falls back to `api.queryGraphRAG(query)` if search fails
- Handles both search queries and natural language questions

**Test**:
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "resource"}'
```

**Status**: ✅ Connected

---

### ✅ Step 4: Paper Details Connection

**Component**: `src/components/screens/PaperDetail.js`

**Connection**:
- Calls `api.getPaper(paperId)` on mount
- Displays full paper information
- Shows theories, methods, research questions

**Test**:
```bash
# First get a paper_id from search, then:
curl http://localhost:5000/api/papers/{paper_id}
```

**Status**: ✅ Connected

---

### ⏳ Step 5: Query Interface (Coming Next)

**Component**: Will be created

**Connection**:
- Uses `api.queryGraphRAG(query)` for natural language questions
- Displays answer and sources

**Status**: ⏳ Pending

---

## API Endpoints Summary

### Available Endpoints:

1. **GET /api/health**
   - Health check
   - Returns: `{status, neo4j_connected, timestamp}`

2. **GET /api/stats**
   - Statistics
   - Returns: `{papers, theories, methods, authors, ...}`

3. **POST /api/search**
   - Search papers
   - Body: `{query: "search term"}`
   - Returns: `{papers: [...], count: N}`

4. **GET /api/papers/{paper_id}**
   - Get paper details
   - Returns: Full paper object with relationships

5. **POST /api/query**
   - GraphRAG query
   - Body: `{query: "question"}`
   - Returns: `{answer, graphData, sources, timestamp}`

---

## Testing the Connection

### Test 1: Dashboard Stats
1. Open http://localhost:3000
2. Check if stats cards show numbers
3. Should load from `/api/stats`

### Test 2: Search
1. Enter a search term (e.g., "resource")
2. Click Search
3. Should show results from `/api/search`

### Test 3: Paper Details
1. Click on a paper card
2. Should load full details from `/api/papers/{id}`

---

## Next Steps

1. ✅ Dashboard stats - Connected
2. ✅ Search functionality - Connected  
3. ✅ Paper details - Connected
4. ⏳ Query interface - Next
5. ⏳ Temporal evolution - Next
6. ⏳ Graph explorer - Next

---

## Troubleshooting

### Issue: Stats not loading
- Check backend is running: `curl http://localhost:5000/api/health`
- Check browser console for errors
- Verify Neo4j connection

### Issue: Search returns no results
- Check if papers exist in Neo4j
- Try a different search term
- Check backend logs

### Issue: Paper details not loading
- Verify paper_id exists
- Check API response format
- Check browser console

---

**Status**: Core connections working! ✅

