# How to Manually Redeploy Backend on Railway

## 🚨 Problem

Backend shows "deployed" but isn't redeploying after setting environment variables.

---

## ✅ Solution: Force Redeploy

### Option 1: Manual Redeploy Button

1. **Railway Dashboard** → **Backend service**
2. **Deployments tab**
3. **Click "Redeploy"** button (usually at the top right)
4. **Or** click the three dots (⋮) on the latest deployment → **"Redeploy"**
5. **Wait 2-3 minutes** for deployment

### Option 2: Trigger via Code Push

If manual redeploy doesn't work, trigger by pushing a small change:

1. **Make a small change** to trigger redeploy:
   ```bash
   cd "Strategic Management Journal"
   echo "# Redeploy trigger" >> .redeploy-trigger
   git add .redeploy-trigger
   git commit -m "Trigger backend redeploy"
   git push
   ```

2. **Railway will automatically detect the push** and redeploy

### Option 3: Delete and Redeploy

1. **Deployments tab** → Find the latest deployment
2. **Click three dots (⋮)** → **"Delete"** (if available)
3. **Or** click **"Redeploy"** button

---

## 🔍 Verify Variables Are Actually Set

Before redeploying, double-check:

1. **Variables tab** → Make sure you see:
   - `NEO4J_URI` = `neo4j+s://d1a3de49.databases.neo4j.io` (no quotes)
   - `NEO4J_USER` = `neo4j` (no quotes)
   - `NEO4J_PASSWORD` = `QGaIl1PSNjXlNIFV1vghPbOBC5yKQPuFFqwb8gMU04I` (no quotes)
   - `OPENAI_API_KEY` = `sk-proj-...` (no quotes)

2. **Check for typos**:
   - Variable names are case-sensitive: `NEO4J_URI` not `neo4j_uri`
   - No extra spaces
   - No quotes around values

---

## ✅ After Redeploy

Check the **Deployments tab** → **Latest deployment** → **View logs**:

**Should see:**
```
✓ Connected to Neo4j
CORS configured: allow_origins=['*'], allow_credentials=False
✓ Advanced analytics endpoints loaded
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**NOT:**
```
ERROR: URI scheme b'' is not supported
✗ Failed to connect to Neo4j
```

---

## 📋 Quick Steps

1. **Go to Deployments tab**
2. **Click "Redeploy" button**
3. **Wait 2-3 minutes**
4. **Check logs** - should show Neo4j connection

---

**Click the "Redeploy" button in Railway Deployments tab to force a new deployment!**
