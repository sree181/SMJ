# Backend Environment Variables for Railway

## ✅ Required Environment Variables

You **MUST** set these in your backend service on Railway:

### 1. Neo4j Database Connection

```
NEO4J_URI=neo4j+s://your-database.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

**Where to find these:**
- Go to your Neo4j Aura dashboard
- Copy the connection URI (usually starts with `neo4j+s://`)
- Copy the username (usually `neo4j`)
- Copy the password (the one you set when creating the database)

### 2. OpenAI API Key

```
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
```

**Where to find this:**
- Go to https://platform.openai.com/api-keys
- Create a new API key or copy an existing one
- Starts with `sk-proj-` or `sk-`

---

## 🔧 Optional Environment Variables

These are optional but can be useful:

### 3. Port (Usually Auto-Set by Railway)

```
PORT=5000
```

**Note**: Railway usually sets this automatically, but you can specify it if needed.

### 4. Frontend URL (For CORS)

```
FRONTEND_URL=https://web-production-ff38d.up.railway.app
```

**Note**: The backend already has CORS configured to allow all origins (`allow_origins=["*"]`), so this is optional.

### 5. Ollama Settings (If Using Local LLM Instead of OpenAI)

```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
USE_OLLAMA=false
```

**Note**: Only needed if you're using Ollama instead of OpenAI. Default is OpenAI.

---

## 📋 How to Set Variables in Railway

### Step 1: Go to Backend Service

1. **Railway Dashboard** → Your **backend service** (e.g., "backend")
2. **Click "Variables" tab**

### Step 2: Add Each Variable

1. **Click "New Variable"**
2. **Enter Name** (e.g., `NEO4J_URI`)
3. **Enter Value** (e.g., `neo4j+s://your-database.databases.neo4j.io`)
4. **Click "Add"**
5. **Repeat for each variable**

### Step 3: Verify All Variables

You should have at least these 4 variables:
- ✅ `NEO4J_URI`
- ✅ `NEO4J_USER`
- ✅ `NEO4J_PASSWORD`
- ✅ `OPENAI_API_KEY`

### Step 4: Redeploy (If Needed)

- Railway will **automatically redeploy** when you add variables
- **OR** go to **Deployments tab** → **Redeploy manually**
- **Wait 2-3 minutes**

---

## ✅ Verify Backend is Working

After setting variables and redeploying:

1. **Check backend logs** in Railway → **Deployments** → **View logs**
2. **Should see**:
   ```
   ✓ Connected to Neo4j
   CORS configured: allow_origins=['*'], allow_credentials=False
   INFO:     Uvicorn running on http://0.0.0.0:5000
   ```

3. **Test backend health**:
   - Visit: `https://your-backend-url.railway.app/api/health`
   - Should see:
     ```json
     {
       "status": "healthy",
       "neo4j_connected": true,
       "timestamp": "..."
     }
     ```

---

## 🚨 Common Issues

### Issue 1: "Neo4j connection failed"
**Solution**: 
- Verify `NEO4J_URI` is correct (includes `neo4j+s://` or `neo4j://`)
- Verify `NEO4J_USER` and `NEO4J_PASSWORD` are correct
- Check Neo4j database is running

### Issue 2: "OpenAI API key invalid"
**Solution**:
- Verify `OPENAI_API_KEY` starts with `sk-`
- Check the key is active in OpenAI dashboard
- Make sure there are no extra spaces in the value

### Issue 3: Backend crashes on startup
**Solution**:
- Check all required variables are set
- Check backend logs for specific error messages
- Verify Python version is 3.12 (check `runtime.txt`)

---

## 📋 Quick Checklist

- [ ] `NEO4J_URI` set (with correct protocol: `neo4j+s://` or `neo4j://`)
- [ ] `NEO4J_USER` set (usually `neo4j`)
- [ ] `NEO4J_PASSWORD` set (your actual password)
- [ ] `OPENAI_API_KEY` set (starts with `sk-`)
- [ ] Backend redeployed after setting variables
- [ ] Backend logs show "Connected to Neo4j"
- [ ] Health endpoint returns `{"status": "healthy"}`

---

**Once all variables are set, your backend should connect to Neo4j and be ready to serve API requests!** 🎉
