# Phenomenon Extraction and Theory-Phenomenon Connection Logic - Detailed Explanation

## Part 1: How Phenomena Are Extracted

### Overview
Phenomena are extracted using **LLM-based extraction** (OLLAMA with llama3.1:8b) with a standardized prompt template and few-shot examples.

---

### Step-by-Step Extraction Process

#### Step 1: Text Preparation
**Code Location**: `redesigned_methodology_extractor.py:508-516`

```python
def extract_phenomena(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
    # Use first 25k chars (covers introduction, literature review, and methodology)
    phenomenon_text = text[:25000]
```

**Why 25,000 characters?**
- **Introduction**: Phenomena are often introduced here
- **Literature Review**: Phenomena are described and contextualized
- **Methodology**: How phenomena are studied is explained
- **Balance**: Covers key sections without being too slow

---

#### Step 2: Prompt Construction
**Code Location**: `redesigned_methodology_extractor.py:519-546`

**Extraction Rules**:
```python
rules = [
    "Extract EXACT phenomenon names as they appear - do NOT summarize or rewrite",
    "Phenomena are observable events, patterns, behaviors, or trends that are being studied",
    "Extract ONLY phenomena that are explicitly stated as the focus of the research",
    "DO NOT extract generic concepts or theories - only concrete phenomena",
    "Be conservative - extract only clearly identified phenomena",
    "Include context about how the phenomenon is studied"
]
```

**Key Principles**:
1. **Exact Names**: Use exact text as written (no paraphrasing)
2. **Concrete Phenomena**: Only observable events/patterns/behaviors/trends
3. **Explicit Focus**: Must be explicitly stated as research focus
4. **Not Theories**: Don't extract theories or generic concepts
5. **Conservative**: Better to miss than to extract incorrectly

---

#### Step 3: JSON Schema
**Code Location**: `redesigned_methodology_extractor.py:528-537`

```python
json_schema = {
    "phenomena": [{
        "phenomenon_name": "exact phenomenon name as written",
        "phenomenon_type": "behavior or pattern or event or trend or process",
        "domain": "strategic_management or organizational_behavior or other",
        "description": "brief description of the phenomenon",
        "section": "introduction or literature_review or methodology",
        "context": "how the phenomenon is studied or examined"
    }]
}
```

**Fields Explained**:
- **`phenomenon_name`**: Exact name as it appears in the paper
- **`phenomenon_type`**: Classification (behavior, pattern, event, trend, process)
- **`domain`**: Research domain
- **`description`**: Brief description from the paper
- **`section`**: Where in the paper it appears
- **`context`**: How the phenomenon is studied (important for connections!)

---

#### Step 4: Few-Shot Examples
**Code Location**: `prompt_template.py:208-260`

**Example 1**: Single phenomenon
```
Input: "This study examines the phenomenon of economic nationalism in court 
       rulings against foreign firms."
Output: {
    "phenomenon_name": "Economic nationalism in court rulings",
    "phenomenon_type": "behavior",
    "description": "Systematic favoritism of domestic firms over foreign firms"
}
```

**Example 2**: Multiple phenomena with theory connection
```
Input: "We study two phenomena: (1) resource allocation patterns during 
       financial crises, and (2) strategic responses to market disruptions. 
       Resource-Based View helps explain why some firms maintain investments 
       while others cut back."
Output: [
    {"phenomenon_name": "Resource allocation patterns during financial crises", ...},
    {"phenomenon_name": "Strategic responses to market disruptions", ...}
]
```

**Why Few-Shot Examples?**
- Guides LLM on what to extract
- Shows expected format
- Demonstrates quality standards

---

#### Step 5: LLM Extraction
**Code Location**: `redesigned_methodology_extractor.py:548-556`

```python
response = self.extract_with_retry(
    prompt, 
    max_tokens=1500, 
    timeout=90, 
    max_retries=2,
    prompt_type="phenomenon",
    input_text=phenomenon_text
)
```

**Optimizations**:
- **1500 tokens**: Sufficient for multiple phenomena
- **90s timeout**: Fast enough for responsiveness
- **2 retries**: Balance between reliability and speed
- **Caching**: Responses are cached to avoid redundant calls

---

#### Step 6: Response Parsing and Validation
**Code Location**: `redesigned_methodology_extractor.py:558-581`

```python
# Parse JSON response
if isinstance(response, str):
    result = self._parse_json_response(response)
else:
    result = response if isinstance(response, dict) else {}

# Normalize structure
phenomena = result.get("phenomena", [])
if not phenomena and "phenomenon_name" in result:
    # Handle single phenomenon at top level
    phenomena = [result]

# Validate and clean
validated_phenomena = []
for phenomenon in phenomena:
    phenomenon_name = phenomenon.get("phenomenon_name", "").strip()
    if phenomenon_name:
        phenomenon["phenomenon_name"] = phenomenon_name
        phenomenon["phenomenon_type"] = phenomenon.get("phenomenon_type", "behavior")
        phenomenon["section"] = phenomenon.get("section", "introduction")
        validated_phenomena.append(phenomenon)
```

