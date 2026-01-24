# Expert Companion Implementation Plan

## 🎯 Vision

Transform from **Dashboard-First** to **Search-First Conversational Expert Companion**

**Key Principles**:
1. Search bar is always visible (primary interface)
2. Conversational results ("I found...", "You might explore...")
3. Flexible navigation in any direction
4. Context-aware suggestions
5. Brainstorming partner

---

## 📋 Implementation Phases

### Phase 1: Unified Search & Conversational Results (Week 1)

#### 1.1 Backend: Unified Search Endpoint
**File**: `api_server.py`

**New Endpoint**:
```python
@app.post("/api/search/unified")
async def unified_search(request: UnifiedSearchRequest):
    """
    Search across papers, theories, phenomena, connections
    Returns everything in one conversational response
    """
    query = request.query
    
    # Search all entities
    papers = search_papers(query)
    theories = search_theories(query)
    phenomena = search_phenomena(query)
    connections = find_connections(query)
    
    # Generate conversational summary
    summary = generate_summary(papers, theories, phenomena, connections)
    
    # Generate suggestions
    suggestions = generate_suggestions(query, papers, theories, phenomena, connections)
    
    return {
        "summary": summary,  # "I found 8 papers, 3 theories, 2 phenomena"
        "papers": papers,
        "theories": theories,
        "phenomena": phenomena,
        "connections": connections,
        "suggestions": suggestions  # Context-aware exploration suggestions
    }
```

**Implementation Steps**:
1. Create `UnifiedSearchRequest` model
2. Implement `search_theories()` function
3. Implement `search_phenomena()` function
4. Implement `find_connections()` function
5. Implement `generate_summary()` function
6. Implement `generate_suggestions()` function

#### 1.2 Backend: Suggestions Endpoint
**File**: `api_server.py`

**New Endpoint**:
```python
@app.get("/api/suggestions/explore")
async def get_exploration_suggestions(
    entity_type: str,  # theory, phenomenon, paper, connection
    entity_id: str,
    context: Optional[str] = None
):
    """
    Get context-aware suggestions for next exploration steps
    """
    # Get related entities
    # Detect patterns
    # Generate suggestions
    return {
        "suggestions": [
            {
                "type": "phenomenon",
                "entity": "Resource allocation",
                "reason": "Strongly connected (0.85)",
                "action": "explore",
                "strength": 0.85
            }
        ]
    }
```

#### 1.3 Frontend: Search-First Interface
**File**: `src/App.js`

**Changes**:
- Make search bar the primary interface
- Remove/minimize dashboard
- Search bar always visible (sticky top)

**New Component**: `src/components/screens/SearchFirst.js`
- Replaces Dashboard as home page
- Large search bar
- Recent searches
- Quick filters

#### 1.4 Frontend: Conversational Results View
**File**: `src/components/screens/SearchResults.js`

**Changes**:
- Show conversational summary ("I found...")
- Display all entity types (papers, theories, phenomena, connections)
- Show suggestions prominently
- Make everything clickable/explorable

---

### Phase 2: Flexible Exploration (Week 2)

#### 2.1 Backend: Comparison Endpoints
**File**: `api_server.py`

**New Endpoints**:
```python
@app.get("/api/compare/theories")
async def compare_theories(theory1: str, theory2: str):
    """Compare two theories side-by-side"""

@app.get("/api/compare/phenomena")
async def compare_phenomena(phenomenon1: str, phenomenon2: str):
    """Compare two phenomena side-by-side"""
```

#### 2.2 Frontend: Modal/Overlay Navigation
**New Component**: `src/components/common/ExplorationModal.js`
- Opens when user clicks any entity
- Shows details + suggestions
- Allows navigation without losing context
- Breadcrumb trail

#### 2.3 Frontend: Context Preservation
- Track exploration path
- Show breadcrumbs
- "You came from..." indicators
- Back navigation preserves context

---

### Phase 3: Brainstorming Features (Week 3)

#### 3.1 Backend: Pattern Detection
**File**: `api_server.py`

**New Endpoint**:
```python
@app.get("/api/insights/patterns")
async def get_patterns(
    entity_type: str,
    entity_id: str
):
    """
    Detect patterns and generate insights
    - Co-occurrence patterns
    - Temporal patterns
    - Strength patterns
    - Gap identification
    """
```

#### 3.2 Frontend: Pattern Visualization
**New Component**: `src/components/common/PatternInsights.js`
- Shows detected patterns
- Visualizes relationships
- Suggests exploration paths

#### 3.3 Frontend: Proactive Suggestions
- "You might also explore..."
- "These theories are often used together"
- "This connection is increasing over time"
- "No papers connect X to Y" (gap identification)

---

## 🛠️ Technical Implementation

### Backend Changes

#### 1. Unified Search Endpoint

