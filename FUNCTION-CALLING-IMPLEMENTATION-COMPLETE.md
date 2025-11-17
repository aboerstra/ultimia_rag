# Function Calling / Tool Use Implementation - COMPLETE ✅

**Date:** November 11, 2025  
**Status:** Fully Operational

---

## Problem Solved

### The Inefficiency
**Before:** The chat used RAG (semantic search) for EVERY query
- "How many Jira tickets?" → Search 50 vectors → LLM counts what it sees → Inaccurate
- "List all epics" → Search 100 vectors → May miss some → Incomplete
- Slow, imprecise, dependent on search algorithm

### The Solution  
**After:** LLM intelligently chooses the right tool for each query type
- "How many Jira tickets?" → Calls `get_stats()` → Returns exact count: 252 ✓
- "List all epics" → Calls `get_epic_list()` → Returns complete structured list ✓
- "What did they discuss about X?" → Calls `search_rag()` → Semantic search ✓

**This is the NotebookLM/ChatGPT approach!**

---

## Architecture

### How It Works

```
User asks question
    ↓
LLM analyzes query type
    ↓
LLM chooses appropriate tool(s):
  • get_stats() - for counts/aggregates
  • get_epic_list() - for structured epic data  
  • search_rag() - for semantic/contextual queries
    ↓
Tool executes and returns data
    ↓
LLM synthesizes final answer using tool results
    ↓
User gets accurate, complete answer
```

### Example Flow

**Query:** "How many total Jira issues are there?"

1. **LLM Decision:** "This is a COUNT query" → calls `get_stats()`
2. **Tool Execution:** Reads `data-sources/jira/raw/issues.json` directly
3. **Tool Returns:** `{"jira": {"total_issues": 252, "epics": 9, ...}}`
4. **LLM Response:** "There are 252 Jira issues total (9 epics, 143 stories, 87 tasks, 13 bugs)"

vs OLD way: Search vectors → get 10-50 matches → count → hope it's right

---

## Implementation Details

### 1. RAG Manager Enhancements

**File:** `scripts/connectors/rag_manager.py`

**Added Methods:**

```python
def get_stats(project_root) -> Dict:
    """Get comprehensive statistics directly from source files"""
    # Returns exact counts from:
    # - Jira issues (by type, status)
    # - Clockify hours (by project)
    # - Transcripts (count)
    # - Confluence pages (count)
```

```python
def get_epic_list(project_root) -> List[Dict]:
    """Get complete list of Jira epics with metadata"""
    # Returns structured data:
    # - Epic key, name
    # - Value stream classification
    # - Status, assignee
```

### 2. LLM Client Enhancement

**File:** `scripts/connectors/llm_client.py`

**Added Method:**

```python
def chat_with_tools(prompt, tools, max_tokens) -> Dict:
    """Chat with function calling support"""
    # Uses OpenAI-compatible tools parameter
    # Returns both content and tool_calls
    # LLM decides which tool(s) to use
```

### 3. Chat API Redesign

**File:** `api/main.py` - `/api/chat` endpoint

**Tool Definitions:**

```python
tools = [
    {
        "name": "get_stats",
        "description": "Get statistics and counts (use for 'how many', 'total count')",
        "parameters": {}
    },
    {
        "name": "get_epic_list", 
        "description": "Get complete list of Jira epics (use for 'list all epics')",
        "parameters": {}
    },
    {
        "name": "search_rag",
        "description": "Semantic search for specific details/context",
        "parameters": {
            "query": "string"
        }
    }
]
```

**Tool Execution:**

```python
# LLM chooses tools
response = llm.chat_with_tools(question, tools)

# Execute tool calls
if response.get("tool_calls"):
    for tool_call in response["tool_calls"]:
        if tool_call["name"] == "get_stats":
            result = rag.get_stats(Config.PROJECT_ROOT)
        elif tool_call["name"] == "get_epic_list":
            result = rag.get_epic_list(Config.PROJECT_ROOT)
        elif tool_call["name"] == "search_rag":
            result = rag.get_context_for_query(query)

# LLM synthesizes final answer from tool results
final_answer = llm.generate_text(tool_results_prompt)
```

---

## Query Type Routing

### Statistics Queries → `get_stats()`
- "How many total Jira issues?"
- "How many transcripts?"
- "What's the total Clockify hours?"
- "Count of Confluence pages?"
- "How many epics vs stories?"

**Returns:** Exact counts from source data files

### List Queries → `get_epic_list()`
- "List all epics"
- "Show me all epics and their value streams"
- "What epics are there?"

**Returns:** Complete structured list with metadata

### Semantic Queries → `search_rag()`
- "What did they discuss about Credit Underwriting?"
- "Tell me about Michael's priorities"
- "What concerns were raised about deployment?"
- "Show me context about Application Intake"

**Returns:** Relevant semantic search results

