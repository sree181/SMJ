# Railway Python Version & NumPy Compatibility Fix

## 🚨 Problem

Railway is using **Python 3.13**, which is incompatible with `numpy==1.24.3`:
```
ERROR: Cannot import 'setuptools.build_meta'
pip._vendor.pyproject_hooks._impl.BackendUnavailable
```

**Root Cause:** NumPy 1.24.3 doesn't support Python 3.13. It requires Python 3.8-3.12.

---

## ✅ Solution: Pin Python Version to 3.12

### Step 1: Create `runtime.txt`

Created `runtime.txt` in the `Strategic Management Journal` directory:
```
python-3.12.7
```

This tells Railway to use Python 3.12 instead of 3.13.

### Step 2: Update NumPy Version (Optional but Recommended)

Updated both `requirements.txt` and `requirements.backend.txt`:
- **Before**: `numpy==1.24.3`
- **After**: `numpy>=1.26.0` (compatible with Python 3.12 and 3.13)

### Step 3: Update Build Command in Railway

1. **Railway Dashboard** → Backend service
2. **Settings** → **Build** section
3. **Custom Build Command**: Change to:
   ```
   pip install -r requirements.backend.txt
   ```
4. **Save** and **Redeploy**

---

## 📋 Alternative: Use requirements.backend.txt

If Railway still uses `requirements.txt`, you can:

1. **Railway Settings** → **Build**
2. **Custom Build Command**: 
   ```
   pip install -r requirements.backend.txt
   ```
3. This file already has updated numpy version

---

## ✅ Expected Result

After fix:
- Railway uses Python 3.12 (from `runtime.txt`)
- NumPy installs successfully
- All dependencies install without errors
- Backend starts correctly

---

## 🔍 Verification

After deployment, check logs should show:
```
Collecting numpy>=1.26.0
Successfully installed numpy-1.26.x ...
```

**NOT:**
```
ERROR: Cannot import 'setuptools.build_meta'
```

---

**The fix is in `runtime.txt` - Railway will use Python 3.12 automatically!**