**Validation Steps**:
1. Parse JSON response
2. Handle edge cases (single phenomenon, wrong structure)
3. Ensure required fields exist
4. Set defaults for missing fields
5. Filter out empty/invalid entries

---

## Part 2: Theory-Phenomenon Connection Logic

### Overview
The system automatically creates `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)` relationships when theories are used to explain phenomena.

**Code Location**: `redesigned_methodology_extractor.py:2101-2145`

---

### Connection Algorithm

#### Step 1: Context Extraction
```python
# Extract context from phenomenon
phenomenon_context = (validated_phenomenon.context or "").lower()
phenomenon_description = (validated_phenomenon.description or "").lower()

# Extract context from theory
theory_usage = (theory.get("usage_context", "") or "").lower()
```

**What is Context?**
- **Phenomenon context**: How the phenomenon is studied (from extraction)
- **Theory usage context**: How the theory is used (from theory extraction)
- These are compared to find connections

---

#### Step 2: Connection Decision Logic

**Two Connection Strategies**:

##### Strategy 1: Primary Theory + Same Section
```python
should_connect = False

# Check if theory is primary and phenomenon is mentioned in same section
if theory.get("role") == "primary" and validated_phenomenon.section == theory.get("section"):
    should_connect = True
```

**Logic**:
- If theory is **primary** (main framework)
- AND phenomenon appears in **same section** as theory
- → **Connect them** (connection strength: 0.7)

**Why?**
- Primary theories are central to the paper
- Same section suggests direct relationship
- High confidence connection

**Example**:
```
Theory: "Resource-Based View" (primary, section: "introduction")
Phenomenon: "Resource allocation patterns" (section: "introduction")
→ Connection created with strength 0.7
```

---

##### Strategy 2: Context Keyword Overlap
```python
# Check if theory usage context mentions phenomenon keywords
if phenomenon_context and theory_usage:
    # Simple keyword matching
    phenomenon_words = set(phenomenon_context.split())
    theory_words = set(theory_usage.split())
    # If there's significant overlap, connect them
    if len(phenomenon_words.intersection(theory_words)) >= 2:
        should_connect = True
```

**Logic**:
- Extract words from phenomenon context
- Extract words from theory usage context
- If ≥2 words overlap → **Connect them** (connection strength: 0.5)

**Why ≥2 words?**
- Single word overlap could be coincidental ("the", "a", "is")
- Multiple words suggest semantic relationship
- More reliable connection

**Example**:
```
Theory usage: "explains how firms allocate resources during crises"
Phenomenon context: "resource allocation patterns during financial crises"
Overlap: {"resource", "allocation", "during", "crises"} = 4 words
→ Connection created with strength 0.5
```

---

#### Step 3: Relationship Creation
```python
if should_connect:
    # Create EXPLAINS_PHENOMENON relationship
    tx.run("""
        MATCH (t:Theory {name: $theory_name})
        MATCH (ph:Phenomenon {phenomenon_name: $phenomenon_name})
        MERGE (t)-[r:EXPLAINS_PHENOMENON {
            paper_id: $paper_id,
            theory_role: $theory_role,
            section: $section,
            connection_strength: $connection_strength
        }]->(ph)
    """,
    theory_name=normalized_theory_name,
    phenomenon_name=normalized_phenomenon_name,
    paper_id=paper_id,
    theory_role=theory.get("role", "supporting"),
    section=theory.get("section", "literature_review"),
    connection_strength=0.7 if theory.get("role") == "primary" else 0.5)
```

**⚠️ NOTE**: This is the OLD simple model. The NEW mathematical model uses 5 factors and continuous scale (0.0-1.0). See `CONNECTION_STRENGTH_LOGIC.md` for details.

**Relationship Properties** (NEW MODEL):
- **`paper_id`**: Which paper establishes this connection
- **`theory_role`**: How theory is used (primary, supporting, etc.)
- **`section`**: Where connection is made
- **`connection_strength`**: Calculated score (0.0-1.0) from 5 factors
- **`role_weight`**: Factor 1 score (0.0-0.4)
- **`section_score`**: Factor 2 score (0.0-0.2)
- **`keyword_score`**: Factor 3 score (0.0-0.2)
- **`semantic_score`**: Factor 4 score (0.0-0.2)
- **`explicit_bonus`**: Factor 5 score (0.0-0.1)

