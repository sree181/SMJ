# Final Fix: Force Node.js Detection When Railpack Detects Python

## 🚨 Problem

Railway's Railpack is detecting **Python** instead of **Node.js** for the frontend service, even though:
- ✅ Root Directory is empty
- ✅ Build Command is set: `npm ci && npm run build`
- ✅ Start Command is set: `npx serve -s build -l $PORT --single`
- ❌ Cannot change builder (Nixpacks is deprecated)

**Root Cause**: Railway's Railpack sees `requirements.txt` in the repo root and prioritizes Python detection over Node.js.

---

## ✅ Solution: Hide requirements.txt from Frontend Build

Since we can't change the builder, we need to prevent Railway from seeing `requirements.txt` during the frontend build.

### Option 1: Rename requirements.txt (Recommended)

**Temporary fix** - Rename `requirements.txt` so Railway doesn't detect it:

1. **In your local repo**:
   ```bash
   cd "Strategic Management Journal"
   git mv requirements.txt requirements.backend-only.txt
   ```

2. **Update backend service** in Railway:
   - **Settings** → **Build** section
   - **Custom Build Command**: `pip install -r requirements.backend-only.txt`
   - **Save**

3. **Commit and push**:
   ```bash
   git add requirements.backend-only.txt
   git commit -m "Rename requirements.txt to prevent Python detection in frontend"
   git push
   ```

4. **Redeploy frontend** - Railway should now detect Node.js!

### Option 2: Use .railwayignore (If Supported)

Created `.railwayignore` file to exclude Python files from frontend builds. Railway may or may not support this, but it's worth trying.

### Option 3: Move requirements.txt to Subdirectory

1. **Create `backend/` directory** in repo root
2. **Move `requirements.txt`** to `backend/requirements.txt`
3. **Update backend service**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
4. **Frontend service**:
   - **Root Directory**: Empty (or root)
   - Railway won't see `requirements.txt` in root

---

## 🔧 Quick Fix: Rename requirements.txt

**This is the fastest solution:**

1. **Rename the file**:
   ```bash
   git mv requirements.txt requirements.backend-only.txt
   ```

2. **Update Railway backend build command**:
   - Backend service → Settings → Build
   - Build Command: `pip install -r requirements.backend-only.txt`

3. **Commit and push**:
   ```bash
   git add requirements.backend-only.txt
   git commit -m "Rename requirements.txt to fix frontend Node.js detection"
   git push
   ```

4. **Frontend will automatically redeploy** and should detect Node.js!

---

## ✅ Expected Result

After renaming `requirements.txt`:
- Frontend build should detect Node.js
- Build logs should show: `Installing Node.js...`, `npm ci`, `npm run build`
- Backend will use `requirements.backend-only.txt` (same content, different name)

---

## 📋 Why This Works

Railway's Railpack auto-detection:
1. Sees `requirements.txt` → thinks Python
2. Sees `package.json` → thinks Node.js
3. **Python detection takes priority** when both exist

**Solution**: Remove `requirements.txt` from root, so only `package.json` is detected.

---

**Rename `requirements.txt` to `requirements.backend-only.txt` and update the backend build command!**
