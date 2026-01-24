# Fix: Backend Service Running npx (Node.js) Instead of Python

## 🚨 Problem

Backend service is crashing with:
```
/bin/bash: line 1: npx: command not found
```

**Root Cause**: Railway is detecting `nixpacks.toml` (Node.js config) and trying to run the frontend start command for the backend service.

---

## ✅ Solution: Fix Backend Service Configuration

### Step 1: Verify Root Directory in Railway

1. **Railway Dashboard** → Backend service (e.g., "artistic-upliftment")
2. **Settings tab** → **Source** section
3. **Root Directory** should be: `Strategic Management Journal`
4. **If it's empty or `/`**, change it to `Strategic Management Journal`
5. **Save**

### Step 2: Set Start Command Explicitly

1. **Settings tab** → **Deploy** section
2. **Custom Start Command**: 
   ```
   python api_server.py
   ```
3. **Save**

### Step 3: Set Build Command

1. **Settings tab** → **Build** section
2. **Custom Build Command**:
   ```
   pip install -r requirements.backend.txt
   ```
   OR
   ```
   pip install -r requirements.txt
   ```
3. **Save**

### Step 4: Verify Service Type

1. **Settings tab** → Check if there's a **"Service Type"** field
2. **Should be**: `Python` (not `Node.js`)
3. **If it shows Node.js**, Railway is detecting wrong

### Step 5: Delete/Rename nixpacks.toml (If Needed)

If Railway is still detecting Node.js, the `nixpacks.toml` in root might be interfering:

**Option A**: Rename it (if frontend needs it):
```bash
mv nixpacks.toml nixpacks.frontend.toml
```

**Option B**: Ensure backend root directory excludes it (should already be the case if root is `Strategic Management Journal`)

### Step 6: Use Procfile (Already Correct)

The `Procfile` in `Strategic Management Journal` directory already has:
```
web: python api_server.py
```

Railway should use this if root directory is set correctly.

---

## 🔧 Alternative: Create Backend-Specific Config

If the above doesn't work, create `nixpacks.backend.toml` in `Strategic Management Journal`:

```toml
[phases.setup]
nixPkgs = ["python312"]

[phases.install]
cmds = ["pip install -r requirements.backend.txt"]

[start]
cmd = "python api_server.py"
```

---

## ✅ Expected Result

After fix, backend logs should show:
```
Collecting fastapi
Collecting uvicorn
...
✓ Connected to Neo4j
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**NOT:**
```
/bin/bash: line 1: npx: command not found
```

---

## 📋 Quick Checklist

- [ ] Root Directory: `Strategic Management Journal`
- [ ] Start Command: `python api_server.py`
- [ ] Build Command: `pip install -r requirements.backend.txt`
- [ ] Service Type: Python (not Node.js)
- [ ] Redeploy after changes
- [ ] Logs show Python starting (not npx errors)

---

**The key is ensuring Railway uses Python config, not Node.js config!**
