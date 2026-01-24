# Force Railway to Use Node.js for Frontend Service

## 🚨 Problem

Railway's Railpack is detecting **Python 3.12.7** instead of **Node.js** for the frontend service, causing `npx: command not found` errors.

---

## ✅ Solution: Force Node.js Detection

### Step 1: Clear Root Directory (Critical!)

1. **Railway Dashboard** → "web" service
2. **Settings tab** → **Source** section
3. **Root Directory**: **EMPTY** (clear it completely)
4. **Save**

**Why**: Railway needs to see `package.json` in the root to detect Node.js.

### Step 2: Set Explicit Build Command

1. **Settings tab** → **Build** section
2. **Custom Build Command**:
   ```
   npm ci && npm run build
   ```
3. **Save**

This forces Railway to use Node.js for building.

### Step 3: Set Explicit Start Command

1. **Settings tab** → **Deploy** section  
2. **Custom Start Command**:
   ```
   npx serve -s build -l $PORT --single
   ```
3. **Save**

### Step 4: Check Builder Settings

1. **Settings tab** → Look for **"Builder"** section
2. If you see **"Railpack"** with Python, try:
   - **Option A**: Change to **"Nixpacks"** (if available)
   - **Option B**: Keep Railpack but ensure root directory is empty

### Step 5: Verify nixpacks.toml is in Root

The `nixpacks.toml` file should be in the repo root (same level as `package.json`). It contains:
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

### Step 6: Redeploy

1. **Deployments tab** → **Redeploy**
2. **Wait 2-3 minutes**
3. **Check logs** - should show Node.js installation

---

## 🔧 Alternative: If Railpack Still Detects Python

If Railway's Railpack still detects Python after clearing root directory:

### Option 1: Temporarily Hide requirements.txt

**Note**: This might affect backend, so only do this if frontend and backend are separate services.

1. Rename `requirements.txt` to `requirements.backend.txt` in root
2. Redeploy frontend
3. Backend should use `requirements.backend.txt` anyway

### Option 2: Use Explicit Nixpacks Config

Ensure `nixpacks.toml` is in root and contains Node.js config (already done).

### Option 3: Set Environment Variable

In Railway Variables tab for "web" service:
```
NIXPACKS_BUILDER=nodejs
```

---

## ✅ Expected Result

After fix, Railway should:
- Detect Node.js (not Python)
- Show `nodejs@18.x` or similar in builder
- Install npm packages
- Run `npm run build`
- Start with `npx serve`

**Logs should show:**
```
Installing Node.js 18...
npm ci
npm run build
npx serve -s build -l $PORT --single
```

**NOT:**
```
python@3.12.7
/bin/bash: line 1: npx: command not found
```

---

## 📋 Quick Checklist

- [ ] Root Directory: **EMPTY** (most important!)
- [ ] Build Command: `npm ci && npm run build`
- [ ] Start Command: `npx serve -s build -l $PORT --single`
- [ ] `nixpacks.toml` exists in repo root
- [ ] `package.json` exists in repo root
- [ ] Redeploy after changes
- [ ] Builder shows Node.js (not Python)

---

**The key is ensuring Root Directory is EMPTY so Railway can see `package.json` and detect Node.js!**
