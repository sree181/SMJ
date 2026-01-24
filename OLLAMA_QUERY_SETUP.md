# OLLAMA Query Setup

## Issue
You're seeing fallback answers instead of LLM-generated responses because OpenAI API key is not set.

## Solution: Use OLLAMA Instead

OLLAMA is already set up for extraction. Now it's also available for query answering.

---

## ✅ Implementation Complete

**Backend Updated**: `api_server.py`

**Changes**:
1. Added OLLAMA support to `LLMClient`
2. Falls back: OLLAMA → OpenAI → Fallback
3. Uses same OLLAMA setup as extraction pipeline

---

## 🔧 Configuration

### Option 1: Enable OLLAMA (Recommended)

Add to your `.env` file:
```bash
USE_OLLAMA=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Option 2: Use OpenAI

Add to your `.env` file:
```bash
OPENAI_API_KEY=your_api_key_here
```

---

## 🚀 How It Works

**Priority Order**:
1. **OLLAMA** (if `USE_OLLAMA=true`)
2. **OpenAI** (if `OPENAI_API_KEY` is set)
3. **Fallback** (if neither available)

**Current Behavior**:
- If OLLAMA is enabled → Uses OLLAMA
- If only OpenAI key is set → Uses OpenAI
- If neither → Shows fallback message

---

## ✅ Restart Backend

After updating `.env`, restart the backend:

```bash
# Stop current server (Ctrl+C)
# Then restart:
cd "Strategic Management Journal"
source ../smj/bin/activate
python3 api_server.py
```

---

## 🧪 Test

### Test OLLAMA Connection:
```bash
curl http://localhost:11434/api/tags
```

Should return list of available models.

### Test Query with OLLAMA:
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What papers use Resource-Based View?"}'
```

Should return LLM-generated answer (not fallback).

---

## 📋 Quick Setup

1. **Check OLLAMA is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Add to `.env`**:
   ```bash
   USE_OLLAMA=true
   ```

3. **Restart backend**:
   ```bash
   # In terminal with venv activated
   python3 api_server.py
   ```

4. **Test query**:
   - Go to `http://localhost:3000/query`
   - Ask: "What papers use Resource-Based View?"
   - Should get LLM answer (not fallback)

---

## 🎯 Expected Result

**Before** (Fallback):
> "I found 378 research questions... To provide a more detailed answer, I would need access to an LLM service..."

**After** (OLLAMA):
> "Based on the research data, Resource-Based View (RBV) is used in several papers... [detailed LLM-generated answer]"

---

**Add `USE_OLLAMA=true` to your `.env` file and restart the backend to enable OLLAMA for queries!**