```python
# api_server.py

class UnifiedSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20

@app.post("/api/search/unified")
async def unified_search(request: UnifiedSearchRequest):
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        query = request.query.lower().strip()
        limit = request.limit
        
        with neo4j_service.driver.session() as session:
            # Search papers
            papers_result = session.run("""
                MATCH (p:Paper)
                WHERE toLower(p.title) CONTAINS $query
                   OR toLower(p.abstract) CONTAINS $query
                   OR any(kw in p.keywords WHERE toLower(kw) CONTAINS $query)
                RETURN p
                LIMIT $limit
            """, query=query, limit=limit).data()
            
            papers = [format_paper(record["p"]) for record in papers_result]
            
            # Search theories
            theories_result = session.run("""
                MATCH (t:Theory)
                WHERE toLower(t.name) CONTAINS $query
                OPTIONAL MATCH (t)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WITH t, count(DISTINCT ph) as phenomenon_count,
                     count(DISTINCT r.paper_id) as paper_count
                RETURN t.name, t.domain, phenomenon_count, paper_count
                LIMIT $limit
            """, query=query, limit=limit).data()
            
            theories = [
                {
                    "name": record["t.name"],
                    "domain": record.get("t.domain"),
                    "phenomenon_count": record.get("phenomenon_count", 0),
                    "paper_count": record.get("paper_count", 0)
                }
                for record in theories_result
            ]
            
            # Search phenomena
            phenomena_result = session.run("""
                MATCH (ph:Phenomenon)
                WHERE toLower(ph.phenomenon_name) CONTAINS $query
                OPTIONAL MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph)
                WITH ph, count(DISTINCT t) as theory_count,
                     count(DISTINCT r.paper_id) as paper_count
                RETURN ph.phenomenon_name, ph.phenomenon_type, 
                       ph.domain, theory_count, paper_count
                LIMIT $limit
            """, query=query, limit=limit).data()
            
            phenomena = [
                {
                    "phenomenon_name": record["ph.phenomenon_name"],
                    "phenomenon_type": record.get("ph.phenomenon_type"),
                    "domain": record.get("ph.domain"),
                    "theory_count": record.get("theory_count", 0),
                    "paper_count": record.get("paper_count", 0)
                }
                for record in phenomena_result
            ]
            
            # Find connections
            connections_result = session.run("""
                MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                WHERE toLower(t.name) CONTAINS $query
                   OR toLower(ph.phenomenon_name) CONTAINS $query
                WITH t, ph, r,
                     COALESCE(r.connection_strength, 0.5) as strength
                RETURN t.name as theory_name,
                       ph.phenomenon_name,
                       strength,
                       r.paper_id
                ORDER BY strength DESC
                LIMIT $limit
            """, query=query, limit=limit).data()
            
            connections = [
                {
                    "theory": record["theory_name"],
                    "phenomenon": record["phenomenon_name"],
                    "strength": round(record.get("strength", 0.0), 3),
                    "paper_id": record.get("r.paper_id")
                }
                for record in connections_result
            ]
            
            # Generate conversational summary
            summary = generate_conversational_summary(
                len(papers), len(theories), len(phenomena), len(connections)
            )
            
            # Generate suggestions
            suggestions = generate_exploration_suggestions(
                papers, theories, phenomena, connections
            )
            
            return {
                "summary": summary,
                "papers": papers,
                "theories": theories,
                "phenomena": phenomena,
                "connections": connections,
                "suggestions": suggestions
            }
            
    except Exception as e:
        logger.error(f"Error in unified search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_conversational_summary(papers_count, theories_count, 
                                    phenomena_count, connections_count):
    """Generate natural language summary"""
    parts = []
    if papers_count > 0:
        parts.append(f"{papers_count} paper{'s' if papers_count != 1 else ''}")
    if theories_count > 0:
        parts.append(f"{theories_count} theor{'ies' if theories_count != 1 else 'y'}")
    if phenomena_count > 0:
        parts.append(f"{phenomena_count} {'phenomena' if phenomena_count != 1 else 'phenomenon'}")
    if connections_count > 0:
        parts.append(f"{connections_count} connection{'s' if connections_count != 1 else ''}")
    
    if not parts:
        return "I couldn't find anything matching your search."
    
    return f"I found {', '.join(parts)}."

def generate_exploration_suggestions(papers, theories, phenomena, connections):
    """Generate context-aware exploration suggestions"""
    suggestions = []
    
    # If theories found, suggest exploring phenomena
    if theories:
        top_theory = theories[0]
        suggestions.append({
            "type": "explore",
            "entity_type": "theory",
            "entity": top_theory["name"],
            "reason": f"Explore {top_theory['phenomenon_count']} phenomena explained by this theory",
            "action": f"/api/connections/theory-phenomenon/{top_theory['name']}"
        })
    
    # If phenomena found, suggest exploring theories
    if phenomena:
        top_phenomenon = phenomena[0]
        suggestions.append({
            "type": "explore",
            "entity_type": "phenomenon",
            "entity": top_phenomenon["phenomenon_name"],
            "reason": f"Explore {top_phenomenon['theory_count']} theories explaining this phenomenon",
            "action": f"/api/connections/phenomenon-theory/{top_phenomenon['phenomenon_name']}"
        })
    
    # If connections found, suggest strongest
    if connections:
        strongest = connections[0]
        suggestions.append({
            "type": "explore",
            "entity_type": "connection",
            "entity": f"{strongest['theory']} → {strongest['phenomenon']}",
            "reason": f"Strong connection (strength: {strongest['strength']})",
            "action": f"/api/connections/{strongest['theory']}::{strongest['phenomenon']}/factors"
        })
    
    return suggestions
```

