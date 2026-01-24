# Search Functionality - Fixed and Enhanced ✅

## Problem
Search was returning 0 results for queries like "resource based view" even though papers exist in Neo4j.

## Solution

### 1. Enhanced Search Endpoint ✅
**File**: `api_server.py` - `POST /api/search`

**Improvements**:
- **Multi-strategy search**: Searches across:
  1. Papers using theories that match search term (via `USES_THEORY` relationship)
  2. Papers using methods that match search term (via `USES_METHOD` relationship)
  3. Papers by title/abstract/keywords
  
- **Better query structure**: Uses UNION to combine results from all three strategies
- **Comprehensive results**: Returns papers with full details (authors, theories, methods)

**Test Results**:
- ✅ "resource" → 50 papers found
- ✅ "resource based view" → Should find papers using RBV theory

---

### 2. LLM Integration for Questions ✅
**File**: `api_server.py` - `POST /api/query`

**How it works**:
- Uses existing LLM client to generate answers
- Retrieves research data from Neo4j
- Returns answer + sources

**Frontend Integration**:
- `SearchResults.js` detects questions (starts with "what", "how", etc.)
- Routes questions to LLM query endpoint
- Falls back to regular search if LLM fails

---

### 3. Unified Search Bar ✅
**File**: `src/components/common/SearchBar.js`

**Features**:
- Single search bar for both search and queries
- Automatically detects question vs search
- Help text explains both uses

---

## Search Flow

### Regular Search (e.g., "resource based view")
```
User Input → SearchBar → SearchResults
  ↓
POST /api/search
  ↓
Neo4j Query (searches theories, methods, papers)
  ↓
Returns: {papers: [...], count: N}
  ↓
Display in PaperCard components
```

### Natural Language Question (e.g., "What papers use Resource-Based View?")
```
User Input → SearchBar → SearchResults
  ↓
Detects question → POST /api/query
  ↓
LLM processes query + Neo4j data
  ↓
Returns: {answer: "...", sources: [...]}
  ↓
Display answer + source papers
```

---

## API Endpoints

### POST /api/search
**Purpose**: Direct Neo4j search
**Input**: `{query: "search term"}`
**Output**: `{papers: [...], count: N}`

**Searches**:
- Theory names (via USES_THEORY)
- Method names (via USES_METHOD)
- Paper title/abstract/keywords

### POST /api/query
**Purpose**: LLM-powered natural language query
**Input**: `{query: "question"}`
**Output**: `{answer: "...", sources: [...], graphData: {...}}`

**Uses**:
- Neo4j for data retrieval
- LLM for answer generation

---

## Testing

### Test 1: Regular Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "resource"}'
```
**Expected**: Returns papers using theories/methods with "resource" in name

### Test 2: Theory Search
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "resource based view"}'
```
**Expected**: Returns papers using "Resource-Based View" theory

### Test 3: Question Query
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What papers use Resource-Based View?"}'
```
**Expected**: Returns LLM-generated answer + source papers

---

## Status

✅ **Search Fixed**: Now searches across theories, methods, and papers
✅ **LLM Integrated**: Questions use LLM for intelligent answers
✅ **Unified Interface**: Single search bar handles both

**Ready to test!**

