# Agentic AI Architecture - ReAct Framework Implementation (FUTURE ENHANCEMENT)

> **⚠️ NOTE**: This document describes a planned future enhancement to upgrade from the current Static Hybrid RAG to an Agentic AI architecture. The current implementation uses Static Hybrid RAG. This document is kept for reference and future development.

## Current Status: NOT IMPLEMENTED

**Reason for Rollback**: Compatibility issues with `create_react_agent()` API in the current LangGraph version.

**Current Architecture**: Static Hybrid RAG (Manual data fetch + string injection)

---

## Overview

This document describes the upgrade from **Static Hybrid RAG** to **Agentic AI** using the **ReAct (Reasoning + Acting) framework** via LangChain and LangGraph, applied to defensive Blue Team SOC operations.

## Architecture Comparison

### Previous Architecture: Static Hybrid RAG
```
User Query → Manual Data Fetch (Wazuh + MITRE) → String Injection → LLM → Response
```

**Limitations:**
- Fixed data retrieval (always fetches everything)
- No dynamic reasoning about what information is needed
- Large context windows (inefficient token usage)
- No iterative refinement

### New Architecture: Agentic ReAct
```
User Query → Agent Reasoning → Tool Selection → MCP Server Call → Observation → 
Reasoning Loop (iterates) → Final Response
```

**Advantages:**
- Dynamic tool invocation based on query context
- Iterative reasoning (agent can call tools multiple times)
- Efficient token usage (only fetches relevant data)
- Self-correcting behavior
- Aligns with SEPTA methodology (supervisor's research)

## ReAct Framework Implementation

### 1. Tool Definition

**LangChain @tool Pattern:**
```python
@tool
def fetch_wazuh_alert() -> str:
    """Fetch the current security alert from Wazuh SIEM."""
    # Tool implementation with comprehensive docstring
    # Docstring is used by agent for reasoning
```

**Registered Tools:**
- `fetch_wazuh_alert()` - Retrieves current SIEM alerts
- `fetch_mitre_intelligence(technique_id: str)` - Fetches MITRE ATT&CK data

### 2. Agent Initialization

```python
agent = create_react_agent(
    llm=ChatOllama(model=selected_model),
    tools=[fetch_wazuh_alert, fetch_mitre_intelligence],
    state_modifier=system_message,  # SOC analyst persona + tier focus
    checkpointer=MemorySaver()      # Conversation state persistence
)
```

**Key Components:**
- **LLM**: ChatOllama with configurable model (Llama 3.2, 3.1, etc.)
- **Tools**: MCP server wrappers for security data retrieval
- **State Modifier**: System prompt defining agent persona and intelligence tier
- **Checkpointer**: Maintains conversation history across interactions

### 3. Agent Execution Loop

**ReAct Cycle:**
1. **Thought**: Agent reasons about the user's question
2. **Action**: Decides which tool to call (if any)
3. **Observation**: Processes tool output
4. **Thought**: Reasons about the observation
5. **Action/Final Answer**: Either calls another tool or provides final response

**Streaming Implementation:**
```python
for chunk in agent.stream(
    {"messages": [HumanMessage(content=prompt)]},
    config={"configurable": {"thread_id": thread_id}},
    stream_mode="values"
):
    # Process and display agent's reasoning and responses
```

## Intelligence Tier Integration

The agent's behavior adapts based on the selected intelligence tier:

### Tier 1: Playbook Only
- Agent focuses on procedural response steps
- Emphasizes immediate mitigation actions

### Tier 2: Summary (Description + Tactics)
- Agent provides concise MITRE technique explanations
- Balances context with brevity

### Tier 3: Deep Dive (Full Intelligence)
- Agent delivers comprehensive technical analysis
- Includes platforms, data sources, detection methods

### Hybrid (Default)
- Agent combines playbook procedures with deep MITRE analysis
- Optimal for complete incident response workflows

## MCP Server Integration

### Asynchronous Tool Execution

Tools maintain async communication with MCP servers:

```python
async def get_mitre_data():
    async with AsyncExitStack() as stack:
        # Connect to MITRE MCP server
        mitre_transport = await stack.enter_async_context(stdio_client(mitre_server))
        mitre_session = await stack.enter_async_context(ClientSession(...))
        
        # Call MCP tool based on intelligence tier
        result = await mitre_session.call_tool(tool_name, arguments={...})
        return result.content[0].text
```

### Tool-MCP Mapping

| LangChain Tool | MCP Server | MCP Tool Called |
|---------------|------------|-----------------|
| `fetch_wazuh_alert()` | wazuh_server.py | Session state cache |
| `fetch_mitre_intelligence()` | mitre_server.py | `get_playbook` / `get_summary` / `get_deep_analysis` / `get_full_context` |

## Memory and State Management

### Thread-Based Conversations

```python
thread_id = str(uuid.uuid4())  # Unique per Streamlit session
config = {"configurable": {"thread_id": thread_id}}
```

- Each user session has a persistent thread ID
- MemorySaver maintains conversation history
- Agent can reference previous interactions

### Session State Structure

```python
st.session_state = {
    "alert_data": {...},           # Cached Wazuh alert
    "knowledge_context": "...",    # Cached MITRE data (legacy)
    "messages": [...],             # Chat history
    "intel_mode": "hybrid",        # Intelligence tier selection
    "thread_id": "uuid..."         # Agent memory thread
}
```

## Comparison with SEPTA Methodology

### Similarities
- Uses ReAct framework for agent reasoning
- Tool-based architecture for modular data retrieval
- Stateful conversation management
- Dynamic decision-making based on context

### Adaptations for SOC Context
- **Domain**: Offensive Red Team (SEPTA) → Defensive Blue Team (This Project)
- **Tools**: Penetration testing commands → SIEM alert retrieval + MITRE intelligence
- **Objective**: Autonomous exploitation → Threat analysis and incident response

## Performance Considerations

### Token Efficiency
- **Before**: Always injected full alert + full MITRE data (~5000 tokens)
- **After**: Agent only fetches data when needed (~1500-3000 tokens average)

### Reasoning Overhead
- Agent adds 2-5 reasoning steps per query
- Tradeoff: Slightly slower but more accurate and contextual

### Model Requirements
- Requires function-calling capable models (Llama 3.2+, 3.1+)
- Smaller models (7B-8B) work well for structured SOC tasks

## Future Enhancements

1. **Multi-Agent Orchestration**: Separate agents for triage, investigation, and remediation
2. **Tool Expansion**: Add tools for automated response actions (e.g., block IP, isolate host)
3. **Memory Types**: Implement semantic memory for alert pattern recognition
4. **Evaluation Framework**: Measure agent performance against static RAG baseline

## References

- LangChain Documentation: https://python.langchain.com/
- LangGraph ReAct Pattern: https://langchain-ai.github.io/langgraph/
- SEPTA Project: [Supervisor's Research Reference]
- MITRE ATT&CK: https://attack.mitre.org/

---

**Author**: Master's Thesis Project  
**Date**: March 2026  
**Version**: 1.0 (Agentic Architecture)
