# Railway Force Fresh Deployment - OLLAMA Still Showing

## Problem
Railway backend logs still show:
```
INFO:api_server:Using OLLAMA at http://localhost:11434 with model llama3.1:8b
```

But the local code (commit `34fe29f` and later) has **ZERO** OLLAMA references. Railway is running old cached code.

## Solution: Force Complete Fresh Deployment

### Step 1: Verify Latest Code is Pushed
```bash
# Check current commit
git log --oneline -1

# Should show: 34fe29f Add CSV export script...
# Or later commits

# Verify no OLLAMA in HEAD
git show HEAD:api_server.py | grep -i ollama
# Should return: (empty - no matches)
```

### Step 2: Create a Dummy Change to Force Redeploy
Since Railway might be caching builds, we need to trigger a fresh build:

1. **Add a comment to `api_server.py`** to force a new commit:
   ```python
   # Force Railway redeploy - OLLAMA removed in commit 820d85f
   ```

2. **Commit and push**:
   ```bash
   git add api_server.py
   git commit -m "Force Railway redeploy - ensure OLLAMA removal is deployed"
   git push origin main
   ```

### Step 3: Railway Dashboard Actions

#### A. Delete and Recreate Service (Most Aggressive)
1. Go to Railway Dashboard: https://railway.app
2. Select your **backend service**
3. Go to **Settings** → **Danger Zone**
4. **Delete the service** (this will NOT delete your database or environment variables)
5. Create a **new service** from the same GitHub repo
6. Railway will do a completely fresh build

#### B. Clear Build Cache (Alternative)
1. Go to Railway Dashboard
2. Select your **backend service**
3. Go to **Settings** → **Build**
4. Look for **"Clear Build Cache"** or **"Rebuild"** option
5. Click it to force a fresh build

#### C. Manual Redeploy with Latest Commit
1. Go to Railway Dashboard
2. Select your **backend service**
3. Go to **Deployments** tab
4. Find the **latest commit** (should match your local `git log`)
5. Click **"Redeploy"** on that specific deployment
6. **Monitor logs** - you should see:
   ```
   INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
   ```
   And **NO** OLLAMA messages

### Step 4: Verify Environment Variables
After redeploy, verify these are set in Railway:
- `NEO4J_URI` (no quotes)
- `NEO4J_USER` (no quotes)
- `NEO4J_PASSWORD` (no quotes)
- `OPENAI_API_KEY` (no quotes)
- `PORT` (Railway sets this automatically)

**Important**: Do NOT set:
- `OLLAMA_BASE_URL` (should be removed if present)
- `OLLAMA_MODEL` (should be removed if present)
- `USE_OLLAMA` (should be removed if present)

### Step 5: Verify Deployment
After redeploy, check logs for:
```
✓ Connected to Neo4j
INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
INFO:api_server:Application startup complete
```

**Should NOT see**:
```
INFO:api_server:Using OLLAMA...
```

### Step 6: Test API
```bash
curl https://your-backend.railway.app/api/health
```

Should return 200 OK.

## Why This Happens
Railway caches:
- Build artifacts
- Docker layers
- Python package installations

Sometimes the cache isn't invalidated even when code changes, especially if:
- Dependencies haven't changed
- File structure is similar
- Build commands are identical

## Nuclear Option: New Service
If nothing else works:
1. Create a **completely new Railway service**
2. Connect to the same GitHub repo
3. Set all environment variables again
4. Deploy

This guarantees a fresh build with no cache.

## Verification Checklist
- [ ] Latest code pushed to GitHub (commit `34fe29f` or later)
- [ ] No OLLAMA references in `api_server.py` (verified locally)
- [ ] Railway service redeployed
- [ ] Logs show "Using OpenAI" not "Using OLLAMA"
- [ ] Environment variables set correctly
- [ ] API health check returns 200

## Expected Result
After successful redeploy:
- Backend logs: `INFO:api_server:Using OpenAI for LLM (OpenAI API key found)`
- No OLLAMA messages anywhere
- API endpoints work correctly
- Frontend can connect without CORS errors
