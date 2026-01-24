# Railway Backend Configuration Fix

## 🚨 Problem

The backend service is running the **frontend** (npm/Node.js) instead of the **Python FastAPI backend**.

**Evidence from logs:**
- `npm warn config production`
- `INFO  Accepting connections at http://localhost:8080`
- OPTIONS requests returning 200 but no CORS headers

**Root Cause:** Railway is using the wrong start command or detecting the wrong service type.

---

## ✅ Solution: Configure Backend Service Correctly

### Step 1: Set Root Directory

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab**
3. **Find "Root Directory"**
4. **Set to**: `Strategic Management Journal`
5. **Save**

### Step 2: Set Start Command

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab**
3. **Find "Start Command"** (or "Deploy" section)
4. **Set to**: `python api_server.py`
5. **Save**

**OR** if Railway uses environment variable:
- Set `START_COMMAND=python api_server.py` in Variables

### Step 3: Verify Build Settings

1. **Settings tab** → **Build**
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python api_server.py`
4. **Save**

### Step 4: Ensure Python is Detected

Railway should auto-detect Python from:
- `requirements.txt` file
- `api_server.py` file
- Python code in the directory

If it's still detecting Node.js:
- Make sure `package.json` is NOT in the root directory used by backend
- Or explicitly set the service type to Python

### Step 5: Redeploy

1. **Settings tab** → **Redeploy** button
2. **OR** push a new commit to trigger redeploy
3. **Wait 2-5 minutes**

### Step 6: Verify Backend Logs

After redeploy, check logs should show:
- `✓ Connected to Neo4j`
- `CORS configured: allow_origins=['*'], allow_credentials=False`
- `🚀 Starting SMJ Research Chatbot API Server` (or similar)
- **NOT** `npm warn` or `Accepting connections at http://localhost:8080`

---

## 🔍 Alternative: Use Railway Service Settings

If the above doesn't work:

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab**
3. **Service Type**: Should be "Python" (not "Node.js")
4. **If it shows "Node.js"**, Railway might be auto-detecting wrong
5. **Try deleting and recreating the service** with explicit Python configuration

---

## 📋 Quick Checklist

- [ ] Root Directory set to `Strategic Management Journal`
- [ ] Start Command set to `python api_server.py`
- [ ] Build Command set to `pip install -r requirements.txt`
- [ ] Service type is "Python" (not "Node.js")
- [ ] Environment variables set (NEO4J_URI, etc.)
- [ ] Redeployed after changes
- [ ] Logs show Python/FastAPI starting (not npm)

---

## 🐛 If Still Not Working

### Option 1: Create railway.json for Backend

Create `railway.json` in `Strategic Management Journal` directory:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python api_server.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2: Use Procfile

Create `Procfile` in `Strategic Management Journal` directory:

```
web: python api_server.py
```

**Note:** This will conflict with the frontend Procfile, so you might need separate directories or use `railway.json` instead.

---

## ✅ Expected Logs After Fix

```
INFO:     Started server process
INFO:     Waiting for application startup.
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
✓ Advanced analytics endpoints loaded
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**NOT:**
```
npm warn config production
INFO  Accepting connections at http://localhost:8080
```

---

**The backend MUST run Python, not Node.js!**
