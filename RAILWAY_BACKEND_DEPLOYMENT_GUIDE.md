# Railway Backend Deployment - Complete Step-by-Step Guide

## 🎯 Goal
Deploy your FastAPI backend to Railway so your frontend (`web-production-ff38d.up.railway.app`) can connect to it.

---

## 📋 Prerequisites

Before starting, make sure you have:
- ✅ Railway account (you already have this)
- ✅ Neo4j database credentials (URI, username, password)
- ✅ OpenAI API key (or OLLAMA if using local LLM)
- ✅ GitHub repository connected to Railway

---

## 🚀 Step 1: Create New Backend Service in Railway

1. **Go to Railway Dashboard**: https://railway.app
2. **Select your existing project** (the one with your "web" frontend service)
3. **Click "New Service"** (top right, or "+" button)
4. **Select "Deploy from GitHub repo"**
5. **Choose the same repository** you used for the frontend
6. **Railway will start detecting the project**

---

## ⚙️ Step 2: Configure Backend Service

### 2.1 Set Root Directory

1. **In the new service**, go to **"Settings"** tab
2. **Find "Root Directory"** setting
3. **Set it to**: `Strategic Management Journal`
   - (Or whatever directory contains `api_server.py`)
4. **Save**

### 2.2 Railway Will Auto-Detect Python

Railway should automatically:
- Detect it's a Python project
- Use Python buildpack
- Look for `requirements.txt`

**If it doesn't auto-detect:**
- Go to **Settings** → **Build**
- Set **Build Command**: `pip install -r requirements.txt`
- Set **Start Command**: `python api_server.py`

---

## 🔐 Step 3: Set Environment Variables

**Critical:** You must set these environment variables for the backend to work.

1. **In Railway Dashboard** → Your **backend service**
2. **Go to "Variables" tab**
3. **Add each of these variables:**

### Required Variables:

```
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
OPENAI_API_KEY=sk-your-openai-key-here
PORT=5000
```

### Optional Variables (if needed):

```
FRONTEND_URL=https://web-production-ff38d.up.railway.app
```

**Important Notes:**
- Replace all placeholder values with your actual credentials
- `PORT` is usually set automatically by Railway, but you can specify it
- `FRONTEND_URL` helps with CORS (though the regex pattern should already allow it)

### How to Add Variables:

1. Click **"New Variable"**
2. Enter **Name** (e.g., `NEO4J_URI`)
3. Enter **Value** (e.g., `neo4j+s://your-database.databases.neo4j.io`)
4. Click **"Add"**
5. Repeat for each variable

---

## 🏗️ Step 4: Configure Build Settings

### Option A: Let Railway Auto-Detect (Recommended)

Railway should automatically:
- Detect Python from `requirements.txt`
- Install dependencies
- Run `api_server.py`

### Option B: Manual Configuration

If auto-detection doesn't work:

1. **Go to Settings** → **Build**
2. **Build Command**: 
   ```bash
   pip install -r requirements.txt
   ```
3. **Start Command**:
   ```bash
   python api_server.py
   ```

**OR** if Railway sets `PORT` automatically, you might need:

```bash
uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

---

## 📝 Step 5: Create Railway Configuration Files (Optional but Recommended)

Create these files in your repository to help Railway:

### `Procfile` (for backend)

Create `Procfile` in the `Strategic Management Journal` directory:

```
web: python api_server.py
```

**OR** if Railway uses `$PORT`:

```
web: uvicorn api_server:app --host 0.0.0.0 --port $PORT
```

### `railway.json` (for backend)

Create `railway.json` in the `Strategic Management Journal` directory:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python api_server.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## 🚀 Step 6: Deploy

1. **Railway will automatically start building** when you:
   - Add the service
   - Push changes to GitHub
   - Update environment variables

2. **Watch the build logs**:
   - Go to **"Deployments"** tab
   - Click on the deployment
   - Watch for errors

3. **Wait for deployment to complete** (usually 2-5 minutes)

---

## 🔗 Step 7: Get Your Backend URL

1. **After deployment succeeds**, go to **"Settings"** tab
2. **Find "Domains"** or **"Networking"** section
3. **Copy your backend URL** (e.g., `https://your-backend-production.up.railway.app`)

