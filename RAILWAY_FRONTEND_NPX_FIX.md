# Fix: Frontend Service Running Python Instead of Node.js

## 🚨 Problem

Frontend service ("web") is crashing with:
```
/bin/bash: line 1: npx: command not found
```

**Root Cause**: Railway is detecting the frontend as **Python** (`python@3.12.7`) instead of **Node.js**, so `npx` command doesn't exist.

---

## ✅ Solution: Fix Frontend Service Configuration

### Step 1: Check Root Directory

1. **Railway Dashboard** → "web" service
2. **Settings tab** → **Source** section
3. **Root Directory** should be: **EMPTY** (or `/`)
4. **If it shows `Strategic Management Journal`**, clear it!
5. **Save**

**Why**: The frontend files (`package.json`, `nixpacks.toml`) are in the repo root, not in a subdirectory.

### Step 2: Verify Service Type

1. **Settings tab** → Check the service type
2. **Should be**: `Node.js` (not `Python`)
3. **If it shows Python**, Railway is detecting wrong

### Step 3: Set Build Command Explicitly

1. **Settings tab** → **Build** section
2. **Custom Build Command**:
   ```
   npm ci && npm run build
   ```
3. **Save**

### Step 4: Set Start Command Explicitly

1. **Settings tab** → **Deploy** section
2. **Custom Start Command**:
   ```
   npx serve -s build -l $PORT --single
   ```
3. **Save**

### Step 5: Ensure nixpacks.toml is Detected

The `nixpacks.toml` file should be in the repo root with:
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

If Railway isn't detecting it, you may need to:
- Ensure root directory is empty
- Or explicitly set the build/start commands in Railway settings

### Step 6: Redeploy

1. **Deployments tab** → **Redeploy**
2. **Wait 2-5 minutes**
3. **Check logs** - should show Node.js installation, not Python

---

## ✅ Expected Result

After fix, frontend logs should show:
```
Installing Node.js 18...
npm ci
npm run build
npx serve -s build -l $PORT --single
INFO  Accepting connections at http://0.0.0.0:8080
```

**NOT:**
```
python@3.12.7
/bin/bash: line 1: npx: command not found
```

---

## 🔍 Why This Happened

Railway detected `requirements.txt` in the repo root and thought it was a Python project. The frontend service needs:
- **Root Directory**: Empty (to access `package.json` and `nixpacks.toml` in root)
- **Service Type**: Node.js (not Python)

---

## 📋 Quick Checklist

- [ ] Root Directory: **EMPTY** (not "Strategic Management Journal")
- [ ] Service Type: **Node.js** (not Python)
- [ ] Build Command: `npm ci && npm run build`
- [ ] Start Command: `npx serve -s build -l $PORT --single`
- [ ] Redeploy after changes
- [ ] Logs show Node.js (not Python)

---

**The key is ensuring the frontend service uses Node.js, not Python!**