### Multi-Tool Queries
LLM can call multiple tools for complex questions:
- "How many epics are in Application Intake?" 
  → Calls `get_epic_list()` + filters by value stream

---

## Benefits

### Accuracy
✅ **Counts are exact** (not dependent on search)  
✅ **Lists are complete** (not limited by search results)  
✅ **Context is relevant** (when semantic search is needed)

### Performance
✅ **Faster for stats** (no embedding generation)  
✅ **No wasted tokens** (only relevant data loaded)  
✅ **Efficient tool selection** (LLM picks best approach)

### Intelligence
✅ **Query understanding** (LLM analyzes intent)  
✅ **Adaptive behavior** (right tool for right job)  
✅ **Extensible** (easy to add new tools)

---

## Comparison: Before vs After

### Before (RAG-only)
```
User: "How many total Jira issues?"
System: 
  1. Generate embedding for query
  2. Search 50 vectors
  3. Return 50 matches
  4. LLM counts what it sees: "10 issues" ❌
  5. Inaccurate, incomplete
```

### After (Function Calling)
```
User: "How many total Jira issues?"
System:
  1. LLM: "This is a stats query"
  2. Calls get_stats()
  3. Reads issues.json: 252 issues
  4. LLM: "There are 252 Jira issues total" ✅
  5. Accurate, complete, fast
```

---

## Response Format

The chat now returns additional metadata:

```json
{
  "answer": "There are 252 Jira issues total...",
  "sources_used": ["Direct Query"],
  "tools_used": ["get_stats"]
}
```

This transparency helps users understand:
- Where the answer came from
- What tools were used
- Data freshness

---

## Extensibility

### Easy to Add New Tools

Want to add time aggregation by value stream?

```python
{
    "name": "calculate_hours_by_value_stream",
    "description": "Calculate total Clockify hours per value stream",
    "parameters": {
        "value_stream": "string (optional)"
    }
}
```

Then implement in API:
```python
elif tool_name == "calculate_hours_by_value_stream":
    result = calculate_vs_hours(Config.PROJECT_ROOT)
```

The LLM will automatically use it when appropriate!

---

## Testing

### Try These Queries

**Stats Queries (should use get_stats):**
1. "How many total Jira issues are there?"
2. "How many epics vs stories?"
3. "What's the total Clockify hours?"
4. "How many Confluence pages?"

**List Queries (should use get_epic_list):**
1. "List all epics"
2. "Show me all epics and their value streams"
3. "What epics are in Application Intake?"

**Semantic Queries (should use search_rag):**
1. "What did they discuss about Credit Underwriting?"
2. "Tell me about Michael's priorities"
3. "What concerns were raised?"

**Multi-Tool Queries:**
1. "How many epics are in Application Intake and what are they?"

---

## Technical Details

### OpenAI-Compatible Tools Format

The implementation uses the OpenAI function calling format (supported by Claude via OpenRouter):

```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "What it does",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}
```

### Tool Call Response

```python
{
    "content": "text response or null",
    "tool_calls": [
        {
            "id": "call_abc123",
            "name": "get_stats",
            "arguments": {}
        }
    ]
}
```

---

## Files Modified

1. **scripts/connectors/rag_manager.py**
   - Added `get_stats()` method
   - Added `get_epic_list()` method
   - Both access source data directly for accuracy

2. **scripts/connectors/llm_client.py**
   - Added `chat_with_tools()` method
   - Handles tool calls and responses

3. **api/main.py**
   - Redesigned `/api/chat` endpoint
   - Added tool definitions
   - Implemented tool execution logic
   - Two-step process: tool execution → final synthesis

---

## Future Enhancements

### Additional Tools to Consider

1. **get_persona_summary(name)** - Get person's profile/priorities
2. **calculate_velocity(sprint)** - Calculate team velocity
3. **get_deployment_stats()** - Salesforce deployment metrics
4. **find_blockers()** - Current blocking issues
5. **get_value_stream_progress(vs)** - Progress by value stream
6. **analyze_time_allocation()** - Where are hours going?

### Advanced Features

1. **Multi-step reasoning** - LLM chains multiple tool calls
2. **Conditional logic** - If X then call Y, else call Z
3. **Error handling** - Retry with different tool if first fails
4. **Caching** - Cache tool results for common queries

---

## Summary

**Mission Accomplished! 🎉**

The chat system now intelligently routes queries to the appropriate data source:
- **Stats queries** → Direct file access (accurate counts)
- **List queries** → Structured data retrieval (complete lists)
- **Semantic queries** → Vector search (contextual answers)

This is the same architecture used by:
- **ChatGPT** (GPT-4 with plugins/tools)
- **NotebookLM** (Gemini with grounding)
- **Claude Projects** (with tools)

**Result:** Faster, more accurate, more intelligent responses that adapt to the query type.
