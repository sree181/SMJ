# Connect Frontend to Backend on Railway

## ✅ Backend is Deployed!

Your backend service is now successfully deployed. Now you need to connect the frontend to it.

---

## 🔗 Step 1: Get Backend URL

1. **Railway Dashboard** → **Backend service** (e.g., "backend" or "artistic-upliftment")
2. **Settings tab** → **Domains** section
3. **Copy the URL** (e.g., `https://backend-production-xxxx.up.railway.app`)
4. **Or check the service card** - it might show the URL there

**Note**: The backend URL should be different from the frontend URL (`web-production-ff38d.up.railway.app`)

---

## 🔧 Step 2: Set Frontend Environment Variable

1. **Railway Dashboard** → **"web" service** (frontend)
2. **Variables tab**
3. **Click "New Variable"**
4. **Name**: `REACT_APP_API_URL`
5. **Value**: `https://YOUR-BACKEND-URL.railway.app/api`
   - Replace `YOUR-BACKEND-URL.railway.app` with your actual backend URL from Step 1
   - **Important**: Include `/api` at the end!
6. **Click "Add"**

**Example**:
```
REACT_APP_API_URL=https://backend-production-7408.up.railway.app/api
```

---

## 🔄 Step 3: Redeploy Frontend

After adding the environment variable:

1. Railway will **automatically redeploy** the frontend
2. **OR** go to **Deployments tab** → **Redeploy** manually
3. **Wait 2-3 minutes** for deployment

---

## ✅ Step 4: Verify Connection

1. **Visit**: `https://web-production-ff38d.up.railway.app`
2. **Open browser console** (F12)
3. **Navigate to** `/analytics` page
4. **Check console** - should see API calls to your backend URL
5. **Should NOT see** errors like:
   - `Failed to fetch`
   - `CORS policy`
   - `localhost:5000`

---

## 🔍 How to Find Backend URL

If you can't find the backend URL:

1. **Backend service** → **Settings** → **Domains**
2. **Or** check the **service card** in the left sidebar
3. **Or** check **Deployments tab** → Latest deployment → **View logs** (might show the URL)

---

## 📋 Quick Checklist

- [ ] Found backend URL in Railway
- [ ] Added `REACT_APP_API_URL` variable to frontend service
- [ ] Value includes `/api` at the end
- [ ] Frontend redeployed
- [ ] Tested frontend - API calls work
- [ ] No CORS errors in console

---

## 🚨 Common Issues

### Issue 1: CORS Errors
**Solution**: Backend CORS is already configured to allow all origins. If you still see CORS errors, check backend logs.

### Issue 2: 404 Errors
**Solution**: Make sure the `REACT_APP_API_URL` includes `/api` at the end:
- ✅ Correct: `https://backend-url.railway.app/api`
- ❌ Wrong: `https://backend-url.railway.app`

### Issue 3: Connection Refused
**Solution**: 
- Verify backend is running (check backend logs)
- Verify backend URL is correct
- Check backend environment variables are set (NEO4J_URI, etc.)

---

**Once you set `REACT_APP_API_URL`, the frontend will automatically connect to your backend!** 🎉
