# Railway Frontend Fix - Immediate Steps

## ✅ What Was Done

1. **Renamed `requirements.txt`** → `requirements.backend-only.txt`
   - This prevents Railway from detecting Python for the frontend
   - Backend will still work (just needs updated build command)

2. **Created `.railwayignore`** - Excludes Python files from frontend builds

3. **Updated `railway.frontend.json`** - Added explicit build command

---

## 🔧 Next Steps in Railway Dashboard

### Step 1: Update Backend Build Command

1. **Railway Dashboard** → **Backend service**
2. **Settings** → **Build** section
3. **Custom Build Command**: Change from:
   ```
   pip install -r requirements.txt
   ```
   To:
   ```
   pip install -r requirements.backend-only.txt
   ```
4. **Save**

### Step 2: Verify Frontend Settings

1. **Railway Dashboard** → **"web" service** (frontend)
2. **Settings** → **Source** section
3. **Root Directory**: Should be **EMPTY**
4. **Settings** → **Build** section
5. **Custom Build Command**: `npm ci && npm run build`
6. **Settings** → **Deploy** section
7. **Custom Start Command**: `npx serve -s build -l $PORT --single`

### Step 3: Push Changes and Redeploy

1. **Push to GitHub** (if you can allow the secret, or push manually)
2. **Frontend will auto-redeploy** - should now detect Node.js!
3. **Backend** - manually redeploy after updating build command

---

## ✅ Expected Result

**Frontend build logs should now show:**
```
Installing Node.js 18...
npm ci
npm run build
npx serve -s build -l $PORT --single
```

**NOT:**
```
install mise packages: python
pip install -r requirements.txt
npm: not found
```

---

**The key fix: Renaming `requirements.txt` removes Python detection, allowing Railway to detect Node.js from `package.json`!**
