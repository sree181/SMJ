# Railway Backend Fixes - Neo4j Connection & Circular Import

## 🚨 Issues Found

### Issue 1: Neo4j Connection Failed
```
ERROR: URI scheme b'' is not supported
```

**Root Cause**: `NEO4J_URI` environment variable is **not set** or is **empty** in Railway.

### Issue 2: Circular Import Warning
```
WARNING: cannot import name 'router' from partially initialized module 'research_analytics_endpoints'
```

**Root Cause**: `research_analytics_endpoints.py` imports `LLMClient` from `api_server.py`, but `api_server.py` imports `router` from `research_analytics_endpoints.py` - circular dependency!

---

## ✅ Fixes Applied

### Fix 1: Circular Import - Lazy Import Pattern

Changed `research_analytics_endpoints.py` to use lazy import:
- **Before**: `from api_server import LLMClient` (at module level)
- **After**: `def get_llm_client(): ...` (lazy import function)

This breaks the circular dependency.

### Fix 2: Neo4j Connection - Better Error Messages

Updated `api_server.py` to:
- Strip whitespace from environment variables
- Validate that all required variables are set
- Provide clear error messages if variables are missing

---

## 🔧 Required Actions in Railway

### Step 1: Set Neo4j Environment Variables

1. **Railway Dashboard** → **Backend service**
2. **Variables tab**
3. **Add these variables** (if not already set):

```
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

**Important**: 
- Replace with your actual Neo4j credentials
- `NEO4J_URI` must start with `neo4j+s://` or `neo4j://` or `bolt://`
- No extra spaces or quotes

### Step 2: Set OpenAI API Key

```
OPENAI_API_KEY=sk-proj-your-openai-key-here
```

### Step 3: Redeploy Backend

1. **Deployments tab** → **Redeploy**
2. **Wait 2-3 minutes**
3. **Check logs** - should see:
   ```
   ✓ Connected to Neo4j
   INFO:     Uvicorn running on http://0.0.0.0:8080
   ```

**NOT:**
```
ERROR: URI scheme b'' is not supported
```

---

## ✅ Expected Result

After setting environment variables and redeploying:

**Backend logs should show:**
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
✓ Advanced analytics endpoints loaded
✓ Research Analytics endpoints loaded
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**No more:**
- `URI scheme b'' is not supported`
- `cannot import name 'router'` warnings
- `Failed to connect to Neo4j` errors

---

## 📋 Quick Checklist

- [ ] `NEO4J_URI` set in Railway (starts with `neo4j+s://` or `neo4j://`)
- [ ] `NEO4J_USER` set in Railway (usually `neo4j`)
- [ ] `NEO4J_PASSWORD` set in Railway
- [ ] `OPENAI_API_KEY` set in Railway
- [ ] Backend redeployed after setting variables
- [ ] Logs show "✓ Connected to Neo4j"
- [ ] No circular import warnings

---

**The main issue is missing `NEO4J_URI` environment variable - set it in Railway Variables tab!**
