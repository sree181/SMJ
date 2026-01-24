# Railway API URL Fix - HTML Instead of JSON Error

## 🚨 Problem

The error `Unexpected token '<', "<!doctype "... is not valid JSON` means:
- Backend is returning HTML (error page) instead of JSON
- This happens when the API URL is incorrect

**Your current request shows:**
```
artistic-upliftment-production-7d16.up.railway.app/analytics/...
```

**Missing:**
1. `https://` protocol
2. `/api` prefix

---

## ✅ Solution: Fix REACT_APP_API_URL

### Step 1: Go to Railway Frontend Service

1. **Railway Dashboard** → Click on **"web"** service
2. **Go to "Variables" tab**
3. **Find `REACT_APP_API_URL`** variable
4. **Click the three dots** (⋮) next to it → **Edit**

### Step 2: Set Correct Value

**The value should be:**
```
https://artistic-upliftment-production-7d16.up.railway.app/api
```

**Important:**
- ✅ Must start with `https://`
- ✅ Must include `/api` at the end
- ✅ No trailing slash after `/api`
- ✅ Use your actual backend URL (replace if different)

### Step 3: Save and Wait

1. **Click "Save"** or "Update"
2. **Railway will automatically redeploy** the frontend
3. **Wait 2-5 minutes** for deployment to complete

### Step 4: Test

1. **Visit**: `https://web-production-ff38d.up.railway.app`
2. **Hard refresh** browser (Ctrl+Shift+R or Cmd+Shift+R)
3. **Open console** (F12) - errors should be gone
4. **Navigate to `/analytics`** - dashboard should load!

---

## 🔍 Verify Backend URL First

Before fixing the frontend, verify your backend is working:

1. **Visit**: `https://artistic-upliftment-production-7d16.up.railway.app/api/health`
2. **Should see**:
   ```json
   {
     "status": "healthy",
     "neo4j_connected": true,
     "timestamp": "..."
   }
   ```

**If this doesn't work:**
- Check backend service logs in Railway
- Verify backend is actually running
- Check backend environment variables

---

## 📋 Correct URL Format

**Wrong:**
```
artistic-upliftment-production-7d16.up.railway.app
artistic-upliftment-production-7d16.up.railway.app/
https://artistic-upliftment-production-7d16.up.railway.app
```

**Correct:**
```
https://artistic-upliftment-production-7d16.up.railway.app/api
```

---

## 🐛 Common Mistakes

1. **Missing `https://`** → Results in relative URL
2. **Missing `/api`** → Backend returns 404 HTML page
3. **Trailing slash** → `https://...railway.app/api/` (extra `/`)
4. **Wrong domain** → Using frontend URL instead of backend URL

---

## ✅ After Fix

Once `REACT_APP_API_URL` is set correctly:
- API requests will go to: `https://artistic-upliftment-production-7d16.up.railway.app/api/*`
- Backend will return JSON (not HTML)
- Dashboard will load with data
- All errors will be resolved! 🎉

---

**Quick Fix:**
1. Railway → "web" service → Variables
2. Edit `REACT_APP_API_URL`
3. Set to: `https://artistic-upliftment-production-7d16.up.railway.app/api`
4. Save and wait for redeploy
5. Test!
