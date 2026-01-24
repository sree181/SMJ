# Railway CORS & API URL Fix - Quick Guide

## 🚨 Problem

When accessing the Railway frontend from another device, you see:
- `CORS policy: No 'Access-Control-Allow-Origin' header`
- `Failed to fetch` errors
- `Cannot connect to backend server`

**Root Cause:** The frontend is trying to connect to `localhost:5000`, which only works on your local machine.

---

## ✅ Solution: Set Environment Variable in Railway

### Step 1: Get Your Backend URL

**If your backend is on Railway:**
1. Go to Railway Dashboard → Your backend service
2. Find the URL (e.g., `https://your-backend-production.up.railway.app`)
3. Copy this URL

**If your backend is NOT on Railway:**
- You need to deploy it to Railway first (see Step 3 below)
- OR use a different hosting service and get that URL

### Step 2: Set Environment Variable in Railway Frontend

1. **Go to Railway Dashboard**: https://railway.app
2. **Select your frontend project/service**
3. **Click "Variables" tab**
4. **Click "New Variable"**
5. **Add:**
   ```
   Name: REACT_APP_API_URL
   Value: https://your-backend-url.railway.app/api
   ```
   **Important:**
   - Replace `your-backend-url.railway.app` with your actual backend URL
   - The URL should end with `/api` (no trailing slash)
   - Example: `https://smj-backend-production.up.railway.app/api`

6. **Click "Add"**

### Step 3: Redeploy Frontend

After adding the environment variable:
- Railway will **automatically trigger a new deployment**
- Wait 2-5 minutes for the build to complete
- The new build will include the environment variable

---

## 🔧 Step 4: Deploy Backend to Railway (If Not Already Deployed)

If your backend is still running locally, you need to deploy it:

### Option A: Deploy Backend to Railway

1. **In Railway Dashboard** → Your project
2. **Click "New Service"** → **"Deploy from GitHub repo"**
3. **Select the same repository**
4. **Set Root Directory**: `Strategic Management Journal` (or wherever `api_server.py` is)
5. **Railway will auto-detect Python**
6. **Set Environment Variables** in the backend service:
   ```
   NEO4J_URI=your-neo4j-uri
   NEO4J_USER=your-neo4j-user
   NEO4J_PASSWORD=your-neo4j-password
   OPENAI_API_KEY=your-openai-key
   PORT=5000
   ```
7. **Set Start Command**: `python api_server.py`
8. **Get the backend URL** from Railway (e.g., `https://your-backend-production.up.railway.app`)
9. **Update frontend's `REACT_APP_API_URL`** to point to this backend URL

### Option B: Use Existing Backend

If your backend is already hosted elsewhere:
- Just set `REACT_APP_API_URL` to point to your existing backend URL
- Make sure CORS allows your Railway frontend domain

---

## 🔒 Step 5: Verify Backend CORS Settings

Make sure your backend (`api_server.py`) allows requests from Railway:

The backend should already have this (check `api_server.py` lines 432-455):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", ""),  # Set FRONTEND_URL in Railway if using custom domain
    ],
    allow_origin_regex=r"https://.*\.(railway\.app|up\.railway\.app)",  # Allows all Railway apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**This should already be configured** - the regex pattern `https://.*\.(railway\.app|up\.railway\.app)` allows all Railway apps.

---

## ✅ Step 6: Test

1. **Visit your Railway frontend URL** (e.g., `https://web-production-ff38d.up.railway.app`)
2. **Open browser console** (F12 → Console tab)
3. **Check for errors** - should see API calls succeeding
4. **Test the dashboard** - navigate to `/analytics`
5. **Verify data loads** - charts should display

---

## 📋 Quick Checklist

- [ ] Backend deployed to Railway (or accessible from internet)
- [ ] Backend URL obtained (e.g., `https://your-backend.railway.app`)
- [ ] `REACT_APP_API_URL` set in Railway frontend variables
- [ ] Frontend redeployed after setting environment variable
- [ ] Backend CORS allows Railway domains (should already be configured)
- [ ] Tested from another device - dashboard loads correctly

---

## 🆘 Troubleshooting

### Issue: Still getting CORS errors

**Check:**
1. `REACT_APP_API_URL` is set correctly (no trailing slash, includes `/api`)
2. Backend is running and accessible (try opening backend URL in browser)
3. Backend CORS regex pattern matches your Railway domain
4. Browser cache cleared (hard refresh: Ctrl+Shift+R or Cmd+Shift+R)

### Issue: "Cannot connect to backend server"

**Check:**
1. Backend URL is correct in `REACT_APP_API_URL`
2. Backend is actually running (check Railway logs)
3. Backend URL is accessible (try in browser: `https://your-backend.railway.app/api/health`)

### Issue: Environment variable not working

**Check:**
1. Variable name is exactly `REACT_APP_API_URL` (case-sensitive)
2. Frontend was redeployed after adding the variable
3. No typos in the URL
4. URL includes `/api` at the end

---

## 📝 Example Configuration

**Frontend Railway Service:**
```
REACT_APP_API_URL = https://smj-backend-production.up.railway.app/api
```

**Backend Railway Service:**
```
NEO4J_URI = neo4j+s://your-database.databases.neo4j.io
NEO4J_USER = neo4j
NEO4J_PASSWORD = your-password
OPENAI_API_KEY = your-key
PORT = 5000
```

**Result:**
- Frontend: `https://web-production-ff38d.up.railway.app`
- Backend: `https://smj-backend-production.up.railway.app`
- API calls: Frontend → `https://smj-backend-production.up.railway.app/api/*`

---

**Last Updated:** 2025-01-23
