# Frontend Testing Guide for Neo4j GraphRAG

## Overview

This guide shows you how to test the GraphRAG system from a frontend interface.

---

## Step 1: Start the Backend API

### Terminal 1: Start FastAPI Server

```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python graphrag_api.py
```

The API will start on `http://localhost:8000`

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Initializing GraphRAG...
INFO:     ✅ GraphRAG initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 2: Open the Frontend

### Option A: Open HTML File Directly

1. Open `frontend_test.html` in your browser
2. The file is located at:
   ```
   /Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal/frontend_test.html
   ```

### Option B: Serve via HTTP (Recommended)

```bash
# Terminal 2: Start a simple HTTP server
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
python -m http.server 8080
```

Then open: `http://localhost:8080/frontend_test.html`

---

## Step 3: Test the Interface

### Features Available:

1. **Stats Dashboard**: Shows paper count, embeddings, theories, methods, relationships
2. **Query Input**: Enter your question
3. **Options**:
   - **Top K**: Number of papers to retrieve (1-20)
   - **Return Context**: Include retrieved context in response
   - **Use Graph Traversal**: Use VectorCypherRetriever (includes graph relationships)
4. **Example Queries**: Click to use pre-filled queries

### Test Queries:

1. **"What papers use Resource-Based View theory?"**
   - Tests theory-based retrieval

2. **"What research methods are commonly used?"**
   - Tests method extraction

3. **"Find papers about organizational learning"**
   - Tests semantic similarity

4. **"What theories are used in strategic management?"**
   - Tests theory aggregation

5. **"What are the main research questions?"**
   - Tests research question extraction

---

## Step 4: API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "GraphRAG API is running",
  "vector_index_exists": true,
  "papers_count": 8
}
```

### Query Endpoint
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What papers use Resource-Based View theory?",
    "top_k": 5,
    "return_context": false,
    "use_cypher": false
  }'
```

**Response:**
```json
{
  "answer": "Based on the knowledge graph...",
  "query": "What papers use Resource-Based View theory?",
  "sources_count": 5,
  "context": null
}
```

### Stats Endpoint
```bash
curl http://localhost:8000/stats
```

**Response:**
```json
{
  "papers": 8,
  "papers_with_embeddings": 7,
  "theories": 43,
  "methods": 14,
  "relationships": 415
}
```

---

## Troubleshooting

### Issue: "Failed to fetch" or CORS errors

**Solution**: Make sure the API server is running and CORS is enabled (it is by default)

### Issue: "GraphRAG not initialized"

**Solution**: 
1. Check that Neo4j is accessible
2. Verify embeddings exist: Run `advanced_paper_features.py` first
3. Check API logs for errors

### Issue: No response from queries

**Solution**:
1. Check OLLAMA is running: `ollama list`
2. Verify model is available: `ollama show llama3.1:8b`
3. Check API logs for LLM errors

### Issue: Vector index not found

**Solution**: The API will create it automatically, but you can also run:
```python
from neo4j_graphrag_official import OfficialNeo4jGraphRAG
graphrag = OfficialNeo4jGraphRAG()
graphrag.create_vector_index()
graphrag.populate_vector_index()
```

---

## Advanced Testing

### Test with Graph Traversal

Enable "Use Graph Traversal" checkbox to use VectorCypherRetriever, which includes:
- Vector similarity search
- Graph relationship traversal
- Connected entity retrieval

### Test with Context

Enable "Return Context" to see:
- Retrieved papers
- Similarity scores
- Relationship information

---

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Next Steps

1. ✅ **Backend Running**: API server on port 8000
2. ✅ **Frontend Open**: HTML interface loaded
3. ✅ **Test Queries**: Try example queries
4. ⏳ **Customize**: Modify frontend for your needs
5. ⏳ **Deploy**: Deploy to production when ready

---

## Quick Start Commands

```bash
# Terminal 1: Start API
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python graphrag_api.py

# Terminal 2: Start Frontend Server (optional)
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
python -m http.server 8080

# Then open: http://localhost:8080/frontend_test.html
```

---

## Success Indicators

✅ API responds to `/health` endpoint
✅ Stats load in frontend
✅ Queries return answers
✅ No CORS errors in browser console
✅ OLLAMA processes queries (check OLLAMA logs)

---

## Summary

You now have:
1. ✅ **Backend API**: FastAPI server with GraphRAG endpoints
2. ✅ **Frontend Interface**: HTML/JavaScript test interface
3. ✅ **Documentation**: Complete testing guide

**Ready to test!** 🚀