**OR** check the **"Deployments"** tab - the URL should be visible there.

**Example backend URL:**
```
https://smj-backend-production.up.railway.app
```

---

## 🔧 Step 8: Update Frontend to Use Backend URL

1. **Go to Railway Dashboard** → Your **frontend service** ("web")
2. **Go to "Variables" tab**
3. **Add or update**:
   ```
   Name: REACT_APP_API_URL
   Value: https://your-backend-url.railway.app/api
   ```
   **Replace `your-backend-url.railway.app` with your actual backend URL from Step 7**
   
   **Example:**
   ```
   REACT_APP_API_URL=https://smj-backend-production.up.railway.app/api
   ```

4. **Important:** 
   - URL must end with `/api` (no trailing slash)
   - Railway will automatically redeploy the frontend after adding the variable

---

## ✅ Step 9: Test Your Deployment

### Test Backend Directly:

1. **Open your backend URL** in browser:
   ```
   https://your-backend-url.railway.app/api/health
   ```

2. **Expected Response:**
   ```json
   {
     "status": "healthy",
     "neo4j_connected": true,
     "timestamp": "..."
   }
   ```

### Test Frontend:

1. **Visit your frontend URL:**
   ```
   https://web-production-ff38d.up.railway.app
   ```

2. **Open browser console** (F12 → Console tab)

3. **Check for errors** - should see API calls succeeding

4. **Navigate to `/analytics`** - dashboard should load with data

---

## 🐛 Troubleshooting

### Issue: Backend deployment fails

**Check:**
- Build logs for specific errors
- `requirements.txt` exists and is correct
- Python version compatibility
- Environment variables are set correctly

### Issue: Backend starts but returns 500 errors

**Check:**
- Neo4j credentials are correct
- Neo4j database is accessible from Railway
- Check backend logs in Railway dashboard

### Issue: CORS errors in frontend

**Check:**
- Backend CORS regex pattern allows Railway domains (should already be configured)
- `REACT_APP_API_URL` is set correctly in frontend
- Backend URL is correct (no typos)

### Issue: "Cannot connect to backend"

**Check:**
- Backend is actually running (check Railway logs)
- Backend URL is accessible (try in browser)
- `REACT_APP_API_URL` points to correct backend URL
- Frontend was redeployed after setting environment variable

---

## 📊 Summary: What You'll Have

After completing these steps:

**Frontend Service:**
- URL: `https://web-production-ff38d.up.railway.app`
- Environment Variable: `REACT_APP_API_URL=https://your-backend.railway.app/api`

**Backend Service:**
- URL: `https://your-backend-production.up.railway.app`
- Environment Variables:
  - `NEO4J_URI`
  - `NEO4J_USER`
  - `NEO4J_PASSWORD`
  - `OPENAI_API_KEY`
  - `PORT=5000`

**Result:**
- Frontend makes API calls to: `https://your-backend-production.up.railway.app/api/*`
- Backend serves API and connects to Neo4j
- Everything works from any device! 🎉

---

## 🎯 Quick Checklist

- [ ] Created new backend service in Railway
- [ ] Set root directory to `Strategic Management Journal`
- [ ] Added all required environment variables
- [ ] Backend deployed successfully
- [ ] Got backend URL from Railway
- [ ] Set `REACT_APP_API_URL` in frontend service
- [ ] Frontend redeployed
- [ ] Tested backend health endpoint
- [ ] Tested frontend dashboard
- [ ] Verified from another device

---

**Last Updated:** 2025-01-23  
**Your Frontend URL:** `https://web-production-ff38d.up.railway.app`
