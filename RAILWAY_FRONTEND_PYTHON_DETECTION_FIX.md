# Fix: Frontend Service Detecting Python Instead of Node.js

## 🚨 Problem

Frontend build is failing because Railway is detecting it as **Python** instead of **Node.js**:
```
install mise packages: python
pip install -r requirements.txt
npm ci && npm run build
sh: 1: npm: not found
```

**Root Cause**: Railway's Railpack sees `requirements.txt` in the root and thinks it's a Python project.

---

## ✅ Solution: Force Node.js Detection

### Step 1: Clear Root Directory (CRITICAL!)

1. **Railway Dashboard** → **"web" service** (frontend)
2. **Settings tab** → **Source** section
3. **Root Directory**: **EMPTY** (clear it completely - should be blank)
4. **Save**

**Why**: With empty root, Railway should see `package.json` first and detect Node.js.

### Step 2: Set Explicit Build Command

1. **Settings tab** → **Build** section
2. **Custom Build Command**:
   ```
   npm ci && npm run build
   ```
3. **Save**

### Step 3: Set Explicit Start Command

1. **Settings tab** → **Deploy** section
2. **Custom Start Command**:
   ```
   npx serve -s build -l $PORT --single
   ```
3. **Save**

### Step 4: Check Builder Settings

1. **Settings tab** → **Builder** section
2. If it shows **"Railpack"** with Python, try:
   - **Option A**: Change to **"Nixpacks"** (if available)
   - **Option B**: Keep Railpack but ensure root directory is empty

### Step 5: Verify Files in Root

Make sure these files exist in your repo root:
- ✅ `package.json` (Node.js project file)
- ✅ `nixpacks.toml` (Node.js config)
- ❌ `requirements.txt` should NOT be in root (or should be ignored)

**If `requirements.txt` is in root**, Railway might detect Python. Options:
- Move it to a subdirectory
- Or ensure root directory is empty so Railway sees `package.json` first

### Step 6: Redeploy

1. **Deployments tab** → **Redeploy**
2. **Wait 2-3 minutes**
3. **Check logs** - should show Node.js installation, not Python

---

## 🔧 Alternative: Use Nixpacks Explicitly

If Railpack keeps detecting Python, ensure `nixpacks.toml` is in root with:

```toml
[phases.setup]
nixPkgs = ["nodejs-18_x"]

[phases.install]
cmds = ["npm ci"]

[phases.build]
cmds = ["npm run build"]

[start]
cmd = "npx serve -s build -l $PORT --single"
```

This should force Node.js detection.

---

## 🔍 Why This Happens

Railway's Railpack auto-detection:
1. Sees `requirements.txt` → thinks Python
2. Sees `package.json` → thinks Node.js
3. **First file found wins** (or most prominent)

**Solution**: 
- Empty root directory ensures Railway looks at repo structure
- `package.json` should be detected first
- Or use explicit build commands

---

## ✅ Expected Result

After fix, build logs should show:
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

## 📋 Quick Checklist

- [ ] Root Directory: **EMPTY** (most important!)
- [ ] Build Command: `npm ci && npm run build`
- [ ] Start Command: `npx serve -s build -l $PORT --single`
- [ ] `package.json` exists in repo root
- [ ] `nixpacks.toml` exists in repo root (with Node.js config)
- [ ] Redeploy after changes
- [ ] Builder shows Node.js (not Python)

---

**The key is ensuring Root Directory is EMPTY so Railway can see `package.json` and detect Node.js!**
