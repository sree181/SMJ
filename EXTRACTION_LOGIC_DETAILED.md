# Detailed Extraction Logic - Theories, Roles, and Phenomena

## 1. Theory Extraction Process

### Overview
Theories are extracted using **LLM-based extraction** (OLLAMA with llama3.1:8b) with strict, conservative rules to ensure high quality.

### Extraction Flow

```
1. Text Preparation
   ↓
   - Uses first 20,000 characters of paper
   - Focuses on Introduction + Literature Review sections
   - These sections contain the most theory discussion
   
2. LLM Extraction
   ↓
   - Uses standardized prompt template (prompt_template.py)
   - Includes few-shot examples
   - Uses JSON schema for structured output
   - Applies strict extraction rules
   
3. Validation & Normalization
   ↓
   - Validates theory names (not empty)
   - Sets default role to "supporting" if missing
   - Sets default section to "literature_review" if missing
   - Filters out invalid entries
```

### Code Location
**File**: `redesigned_methodology_extractor.py`
**Method**: `extract_theories(text: str, paper_id: str) -> List[Dict[str, Any]]`
**Lines**: 433-506

### Key Features

1. **Standardized Prompt Template**
   - Uses `prompt_template.py` for consistent structure
   - Includes few-shot examples for better accuracy
   - Provides JSON schema for structured output

2. **Strict Extraction Rules**
   ```python
   rules = [
       "Extract EXACT theory names as they appear - do NOT summarize or rewrite",
       "PRIMARY theories: Only if explicitly stated as MAIN framework AND used in analysis",
       "SUPPORTING theories: Only if EXPLICITLY USED to support arguments (not just mentioned)",
       "DO NOT extract theories only mentioned in literature review without being used",
       "Use canonical names (e.g., 'Resource-Based View' not 'RBV' if both appear)",
       "Be EXTREMELY conservative - fewer accurate theories is better than many generic ones"
   ]
   ```

3. **JSON Schema**
   ```python
   {
       "theories": [{
           "theory_name": "exact theory name as written",
           "theory_type": "framework or concept or model or perspective",
           "domain": "strategic_management or organizational_behavior or other",
           "role": "primary or supporting or challenging or extending",
           "section": "introduction or literature_review or discussion",
           "usage_context": "brief description of how theory is used",
           "description": "brief description of theory if provided in paper"
       }]
   }
   ```

4. **Caching**
   - Uses LLM response caching to avoid redundant API calls
   - Cache key: `(input_text, prompt_type, prompt_version)`
   - Speeds up re-processing of same papers

---

## 2. Primary vs Supporting Theory Differentiation

### Role Field
The `role` field in the theory extraction determines how the theory is used:
- `primary`: Main theoretical framework
- `supporting`: Used to support arguments
- `challenging`: Theories that are critiqued
- `extending`: Theories that are extended or built upon

### How Primary Theories are Identified

**CRITICAL RULES** (from prompt, lines 553-560):

A theory is marked as **PRIMARY** ONLY if **ALL** of these are true:
1. ✅ Explicitly stated as the paper's **MAIN** theoretical framework
2. ✅ Used to develop hypotheses or research questions
3. ✅ Central to the paper's argument and analysis
4. ✅ Actively used in the methodology or results discussion
5. ✅ **NOT** just mentioned in literature review
6. ✅ **NOT** just cited in passing
7. ✅ If a theory is mentioned but not used to guide the research, it is **NOT** primary

**Example of PRIMARY theory**:
```
"This paper uses Resource-Based View (RBV) as its main theoretical framework 
to explain firm performance differences. We develop hypotheses based on RBV 
predictions and test them using regression analysis."
→ Role: "primary"
```

### How Supporting Theories are Identified

**VERY RESTRICTIVE RULES** (from prompt, lines 562-572):

A theory is marked as **SUPPORTING** ONLY if:
1. ✅ The theory is **EXPLICITLY USED** to support a specific argument or finding
2. ✅ The theory is **DISCUSSED in detail** (not just named)
3. ✅ The theory appears in the methodology, results, or discussion sections
4. ✅ The theory is used to interpret or explain results

**DO NOT extract as supporting if**:
- ❌ Theory is only mentioned in literature review
- ❌ Theory is only cited without discussion
- ❌ Theory appears only once or twice
- ❌ Theory is listed among many others without specific use
- ❌ Context says "mentioned in literature review" or "without being used"

