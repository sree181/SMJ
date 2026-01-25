# URGENT: Fix Railway Backend Start Command

## Problem Found

Your Railway backend service has the **WRONG start command**:

**Current (WRONG):**
```
npx serve -s build -l $PORT --single
```
This is the **frontend** start command, not the backend!

**Should be:**
```
python api_server.py
```

## Why This Matters

Railway is trying to run a Node.js command (`npx serve`) on your Python backend, which:
1. Won't work (Python service can't run Node.js commands)
2. May be falling back to cached/old builds
3. Explains why OLLAMA logs are still showing

## Fix Steps

### Option 1: Update Start Command in Railway (Recommended)

1. Go to Railway Dashboard: https://railway.app
2. Select your **backend service**
3. Go to **Settings** tab
4. Scroll to **"Deploy"** section
5. Find **"Start Command"** field
6. **Change it to:**
   ```
   python api_server.py
   ```
7. **Save** the changes
8. Railway will automatically redeploy

### Option 2: Use Environment Variable (If field is not editable)

1. Go to **Variables** tab
2. Add a new variable:
   - **Name**: `START_COMMAND`
   - **Value**: `python api_server.py`
3. Save and redeploy

### Option 3: Use Procfile (If Railway supports it)

Railway should automatically detect `Procfile` in the root. Make sure your `Procfile` contains:
```
web: python api_server.py
```

## Also Check Build Command

While you're in Settings, verify the **Build Command** is:
```
pip install -r requirements.backend.txt
```

## After Fixing

1. **Redeploy** the service (Railway should auto-redeploy after saving)
2. **Check Logs** - you should see:
   ```
   INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
   ```
3. **No more OLLAMA messages**

## Why Commit Hash Doesn't Match

The commit hash `8e9c1eb2` vs `a888239` might be:
- Railway's internal commit reference (different from GitHub commit hash)
- A different branch being deployed
- A caching issue

**Focus on fixing the start command first** - that's the critical issue preventing proper deployment.

## Verification Checklist

After fixing:
- [ ] Start command is `python api_server.py`
- [ ] Build command is `pip install -r requirements.backend.txt`
- [ ] Service redeploys successfully
- [ ] Logs show "Using OpenAI" not "Using OLLAMA"
- [ ] API health check works: `https://your-backend-url/api/health`
