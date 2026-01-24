# URGENT: Set Neo4j Environment Variables in Railway

## 🚨 Critical Issue

Your backend is failing with:
```
ERROR: URI scheme b'' is not supported
✗ Failed to connect to Neo4j
```

**This means `NEO4J_URI` environment variable is NOT SET or is EMPTY in Railway!**

---

## ✅ IMMEDIATE FIX

### Step 1: Go to Railway Backend Service

1. **Railway Dashboard** → **Backend service** (e.g., "backend")
2. **Click "Variables" tab**

### Step 2: Add Required Variables

Click **"New Variable"** for each:

#### Variable 1: NEO4J_URI
- **Name**: `NEO4J_URI`
- **Value**: `neo4j+s://your-database.databases.neo4j.io`
  - Replace with your actual Neo4j Aura URI
  - Should start with `neo4j+s://` or `neo4j://` or `bolt://`
  - Example: `neo4j+s://d1a3de49.databases.neo4j.io`

#### Variable 2: NEO4J_USER
- **Name**: `NEO4J_USER`
- **Value**: `neo4j`
  - Usually just `neo4j` (default username)

#### Variable 3: NEO4J_PASSWORD
- **Name**: `NEO4J_PASSWORD`
- **Value**: `your-actual-password`
  - Your Neo4j database password
  - Copy from Neo4j Aura dashboard

#### Variable 4: OPENAI_API_KEY
- **Name**: `OPENAI_API_KEY`
- **Value**: `sk-proj-your-key-here`
  - Your OpenAI API key
  - Starts with `sk-proj-` or `sk-`

### Step 3: Verify Variables

Make sure you have **all 4 variables**:
- ✅ `NEO4J_URI`
- ✅ `NEO4J_USER`
- ✅ `NEO4J_PASSWORD`
- ✅ `OPENAI_API_KEY`

### Step 4: Redeploy Backend

1. **Deployments tab** → **Redeploy**
2. **Wait 2-3 minutes**
3. **Check logs** - should now show:
   ```
   ✓ Connected to Neo4j
   INFO:     Uvicorn running on http://0.0.0.0:8080
   ```

---

## 🔍 How to Find Your Neo4j Credentials

1. **Go to Neo4j Aura**: https://console.neo4j.io
2. **Select your database**
3. **Click "Connection details"** or **"Details"**
4. **Copy**:
   - **URI** (e.g., `neo4j+s://xxxxx.databases.neo4j.io`)
   - **Username** (usually `neo4j`)
   - **Password** (the one you set when creating the database)

---

## ✅ Expected Result

After setting variables and redeploying:

**Backend logs should show:**
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
✓ Advanced analytics endpoints loaded
✓ Research Analytics endpoints loaded
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**NOT:**
```
ERROR: URI scheme b'' is not supported
✗ Failed to connect to Neo4j
```

---

## 📋 Quick Checklist

- [ ] `NEO4J_URI` added in Railway Variables (starts with `neo4j+s://`)
- [ ] `NEO4J_USER` added (usually `neo4j`)
- [ ] `NEO4J_PASSWORD` added (your actual password)
- [ ] `OPENAI_API_KEY` added (starts with `sk-`)
- [ ] Backend redeployed
- [ ] Logs show "✓ Connected to Neo4j"

---

**The backend cannot work without these environment variables! Set them now in Railway Variables tab!**
