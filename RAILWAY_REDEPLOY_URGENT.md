# Urgent: Railway Backend Not Deployed with Latest Code

## Problem

Railway backend logs show it's still using OLLAMA:
```
INFO:api_server:Using OLLAMA at http://localhost:11434 with model llama3.1:8b
```

But the latest code (commit `cbfbab2` and `de3d451`) has **removed all OLLAMA code**.

## Root Cause

Railway backend service hasn't redeployed with the latest code from GitHub.

## Solution: Force Railway Redeploy

### Option 1: Manual Redeploy (Recommended)

1. Go to Railway Dashboard: https://railway.app
2. Select your **backend service** (not frontend)
3. Go to **Deployments** tab
4. Click **"Redeploy"** on the latest deployment
5. Or click **"Deploy"** → **"Deploy Latest Commit"**

### Option 2: Trigger via Git Push

The code is already pushed. If Railway auto-deploy is enabled, it should deploy automatically. If not:

1. Check Railway service settings:
   - Go to your backend service
   - Settings → **Source**
   - Ensure **"Auto Deploy"** is enabled
   - Ensure it's connected to the correct GitHub repo and branch (`main`)

2. If auto-deploy is disabled, manually trigger:
   - Deployments → **"Deploy Latest Commit"**

### Option 3: Force Redeploy via Environment Variable

1. Go to backend service → **Variables**
2. Add a temporary variable: `FORCE_REDEPLOY=1`
3. Save (this triggers a redeploy)
4. Remove the variable after deployment

## Verify Deployment

After redeploy, check the logs. You should see:
```
INFO:api_server:Using OpenAI for LLM (OpenAI API key found)
```

**NOT:**
```
INFO:api_server:Using OLLAMA at http://localhost:11434
```

## Frontend Dashboard Issues

The Topics and Authors tabs are not visible because:

1. **Frontend might not be rebuilt** - Check frontend service deployment status
2. **Backend endpoints might be failing** - Check browser console for API errors
3. **Data might not be loading** - Check Network tab in browser DevTools

### Fix Frontend:

1. Go to Railway Dashboard
2. Select **frontend service** (usually named "web")
3. Go to **Deployments** tab
4. Click **"Redeploy"** or **"Deploy Latest Commit"**
5. Wait for build to complete (2-5 minutes)

## Expected Behavior After Fix

✅ Backend logs show: `Using OpenAI for LLM`
✅ No OLLAMA references in logs
✅ Frontend shows "Authors" and "Phenomena" tabs
✅ "Topics by Period" chart appears in Analytics Chart tab
✅ All API endpoints return data successfully

## Quick Checklist

- [ ] Backend service redeployed (check logs for "Using OpenAI")
- [ ] Frontend service redeployed (check build completed)
- [ ] Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- [ ] Check browser console for errors
- [ ] Verify API calls in Network tab
