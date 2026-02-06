# Quick Fix: Railway Showing 751 Instead of 1029

## ✅ Code is Correct
- ✅ Backend: `end_year=2026` (committed)
- ✅ Frontend: `endYear=2026` (committed)  
- ✅ Database: All 1029 papers have valid years

## 🚀 Quick Fix (2 minutes)

### Step 1: Force Railway Backend Redeploy

1. Go to **Railway Dashboard**: https://railway.app
2. Select your **Backend service**
3. Click **"Deployments"** tab
4. Click **"Redeploy"** button (or "Deploy Latest")
5. Wait 2-5 minutes for deployment to complete

### Step 2: Force Railway Frontend Redeploy

1. Still in Railway Dashboard
2. Select your **Frontend service** (usually named "web")
3. Click **"Deployments"** tab  
4. Click **"Redeploy"** button
5. Wait 2-3 minutes

### Step 3: Clear Browser Cache

1. Open your Railway frontend in browser
2. Press **Ctrl+Shift+R** (Windows) or **Cmd+Shift+R** (Mac)
3. Or use **Incognito/Private window**

### Step 4: Verify

1. Visit Analytics Dashboard
2. Check "Total Papers" - should show **1029** ✅

---

## 🔍 If Still Showing 751

### Check Railway Logs

1. Railway Dashboard → Backend → Logs
2. Look for errors or warnings
3. Should see: `✓ Connected to Neo4j`

### Test API Directly

Open browser console (F12) and run:

```javascript
fetch('https://your-backend.railway.app/api/analytics/papers/by-interval?end_year=2026')
  .then(r => r.json())
  .then(data => {
    const total = data.intervals.reduce((sum, i) => sum + i.count, 0);
    console.log('Total papers:', total);
  });
```

**Should return:** `Total papers: 1029`

**If returns 751:** Railway is still using old code - wait a few more minutes and redeploy again.

---

## 📝 Summary

**The fix is already in the code.** Railway just needs to:
1. ✅ Redeploy backend (2-5 min)
2. ✅ Redeploy frontend (2-3 min)  
3. ✅ Clear browser cache
4. ✅ Refresh dashboard

**Total time:** ~5 minutes