#### 2. Suggestions Endpoint

```python
@app.get("/api/suggestions/explore")
async def get_exploration_suggestions(
    entity_type: str,
    entity_id: str,
    context: Optional[str] = None
):
    """Get context-aware exploration suggestions"""
    try:
        if not neo4j_service.is_connected():
            raise HTTPException(status_code=503, detail="Neo4j not connected")
        
        suggestions = []
        
        if entity_type == "theory":
            # Get phenomena explained by this theory
            with neo4j_service.driver.session() as session:
                result = session.run("""
                    MATCH (t:Theory {name: $theory_name})-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon)
                    WITH ph, r.connection_strength as strength
                    ORDER BY strength DESC
                    LIMIT 5
                    RETURN ph.phenomenon_name, strength
                """, theory_name=entity_id).data()
                
                for record in result:
                    suggestions.append({
                        "type": "phenomenon",
                        "entity": record["ph.phenomenon_name"],
                        "reason": f"Strongly connected (strength: {round(record['strength'], 2)})",
                        "action": "explore",
                        "strength": round(record["strength"], 3)
                    })
        
        elif entity_type == "phenomenon":
            # Get theories explaining this phenomenon
            with neo4j_service.driver.session() as session:
                result = session.run("""
                    MATCH (t:Theory)-[r:EXPLAINS_PHENOMENON]->(ph:Phenomenon {phenomenon_name: $phenomenon_name})
                    WITH t, r.connection_strength as strength
                    ORDER BY strength DESC
                    LIMIT 5
                    RETURN t.name as theory_name, strength
                """, phenomenon_name=entity_id).data()
                
                for record in result:
                    suggestions.append({
                        "type": "theory",
                        "entity": record["theory_name"],
                        "reason": f"Explains this phenomenon (strength: {round(record['strength'], 2)})",
                        "action": "explore",
                        "strength": round(record["strength"], 3)
                    })
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Changes

#### 1. Search-First Home Page

```javascript
// src/components/screens/SearchFirst.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../common/SearchBar';

