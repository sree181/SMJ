# Backend Server Startup Guide

## Issue: "Failed to fetch" Error

This error means the frontend cannot connect to the backend API server.

---

## ✅ Solution: Start Backend Server

### Option 1: Using Python Directly

```bash
cd "Strategic Management Journal"
python3 api_server.py
```

The server will start on `http://localhost:5000`

---

### Option 2: Using uvicorn (Recommended)

```bash
cd "Strategic Management Journal"
uvicorn api_server:app --host 0.0.0.0 --port 5000 --reload
```

---

### Option 3: Using npm script

```bash
cd "Strategic Management Journal"
npm run server
```

---

## 🔍 Verify Backend is Running

### Check Health Endpoint:
```bash
curl http://localhost:5000/api/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "timestamp": "2024-12-04T..."
}
```

### Check in Browser:
Open: `http://localhost:5000/api/health`

---

## 🚨 Common Issues

### 1. Port 5000 Already in Use

**Error**: `Address already in use`

**Solution**:
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
uvicorn api_server:app --port 5001
# Then update API_BASE in src/services/api.js
```

---

### 2. Neo4j Not Connected

**Error**: `Neo4j connection failed`

**Solution**:
1. Check `.env` file has correct Neo4j credentials:
   ```
   NEO4J_URI=neo4j+s://...
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=...
   ```

2. Test Neo4j connection:
   ```bash
   python3 -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('YOUR_URI', auth=('USER', 'PASS')); driver.verify_connectivity(); print('Connected!')"
   ```

---

### 3. CORS Errors

**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**: CORS is already configured in `api_server.py`:
```python
allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"]
```

If you're using a different port, update this list.

---

### 4. Module Import Errors

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 📋 Quick Start Checklist

- [ ] Backend server running on port 5000
- [ ] Health endpoint responds: `http://localhost:5000/api/health`
- [ ] Neo4j connection successful (check logs)
- [ ] Frontend running on port 3000
- [ ] CORS configured correctly

---

## 🔄 Restart Both Servers

### Terminal 1 (Backend):
```bash
cd "Strategic Management Journal"
python3 api_server.py
```

### Terminal 2 (Frontend):
```bash
cd "Strategic Management Journal"
npm start
```

---

## ✅ Verify Everything Works

1. **Backend Health**: `http://localhost:5000/api/health`
2. **Frontend**: `http://localhost:3000`
3. **Test Query**: Go to `/query` and try a question
4. **Check Console**: Open browser DevTools (F12) and check for errors

---

## 🐛 Debugging

### Check Backend Logs:
Look for:
- `✓ Connected to Neo4j`
- `🚀 Starting SMJ Research Chatbot API Server`
- Any error messages

### Check Frontend Console (F12):
Look for:
- API request URLs
- Error messages
- Network tab for failed requests

### Test API Directly:
```bash
# Test query endpoint
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What papers use Resource-Based View?"}'
```

---

**The backend server should now be starting. Wait 5-10 seconds, then try your query again.**

