# agent.py

from typing import Annotated, Sequence, TypedDict, Literal
import operator
import json

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# ==========================================
# 1. Agent State Definition
# ==========================================
class AgentState(TypedDict):
    # 'operator.add' ensures new messages are appended to the list rather than replacing it
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ==========================================
# 2. Tool Binding (MCP Wrappers)
# ==========================================
def create_agent_tools(wazuh_session, mitre_session):
    """
    Wraps the active MCP client sessions into LangChain tools.
    """
    
    @tool
    async def fetch_wazuh_alerts() -> str:
        """
        Fetches the latest high-severity security alerts from the Wazuh SIEM. 
        Call this FIRST to see what needs triaging and to get the MITRE technique ID from the alert.
        """
        try:
            # We use get_latest_alerts so that the injected mock scenarios (alert.json) are used, 
            # rather than live alerts which might be stuck on old brute force attacks from Wazuh.
            result = await wazuh_session.call_tool("get_latest_alerts", arguments={})
            # result = await wazuh_session.call_tool("get_real_wazuh_alerts", arguments={"limit": 5})

            return result.content[0].text
        except Exception as e:
            return f"Error fetching alerts: {str(e)}"

    @tool
    async def get_tier1_playbook(technique_id: str) -> str:
        """
        Tier 1 (Internal Playbooks): Fetch internal SOC rules and immediate hardcoded response procedures.
        Use this first when you find an alert with a MITRE technique ID from fetch_wazuh_alerts.
        """
        try:
            result = await mitre_session.call_tool("get_playbook", arguments={"technique_id": technique_id})
            if result.isError:
                return f"O servidor MCP devolveu um erro: {result.content}"
            return "\n".join(c.text for c in result.content if c.type == "text")
            #return result.content[0].text
        except Exception as e:
            return f"Error fetching Tier 1 playbook: {str(e)}"

    @tool
    async def get_tier2_mitre_data(technique_id: str) -> str:
        """
        Tier 2 (MITRE Data): Fetch official context, tactics, and data sources for a given MITRE technique ID.
        Use this if Tier 1 lacks information.
        """
        try:
            result = await mitre_session.call_tool("get_tier2_mitre_data", arguments={"technique_id": technique_id})
            return result.content[0].text
        except Exception as e:
            return f"Error fetching Tier 2 MITRE data: {str(e)}"

    return [fetch_wazuh_alerts, get_tier1_playbook, get_tier2_mitre_data]

# ==========================================
# 3 & 4. Graph Nodes and Edges
# ==========================================
def build_react_agent(wazuh_session, mitre_session, selected_model="llama3.2"):
    tools = create_agent_tools(wazuh_session, mitre_session)
    
    # Initialize the LLM
    llm = ChatOllama(model=selected_model, temperature=0.1)
    
    # Define the Agent Node with Dynamic Tool Binding to enforce logic
    async def agent_node(state: AgentState):
        messages = state["messages"]
        
        # 1. Inspect conversation history to determine what tools have been executed
        has_fetched_alerts = False
        has_fetched_tier1 = False
        
        for m in messages:
            if getattr(m, "tool_calls", None):
                for tc in m.tool_calls:
                    if tc["name"] == "fetch_wazuh_alerts":
                        has_fetched_alerts = True
                    elif tc["name"] == "get_tier1_playbook":
                        has_fetched_tier1 = True

        # 2. Dynamically bind ONLY the tools appropriate for the current step.
        # This absolutely forces the LLM to follow the Tier 1 -> Tier 2 sequence.
        tool_choice = "auto"
        if not has_fetched_alerts:
            # Step 1: Force it to fetch alerts first
            current_tools = [tools[0]] # index 0 is fetch_wazuh_alerts
            # tool_choice = "fetch_wazuh_alerts"  # Forces the exact tool
        elif not has_fetched_tier1:
            # Step 2: Force it to check the Tier 1 playbook next
            current_tools = [tools[1]] # index 1 is get_tier1_playbook
            # tool_choice = "get_tier1_playbook" # Forces the exact tool
        else:
            # Step 3: Allow fallback (Tier 2) if Tier 1 failed, 
            # otherwise it will just write the report because no other tools are needed.
            # If Tier 2 fails, it will natively fall back to Tier 3 (LLM Latent Knowledge)
            current_tools = [tools[2]]
            
        llm_with_tools = llm.bind_tools(current_tools)
        
        # NOTE: Not using strict tool_choice="tool_name" because Ollama's bind_tools implementation
        # sometimes rejects strict forcing strings vs dicts, but drastically limiting `current_tools` 
        # usually accomplishes the same. If it still skips, we will use graph logic.
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}
    
    # Define the routing logic
    def should_continue(state: AgentState) -> Literal["tools", "correction", "__end__"]:
        last_message = state["messages"][-1]
        # If the LLM makes a tool call, route to the "tools" node
        if getattr(last_message, "tool_calls", None):
            return "tools"
            
        # Catch hallucinated tool calls (JSON plain text in normal output)
        content = str(last_message.content)
        if "{" in content and ("get_tier" in content or "fetch_wazuh" in content or '"name"' in content):
            return "correction"
            
        return "__end__"

    def correction_node(state: AgentState):
        warning = "System Error: You attempted to call a tool using plain text JSON. You MUST use the native tool calling API. Do not output conversational text or raw JSON blocks in your response. Invoke the tool correctly."
        return {"messages": [HumanMessage(content=warning)]}

    # Build the Graph
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("correction", correction_node)
    
    workflow.set_entry_point("agent")
    
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "correction": "correction",
            "__end__": END
        }
    )
    
    workflow.add_edge("tools", "agent")
    workflow.add_edge("correction", "agent")
    
    return workflow.compile()