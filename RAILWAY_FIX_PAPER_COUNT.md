# Fix Railway Showing 0 Papers

## 🚨 Issue
Railway dashboard is showing **0 papers** instead of **1029**.

## 🔍 Root Cause
Railway connects to a Neo4j database. The database might:
1. Have papers with `year = 0` or `year = NULL` (excluded from dashboard)
2. Be a different database than your local one
3. Need the year values to be fixed

## ✅ Solution: Fix the Database

### Step 1: Verify Railway's Neo4j Connection

1. **Go to Railway Dashboard**: https://railway.app
2. **Select your backend service**
3. **Go to "Variables" tab**
4. **Check these variables:**
   - `NEO4J_URI` - Should be your Neo4j Aura URI
   - `NEO4J_USER` - Usually `neo4j`
   - `NEO4J_PASSWORD` - Your Neo4j password

**Important**: Railway uses these environment variables. Make sure they point to the **same Neo4j database** you're using locally.

### Step 2: Run the Fix Script

The script `fix_railway_database.py` will:
- Connect to the Neo4j database (using your `.env` file)
- Find papers with `year = 0` or `year = NULL`
- Set them to `year = 2025`
- Verify all papers are now included

**Run it:**

```bash
cd "Strategic Management Journal"
source ../smj/bin/activate  # or your virtual environment
python3 fix_railway_database.py
```

**Expected Output:**
```
📊 Current Status:
   Total papers: 1029
   Papers with invalid year: 276
   Papers in dashboard range: 751

🔄 Updating year to 2025...
✅ Updated 276 papers to year = 2025

📊 Updated Statistics:
   Total papers: 1029
   Papers with valid year: 1029
   Papers in dashboard range (1985-2026): 1029

✅ SUCCESS! Railway dashboard will now show all papers!
```

### Step 3: Verify Railway Database

**Option A: If Railway uses the SAME database**
- The fix script already updated it
- Railway should automatically see the changes
- Refresh the dashboard

**Option B: If Railway uses a DIFFERENT database**
- You need to set the Railway database credentials in your `.env` file
- Then run the fix script again
- OR manually update Railway's database using Neo4j Browser

### Step 4: Check Railway Environment Variables

Make sure Railway's `NEO4J_URI` points to the **correct database**:

1. **Railway Dashboard** → **Backend service** → **Variables**
2. **Check `NEO4J_URI`**:
   - Should match your local `.env` file
   - Format: `neo4j+s://xxxxx.databases.neo4j.io`
3. **If different**, you have two databases:
   - Update Railway's database separately
   - OR change Railway to use the same database

### Step 5: Redeploy Railway (if needed)

If the database is fixed but Railway still shows 0:

1. **Railway Dashboard** → **Backend service**
2. **Deployments tab** → **Redeploy**
3. **Wait 2-3 minutes**
4. **Check logs** - should show:
   ```
   ✓ Connected to Neo4j
   ```

### Step 6: Verify Dashboard

1. **Visit Railway frontend**
2. **Go to Analytics Dashboard**
3. **Check "Total Papers"** - should show **1029**

---

## 🔧 Manual Fix via Neo4j Browser

If you prefer to fix it manually:

1. **Open Neo4j Browser** (Aura Console)
2. **Run this query:**

```cypher
MATCH (p:Paper)
WHERE p.year IS NULL OR p.year <= 0
SET p.year = 2025
RETURN count(p) as updated
```

3. **Verify:**

```cypher
MATCH (p:Paper)
WHERE p.year >= 1985 AND p.year < 2026 AND p.year > 0
RETURN count(p) as total
```

Should return **1029**.

---

## 🐛 Troubleshooting

### Railway still shows 0 after fix

1. **Check Railway logs**:
   - Railway Dashboard → Backend → Logs
   - Look for Neo4j connection errors
   - Look for API errors

2. **Verify API endpoint**:
   ```bash
   curl https://your-backend.railway.app/api/analytics/papers/by-interval
   ```
   Should return paper counts, not empty array

3. **Check frontend API URL**:
   - Railway Dashboard → Frontend service → Variables
   - Verify `REACT_APP_API_URL` points to correct backend

### Database connection issues

1. **Verify Neo4j credentials** in Railway Variables
2. **Test connection**:
   ```bash
   python3 -c "
   from neo4j import GraphDatabase
   import os
   from dotenv import load_dotenv
   load_dotenv()
   driver = GraphDatabase.driver(
       os.getenv('NEO4J_URI'),
       auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
   )
   with driver.session() as s:
       print('✅ Connected!')
       print('Papers:', s.run('MATCH (p:Paper) RETURN count(p)').single()['count'])
   "
   ```

---

## ✅ Success Criteria

After fixing, you should see:
- ✅ **1029 papers** in Railway dashboard
- ✅ All intervals showing correct counts
- ✅ No papers excluded

---

## 📝 Summary

1. **Run `fix_railway_database.py`** to fix year values
2. **Verify Railway's `NEO4J_URI`** points to correct database
3. **Redeploy Railway** if needed
4. **Check dashboard** - should show 1029 papers
