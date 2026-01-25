# Chat LLM Fix - OpenAI API Integration

## Problem

The chat agent is returning fallback responses instead of using OpenAI:
```
To provide a more detailed answer, I would need access to an LLM service.
```

## Root Cause

The LLM client is falling back to `_generate_fallback_answer` because:
1. **OPENAI_API_KEY not set** in Railway environment variables, OR
2. **OpenAI API call is failing** and being caught silently

## Solution

### Changes Made

1. **Enhanced Logging**:
   - Added detailed logging when OpenAI API key is checked
   - Logs API key presence (length only, not the key itself)
   - Logs when OpenAI API calls are made
   - Logs errors with full details

2. **Better Error Handling**:
   - Updated OpenAI model to `gpt-4-turbo-preview` (more recent)
   - Increased `max_tokens` from 1000 to 2000
   - Added validation for OpenAI response structure
   - Better error messages in logs

3. **Improved Diagnostics**:
   - Logs whether Graph RAG or standard method is used
   - Logs when OPENAI_API_KEY is missing
   - Clear warnings about missing API key

## How to Fix

### Step 1: Verify OPENAI_API_KEY in Railway

1. Go to Railway Dashboard → Backend service
2. Go to **Variables** tab
3. Check if `OPENAI_API_KEY` is set
4. **If not set**, add it:
   - **Name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (starts with `sk-...`)
   - **Important**: Do NOT use quotes around the value

### Step 2: Check Backend Logs

After setting the API key, check Railway logs for:
```
INFO:api_server:Using OpenAI for LLM (OpenAI API key found, length: XX)
INFO:api_server:OPENAI_API_KEY found - using OpenAI for answer generation
INFO:api_server:Sending request to OpenAI API...
INFO:api_server:Successfully received answer from OpenAI
```

**If you see**:
```
WARNING:api_server:OpenAI API key not found. LLM features will be limited to fallback responses.
WARNING:api_server:OPENAI_API_KEY not set - LLM features disabled.
```

Then the API key is not set correctly.

### Step 3: Test Chat

After setting the API key and redeploying:
1. Try a query in the chat
2. You should get a detailed LLM-generated answer
3. Not the fallback message

## Expected Behavior

**Before (Fallback)**:
```
I found 500 research questions, 500 methods, 0 findings, 500 theory uses, and 500 phenomena...
To provide a more detailed answer, I would need access to an LLM service.
```

**After (With OpenAI)**:
```
Based on the research data from Strategic Management Journal, research gaps in the field include:

1. [Detailed analysis of gaps]
2. [Specific areas needing research]
3. [Theoretical gaps]
...

[Comprehensive, well-structured answer with citations]
```

## Troubleshooting

### If Still Getting Fallback:

1. **Check Railway Logs**:
   - Look for `OPENAI_API_KEY` related messages
   - Check for OpenAI API errors

2. **Verify API Key Format**:
   - Should start with `sk-`
   - No quotes or spaces
   - Full key copied correctly

3. **Check API Key Validity**:
   - Test the key at https://platform.openai.com/api-keys
   - Ensure it has credits/usage available

4. **Check Model Availability**:
   - `gpt-4-turbo-preview` should be available
   - If not, we can switch to `gpt-4` or `gpt-3.5-turbo`

## Code Changes Summary

- `api_server.py`:
  - Enhanced LLMClient initialization logging
  - Better error handling in `_generate_answer_with_openai`
  - Updated model to `gpt-4-turbo-preview`
  - Increased max_tokens to 2000
  - Added logging in query endpoint
