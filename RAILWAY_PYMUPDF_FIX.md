# Railway PyMuPDF Build Fix

## 🚨 Problem

Build fails with:
```
error: metadata-generation-failed
× Encountered error while generating package metadata.
╰─> PyMuPDF
```

**Root Cause:** PyMuPDF requires system libraries that Railway's build environment doesn't have by default.

---

## ✅ Solution: Use Backend-Only Requirements

PyMuPDF is **NOT needed** for the backend API server (`api_server.py`). It's only used in ingestion pipeline scripts.

### Option 1: Use Backend Requirements File (Recommended)

1. **Railway Dashboard** → "SMJ" service (backend)
2. **Settings** → **Build** section
3. **Custom Build Command**: Change from:
   ```
   pip install -r requirements.txt
   ```
   To:
   ```
   pip install -r requirements.backend.txt
   ```
4. **Save** and **Deploy**

### Option 2: Install System Dependencies First

If you need PyMuPDF later, add system dependencies:

**Build Command:**
```bash
apt-get update && apt-get install -y build-essential python3-dev && pip install -r requirements.txt
```

But this is **not recommended** - PyMuPDF isn't needed for the API server.

---

## 📋 Updated Build Configuration

**Build Command:**
```
pip install -r requirements.backend.txt
```

**Start Command:**
```
python api_server.py
```

**Root Directory:**
Empty (or `/`)

---

## ✅ After Fix

Build should succeed and install:
- FastAPI
- Neo4j driver
- OpenAI
- NetworkX
- scikit-learn
- etc.

**NOT** PyMuPDF (which isn't needed for the API server)

---

**Change your build command to use `requirements.backend.txt` instead!**
