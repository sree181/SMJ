# Railway Backend: Force Python Detection

## 🚨 Problem

Railway is detecting **Node.js** instead of **Python** for the backend service:

```
INFO No package manager inferred, using npm default
↳ Detected Node
↳ Using npm package manager
pip: not found
```

**Root Cause**: Railway sees `package.json` and `Procfile` in root and detects Node.js, but the build command needs Python (`pip install`).

## ✅ Solution: Force Python Detection

### What I Did

1. **Created `requirements.txt`** - Railway uses this to detect Python projects
2. **Created `runtime.txt`** - Specifies Python version (3.12.7)
3. **Pushed to GitHub** - Railway will auto-detect Python on next deployment

### What Railway Should Do Now

After the new commit deploys, Railway should:
1. **Detect Python** (from `requirements.txt` and `runtime.txt`)
2. **Install Python 3.12.7** (from `runtime.txt`)
3. **Run build command**: `pip install -r requirements.backend.txt`
4. **Run start command**: `python api_server.py`

## Verify in Railway

### Step 1: Check Latest Deployment

1. Go to **Deployments** tab
2. Latest deployment should show commit with "Add requirements.txt and runtime.txt"
3. **Build logs** should show:
   ```
   ↳ Detected Python
   ↳ Using pip package manager
   ```

### Step 2: Check Logs

After deployment, logs should show:
```
INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**NOT:**
```
INFO No package manager inferred, using npm default
↳ Detected Node
pip: not found
```

## If Still Detecting Node.js

If Railway still detects Node.js after this fix:

### Option 1: Set Root Directory

1. **Settings** → **Source** section
2. **Root Directory**: Set to `Strategic Management Journal` (not `/`)
3. This ensures Railway only sees Python files, not `package.json`

### Option 2: Delete and Recreate Service

1. **Settings** → **Danger Zone** → **Delete Service**
2. **Create new service** from GitHub
3. **Root Directory**: `Strategic Management Journal`
4. Railway should auto-detect Python

## Files Created

- `requirements.txt` - Python dependencies (copied from `requirements.backend.txt`)
- `runtime.txt` - Python version specification (`python-3.12.7`)

These files help Railway detect Python instead of Node.js.
