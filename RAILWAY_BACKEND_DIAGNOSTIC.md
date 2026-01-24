# Railway Backend CORS Diagnostic Guide

## 🚨 Problem: CORS Errors Persist

Even after code changes, CORS errors continue. This suggests the backend may not have redeployed or isn't running properly.

---

## ✅ Step 1: Verify Backend Has Redeployed

1. **Go to Railway Dashboard**: https://railway.app
2. **Click on "artistic-upliftment" service** (your backend)
3. **Go to "Deployments" tab**
4. **Check the latest deployment:**
   - Should show commit message: `"Fix CORS: set allow_credentials=False when using allow_origins=['*']"`
   - Should show status: **"Deployment successful"** ✅
   - Should be from **within the last 10 minutes**

**If deployment is still in progress or failed:**
- Wait for it to complete
- If it failed, check the logs for errors

---

## ✅ Step 2: Test Backend Directly

Open a new browser tab and visit:

```
https://artistic-upliftment-production-7d16.up.railway.app/api/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "neo4j_connected": true,
  "timestamp": "..."
}
```

**If this doesn't work:**
- Backend is not running or not accessible
- Check backend logs in Railway
- Verify environment variables are set

---

## ✅ Step 3: Test CORS from Browser Console

1. **Open your frontend**: `https://web-production-ff38d.up.railway.app`
2. **Open browser console** (F12)
3. **Run this command:**
   ```javascript
   fetch('https://artistic-upliftment-production-7d16.up.railway.app/api/health', {
     method: 'GET',
     headers: {
       'Content-Type': 'application/json'
     }
   })
   .then(response => {
     console.log('Status:', response.status);
     console.log('Headers:', [...response.headers.entries()]);
     return response.json();
   })
   .then(data => console.log('Data:', data))
   .catch(error => console.error('Error:', error));
   ```

**What to look for:**
- If it works: CORS is fixed! ✅
- If CORS error: Backend hasn't redeployed or CORS config is wrong
- If network error: Backend is not running

---

## ✅ Step 4: Check Backend Logs

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Deployments tab** → Click on latest deployment
3. **Click "View logs"**
4. **Look for:**
   - `✓ Connected to Neo4j`
   - `✓ Advanced analytics endpoints loaded`
   - `Application startup complete`
   - Any error messages

**Common errors:**
- `ModuleNotFoundError` → Dependencies not installed
- `Neo4j connection failed` → Wrong credentials
- `Port already in use` → Port conflict

---

## ✅ Step 5: Manually Trigger Redeploy

If the backend hasn't redeployed automatically:

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab**
3. **Find "Redeploy" or "Deploy" button**
4. **Click it** to manually trigger a new deployment
5. **Wait 2-5 minutes** for deployment to complete

---

## ✅ Step 6: Verify Environment Variables

Make sure these are set in the backend service:

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Variables tab**
3. **Verify these exist:**
   - `NEO4J_URI`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`
   - `OPENAI_API_KEY`
   - `PORT` (optional, Railway sets this automatically)

---

## 🔧 Alternative: Check if Backend is Using Correct Code

The CORS configuration should be:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)
```

**To verify:**
1. Check the latest commit in Railway shows the CORS fix
2. Or check backend logs for CORS-related messages

---

## 🆘 If Still Not Working

### Option 1: Restart Backend Service

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab**
3. **Find "Restart" button**
4. **Click it** to restart the service

### Option 2: Check Railway Service Status

1. **Railway Dashboard** → "artistic-upliftment" service
2. **Check if status shows "Online"** (green dot)
3. **If "Offline" or "Error"**, there's a problem with the service

### Option 3: Test with curl

From your terminal:
```bash
curl -X OPTIONS https://artistic-upliftment-production-7d16.up.railway.app/api/health \
  -H "Origin: https://web-production-ff38d.up.railway.app" \
  -H "Access-Control-Request-Method: GET" \
  -v
```

**Look for:**
- `Access-Control-Allow-Origin: *` in response headers
- Status 200 or 204

---

## 📋 Quick Checklist

- [ ] Backend has redeployed (check Deployments tab)
- [ ] Backend health endpoint works (`/api/health`)
- [ ] Backend logs show no errors
- [ ] Environment variables are set correctly
- [ ] Backend service status is "Online"
- [ ] Tested CORS from browser console
- [ ] Still getting CORS errors? → Check backend logs for startup errors

---

**Most likely issue:** Backend hasn't redeployed yet. Wait 5-10 minutes after the git push, or manually trigger a redeploy in Railway.
