# Railway Backend Still Showing OLLAMA - Clear Cache Fix

## ✅ Settings Are Correct!

Your Railway backend settings show:
- ✅ Start command: `python api_server.py` (correct)
- ✅ Build command: `pip install -r requirements.backend.txt` (correct)
- ✅ Root directory: `/` (correct)

But OLLAMA logs are still appearing. This means Railway is using a **cached build**.

## Solution: Force Fresh Build

### Option 1: Delete and Recreate Service (Most Reliable)

Since settings are correct but deployment is wrong, Railway is likely using cached build artifacts.

1. **Save your environment variables first:**
   - Go to **Variables** tab
   - Copy all values:
     - `NEO4J_URI`
     - `NEO4J_USER`
     - `NEO4J_PASSWORD`
     - `OPENAI_API_KEY`
     - Any others

2. **Delete the backend service:**
   - Go to **Settings** tab
   - Scroll to bottom → **"Danger Zone"**
   - Click **"Delete Service"**
   - Confirm

3. **Create new backend service:**
   - Click **"New Service"** → **"Deploy from GitHub repo"**
   - Select same repository: `sree181/SMJ`
   - **Root Directory**: `/` (or leave empty)
   - Railway should auto-detect Python
   - **Verify** start command shows: `python api_server.py`

4. **Set environment variables:**
   - Go to **Variables** tab
   - Add all the variables you saved earlier
   - **Important**: Don't use quotes in values

5. **Wait for deployment** (2-5 minutes)

6. **Check logs** - should show:
   ```
   INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
   ```

### Option 2: Clear Build Cache (If Available)

1. Go to **Settings** → **Build** section
2. Look for **"Clear Build Cache"** or **"Rebuild"** button
3. Click it
4. Wait for redeploy

### Option 3: Trigger Fresh Build with Code Change

Since Railway might be caching based on file hashes, make a small change:

1. **Add a comment to `api_server.py`**:
   ```python
   # Railway cache bust - force fresh build at 2026-01-25
   ```

2. **Commit and push**:
   ```bash
   git add api_server.py
   git commit -m "Force Railway fresh build - clear cache"
   git push origin main
   ```

3. **Railway should auto-deploy** with the new commit

4. **Monitor logs** - should show OpenAI, not OLLAMA

## Why This Happens

Railway caches:
- Docker image layers
- Python package installations
- Build artifacts

Even when settings are correct, if the code hasn't changed significantly, Railway might reuse cached builds that contain old code.

## Verification After Fix

After redeploy, check logs for:

**✅ CORRECT:**
```
INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**❌ WRONG:**
```
INFO:api_server:Using OLLAMA at http://localhost:11434...
```

## Quick Checklist

- [ ] Settings show `python api_server.py` (already ✅)
- [ ] Environment variables are set (verify in Variables tab)
- [ ] Service deleted and recreated OR cache cleared
- [ ] Latest commit deployed (check Deployments tab)
- [ ] Logs show "Using OpenAI" not "Using OLLAMA"
