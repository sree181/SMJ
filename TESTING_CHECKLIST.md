# Frontend Testing Checklist

## Pre-Testing Setup

- [ ] Neo4j Aura instance is accessible
- [ ] OLLAMA is running (`ollama list` should work)
- [ ] Embeddings are generated (7 papers have embeddings)
- [ ] Vector index exists in Neo4j

## Testing Steps

### 1. Start Backend
```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python graphrag_api.py
```

**Check**:
- [ ] Server starts without errors
- [ ] Shows "Application startup complete"
- [ ] GraphRAG initialized successfully
- [ ] Running on http://localhost:8000

### 2. Verify Backend Endpoints

**Health Check**:
```bash
curl http://localhost:8000/health
```
- [ ] Returns 200 status
- [ ] Shows "healthy" status
- [ ] Shows paper count > 0

**Stats**:
```bash
curl http://localhost:8000/stats
```
- [ ] Returns stats JSON
- [ ] Shows papers, theories, methods counts

### 3. Open Frontend

**Option A**: Direct file
```bash
open frontend_test.html
```

**Option B**: HTTP server
```bash
python -m http.server 8080
# Open: http://localhost:8080/frontend_test.html
```

**Check**:
- [ ] Frontend loads in browser
- [ ] Stats dashboard shows numbers
- [ ] No console errors
- [ ] UI looks correct

### 4. Test Queries

**Test Each**:
- [ ] "What papers use Resource-Based View theory?"
- [ ] "What research methods are commonly used?"
- [ ] "Find papers about organizational learning"
- [ ] "What theories are used in strategic management?"
- [ ] "What are the main research questions?"

**For Each Query**:
- [ ] Query submits successfully
- [ ] Loading indicator shows
- [ ] Answer appears in response card
- [ ] Answer is relevant to query
- [ ] Metadata shows source count

### 5. Test Options

**Top K**:
- [ ] Change Top K to 3 → Returns 3 results
- [ ] Change Top K to 10 → Returns 10 results

**Return Context**:
- [ ] Enable checkbox
- [ ] Context appears in response

**Graph Traversal**:
- [ ] Enable checkbox (may need VectorCypherRetriever fix)
- [ ] Query still works

### 6. Test API Directly

**Using curl**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What papers use Resource-Based View?", "top_k": 5}'
```

- [ ] Returns JSON response
- [ ] Contains "answer" field
- [ ] Contains "sources_count" field

### 7. Check API Documentation

Open: http://localhost:8000/docs

- [ ] Swagger UI loads
- [ ] All endpoints visible
- [ ] Can test endpoints from UI

---

## Success Criteria

✅ Backend starts without errors
✅ Frontend loads and displays stats
✅ Queries return answers
✅ Answers are relevant
✅ No console errors
✅ API endpoints respond correctly

---

## Troubleshooting

### Backend Issues
- Check Neo4j connection
- Verify OLLAMA running
- Check port 8000 available

### Frontend Issues
- Check backend is running
- Verify CORS enabled
- Check browser console

### Query Issues
- Verify embeddings exist
- Check OLLAMA model available
- Review API logs

---

## Ready to Test! 🚀

Follow the checklist above to verify everything works!

