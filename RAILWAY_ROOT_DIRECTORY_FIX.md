# Railway Root Directory Fix

## ✅ Correct Configuration

Since your GitHub repo (`sree181/SMJ`) has files directly in the root:
- `api_server.py` is in the repo root
- `package.json` is in the repo root  
- `requirements.txt` is in the repo root

**For Railway services, Root Directory should be:**
- **Empty** (or `/`)
- **NOT** `Strategic Management Journal`

---

## 🔧 Fix Backend Service

### Step 1: Update Root Directory

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab**
3. **Find "Root Directory"** field
4. **Clear it** (make it empty) or set to `/`
5. **Save**

### Step 2: Verify Start Command

After clearing Root Directory:
1. **Settings tab** → **Deploy section**
2. **Custom Start Command** should now be editable or auto-detect `python api_server.py`
3. **If it still shows npm command**, manually set to: `python api_server.py`

### Step 3: Redeploy

1. **Deployments tab** → **Redeploy**
2. **Wait 2-5 minutes**

### Step 4: Check Logs

After redeploy, logs should show:
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
INFO:     Uvicorn running on http://0.0.0.0:5000
```

---

## 🔧 Fix Frontend Service (if needed)

1. **Railway Dashboard** → "web" service
2. **Settings tab** → **Root Directory**
3. **Should be empty** (or `/`)
4. **Start Command** should be: `npx serve -s build -l $PORT --single`

---

## 📋 Summary

**Repository Structure:**
- GitHub repo root: Contains `api_server.py`, `package.json`, `requirements.txt` directly
- Local directory: Files are in "Strategic Management Journal/" folder (but git repo root is there)

**Railway Configuration:**
- **Backend Root Directory**: Empty (or `/`)
- **Frontend Root Directory**: Empty (or `/`)

**Why:** Railway connects to GitHub, where files are in the repo root, not in a subdirectory.

---

**Clear the Root Directory field in Railway settings and redeploy!**
