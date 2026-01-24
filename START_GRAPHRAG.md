# Quick Start Guide - Neo4j GraphRAG

## 🚀 Start Everything in 3 Steps

### Step 1: Start Backend API

**Terminal 1:**
```bash
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
source ../smj/bin/activate
python graphrag_api.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

✅ **Backend running on**: `http://localhost:8000`

---

### Step 2: Open Frontend

**Option A: Direct File Open**
```bash
open frontend_test.html
```

**Option B: HTTP Server (Recommended)**
```bash
# Terminal 2:
cd "/Users/sreehasgopinathan/Documents/Auburn/Research/SMJ/Strategic Management Journal"
python -m http.server 8080
```

Then open: **http://localhost:8080/frontend_test.html**

---

### Step 3: Test Queries

1. **Open the frontend** in your browser
2. **See stats** at the top (papers, theories, methods)
3. **Enter a query** or click an example
4. **Click "Search"**
5. **View answer** in the response card

---

## Example Queries to Try

1. **"What papers use Resource-Based View theory?"**
2. **"What research methods are commonly used?"**
3. **"Find papers about organizational learning"**
4. **"What theories are used in strategic management?"**
5. **"What are the main research questions?"**

---

## API Endpoints

- **Health**: http://localhost:8000/health
- **Stats**: http://localhost:8000/stats
- **Query**: http://localhost:8000/query (POST)
- **Docs**: http://localhost:8000/docs (Swagger UI)

---

## Troubleshooting

### Backend won't start
- Check Neo4j connection
- Verify OLLAMA is running: `ollama list`
- Check port 8000 is available

### Frontend can't connect
- Verify backend is running on port 8000
- Check browser console for errors
- Try opening http://localhost:8000/health in browser

### No answers generated
- Check OLLAMA is running
- Verify model is available: `ollama show llama3.1:8b`
- Check API logs for errors

---

## Success Indicators

✅ Backend shows "Application startup complete"
✅ Frontend loads and shows stats
✅ Queries return answers
✅ No errors in browser console

---

## That's It! 🎉

You're ready to query your knowledge graph!

