# Railway Deployment - Quick Start Checklist

## ✅ Pre-Deployment Checklist

- [ ] Backend API is deployed to Railway (or running elsewhere)
- [ ] Backend Railway URL is available (e.g., `https://your-backend.railway.app`)
- [ ] Frontend builds successfully locally (`npm run build`)
- [ ] All files committed to git

## 🚀 Deployment Steps

### 1. Install Dependencies
```bash
npm install
```

### 2. Test Build Locally
```bash
npm run build
```
This should create a `build/` directory.

### 3. Deploy to Railway

1. **Go to Railway**: https://railway.app
2. **New Project** → **Deploy from GitHub repo**
3. **Select your repository**
4. **Configure:**
   - Build Command: `npm install && npm run build`
   - Start Command: `npx serve -s build -l $PORT --single`
   - OR Railway will auto-detect from `Procfile`

### 4. Set Environment Variable

In Railway dashboard → **Variables** tab:

```
REACT_APP_API_URL=https://your-backend.railway.app/api
```

**Important:** Replace `your-backend.railway.app` with your actual backend URL.

### 5. Update Backend CORS

In `api_server.py`, add your Railway frontend URL to CORS:

```python
allow_origins=[
    "http://localhost:3000",
    "https://your-frontend.railway.app",  # Add this
    "https://*.railway.app"  # Or allow all Railway apps
]
```

### 6. Deploy Backend (if needed)

If deploying backend to Railway:
- Add environment variables: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- Build command: `pip install -r requirements.txt`
- Start command: `python api_server.py`

## 📋 Environment Variables Needed

### Frontend (Railway)
- `REACT_APP_API_URL` - Your backend API URL

### Backend (Railway or Local)
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `OPENAI_API_KEY` (or OLLAMA settings)

## 🔗 URLs After Deployment

- **Frontend**: `https://your-frontend.railway.app`
- **Backend API**: `https://your-backend.railway.app/api`

## ✅ Testing

1. Visit frontend URL
2. Check browser console (F12) for errors
3. Test `/analytics` dashboard
4. Verify API calls work

## 🆘 Common Issues

**"Cannot connect to backend"**
- Check `REACT_APP_API_URL` is set correctly
- Verify backend is running
- Check CORS settings

**"Blank page"**
- Check browser console
- Verify build succeeded
- Check environment variables

**"404 on routes"**
- The `--single` flag in serve command should fix this
- If not, check `Procfile` has `--single` flag

---

**Full Guide**: See `RAILWAY_DEPLOYMENT_GUIDE.md` for detailed instructions.
