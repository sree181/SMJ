# Phase 2.2: Contribution-Synthesis Engine - Implementation Plan

## 🎯 Goal

Build a system that identifies research opportunities and gaps by detecting underexplored theory-phenomenon combinations, theory-method combinations, and rare/emerging constructs.

---

## ✅ Current Status

**Phase 1: Foundation & Core Intelligence** - ✅ COMPLETE
- Phase 1.1: Knowledge Reputation & Strength Metrics
- Phase 1.2: Reasoning Personas
- Phase 1.3: Theory Reasoning Engine - MVP

**Phase 2: Advanced Reasoning & Synthesis**
- Phase 2.1: Theory Reasoning Engine - Full - ✅ COMPLETE
- **Phase 2.2: Contribution-Synthesis Engine** - ⏳ NEXT

---

## 📋 Implementation Plan

### Backend: Contribution Opportunities Endpoint

**New Endpoint**: `GET /api/contributions/opportunities?query=...`

**Query Parameters**:
- `query` (optional): User query to filter opportunities
- `type` (optional): Filter by opportunity type (`theory-phenomenon`, `theory-method`, `construct`, `all`)
- `min_potential` (optional): Minimum potential score (0.0-1.0)
- `limit` (optional): Max results (default: 20)

**What to Detect**:

1. **Underexplored Theory-Phenomenon Combinations**:
   - Low `connection_strength` (< 0.5) or missing connections
   - High potential based on:
     - Theory explains similar phenomena
     - Phenomenon is explained by similar theories
     - Semantic similarity
   - Calculate "opportunity score" (0.0-1.0)

2. **Underexplored Theory-Method Combinations**:
   - Theories rarely used with certain methods
   - Methods that could enhance theory testing
   - Novel methodological approaches
   - Calculate "novelty score"

3. **Rare/Emerging Constructs**:
   - Constructs used in few papers (< 3 papers)
   - Emerging constructs with potential
   - Constructs that bridge theories
   - Calculate "emergence score"

4. **Sparsity Analysis**:
   - Identify gaps in the knowledge graph
   - Areas with low research density
   - Unexplored connections
   - Calculate "gap score"

**LLM Integration**:
- Generate contribution statements
- Create gap statements
- Suggest integration angles
- Propose research questions

**Response Structure**:
```json
{
  "opportunities": [
    {
      "type": "theory-phenomenon",
      "theory": "Resource-Based View",
      "phenomenon": "Digital Transformation",
      "opportunity_score": 0.85,
      "evidence": {
        "connection_strength": 0.2,
        "similar_theories": ["Dynamic Capabilities Theory"],
        "similar_phenomena": ["Technology Adoption"]
      },
      "contribution_statement": "LLM-generated...",
      "research_questions": ["LLM-generated..."],
      "rationale": "High potential based on..."
    }
  ],
  "total": 20,
  "summary": "LLM-generated summary of opportunities"
}
```

---

### Frontend: Contribution Opportunity Explorer

**New Component**: `ContributionExplorer.js`

**Features**:
1. **Opportunity List**:
   - Filterable by type
   - Sortable by opportunity score
   - Search functionality
   - Opportunity cards with:
     - Type badge
     - Theory/Phenomenon/Method names
     - Opportunity score (visual indicator)
     - Evidence summary
     - Contribution statement preview

2. **Gap Visualization**:
   - Visual representation of gaps
   - Graph showing missing connections
   - Density maps
   - Interactive exploration

3. **Contribution Statement Generator**:
   - Full contribution statement
   - Research questions
   - Integration angles
   - Export functionality
   - Share with collaborators

4. **Filters & Search**:
   - Filter by opportunity type
   - Filter by minimum score
   - Search by theory/phenomenon/method name
   - Sort options

**UI Components Needed**:
- `OpportunityCard.js`: Display individual opportunity
- `OpportunityFilters.js`: Filter and search controls
- `GapVisualization.js`: Visual gap representation
- `ContributionStatement.js`: Full statement display

---

## 🔧 Technical Implementation

