# Phase 1.3: Theory Reasoning Engine - MVP

## 🎯 Goal

Build a theory comparison system that analyzes compatibility, tensions, and integration opportunities between theories using graph data and LLM reasoning.

---

## ✅ Status: Ready to Start

**Previous Phases**:
- ✅ Phase 1.1: Knowledge Reputation & Strength Metrics - COMPLETE
- ✅ Phase 1.2: Reasoning Personas - COMPLETE

---

## 📋 Implementation Plan

### Backend: Theory Comparison Endpoint

**Endpoint**: `POST /api/theories/compare`

**Input**:
```json
{
  "theories": ["Resource-Based View", "Dynamic Capabilities"],
  "query": "optional user question for context"
}
```

**What to Query from Neo4j**:

1. **Phenomena Each Theory Explains**:
   - Get all `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)` relationships
   - Include connection strengths
   - Get aggregated statistics (avg, max, min strength)

2. **Connection Strengths**:
   - Use `EXPLAINS_PHENOMENON` relationships with `connection_strength` property
   - Compare strength distributions between theories

3. **Co-usage Patterns**:
   - Query `(Theory1)-[:COMMONLY_USED_WITH]->(Theory2)` relationships
   - Check if theories appear together in papers
   - Count co-occurrence frequency

4. **Semantic Similarity**:
   - Use embeddings if available
   - Compare theory embeddings for semantic similarity
   - Check if theories explain similar phenomena

5. **Paper Context**:
   - Get papers using each theory
   - Get methods commonly used with each theory
   - Get temporal usage patterns

**LLM Analysis**:

Generate narrative covering:
- **Compatibility**: Where theories align (shared phenomena, similar methods, co-usage)
- **Tensions**: Where theories conflict (different assumptions, competing explanations)
- **Integration**: How theories could be combined (complementary strengths, integration angles)

**Output**:
```json
{
  "theories": ["Resource-Based View", "Dynamic Capabilities"],
  "compatibility": {
    "score": 0.75,
    "factors": ["Shared phenomena", "Co-usage in papers", "Similar methods"]
  },
  "tensions": [
    {
      "type": "assumption_conflict",
      "description": "...",
      "evidence": "..."
    }
  ],
  "integration": {
    "feasibility": "high",
    "suggestions": ["...", "..."]
  },
  "shared_phenomena": [...],
  "unique_phenomena": {...},
  "narrative": "LLM-generated comparison narrative"
}
```

---

### Frontend: Theory Comparison View

**Components Needed**:

1. **TheoryComparison.js** (Main Screen):
   - Theory selector (multi-select or input)
   - Comparison results display
   - Navigation to individual theory details

2. **TheoryCard.js** (Reusable):
   - Display theory name
   - Key phenomena it explains
   - Connection strength summary
   - Methods commonly used

3. **CompatibilityVisualization.js**:
   - Compatibility score (0-1 scale)
   - Visual indicator (color-coded)
   - Breakdown of compatibility factors

4. **TensionsList.js**:
   - List of identified tensions
   - Evidence for each tension
   - Type of tension (assumption, construct, level of analysis)

5. **IntegrationSuggestions.js**:
   - Integration feasibility score
   - Suggested integration angles
   - Examples from literature (if available)

**UI Flow**:
1. User navigates to `/compare` or `/theories/compare`
2. User selects 2-3 theories to compare
3. System fetches comparison data
4. Display side-by-side theory cards
5. Show compatibility score and visualization
6. List tensions and integration suggestions
7. Display LLM-generated narrative

---

## 🔧 Technical Implementation

### Backend Steps

1. **Create Pydantic Models**:
   ```python
   class TheoryComparisonRequest(BaseModel):
       theories: List[str]
       query: Optional[str] = None
   
   class CompatibilityScore(BaseModel):
       score: float
       factors: List[str]
   
   class Tension(BaseModel):
       type: str
       description: str
       evidence: str
   
   class TheoryComparisonResponse(BaseModel):
       theories: List[str]
       compatibility: CompatibilityScore
       tensions: List[Tension]
       integration: Dict[str, Any]
       shared_phenomena: List[Dict]
       unique_phenomena: Dict[str, List[Dict]]
       narrative: str
   ```

2. **Implement Neo4j Queries**:
   - Query phenomena for each theory
   - Query co-usage patterns
   - Query connection strengths
   - Query semantic similarity (if embeddings available)

3. **Implement Compatibility Analysis**:
   - Calculate compatibility score based on:
     - Shared phenomena count
     - Co-usage frequency
     - Semantic similarity
     - Method overlap

4. **Implement Tension Detection**:
   - Identify conflicting assumptions
   - Detect competing explanations for same phenomena
   - Find different levels of analysis

5. **Implement Integration Suggestions**:
   - Identify complementary strengths
   - Suggest integration angles
   - Reference existing integrations (if any)

6. **LLM Narrative Generation**:
   - Build context from graph data
   - Generate comparison narrative
   - Include compatibility, tensions, integration

### Frontend Steps

1. **Create API Service Method**:
   ```javascript
   export const compareTheories = async (theories, query = null) => {
     const response = await fetch(`${API_BASE}/api/theories/compare`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ theories, query })
     });
     return response.json();
   };
   ```

2. **Create Components**:
   - TheoryComparison.js
   - TheoryCard.js
   - CompatibilityVisualization.js
   - TensionsList.js
   - IntegrationSuggestions.js

3. **Add Route**:
   ```javascript
   <Route path="/theories/compare" element={<TheoryComparison />} />
   ```

4. **Styling**:
   - Use existing design system (Libre Franklin font, card-based UI)
   - Ensure responsive layout
   - Add loading states

---

## 📊 Data Requirements

**Neo4j Graph Must Have**:
- ✅ `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)` relationships with `connection_strength`
- ✅ `(Theory)-[:COMMONLY_USED_WITH]->(Theory)` relationships (if available)
- ✅ `(Paper)-[:USES_THEORY]->(Theory)` relationships
- ✅ `(Paper)-[:USES_METHOD]->(Method)` relationships
- ✅ Theory embeddings (optional, for semantic similarity)

**If Missing**:
- Need to compute co-usage patterns from paper-theory relationships
- May need to compute semantic similarity from theory names/phenomena

---

## 🧪 Testing Plan

1. **Unit Tests**:
   - Compatibility score calculation
   - Tension detection logic
   - Integration suggestion generation

2. **Integration Tests**:
   - Endpoint with 2 theories
   - Endpoint with 3 theories
   - Edge cases (theories with no shared phenomena, etc.)

3. **LLM Output Validation**:
   - Narrative quality
   - Grounded in graph data
   - Accurate compatibility assessment

---

## 📝 Success Criteria

- ✅ Users can compare 2-3 theories
- ✅ System identifies compatibility factors
- ✅ System detects tensions between theories
- ✅ System suggests integration opportunities
- ✅ LLM narrative is accurate and grounded
- ✅ UI is intuitive and informative

---

## 🚀 Next Steps

1. **Start Backend Implementation**:
   - Create endpoint structure
   - Implement Neo4j queries
   - Implement compatibility analysis
   - Implement LLM narrative generation

2. **Start Frontend Implementation**:
   - Create comparison UI
   - Add route and navigation
   - Integrate with backend

3. **Test & Refine**:
   - Test with real theories
   - Refine compatibility scoring
   - Improve LLM prompts

---

**Ready to start Phase 1.3 implementation!**

