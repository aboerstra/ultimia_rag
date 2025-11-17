# Gemini 2.5 Pro Function Calling Implementation

## Summary

Attempted to migrate from OpenRouter to Google Gemini 2.5 Pro for native function calling support in the AI chat system.

## What Was Implemented

### 1. Gemini Client (`scripts/connectors/gemini_client.py`)
- Created dedicated client for Gemini 2.5 Pro
- Uses `google-generativeai` SDK v0.8.5
- Supports function calling and text generation

### 2. Updated Configuration (`scripts/config.py`)
- Added `GEMINI_API_KEY` environment variable
- Model: `gemini-2.5-pro` (1M token context window)

### 3. Updated API Endpoint (`api/main.py`)
- Modified `/api/chat` to use GeminiClient instead of LLMClient
- Maintains same tool calling interface

## Issues Discovered

### Issue 1: API Not Enabled
```
403 Generative Language API has not been used in project 640786458847 before or it is disabled.
```

**Solution Required:**
- Visit https://console.developers.google.com/apis/api/generativelanguage.googleapis.com/overview?project=640786458847
- Enable the Generative Language API
- Wait a few minutes for propagation

### Issue 2: Schema Format Incompatibility
```
ValueError: Protocol message Schema has no "type" field
KeyError: 'object'
```

**Root Cause:**
Our tool definitions use OpenAI format:
```python
{
    "type": "function",
    "function": {
        "name": "get_stats",
        "parameters": {
            "type": "object",  # ← This causes the error
            "properties": {},
            "required": []
        }
    }
}
```

Gemini expects native `Schema` format using enums, not string "object".

**Solution Required:**
Convert schemas to Gemini's native format:
```python
from google.generativeai import protos

# Instead of "type": "object"
schema = protos.Schema(
    type=protos.Type.OBJECT,  # Enum, not string
    properties={...} 
)
```

## Next Steps

### Option 1: Fix Gemini Implementation (Recommended if API enabled)
1. Enable Generative Language API in Google Cloud Console
2. Fix schema conversion in `GeminiClient.chat_with_tools()`:
   - Convert OpenAI "type": "object" → Gemini Type.OBJECT enum
   - Convert "type": "string" → Type.STRING
   - Convert "type": "integer" → Type.INTEGER
   - etc.
3. Test and verify function calling works

### Option 2: Keep OpenRouter (Current Fallback)
- OpenRouter works but has tool calling limitations
- More expensive per token
- No access to Gemini 2.5 Pro's 1M context window

## Model Comparison

| Feature | Gemini 2.5 Pro (Direct) | OpenRouter |
|---------|------------------------|------------|
| Context Window | 1M tokens | Varies by model |
| Function Calling | Native support | Proxied/limited |
| Cost | Direct API pricing | Markup applied |
| Performance | Best for RAG/tools | General purpose |
| Requirements | Enable API + fix schema | Working now |

## Files Modified

1. `scripts/connectors/gemini_client.py` - New Gemini client
2. `scripts/config.py` - Added GEMINI_API_KEY config
3. `api/main.py` - Updated chat endpoint
4. `.env` - Added GEMINI_API_KEY=<key>
5. `test_gemini.py` - Test script for debugging

## Recommendation

**If you can enable the Generative Language API:**
- Complete the schema conversion fix
- Gemini 2.5 Pro will provide better function calling and massive context window

**If API cannot be enabled:**
- Revert to OpenRouter/Claude
- Consider alternative: Anthropic Claude (direct API)

## Code Reference

Key error location in `gemini_client.py` line 50:
```python
# This fails because Gemini doesn't accept string "object"
gemini_tools.append({
    "name": func["name"],
    "description": func["description"],
    "parameters": func.get("parameters", {})  # ← Contains "type": "object"
})
```

Fix needed: Convert to proper Schema objects before passing to Gemini.
