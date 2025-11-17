# Clockify RAG Integration Fix

## Issue
AI chat was responding with:
> "I apologize, but I do not have access to any Clockify details. My capabilities do not include accessing external time-tracking systems like Clockify."

Despite Clockify time entries being downloaded and indexed in the RAG system.

## Investigation Summary

### What We Found

1. ✅ **Clockify Data Exists**
   - Location: `data-sources/clockify/raw/project_summary.json`
   - Contains: 4 MAXCOM projects with 461.5 total hours tracked
   - Projects indexed: MAXCOM-020, MAXCOM-021, MAXCOM-022, MAXCOM-023

2. ✅ **RAG System Properly Indexes Clockify**
   - Code in `scripts/connectors/rag_manager.py` (lines 256-281)
   - Each project indexed individually with metadata
   - Verified: 993 documents total in vector database

3. ✅ **System Context Lists Clockify**
   - `data-sources/custom-context/system-context.md` mentions Clockify as available data source

4. ❌ **Root Cause: AI Not Using Tools**
   - Gemini was responding based on training data instead of calling RAG search tools
   - System context didn't explicitly **require** tool usage before responding
   - When no tools called → AI defaults to "I don't have access" response

## Root Cause

**The system-context.md file was not directive enough.** It described what data sources were available but didn't explicitly **instruct** the AI to use the search tools before responding. This caused Gemini to answer based on its training data rather than searching the indexed RAG data.

## Solution

Updated `data-sources/custom-context/system-context.md` with explicit, directive instructions:

### Key Changes

1. **Added "CRITICAL INSTRUCTION" section**
   - Explicitly states: "YOU MUST use the available tools to search the indexed data"
   - Lists specific scenarios when tools MUST be used (Jira, Clockify, Confluence, etc.)

2. **Made tool usage mandatory**
   - Changed from descriptive ("Search internal data FIRST") 
   - To directive ("**ALWAYS call search_rag FIRST** - Do not respond without searching")

3. **Prohibited incorrect responses**
   - Added: "**DO NOT respond with 'I don't have access' - Instead: Call search_rag**"
   - Clear instruction to search first, only say "No results found" if truly empty

4. **Listed available tools explicitly**
   - `search_rag` - Semantic search across ALL data sources
   - `get_stats` - Get counts and statistics
   - `get_epic_list` - List all Jira epics

## Testing Required

After this fix, test the following queries to verify:

1. **Clockify-specific queries:**
   - "How many hours were tracked for MAXCOM projects?"
   - "Show me Clockify time entries"
   - "What are the billable hours for Axia Platinum?"

2. **Expected behavior:**
   - AI should call `search_rag` or `get_stats` tool
   - Should return Clockify data from indexed projects
   - Should cite "Clockify" as a source

3. **Verification:**
   - Check that tool_calls array in response includes "search_rag" or "get_stats"
   - Verify sources_used includes "Clockify" or "Semantic Search"

## Files Changed

1. **data-sources/custom-context/system-context.md**
   - Added CRITICAL INSTRUCTION section
   - Made tool usage mandatory before responding
   - Prohibited "I don't have access" responses without searching

## System Architecture Notes

The AI chat system works as follows:

```
User Question
    ↓
api/main.py /api/chat endpoint
    ↓
Loads system-context.md (always included)
    ↓
gemini_client.py with function calling
    ↓
Gemini decides: call tools OR respond directly
    ↓
If tools called → rag_manager.py searches vector DB
    ↓
Results returned → Gemini synthesizes final answer
```

The fix ensures Gemini **always calls tools** for data queries rather than responding directly based on training data.

## Additional Notes

- RAG system currently has **993 documents** indexed
- Clockify projects are indexed with metadata (source, project name, total_hours)
- Each Clockify project is indexed separately for better search granularity
- System context is loaded on **every chat request** so changes take effect immediately

## Next Steps

1. ✅ System context updated with directive instructions
2. ⏳ Test chat endpoint with Clockify queries
3. ⏳ Verify tool calling behavior
4. ⏳ Confirm Clockify data retrieval works correctly

---

**Date:** November 12, 2025  
**Issue Type:** Configuration / Prompting  
**Severity:** Medium (degraded functionality)  
**Status:** Fixed - Awaiting verification
