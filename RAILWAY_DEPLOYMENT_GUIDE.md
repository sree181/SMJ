# Railway Deployment Guide - Frontend Dashboard

This guide will help you deploy the React frontend dashboard to Railway so your coauthor can access it.

---

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be in a GitHub repository (or Railway will create one)
3. **Backend API URL**: You'll need the URL of your deployed backend API (also on Railway or elsewhere)

---

## Step 1: Prepare Your Repository

### 1.1 Ensure All Files Are Committed

Make sure all your frontend files are committed to git:

```bash
cd "Strategic Management Journal"
git add .
git commit -m "Prepare for Railway deployment"
git push
```

### 1.2 Verify Build Works Locally

Test that the build process works:

```bash
npm install
npm run build
```

This should create a `build/` directory with your compiled React app.

---

## Step 2: Deploy Backend API First (If Not Already Deployed)

**Important:** The frontend needs your backend API to be running. You have two options:

### Option A: Deploy Backend to Railway

1. Create a new Railway project for your backend
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python api_server.py`
5. Add environment variables:
   - `NEO4J_URI`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`
   - `OPENAI_API_KEY` (or OLLAMA settings)
6. Note the Railway URL (e.g., `https://your-backend.railway.app`)

### Option B: Keep Backend Running Locally (Not Recommended for Production)

If you keep the backend running locally, you'll need to:
- Use a tunneling service (ngrok, localtunnel) to expose it
- Update the frontend API URL to point to the tunnel

---

## Step 3: Deploy Frontend to Railway

### 3.1 Create New Railway Project

1. Go to [railway.app](https://railway.app)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Select the **"Strategic Management Journal"** directory (or root if that's where your frontend is)

### 3.2 Configure Build Settings

Railway should auto-detect it's a Node.js project. Verify these settings:

**Build Command:**
```bash
npm install && npm run build
```

**Start Command:**
```bash
npx serve -s build -l $PORT
```

**OR** Railway will use the `Procfile` or `nixpacks.toml` we created.

### 3.3 Install Serve Package (If Needed)

Add `serve` to your `package.json` dependencies:

```json
{
  "dependencies": {
    ...
    "serve": "^14.2.0"
  }
}
```

Or Railway will install it via `npx serve`.

### 3.4 Set Environment Variables

In Railway dashboard, go to your project → **Variables** tab and add:

```
REACT_APP_API_URL=https://your-backend.railway.app/api
```

**Important:** 
- Replace `your-backend.railway.app` with your actual backend Railway URL
- The URL should NOT have a trailing slash
- The URL should include `/api` at the end

### 3.5 Deploy

1. Railway will automatically start building
2. Watch the build logs for any errors
3. Once built, Railway will start the server
4. Railway will provide a URL like: `https://your-frontend.railway.app`

---

## Step 4: Configure CORS (Backend)

Make sure your backend (`api_server.py`) allows requests from your Railway frontend URL.

In `api_server.py`, update CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-frontend.railway.app",  # Add your Railway URL
        "https://*.railway.app"  # Or allow all Railway apps
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Redeploy your backend after this change.

---

## Step 5: Test Deployment

1. Visit your Railway frontend URL
2. Check browser console for any errors
3. Test the dashboard:
   - Navigate to `/analytics`
   - Check if API calls are working
   - Verify data loads correctly

---

## Step 6: Share with Coauthor

1. Share the Railway frontend URL with your coauthor
2. They can access it from any browser
3. No local setup required!

---

## Troubleshooting

### Issue: "Cannot connect to backend server"

**Solution:**
- Verify `REACT_APP_API_URL` is set correctly in Railway
- Check backend is running and accessible
- Verify CORS settings in backend

### Issue: "Build fails"

**Solution:**
- Check Railway build logs
- Ensure `package.json` has all dependencies
- Verify Node.js version (Railway uses Node 18 by default)

### Issue: "Blank page after deployment"

**Solution:**
- Check browser console for errors
- Verify `REACT_APP_API_URL` is set
- Check that `build/` directory was created
- Verify `serve` command is working

### Issue: "Routes not working (404 errors)"

**Solution:**
- This is a known issue with React Router on static hosting
- We need to configure `serve` to handle client-side routing
- Update `Procfile` or start command to use `serve -s build -l $PORT --single`

---

## Advanced Configuration

### Custom Domain

Railway allows you to add a custom domain:
1. Go to project → **Settings** → **Domains**
2. Add your custom domain
3. Update CORS in backend to include your custom domain

### Environment-Specific Builds

You can create different builds for different environments:

```bash
# Development
REACT_APP_API_URL=http://localhost:5000/api

# Production
REACT_APP_API_URL=https://your-backend.railway.app/api
```

---

## File Structure for Railway

Railway will look for these files (in order of priority):

1. `Procfile` - Contains start command
2. `nixpacks.toml` - Nixpacks configuration
3. `railway.json` - Railway configuration
4. Auto-detection based on `package.json`

---

## Quick Reference

**Frontend Railway URL:** `https://your-frontend.railway.app`  
**Backend API URL:** `https://your-backend.railway.app/api`  
**Environment Variable:** `REACT_APP_API_URL=https://your-backend.railway.app/api`

---

## Next Steps

1. ✅ Deploy backend to Railway (if not already done)
2. ✅ Deploy frontend to Railway
3. ✅ Set `REACT_APP_API_URL` environment variable
4. ✅ Update backend CORS settings
5. ✅ Test deployment
6. ✅ Share URL with coauthor

---

**Need Help?** Check Railway's documentation: https://docs.railway.app
