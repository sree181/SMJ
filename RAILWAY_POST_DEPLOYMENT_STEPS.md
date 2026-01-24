# Railway Post-Deployment Steps

## ✅ Deployment Successful!

Your frontend is now deployed on Railway. Here are the next steps to make it fully functional:

---

## Step 1: Get Your Railway URL

1. **Go to Railway Dashboard**: https://railway.app
2. **Select your project** (the one you just deployed)
3. **Click on your service** (the frontend service)
4. **Find the "Settings" tab** → Look for "Domains" or "Networking"
5. **Copy your Railway URL** (e.g., `https://your-app-name.up.railway.app`)

**Or check the "Deployments" tab** - the URL should be visible there.

---

## Step 2: Set Environment Variables

### Critical: Set `REACT_APP_API_URL`

1. **In Railway Dashboard** → Your frontend service
2. **Go to "Variables" tab**
3. **Click "New Variable"**
4. **Add the following**:

   ```
   Name: REACT_APP_API_URL
   Value: https://your-backend-url.railway.app/api
   ```

   **Important Notes:**
   - Replace `your-backend-url.railway.app` with your actual backend Railway URL
   - The URL should end with `/api` (no trailing slash)
   - If your backend is on Railway, you'll find its URL in the backend service's settings

5. **Click "Add"**

### Example:
```
REACT_APP_API_URL = https://smj-backend-production.up.railway.app/api
```

---

## Step 3: Redeploy After Setting Environment Variables

**After adding environment variables, Railway will automatically trigger a new deployment.**

- Wait for the deployment to complete (usually 2-5 minutes)
- The new build will include the environment variables

---

## Step 4: Test Your Deployment

1. **Visit your Railway URL** (e.g., `https://your-app.up.railway.app`)
2. **Navigate to `/analytics`** (e.g., `https://your-app.up.railway.app/analytics`)
3. **Check browser console** (F12 → Console tab) for any errors
4. **Test the chat interface** - click the "Research Assistant" button
5. **Verify API calls** - check Network tab in browser dev tools

### Expected Behavior:
- ✅ Dashboard loads with all tabs
- ✅ Charts display data
- ✅ Chat interface opens from the right side
- ✅ API calls succeed (check Network tab)

---

## Step 5: Backend Deployment (If Not Already Deployed)

If your backend is not yet on Railway, you'll need to deploy it:

### Option A: Deploy Backend to Railway

1. **Create a new service** in the same Railway project
2. **Connect your GitHub repository** (same repo)
3. **Set Root Directory**: `Strategic Management Journal` (or wherever `api_server.py` is)
4. **Railway will auto-detect Python**
5. **Set Environment Variables**:
   ```
   NEO4J_URI=your-neo4j-uri
   NEO4J_USER=your-neo4j-user
   NEO4J_PASSWORD=your-neo4j-password
   OPENAI_API_KEY=your-openai-key (or configure OLLAMA)
   PORT=5000 (Railway sets this automatically, but you can specify)
   ```
6. **Set Start Command**: `python api_server.py`
7. **Get the backend URL** from Railway
8. **Update frontend's `REACT_APP_API_URL`** to point to this backend URL

### Option B: Use Existing Backend

If your backend is already hosted elsewhere:
- Just set `REACT_APP_API_URL` to point to your existing backend URL

---

## Step 6: Custom Domain (Optional)

If you want a custom domain:

1. **In Railway Dashboard** → Your service → Settings
2. **Go to "Domains" section**
3. **Click "Generate Domain"** or **"Custom Domain"**
4. **Follow Railway's instructions** for DNS configuration

---

## Step 7: Share with Your Coauthor

Once everything is working:

1. **Share the Railway URL** with your coauthor
2. **They can access**: `https://your-app.up.railway.app/analytics`
3. **No local setup required** - everything runs in the browser!

---

## Troubleshooting

### Issue: Dashboard loads but shows "Failed to load analytics data"

**Solution:**
- Check that `REACT_APP_API_URL` is set correctly
- Verify backend is running and accessible
- Check browser console for CORS errors
- Ensure backend CORS settings allow your Railway frontend URL

### Issue: 404 on routes like `/analytics`

**Solution:**
- Verify `Procfile` contains: `web: npx serve -s build -l $PORT --single`
- The `--single` flag is crucial for React Router
- Redeploy if you changed the Procfile

### Issue: Environment variables not working

**Solution:**
- Environment variables starting with `REACT_APP_` must be set **before** the build
- Railway rebuilds automatically when you add variables
- Wait for the new deployment to complete
- Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)

### Issue: API calls timing out

**Solution:**
- Check backend is running
- Verify backend URL is correct
- Check Railway logs for backend errors
- Ensure backend CORS allows Railway domain

---

## Quick Checklist

- [ ] Frontend deployed successfully
- [ ] Got Railway URL for frontend
- [ ] Backend deployed (or using existing backend)
- [ ] Set `REACT_APP_API_URL` environment variable
- [ ] Redeployed after setting environment variables
- [ ] Tested dashboard at `/analytics`
- [ ] Tested chat interface
- [ ] Verified API calls work
- [ ] Shared URL with coauthor

---

## Monitoring

### View Logs:
1. **Railway Dashboard** → Your service
2. **Click "Deployments"** tab
3. **Click on a deployment** to see logs
4. **Or use "Logs" tab** for real-time logs

### Check Status:
- **Green checkmark** = Deployment successful
- **Yellow/Orange** = Deployment in progress
- **Red X** = Deployment failed (check logs)

---

## Next Steps After Everything Works

1. **Bookmark your Railway URL**
2. **Set up monitoring** (Railway provides basic monitoring)
3. **Consider setting up custom domain** for easier access
4. **Document the deployment** for future reference

---

**Your dashboard should now be live and accessible to your coauthor!** 🎉
