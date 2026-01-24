# Railway Deployment - Setup Complete ✅

## What's Been Done

✅ **Git Repository Initialized**
- Git repository created in your project directory
- Ready to commit and push to GitHub

✅ **Railway Configuration Files Created**
- `railway.json` - Railway build configuration
- `nixpacks.toml` - Nixpacks build configuration  
- `Procfile` - Start command with React Router support
- `.env.example` - Environment variable template

✅ **Backend CORS Updated**
- Updated `api_server.py` to allow Railway domains
- Added regex pattern for Railway URLs: `https://.*\.(railway\.app|up\.railway\.app)`

✅ **Frontend Dependencies**
- Added `serve` package (v14.2.5) for static file serving
- Build tested and working

---

## Next Steps to Deploy

### Step 1: Commit Files to Git

```bash
cd "Strategic Management Journal"
git add .
git commit -m "Add Railway deployment configuration"
```

### Step 2: Create GitHub Repository (if needed)

1. Go to [github.com](https://github.com)
2. Click **"New repository"**
3. Name it (e.g., `smj-research-dashboard`)
4. **Don't** initialize with README (you already have files)
5. Click **"Create repository"**

### Step 3: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub details.

### Step 4: Deploy Frontend to Railway

1. **Go to Railway**: https://railway.app
2. **Sign up/Login** (free tier available)
3. **New Project** → **Deploy from GitHub repo**
4. **Select your repository**
5. Railway will auto-detect it's a Node.js project

**Configure Settings:**
- **Root Directory**: Leave empty (or set to `Strategic Management Journal` if deploying from repo root)
- **Build Command**: `npm install && npm run build` (auto-detected)
- **Start Command**: `npx serve -s build -l $PORT --single` (auto-detected from Procfile)

### Step 5: Set Environment Variable

In Railway dashboard → Your project → **Variables** tab:

**Add:**
```
REACT_APP_API_URL=https://your-backend.railway.app/api
```

**Important:** 
- Replace `your-backend.railway.app` with your actual backend URL
- If backend is on Railway, you'll get a URL like `https://your-backend-production.up.railway.app`
- The URL should end with `/api` (no trailing slash)

### Step 6: Deploy Backend (if not already deployed)

If you need to deploy the backend to Railway:

1. **Create new Railway project** for backend
2. **Connect same GitHub repo**
3. **Set Root Directory**: `Strategic Management Journal` (or wherever `api_server.py` is)
4. **Build Command**: `pip install -r requirements.txt`
5. **Start Command**: `python api_server.py`
6. **Add Environment Variables**:
   - `NEO4J_URI`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`
   - `OPENAI_API_KEY` (or OLLAMA settings if using local LLM)
   - `PORT` (Railway sets this automatically)

### Step 7: Update Frontend Environment Variable

Once backend is deployed, update frontend's `REACT_APP_API_URL` to point to the backend Railway URL.

---

## Testing Deployment

1. **Visit your Railway frontend URL** (e.g., `https://your-frontend.up.railway.app`)
2. **Open browser console** (F12) → Console tab
3. **Check for errors**
4. **Test the dashboard**: Navigate to `/analytics`
5. **Verify API calls work**: Check Network tab in browser dev tools

---

## Troubleshooting

### Issue: "Cannot connect to backend"

**Check:**
- `REACT_APP_API_URL` is set correctly in Railway
- Backend is running and accessible
- CORS is configured correctly in backend

### Issue: "404 on routes like /analytics"

**Solution:** The `--single` flag in Procfile should fix this. If not, verify:
- `Procfile` contains: `web: npx serve -s build -l $PORT --single`
- Railway is using the Procfile

### Issue: "Build fails"

**Check:**
- Railway build logs for specific errors
- All dependencies are in `package.json`
- Node.js version (Railway uses Node 18 by default)

---

## Quick Command Reference

```bash
# Initialize git (already done)
git init

# Add files
git add .

# Commit
git commit -m "Add Railway deployment configuration"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push to GitHub
git push -u origin main
```

---

## Railway URLs After Deployment

- **Frontend**: `https://your-frontend.up.railway.app`
- **Backend**: `https://your-backend.up.railway.app`
- **Backend API**: `https://your-backend.up.railway.app/api`

---

## Share with Coauthor

Once deployed, share the **frontend Railway URL** with your coauthor. They can:
- Access the dashboard from any browser
- No local setup required
- Full access to all analytics features

---

**Need Help?** 
- Railway Docs: https://docs.railway.app
- Full Guide: See `RAILWAY_DEPLOYMENT_GUIDE.md`