const SearchFirst = () => {
  const navigate = useNavigate();
  const [recentSearches, setRecentSearches] = useState(
    JSON.parse(localStorage.getItem('recentSearches') || '[]')
  );

  const handleSearch = (query) => {
    // Save to recent searches
    const updated = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentSearches', JSON.stringify(updated));
    
    // Navigate to results
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-16">
        {/* Logo/Title */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Research Companion
          </h1>
          <p className="text-xl text-gray-600">
            Your expert companion for exploring research
          </p>
        </div>

        {/* Search Bar - Always Visible */}
        <div className="mb-8">
          <SearchBar 
            onSearch={handleSearch}
            placeholder="Search papers, theories, phenomena, or ask a question..."
            className="text-xl"
          />
        </div>

        {/* Recent Searches */}
        {recentSearches.length > 0 && (
          <div className="mb-8">
            <h3 className="text-sm font-semibold text-gray-500 mb-3">Recent Searches</h3>
            <div className="flex flex-wrap gap-2">
              {recentSearches.map((search, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSearch(search)}
                  className="px-4 py-2 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm"
                >
                  {search}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-12 text-center">
          <p className="text-gray-500 mb-4">Quick Actions</p>
          <div className="flex justify-center gap-4">
            <button
              onClick={() => handleSearch('theories')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Browse Theories
            </button>
            <button
              onClick={() => handleSearch('phenomena')}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Browse Phenomena
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchFirst;
```

#### 2. Conversational Results View

```javascript
// src/components/screens/SearchResults.js (Updated)
import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import SearchBar from '../common/SearchBar';
import api from '../../services/api';

const SearchResults = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || '';

  const [results, setResults] = useState({
    summary: '',
    papers: [],
    theories: [],
    phenomena: [],
    connections: [],
    suggestions: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (query) {
      performUnifiedSearch(query);
    }
  }, [query]);

  const performUnifiedSearch = async (searchQuery) => {
    try {
      setLoading(true);
      setError(null);

      const data = await api.unifiedSearch(searchQuery);
      setResults(data);
    } catch (err) {
      console.error('Search error:', err);
      setError(`Failed to perform search: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (newQuery) => {
    navigate(`/search?q=${encodeURIComponent(newQuery)}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Sticky Search Bar */}
        <div className="sticky top-0 z-10 bg-white py-4 border-b border-gray-200 mb-6">
          <SearchBar onSearch={handleSearch} />
        </div>

        {/* Conversational Summary */}
        {results.summary && (
          <div className="mb-6 bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
            <p className="text-lg text-gray-800">{results.summary}</p>
          </div>
        )}

        {/* Suggestions */}
        {results.suggestions && results.suggestions.length > 0 && (
          <div className="mb-6 bg-purple-50 border-l-4 border-purple-500 p-4 rounded-r-lg">
            <h3 className="font-semibold text-gray-900 mb-2">💡 Suggestions</h3>
            <div className="space-y-2">
              {results.suggestions.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSuggestion(suggestion)}
                  className="block text-left text-blue-600 hover:text-blue-700 hover:underline"
                >
                  • {suggestion.reason}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Papers */}
          {results.papers.length > 0 && (
            <div className="lg:col-span-2">
              <h2 className="text-2xl font-bold mb-4">Papers ({results.papers.length})</h2>
              <div className="space-y-4">
                {results.papers.map((paper) => (
                  <PaperCard key={paper.paper_id} paper={paper} />
                ))}
              </div>
            </div>
          )}

          {/* Theories */}
          {results.theories.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Theories ({results.theories.length})</h2>
              <div className="space-y-3">
                {results.theories.map((theory) => (
                  <TheoryCard key={theory.name} theory={theory} />
                ))}
              </div>
            </div>
          )}

          {/* Phenomena */}
          {results.phenomena.length > 0 && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Phenomena ({results.phenomena.length})</h2>
              <div className="space-y-3">
                {results.phenomena.map((phenomenon) => (
                  <PhenomenonCard key={phenomenon.phenomenon_name} phenomenon={phenomenon} />
                ))}
              </div>
            </div>
          )}

          {/* Connections */}
          {results.connections.length > 0 && (
            <div className="lg:col-span-2">
              <h2 className="text-2xl font-bold mb-4">Connections ({results.connections.length})</h2>
              <div className="space-y-3">
                {results.connections.map((conn, idx) => (
                  <ConnectionCard key={idx} connection={conn} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchResults;
```

---

## 📊 API Integration Map

### Search-First Flow

```
User searches
  ↓
POST /api/search/unified
  ↓
Returns: summary, papers, theories, phenomena, connections, suggestions
  ↓
User clicks theory
  ↓
GET /api/connections/theory-phenomenon/{theory_name}
GET /api/suggestions/explore?entity_type=theory&entity_id={theory}
  ↓
Shows phenomena + suggestions
  ↓
User clicks phenomenon
  ↓
GET /api/phenomena/{phenomenon_name}
GET /api/suggestions/explore?entity_type=phenomenon&entity_id={phenomenon}
  ↓
Shows details + suggestions
  ↓
User explores further...
```

---

## ✅ Implementation Checklist

### Phase 1: Core (Week 1)
- [ ] Backend: Unified search endpoint
- [ ] Backend: Suggestions endpoint
- [ ] Frontend: Search-first home page
- [ ] Frontend: Conversational results view
- [ ] Frontend: Entity cards (Theory, Phenomenon, Connection)

### Phase 2: Exploration (Week 2)
- [ ] Backend: Comparison endpoints
- [ ] Frontend: Modal/overlay navigation
- [ ] Frontend: Context preservation
- [ ] Frontend: Breadcrumb trail

### Phase 3: Brainstorming (Week 3)
- [ ] Backend: Pattern detection
- [ ] Frontend: Pattern visualization
- [ ] Frontend: Proactive suggestions
- [ ] Frontend: Gap identification

---

## 🎯 Success Metrics

1. **Search-First**: Search bar is primary interface
2. **Conversational**: Results feel like talking to a colleague
3. **Flexible**: Can explore in any direction
4. **Suggestive**: Proactively suggests next steps
5. **Expert-Level**: Shows full complexity when needed

---

## Summary

**Transformation**: Dashboard → Search-First Expert Companion

**Key Changes**:
1. Unified search endpoint (searches everything)
2. Conversational results ("I found...")
3. Context-aware suggestions
4. Flexible navigation (any direction)
5. Brainstorming features (patterns, gaps, comparisons)

**This transforms the tool into an intelligent research companion!**

