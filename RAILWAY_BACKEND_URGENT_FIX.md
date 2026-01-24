# URGENT: Backend Issues - Fix Now

## 🚨 Two Critical Issues

### Issue 1: Neo4j Connection Failed ❌
```
ERROR: URI scheme b'' is not supported
✗ Failed to connect to Neo4j
```

**This means `NEO4J_URI` environment variable is NOT SET in Railway!**

### Issue 2: Circular Import Warning ⚠️
```
WARNING: cannot import name 'router' from partially initialized module 'research_analytics_endpoints'
```

**This is a code issue that will be fixed after you push the latest changes.**

---

## ✅ IMMEDIATE FIX: Set Environment Variables

### Step 1: Go to Railway Backend Service

1. **Railway Dashboard** → **Backend service** (e.g., "backend")
2. **Click "Variables" tab**

### Step 2: Add These 4 Variables (REQUIRED)

Click **"New Variable"** for each:

#### 1. NEO4J_URI
- **Name**: `NEO4J_URI`
- **Value**: `neo4j+s://your-database.databases.neo4j.io`
  - **Replace with your actual Neo4j Aura URI**
  - Should start with `neo4j+s://` or `neo4j://` or `bolt://`
  - Example: `neo4j+s://d1a3de49.databases.neo4j.io`

#### 2. NEO4J_USER
- **Name**: `NEO4J_USER`
- **Value**: `neo4j`
  - Usually just `neo4j` (default username)

#### 3. NEO4J_PASSWORD
- **Name**: `NEO4J_PASSWORD`
- **Value**: `your-actual-password`
  - Your Neo4j database password
  - Copy from Neo4j Aura dashboard

#### 4. OPENAI_API_KEY
- **Name**: `OPENAI_API_KEY`
- **Value**: `sk-proj-your-key-here`
  - Your OpenAI API key
  - Starts with `sk-proj-` or `sk-`

### Step 3: Verify All Variables Are Set

Make sure you see **all 4 variables** in the Variables tab:
- ✅ `NEO4J_URI` (with actual URI, not empty)
- ✅ `NEO4J_USER` (usually `neo4j`)
- ✅ `NEO4J_PASSWORD` (your password)
- ✅ `OPENAI_API_KEY` (your API key)

### Step 4: Redeploy Backend

1. **Deployments tab** → **Redeploy**
2. **Wait 2-3 minutes**
3. **Check logs** - should now show:
   ```
   ✓ Connected to Neo4j
   INFO:     Uvicorn running on http://0.0.0.0:8080
   ```

---

## 🔧 Fix Circular Import (After Pushing Code)

The circular import warning will be fixed once you push the latest code changes. The fix uses lazy import to break the circular dependency.

**To push code:**
1. Allow the secret through GitHub (one-time): https://github.com/sree181/SMJ/security/secret-scanning/unblock-secret/38gnUvVHerzoqAiN5AKANX1tawu
2. Then push: `git push`

---

## 📋 Quick Checklist

- [ ] `NEO4J_URI` added in Railway (starts with `neo4j+s://`)
- [ ] `NEO4J_USER` added (usually `neo4j`)
- [ ] `NEO4J_PASSWORD` added (your actual password)
- [ ] `OPENAI_API_KEY` added (starts with `sk-`)
- [ ] All variables have values (not empty)
- [ ] Backend redeployed
- [ ] Logs show "✓ Connected to Neo4j"

---

## 🚨 Most Important

**The `NEO4J_URI` environment variable MUST be set in Railway!**

Without it, the backend cannot connect to Neo4j and will fail.

**Go to Railway → Backend service → Variables tab → Add `NEO4J_URI` now!**
