# Comprehensive Fields Extraction Logic

## Overview

The comprehensive fields extraction is **100% LLM-based** - there is **NO string matching** involved. The system uses OLLAMA (CodeLlama 7B) to semantically understand and extract methodology information from research papers.

## Extraction Flow

### Step 1: Text Preparation (Rule-Based Section Detection)
- **Purpose**: Identify the methodology section in the paper
- **Method**: Rule-based keyword matching
- **Keywords searched**: "methodology", "methods", "research design", "data and methods", "empirical strategy", "analysis", "method", "approach"
- **Output**: Methodology section text (up to 8,000 characters) or empty if not found

**This is the ONLY rule-based step** - it just finds where the methodology section is, but doesn't extract any content.

### Step 2: LLM-Based Comprehensive Extraction
- **Purpose**: Extract all methodology details using semantic understanding
- **Method**: LLM (OLLAMA CodeLlama 7B) with structured prompt
- **Input**: 
  - Methodology section (if found) - up to 5,000 characters
  - Full paper text sample - up to 15,000 characters
  - Detailed extraction instructions
  - JSON schema with examples

**This is where ALL comprehensive fields are extracted** - completely LLM-based, no string matching.

## How LLM Extracts Comprehensive Fields

### Variables/Constructs Extraction
**LLM Logic:**
- Reads the methodology section
- Identifies sentences mentioning "dependent variable", "outcome", "DV", "Y variable"
- Identifies sentences mentioning "independent variable", "predictor", "IV", "X variable"
- Identifies control variables mentioned in regression models
- Identifies moderators/mediators from hypothesis statements or analysis sections

**Example LLM Understanding:**
- "Our dependent variable is firm performance measured by ROA" → Extracts: "Firm Performance"
- "We control for firm size, industry, and year" → Extracts: ["Firm Size", "Industry", "Year"]
- "Market competition moderates the relationship" → Extracts moderator: "Market Competition"

### Validity/Reliability Extraction
**LLM Logic:**
- Searches for mentions of reliability measures: "Cronbach's Alpha", "reliability", "inter-rater", "test-retest"
- Searches for validity mentions: "construct validity", "convergent validity", "discriminant validity"
- Extracts the actual values if mentioned (e.g., "Cronbach's Alpha = 0.85")

**Example LLM Understanding:**
- "Cronbach's Alpha for all scales exceeded 0.70" → Extracts: "Cronbach's Alpha = 0.70+"
- "We assessed construct validity through factor analysis" → Extracts: "Construct validity"

### Assumptions Checked Extraction
**LLM Logic:**
- Identifies statistical assumptions mentioned: "normality", "homoscedasticity", "multicollinearity"
- Looks for assumption testing language: "we tested", "we checked", "assumptions were verified"
- Extracts what was actually checked, not just what should be checked

**Example LLM Understanding:**
- "We tested for normality using Shapiro-Wilk test" → Extracts: "Normality"
- "VIF values were below 5, indicating no multicollinearity" → Extracts: "Multicollinearity"

### Limitations Extraction
**LLM Logic:**
- Identifies sections discussing limitations
- Looks for phrases like "limitations", "constraints", "caveats", "potential issues"
- Extracts methodology-specific limitations (not general paper limitations)

**Example LLM Understanding:**
- "A limitation of our study is the cross-sectional design" → Extracts: "Cross-sectional design limits causality"
- "Small sample size may limit generalizability" → Extracts: "Small sample size"

### Time Period Extraction
**LLM Logic:**
- Looks for date ranges in methodology section
- Identifies phrases like "from 2000 to 2020", "2015-2019", "covering the period"
- Extracts the actual time period mentioned

**Example LLM Understanding:**
- "We analyzed data from 2010 to 2020" → Extracts: "2010-2020"
- "The study period spans 2005-2019" → Extracts: "2005-2019"

### Data Collection Methods Extraction
**LLM Logic:**
- Identifies data collection methods: "survey", "interviews", "archival", "observation"
- Distinguishes between primary and secondary data
- Extracts specific methods mentioned

**Example LLM Understanding:**
- "Data were collected through semi-structured interviews" → Extracts: "Interviews"
- "We used archival data from Compustat" → Extracts: "Archival research"

## Why LLM-Based (Not String Matching)?

### Advantages:
1. **Semantic Understanding**: LLM understands context and meaning, not just keywords
2. **Variation Handling**: Handles different phrasings and terminology
3. **Context Awareness**: Understands what's actually stated vs. what should be done
4. **Flexibility**: Adapts to different paper structures and writing styles
5. **Comprehensive**: Can extract multiple related pieces of information together

### Example of LLM Advantage:
**String Matching Would Miss:**
- "The outcome of interest, firm performance, was measured using ROA"
- "Y = α + βX + controls"
- "Our dependent measure captures firm-level performance"

**LLM Understands All These** as referring to dependent variables and extracts appropriately.

## Prompt Engineering

The extraction uses a **highly structured prompt** with:
1. **Clear role definition**: "You are an expert research methodology analyst"
2. **Explicit instructions**: "Extract ONLY what is EXPLICITLY stated"
3. **Detailed examples**: Shows exactly what to extract for each field
4. **Structured output**: JSON schema with all fields defined
5. **Context provision**: Provides methodology section + full text sample

## Current Status

**Important Note**: The comprehensive fields are extracted by the LLM, but:
- The current running process (started before comprehensive extraction was added) is using the old code
- New papers processed after restart will have comprehensive fields
- The LLM is capable of extracting all these fields when the updated code runs

## Verification

To verify LLM-based extraction is working:
1. Check a newly processed paper's methodology node
2. Look for fields like `dependent_variables`, `validity_measures`, etc.
3. These will only appear if the LLM successfully extracted them from the paper text

## Summary

- **Comprehensive extraction = 100% LLM-based**
- **No string matching** for content extraction
- **Only rule-based step** = finding methodology section location
- **LLM uses semantic understanding** to extract all fields
- **Structured prompt** guides LLM to extract specific information
- **JSON schema** ensures consistent output format

