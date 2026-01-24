# Railway Backend Deployment - Quick Start

## 🎯 Your Situation
- ✅ Frontend deployed: `web-production-ff38d.up.railway.app`
- ❌ Backend NOT deployed yet
- 🔧 Need to deploy backend and connect frontend to it

---

## ⚡ Quick Steps (5 minutes)

### 1️⃣ Create Backend Service in Railway

1. Go to **Railway Dashboard** → Your project
2. Click **"New Service"** → **"Deploy from GitHub repo"**
3. Select **same repository** as frontend
4. Railway will start detecting

### 2️⃣ Configure Backend

**In the new service:**

1. **Settings** → **Root Directory**: `Strategic Management Journal`
2. **Variables** tab → Add these:

```
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
OPENAI_API_KEY=sk-your-key-here
```

**Replace with your actual values!**

### 3️⃣ Wait for Deployment

- Railway will auto-build (2-5 minutes)
- Watch **Deployments** tab for progress
- Wait for "Deployment successful" ✅

### 4️⃣ Get Backend URL

After deployment:
- **Settings** → **Domains** section
- Copy the URL (e.g., `https://your-backend-production.up.railway.app`)

### 5️⃣ Connect Frontend to Backend

1. Go to **frontend service** ("web")
2. **Variables** tab → Add:

```
REACT_APP_API_URL=https://your-backend-url.railway.app/api
```

**Replace `your-backend-url.railway.app` with URL from Step 4!**

3. Frontend will auto-redeploy

### 6️⃣ Test

1. Visit: `https://web-production-ff38d.up.railway.app`
2. Open console (F12) - should see API calls working
3. Navigate to `/analytics` - dashboard should load! 🎉

---

## 🔍 Where to Find Things in Railway

**Your Project Structure:**
```
Railway Project
├── web (frontend) → https://web-production-ff38d.up.railway.app
└── [new backend service] → https://your-backend.railway.app
```

**Each Service Has:**
- **Deployments** tab → See build logs and status
- **Variables** tab → Set environment variables
- **Settings** tab → Configure root directory, build commands
- **Metrics** tab → Monitor performance

---

## 🆘 Common Issues

### "Build failed"
- Check build logs in **Deployments** tab
- Verify `requirements.txt` exists
- Check Python version compatibility

### "Cannot connect to backend"
- Verify backend URL is correct in `REACT_APP_API_URL`
- Check backend is running (look at backend service logs)
- Test backend directly: `https://your-backend.railway.app/api/health`

### "CORS error"
- Backend CORS is already configured for Railway
- Just make sure `REACT_APP_API_URL` is set correctly

---

## 📝 Environment Variables Summary

### Frontend Service ("web"):
```
REACT_APP_API_URL=https://your-backend.railway.app/api
```

### Backend Service (new):
```
NEO4J_URI=neo4j+s://...
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
OPENAI_API_KEY=sk-...
```

---

## ✅ Done!

Once both services are deployed and connected:
- Frontend: `https://web-production-ff38d.up.railway.app`
- Backend: `https://your-backend.railway.app`
- They talk to each other automatically! 🚀

---

**Need more details?** See `RAILWAY_BACKEND_DEPLOYMENT_GUIDE.md` for complete instructions.