**Example of SUPPORTING theory**:
```
"We draw on Agency Theory and Institutional Theory to support our arguments 
about corporate governance. These theories help explain why firms adopt 
certain governance structures."
→ Role: "supporting"
```

**Example of what should NOT be extracted**:
```
"The literature review mentions various theories including RBV, Dynamic 
Capabilities, and Transaction Cost Economics, but these are not used in 
our analysis."
→ Should return empty list (no theories extracted)
```

### Default Behavior
- If `role` is missing from LLM response, defaults to `"supporting"` (line 502)
- This is conservative - assumes supporting unless explicitly marked as primary

### Validation
**File**: `data_validator.py`
**Class**: `TheoryData`
```python
role: str = Field(..., pattern='^(primary|supporting|challenging|extending)$')
```

Only these four roles are allowed. Any other value will fail validation.

---

## 3. Phenomenon Extraction

### Current Status: **NOT IMPLEMENTED**

After searching the codebase, **phenomenon extraction is NOT currently implemented** in the extraction pipeline.

### What Was Found

1. **Mention in `ollama_client.py`** (line 217):
   ```python
   "type": "concept|theory|framework|method|construct|variable|phenomenon"
   ```
   - This appears to be a type definition, but no actual extraction logic exists

2. **Mention in JSON output** (one example file):
   - Found "phenomenon" mentioned in a methodology extraction JSON file
   - But this appears to be part of the text content, not extracted as a separate entity

### What Would Be Needed

If you want to extract phenomena, you would need to:

1. **Add Extraction Method**
   ```python
   def extract_phenomena(self, text: str, paper_id: str) -> List[Dict[str, Any]]:
       """
       Extract phenomena from paper
       Phenomena are observable events, patterns, or behaviors studied
       """
       # Similar structure to extract_theories
   ```

2. **Add to Prompt Template**
   - Add `ExtractionType.PHENOMENON` to `prompt_template.py`
   - Create few-shot examples
   - Define JSON schema

3. **Add to Data Validator**
   - Create `PhenomenonData` class in `data_validator.py`
   - Define validation rules

4. **Add to Neo4j Ingestion**
   - Create `Phenomenon` node type
   - Create `(Paper)-[:STUDIES_PHENOMENON]->(Phenomenon)` relationship
   - Add to `ingest_paper_with_methods()` method

5. **Add to Processing Pipeline**
   - Call `extract_phenomena()` in `process_paper()` method
   - Pass to ingestion

### Example of What Phenomena Might Be

In Strategic Management research, phenomena could include:
- "Economic nationalism in court rulings"
- "Firm performance differences"
- "Strategic resource allocation"
- "Organizational learning patterns"
- "Network formation behaviors"

### Recommendation

If you want to extract phenomena, I recommend:
1. **Define what counts as a phenomenon** in your research context
2. **Create extraction method** similar to `extract_theories()`
3. **Add strict rules** to avoid over-extraction
4. **Test on sample papers** before full implementation

---

## Summary

### Theory Extraction ✅
- **Method**: LLM-based with strict rules
- **Input**: First 20k chars (Introduction + Literature Review)
- **Output**: List of theories with role, section, usage_context
- **Quality**: Conservative approach - fewer accurate theories is better

### Primary vs Supporting ✅
- **Primary**: Must be MAIN framework + used in analysis + central to argument
- **Supporting**: Must be EXPLICITLY USED to support arguments (not just mentioned)
- **Default**: If role missing, defaults to "supporting"
- **Validation**: Only 4 roles allowed (primary, supporting, challenging, extending)

### Phenomenon Extraction ❌
- **Status**: NOT IMPLEMENTED
- **Would need**: New extraction method, prompt template, data validator, Neo4j schema
- **Recommendation**: Define requirements first, then implement

---

## Code References

- **Theory Extraction**: `redesigned_methodology_extractor.py:433-506`
- **Prompt Template**: `prompt_template.py:41-84` (theory examples)
- **Data Validation**: `data_validator.py:79-87` (TheoryData class)
- **Strict Rules**: `redesigned_methodology_extractor.py:552-625` (detailed rules in prompt)

