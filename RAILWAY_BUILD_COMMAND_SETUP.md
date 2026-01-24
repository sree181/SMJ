# Railway Build Command Setup

## ✅ For Backend Service (SMJ / artistic-upliftment)

### Build Command:
```
pip install -r requirements.txt
```

This installs all Python dependencies needed for the FastAPI backend.

### Start Command:
```
python api_server.py
```

This starts the FastAPI server.

---

## 📋 Step-by-Step Setup

### Step 1: Add Build Command

1. **In Railway Settings** → "SMJ" service (your backend)
2. **Build section** → **"Custom Build Command"**
3. **Click "+ Build Command"**
4. **Enter**: `pip install -r requirements.txt`
5. **Save**

### Step 2: Verify Start Command

1. **Scroll down** to **"Deploy"** section
2. **Custom Start Command** should be: `python api_server.py`
3. **If it's not**, set it manually

### Step 3: Verify Root Directory

1. **Settings** → **Source** section (or check at top)
2. **Root Directory** should be: **Empty** (or `/`)
3. **NOT** `Strategic Management Journal`

### Step 4: Apply Changes

1. **Click "Apply 5 changes"** button (top right)
2. **Or click "Deploy"** button
3. **Wait 2-5 minutes** for deployment

---

## ✅ Expected Build Process

After setting build command, Railway will:

1. **Detect Python** (from `requirements.txt`)
2. **Run Build Command**: `pip install -r requirements.txt`
3. **Install dependencies**: FastAPI, Neo4j, OpenAI, etc.
4. **Run Start Command**: `python api_server.py`
5. **Start FastAPI server** on Railway's PORT

---

## 🔍 What to Check After Deployment

**Build Logs should show:**
```
Collecting fastapi
Collecting uvicorn
Collecting neo4j
...
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...
```

**Deploy Logs should show:**
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
INFO:     Uvicorn running on http://0.0.0.0:5000
```

**NOT:**
```
npm warn config production
INFO  Accepting connections at http://localhost:8080
```

---

## 📋 Quick Checklist

- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `python api_server.py`
- [ ] Root Directory: Empty (or `/`)
- [ ] Environment Variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY
- [ ] Click "Apply changes" or "Deploy"
- [ ] Check logs - should see Python/FastAPI starting

---

**Yes, add the build command: `pip install -r requirements.txt`**
