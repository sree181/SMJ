# IMPORTANT: Railway Doesn't Read .env Files!

## 🚨 Critical Understanding

**Railway does NOT automatically read `.env` files!**

If you set variables in a `.env` file locally, Railway **will not see them**. You **MUST** set environment variables in Railway's dashboard.

---

## ✅ How to Set Variables in Railway

### Step 1: Go to Railway Dashboard

1. **Railway Dashboard** → **Backend service** (e.g., "backend")
2. **Click "Variables" tab**

### Step 2: Add Variables (NOT from file!)

Click **"New Variable"** for each variable. **Important**: Do NOT include quotes in the values!

#### Variable 1: NEO4J_URI
- **Name**: `NEO4J_URI`
- **Value**: `neo4j+s://d1a3de49.databases.neo4j.io`
  - **NO quotes!** Just the URI itself
  - ❌ Wrong: `"neo4j+s://d1a3de49.databases.neo4j.io"`
  - ✅ Correct: `neo4j+s://d1a3de49.databases.neo4j.io`

#### Variable 2: NEO4J_USER
- **Name**: `NEO4J_USER`
- **Value**: `neo4j`
  - **NO quotes!** Just `neo4j`

#### Variable 3: NEO4J_PASSWORD
- **Name**: `NEO4J_PASSWORD`
- **Value**: `QGaIl1PSNjXlNIFV1vghPbOBC5yKQPuFFqwb8gMU04I`
  - **NO quotes!** Just the password itself

#### Variable 4: OPENAI_API_KEY
- **Name**: `OPENAI_API_KEY`
- **Value**: `sk-proj-your-key-here`
  - **NO quotes!** Just the key itself

### Step 3: Verify Variables Are Set

In Railway Variables tab, you should see:
```
NEO4J_URI = neo4j+s://d1a3de49.databases.neo4j.io
NEO4J_USER = neo4j
NEO4J_PASSWORD = QGaIl1PSNjXlNIFV1vghPbOBC5yKQPuFFqwb8gMU04I
OPENAI_API_KEY = sk-proj-...
```

**Notice**: No quotes around the values!

### Step 4: Redeploy Backend

1. **Deployments tab** → **Redeploy**
2. **Wait 2-3 minutes**
3. **Check logs** - should now show:
   ```
   ✓ Connected to Neo4j
   ```

---

## 🔍 Why This Matters

If you have a `.env` file with:
```
NEO4J_URI="neo4j+s://d1a3de49.databases.neo4j.io"
```

Railway **will NOT read this file**. You must:
1. **Manually add each variable** in Railway's Variables tab
2. **Without quotes** in the values
3. **Redeploy** after adding variables

---

## 📋 Quick Checklist

- [ ] Variables added in **Railway Dashboard** → **Variables tab** (NOT in a file)
- [ ] Values have **NO quotes** around them
- [ ] All 4 variables are set: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENAI_API_KEY`
- [ ] Backend redeployed after setting variables
- [ ] Logs show "✓ Connected to Neo4j"

---

## 🚨 Common Mistake

**Setting variables in `.env` file and expecting Railway to read it** ❌

**Correct**: Set variables in Railway Dashboard → Variables tab ✅

---

**Railway requires you to set environment variables in the dashboard, not in files!**
