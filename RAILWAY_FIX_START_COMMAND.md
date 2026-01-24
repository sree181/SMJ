# Fix Railway Backend Start Command

## 🚨 Problem

The backend service ("artistic-upliftment") is using the **frontend start command**:
```
npx serve -s build -l $PORT --single
```

This is why it's running npm/Node.js instead of Python/FastAPI!

---

## ✅ Solution: Change Start Command in Railway

### Step 1: Update Start Command in Railway

1. **In Railway Dashboard** → "artistic-upliftment" service
2. **Settings tab** (you're already here!)
3. **Find "Custom Start Command"** section
4. **Click the input field** that shows: `npx serve -s build -l $PORT --single`
5. **Delete that command** and replace with:
   ```
   python api_server.py
   ```
6. **Click "Save"** or press Enter

### Step 2: Verify Build Command

While you're in Settings:
1. **Scroll down** or look for **"Build"** section
2. **Build Command** should be: `pip install -r requirements.txt`
3. If it's different, update it

### Step 3: Redeploy

1. **Go to "Deployments" tab**
2. **Click "Redeploy"** button (or wait for Railway to auto-redeploy)
3. **Wait 2-5 minutes** for deployment

### Step 4: Check Logs

After redeploy, go to **Deployments** → **Latest deployment** → **View logs**

**Should see:**
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**Should NOT see:**
```
npm warn config production
INFO  Accepting connections at http://localhost:8080
```

---

## 🔍 Why This Happened

The `railway.json` file in your repo has the frontend command, and Railway is using it for both services. Since both services are in the same repository, Railway might be auto-detecting the wrong config.

**Solution:** Manually override the start command in Railway settings for the backend service.

---

## 📋 Quick Steps

1. **Settings tab** → "artistic-upliftment" service
2. **Custom Start Command** field
3. **Change from**: `npx serve -s build -l $PORT --single`
4. **Change to**: `python api_server.py`
5. **Save**
6. **Redeploy**
7. **Check logs** - should show Python/FastAPI starting

---

## ✅ After Fix

Once the start command is changed and redeployed:
- Backend will run Python (`python api_server.py`)
- CORS will work (because Python code is actually running)
- API endpoints will respond correctly
- Frontend will be able to fetch data! 🎉

---

**The key is changing that start command field in Railway settings!**