---

### Connection Strength Explained

#### Connection Strength 0.7 (Strong)
**Conditions**:
- Theory role = "primary"
- Phenomenon section = Theory section

**Why Strong?**
- Primary theories are central to the paper
- Same section indicates direct relationship
- High confidence that theory explains phenomenon

**Example**:
```
Paper: "Strategic management during financial crisis"
Theory: "Resource-Based View" (primary, introduction)
Phenomenon: "Resource allocation patterns" (introduction)
→ Strong connection (0.7)
```

---

#### Connection Strength 0.5 (Moderate)
**Conditions**:
- Theory usage context and phenomenon context share ≥2 keywords

**Why Moderate?**
- Keyword overlap suggests relationship
- But less direct than same section
- Medium confidence

**Example**:
```
Theory usage: "explains firm performance differences"
Phenomenon context: "firm performance variations across industries"
Overlap: {"firm", "performance"} = 2 words
→ Moderate connection (0.5)
```

---

### Complete Connection Flow

```
1. Paper is processed
   ↓
2. Theories are extracted (with usage_context)
   ↓
3. Phenomena are extracted (with context)
   ↓
4. For each phenomenon:
   ↓
5. For each theory:
   ↓
6. Check connection criteria:
   - Is theory primary + same section? → Connect (0.7)
   - OR context overlap ≥2 words? → Connect (0.5)
   ↓
7. Create EXPLAINS_PHENOMENON relationship
```

---

## Example: Complete Extraction and Connection

### Input Paper Text
```
"This study examines the phenomenon of economic nationalism in court 
rulings against foreign firms. We use Resource-Based View (RBV) as our 
main theoretical framework to explain why domestic courts systematically 
favor domestic firms over foreign firms in legal disputes."
```

### Step 1: Phenomenon Extraction
**LLM Output**:
```json
{
  "phenomena": [{
    "phenomenon_name": "Economic nationalism in court rulings",
    "phenomenon_type": "behavior",
    "description": "Systematic favoritism of domestic firms over foreign firms",
    "section": "introduction",
    "context": "Examined through court rulings and legal disputes"
  }]
}
```

### Step 2: Theory Extraction
**LLM Output**:
```json
{
  "theories": [{
    "theory_name": "Resource-Based View",
    "role": "primary",
    "section": "introduction",
    "usage_context": "Main theoretical framework to explain why domestic courts favor domestic firms"
  }]
}
```

### Step 3: Connection Logic
**Checks**:
1. **Primary + Same Section?**
   - Theory role = "primary" ✅
   - Theory section = "introduction" ✅
   - Phenomenon section = "introduction" ✅
   - **Result**: Connect with strength 0.7 ✅

2. **Context Overlap?**
   - Theory usage: "explain why domestic courts favor domestic firms"
   - Phenomenon context: "Examined through court rulings and legal disputes"
   - Overlap: {"domestic", "courts"} = 2 words ✅
   - **Result**: Would also connect with strength 0.5 (but 0.7 takes precedence)

### Step 4: Relationship Created
```cypher
(Theory {name: "Resource-Based View"})-[:EXPLAINS_PHENOMENON {
    paper_id: "2021_4327",
    theory_role: "primary",
    section: "introduction",
    connection_strength: 0.7
}]->(Phenomenon {phenomenon_name: "Economic nationalism in court rulings"})
```

---

## Why This Approach?

### Conservative Connection Strategy

**Current Approach**: Keyword matching + section overlap
- **Pros**: Fast, reliable, no additional LLM calls
- **Cons**: May miss some connections, may create false positives

**Future Enhancement**: LLM-based connection
- Use LLM to explicitly determine if theory explains phenomenon
- More accurate but slower
- Could be added as optional enhancement

### Connection Strength

**Why Two Levels?**
- **0.7 (Strong)**: High confidence (primary theory + same section)
- **0.5 (Moderate)**: Medium confidence (keyword overlap)
- Allows filtering by confidence level in queries

---

## Summary

### Phenomenon Extraction
1. **Input**: First 25k chars (Introduction + Literature Review + Methodology)
2. **LLM**: Uses standardized prompt with few-shot examples
3. **Output**: List of phenomena with name, type, description, section, context
4. **Validation**: Filters empty/invalid entries

### Theory-Phenomenon Connections
1. **Strategy 1**: Primary theory + same section → 0.7 strength
2. **Strategy 2**: Context keyword overlap (≥2 words) → 0.5 strength
3. **Relationship**: `(Theory)-[:EXPLAINS_PHENOMENON]->(Phenomenon)`
4. **Properties**: paper_id, theory_role, section, connection_strength

**Status**: Implemented and working! ✅

