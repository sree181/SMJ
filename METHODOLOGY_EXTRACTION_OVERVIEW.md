# Methodology Extraction Overview

## Current Implementation

The methodology extraction system uses **LLM-based extraction** (OLLAMA with CodeLlama 7B) to extract structured methodology information from research papers. The system is **fully LLM-based** - no regex or rule-based approaches are used for extraction.

## Extraction Flow

### 1. **PDF Text Extraction**
- Uses PyMuPDF (fitz) to extract raw text from PDF files
- Extracts all text from all pages
- No preprocessing or cleaning at this stage

### 2. **Paper Metadata Extraction** (LLM-based)
- **Input**: First 10,000 characters of paper text
- **Model**: OLLAMA CodeLlama 7B
- **Extracted Fields**:
  - Title
  - Abstract (first 500 characters)
  - Authors (list)
  - Year
  - Email (corresponding author)
  - Journal name
  - DOI
  - Keywords (list)

**Prompt Strategy**: Direct JSON extraction with explicit field requirements

### 3. **Methodology Section Identification** (Hybrid Approach)
- **Step 1**: Rule-based section detection (keyword-based)
  - Searches for section headers containing: "methodology", "methods", "research design", "data and methods", "empirical strategy", "analysis", "method", "approach"
  - Extracts text until hitting: "results", "findings", "conclusion", "discussion", "references"
  - Limits to 3000 characters
  
- **Step 2**: If methodology section found, it's included in the LLM prompt
- **Step 3**: If no section found, LLM analyzes the full paper text

### 4. **Detailed Methodology Extraction** (LLM-based)
- **Input**: 
  - First 8,000 characters of full paper text
  - Methodology section (if found, up to 2,000 characters)
- **Model**: OLLAMA CodeLlama 7B
- **Extracted Fields**:
  - `type`: "quantitative" / "qualitative" / "mixed" / "other"
  - `design`: List of research designs (e.g., "experimental", "cross-sectional", "case study")
  - `quant_methods`: List of specific quantitative methods (e.g., "regression", "hazard model")
  - `qual_methods`: List of specific qualitative methods (e.g., "case study", "QCA")
  - `software`: List of software used
  - `sample_size`: Sample size description
  - `data_sources`: List of data sources
  - `analysis_techniques`: List of analysis techniques
  - `statistical_tests`: List of statistical tests
  - `confidence`: Confidence score (0.0-1.0)
  - `extraction_notes`: Notes about what was found

**Prompt Strategy**: 
- Explicitly instructs LLM to **only extract what is actually stated**
- Warns against inventing or guessing details
- Returns empty arrays if nothing is found
- Includes methodology section if available to guide extraction

### 5. **Method Normalization & Relationship Creation** (LLM-based)
- **Method Normalization**: 
  - Uses LLM to extract standardized method names from descriptions
  - Example: "parametric proportional hazards model regressions" → "Hazard Model"
  - Handles variations and extracts canonical names

- **Semantic Similarity Matching**:
  - Uses LLM to compare methods across papers
  - Identifies semantically similar methods even with different descriptions
  - Example: "parametric proportional hazards model regressions" matches "Cox proportional hazards regression"

- **Relationship Creation**:
  - Creates bidirectional `SAME_METHOD` relationships between papers
  - Stores:
    - `method`: Normalized method name
    - `method_type`: "quantitative" or "qualitative"
    - `original_method`: Original description for reference

## Key Features

### ✅ **LLM-Only Approach**
- No regex patterns
- No rule-based extraction
- All extraction uses LLM with structured prompts

### ✅ **Robust Error Handling**
- Retry logic for LLM calls (3 attempts with exponential backoff)
- JSON parsing with fallback handling
- Graceful degradation if extraction fails

### ✅ **Semantic Relationship Creation**
- LLM-based method normalization
- Semantic similarity matching across papers
- Creates meaningful connections between papers

### ✅ **Comprehensive Data Extraction**
- Paper metadata (title, authors, year, etc.)
- Detailed methodology information
- Method relationships between papers

## Current Limitations

1. **Text Length Limits**: 
   - Paper text truncated to 20,000 characters for metadata
   - Methodology section limited to 3,000 characters
   - Full paper text limited to 8,000 characters for methodology extraction

2. **LLM Model**: 
   - Uses CodeLlama 7B (faster but less accurate than larger models)
   - May miss subtle methodology details
   - Confidence scores often 0.0 (not properly extracted)

3. **Method Extraction Quality**:
   - Sometimes extracts generic descriptions instead of specific methods
   - May not capture all variations of method names
   - Software extraction often empty

4. **Processing Speed**:
   - LLM calls can be slow (especially with retries)
   - Each paper requires multiple LLM calls (metadata + methodology + relationships)

## Data Storage

### Neo4j Graph Structure

**Nodes**:
- `Paper`: Contains metadata (title, abstract, authors, year, email, journal, DOI, keywords)
- `Methodology`: Contains methodology details (type, methods, software, etc.)

**Relationships**:
- `HAS_METHODOLOGY`: Paper → Methodology (one-to-one)
- `SAME_METHOD`: Paper → Paper (bidirectional, created based on similar methods)

## Example Extraction

**Input**: PDF paper with methodology section

**Output**:
```json
{
  "paper_metadata": {
    "title": "Double-edged stars: Michelin stars, reactivity, and restaurant exits",
    "authors": ["Daniel B. Sands"],
    "year": 2025,
    "email": "daniel.sands@ucl.ac.uk"
  },
  "methodology_data": {
    "methodology": {
      "type": "quantitative",
      "quant_methods": ["parametric proportional hazards model regressions"],
      "qual_methods": [],
      "software": [],
      "confidence": 0.0
    }
  }
}
```

**Neo4j**:
- Paper node with all metadata
- Methodology node linked to paper
- SAME_METHOD relationships to other papers using similar methods

## Future Improvements

1. **Better Method Extraction**: Improve prompts to extract more specific method details
2. **Confidence Scoring**: Implement proper confidence calculation
3. **Software Detection**: Better extraction of software tools and versions
4. **Larger Context**: Increase text limits or use chunking for longer papers
5. **Better Model**: Consider using larger OLLAMA models for better accuracy