### Backend Steps

1. **Create Pydantic Models**:
   ```python
   class ContributionOpportunity(BaseModel):
       type: str  # "theory-phenomenon", "theory-method", "construct"
       theory: Optional[str]
       phenomenon: Optional[str]
       method: Optional[str]
       opportunity_score: float
       evidence: Dict[str, Any]
       contribution_statement: str
       research_questions: List[str]
       rationale: str
   
   class ContributionOpportunitiesResponse(BaseModel):
       opportunities: List[ContributionOpportunity]
       total: int
       summary: str
   ```

2. **Implement Gap Detection Logic**:
   - Query for low-strength connections
   - Find missing connections (theories that could explain phenomena)
   - Calculate opportunity scores
   - Identify similar theories/phenomena for evidence

3. **Implement Theory-Method Gap Detection**:
   - Find theories with limited method diversity
   - Find methods rarely used with theories
   - Calculate novelty scores

4. **Implement Construct Analysis**:
   - Find rare constructs
   - Identify emerging patterns
   - Calculate emergence scores

5. **LLM Integration**:
   - Generate contribution statements
   - Generate research questions
   - Create gap statements
   - Suggest integration angles

### Frontend Steps

1. **Create API Service Method**:
   ```javascript
   export const getContributionOpportunities = async (query = null, filters = {}) => {
     const params = new URLSearchParams();
     if (query) params.append('query', query);
     if (filters.type) params.append('type', filters.type);
     if (filters.min_potential) params.append('min_potential', filters.min_potential);
     if (filters.limit) params.append('limit', filters.limit);
     
     return api.fetch(`/contributions/opportunities?${params.toString()}`);
   };
   ```

2. **Create Components**:
   - `ContributionExplorer.js` (main screen)
   - `OpportunityCard.js` (reusable)
   - `OpportunityFilters.js`
   - `GapVisualization.js` (optional, can be simple list first)
   - `ContributionStatement.js`

3. **Add Route**:
   ```javascript
   <Route path="/contributions/opportunities" element={<ContributionExplorer />} />
   ```

4. **Add Dashboard Link**:
   - Add "Contribution Opportunities" card to Dashboard

---

## 📊 Opportunity Score Calculation

### Theory-Phenomenon Opportunities

**Score Formula**:
1. **Connection Strength Gap** (40%): `1.0 - current_strength` (if connection exists) or `1.0` (if missing)
2. **Similarity Evidence** (30%): Based on similar theories/phenomena
3. **Research Density** (20%): Inverse of existing research (fewer papers = higher score)
4. **Semantic Fit** (10%): Embedding-based similarity

**Example**:
- Theory: "Resource-Based View"
- Phenomenon: "Digital Transformation"
- Current strength: 0.2 (low)
- Similar theories explain it: Yes
- Research density: Low
- **Opportunity Score**: 0.85

---

## 🧪 Testing Plan

1. **Unit Tests**:
   - Opportunity score calculation
   - Gap detection logic
   - Filter functionality

2. **Integration Tests**:
   - Endpoint with various filters
   - LLM generation quality
   - Edge cases (no opportunities, all opportunities)

3. **LLM Output Validation**:
   - Contribution statements are actionable
   - Research questions are relevant
   - Statements are grounded in evidence

---

## 📝 Success Criteria

- ✅ Users can identify contribution opportunities
- ✅ System generates actionable contribution statements
- ✅ System visualizes gaps in knowledge
- ✅ Opportunities are relevant and evidence-based
- ✅ UI is intuitive and informative

---

## 🚀 Next Steps

1. **Start Backend Implementation**:
   - Create endpoint structure
   - Implement gap detection logic
   - Implement opportunity scoring
   - Implement LLM generation

2. **Start Frontend Implementation**:
   - Create opportunity explorer UI
   - Add filters and search
   - Add route and navigation
   - Integrate with backend

3. **Test & Refine**:
   - Test with real data
   - Refine opportunity scoring
   - Improve LLM prompts

---

**Ready to start Phase 2.2 implementation!**

