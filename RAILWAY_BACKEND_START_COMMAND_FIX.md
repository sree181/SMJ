# Fix Railway Backend Start Command (Field Not Editable)

## 🚨 Problem

The start command field in Railway is **not editable** because it's reading from `railway.json`. The backend service needs to run `python api_server.py` but it's using the frontend command.

---

## ✅ Solution Options

### Option 1: Use Environment Variable (Easiest)

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Variables tab**
3. **Add new variable:**
   ```
   Name: START_COMMAND
   Value: python api_server.py
   ```
4. **Save**
5. **Redeploy**

Railway should use this environment variable to override the start command.

---

### Option 2: Create Procfile for Backend

Since Railway might detect a `Procfile` and use it instead of `railway.json`:

1. **In your local repo**, create/update `Procfile` in `Strategic Management Journal` directory:
   ```
   web: python api_server.py
   ```

2. **Commit and push:**
   ```bash
   cd "Strategic Management Journal"
   git add Procfile
   git commit -m "Add Procfile for backend service"
   git push
   ```

3. **Railway will auto-redeploy** and should use the Procfile

**Note:** This might conflict with the frontend if both services read the same Procfile. If that happens, use Option 1 or 3.

---

### Option 3: Delete and Recreate Backend Service

If the above don't work:

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab** → Scroll to bottom
3. **Find "Danger Zone"** or "Delete Service"
4. **Delete the service** (don't worry, you can recreate it)
5. **Create new service:**
   - **New Service** → **Deploy from GitHub repo**
   - **Select same repository**
   - **Set Root Directory**: `Strategic Management Journal`
   - **Railway should auto-detect Python** (from `requirements.txt` and `api_server.py`)
   - **Set environment variables** (NEO4J_URI, etc.)
   - **Verify start command** shows `python api_server.py` (should auto-detect)

---

### Option 4: Temporarily Remove railway.json

If Railway is prioritizing `railway.json` over other configs:

1. **Rename `railway.json`** to `railway.frontend.json`:
   ```bash
   cd "Strategic Management Journal"
   git mv railway.json railway.frontend.json
   git commit -m "Rename railway.json to avoid backend conflict"
   git push
   ```

2. **Create `Procfile`** with backend command:
   ```
   web: python api_server.py
   ```

3. **Railway will use Procfile** for both services, or auto-detect Python for backend

4. **For frontend**, you can set start command manually in Railway settings (it should be editable now)

---

## 🎯 Recommended: Try Option 1 First

**Easiest and least disruptive:**

1. **Variables tab** → Add `START_COMMAND=python api_server.py`
2. **Redeploy**
3. **Check logs** - should show Python starting

If that doesn't work, try Option 2 (Procfile).

---

## ✅ After Fix

Once the start command is correct, logs should show:
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**NOT:**
```
npm warn config production
INFO  Accepting connections at http://localhost:8080
```

---

**Try Option 1 first - it's the quickest!**
