import streamlit as st
import asyncio
import json
import sys
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import shutil

from langchain_core.messages import SystemMessage, HumanMessage
import agent
from datetime import datetime
import importlib
importlib.reload(agent)
from agent import build_react_agent
import ollama

# Configure Ollama client to use Docker service if OLLAMA_HOST is set
ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Wazuh AI Assistant", page_icon="🛡️")

def get_installed_models():
    try:
        models_info = ollama_client.list()
        return [m['model'] for m in models_info['models']]
    except Exception as e:
        return ["llama3.2", "llama3.1", "mistral", "gemma2"]

with st.sidebar:
    st.header("🎮 Lab Controller")
    st.caption("Inject a specific attack scenario into the mock environment.")
    
    # Dynamically load scenarios from folder while keeping known names mapped
    known_scenarios = {
        "alert_brute.json": "🔒 SSH Brute Force (T1110)",
        "alert_scan.json": "📡 Network Scanning (T1595)",
        "alert_exec.json": "💻 Command Execution (T1059)",
        "alert_sqli.json": "🕸️ SQL Injection (T1190)",
        "alert_scheduled_task.json": "⏱️ Scheduled Task (T1053.005)"
    }
    
    scenarios = {}
    if os.path.exists("scenarios"):
        for file in sorted(os.listdir("scenarios")):
            if file.startswith("alert_") and file.endswith(".json"):
                if file in known_scenarios:
                    scenarios[file] = known_scenarios[file]
                else:
                    # Automatically generate a display name for new scenarios
                    try:
                        with open(os.path.join("scenarios", file), "r", encoding="utf-8") as f:
                            data = json.load(f)
                            desc = data.get("rule", {}).get("description", file.replace(".json", ""))
                            # Truncate description so it fits cleanly in the sidebar
                            if len(desc) > 35:
                                desc = desc[:32] + "..."
                            mitre_info = data.get("rule", {}).get("mitre", {}).get("id", ["Unknown"])
                            mitre_id = mitre_info[0] if mitre_info else "Unknown"
                            scenarios[file] = f"📄 {desc} ({mitre_id})"
                    except Exception:
                        scenarios[file] = f"📄 {file}"
                        
    if not scenarios:
        scenarios["none.json"] = "⚠️ No scenarios found in folder"
    
    selected_scenario_file = st.selectbox(
        "Select Attack Vector:",
        options=list(scenarios.keys()),
        format_func=lambda x: scenarios[x]
    )
    
    if st.button("🔌 Inject Scenario", type="secondary") and selected_scenario_file != "none.json":
        source_file = os.path.join("scenarios", selected_scenario_file)
        
        try:
            shutil.copy(source_file, "alert.json")
            st.success(f"Injected: {scenarios[selected_scenario_file]}")
            
            # Clear state
            if "agent_history" in st.session_state:
                st.session_state["agent_history"] = []
            if "alert_data" in st.session_state:
                del st.session_state["alert_data"]
            if "knowledge_context" in st.session_state:
                del st.session_state["knowledge_context"]
            if "messages" in st.session_state:
                st.session_state.messages = []
                
        except FileNotFoundError:
            st.error(f"Missing file: {source_file}. Did you create the 'scenarios' folder?")

    st.divider()
    
    st.header("⚙️ Architecture Mode")
    app_mode = st.radio(
        "Select Investigation Mode:",
        options=["Agentic RAG (Autonomous)", "Static RAG (Interactive)"],
        help="Switch between autonomous LangGraph agent or manual Interactive Chat."
    )
    
    st.divider()

    st.header("🧠 AI Configuration")
    available_models = get_installed_models()
    selected_model = st.selectbox(
        "Select LLM Model:",
        options=available_models,
        index=0,
        help="Switch models to compare speed vs. accuracy."
    )
    st.caption(f"Active Model: `{selected_model}`")
    
    if app_mode == "Static RAG (Interactive)":
        st.divider()
        st.header("🎯 MITRE Intelligence Source")
        intel_options = {
            "tier1": "📋 Tier 1: Local Playbook",
            "tier2": "📊 Tier 2: Official MITRE Data",
            "tier3": "🧠 Tier 3: LLM Knowledge (Default Chat)",
            "hybrid": "🔄 Hybrid: Playbook + MITRE Data"
        }
        
        intel_mode = st.selectbox(
            "Select Intelligence Tier:",
            options=list(intel_options.keys()),
            format_func=lambda x: intel_options[x],
            index=3,
        )
        st.session_state["intel_mode"] = intel_mode

# --- MCP SERVERS (Windows Configuration) ---
wazuh_server = StdioServerParameters(command=sys.executable, args=["wazuh_server.py"])
mitre_server = StdioServerParameters(command=sys.executable, args=["mitre_server.py"])

# --- ORCHESTRATION FUNCTIONS (Async) ---

async def orchestrate_investigation():
    """STATIC RAG LOGIC: Connects, retrieves data once statically based on selected tier."""
    async with AsyncExitStack() as stack:
        try:
            wazuh_transport = await stack.enter_async_context(stdio_client(wazuh_server))
            wazuh_session = await stack.enter_async_context(ClientSession(wazuh_transport[0], wazuh_transport[1]))
            await wazuh_session.initialize()
        except:
            return None, None
            
        try:
            mitre_transport = await stack.enter_async_context(stdio_client(mitre_server))
            mitre_session = await stack.enter_async_context(ClientSession(mitre_transport[0], mitre_transport[1]))
            await mitre_session.initialize()
        except:
            return None, None

        try:
            alerts_result = await wazuh_session.call_tool("get_latest_alerts", arguments={})
            alerts_data = json.loads(alerts_result.content[0].text)
        except:
            return None, None
        
        if not alerts_data:
            return None, "No alerts found."

        target_alert = alerts_data[0]
        try:
            mitre_id = target_alert['rule']['mitre']['id'][0]
        except KeyError:
            mitre_id = None
        
        context_text = "No MITRE ID found in alert."
        intel_mode = st.session_state.get("intel_mode", "hybrid")
        
        if intel_mode == "tier3":
            # For Tier 3 Static RAG, we deliberately don't inject any MCP context.
            context_text = "N/A (Relying purely on LLM internal knowledge for mitigation strategies)."
        elif mitre_id:
            try:
                tool_map = {
                    "tier1": "get_playbook",
                    "tier2": "get_tier2_mitre_data",
                    "hybrid": "get_full_context"
                }
                tool_name = tool_map.get(intel_mode, "get_full_context")
                mitigation_result = await mitre_session.call_tool(tool_name, arguments={"technique_id": mitre_id})
                context_text = mitigation_result.content[0].text
            except Exception as e:
                context_text = f"Could not retrieve MITRE data: {str(e)}"

        return target_alert, context_text

def run_static_logic():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(orchestrate_investigation())

async def run_agentic_triage(selected_model):
    """
    Connects to both servers, configures the LangGraph Agent, and runs it on the latest alert.
    """
    async with AsyncExitStack() as stack:
        # --- CONNECT TO MCP SERVERS ---
        try:
            st.toast("🔌 Connecting to Wazuh MCP Server...", icon="🔗")
            wazuh_transport = await stack.enter_async_context(stdio_client(wazuh_server))
            wazuh_session = await stack.enter_async_context(ClientSession(wazuh_transport[0], wazuh_transport[1]))
            await wazuh_session.initialize()
            
            st.toast("🔌 Connecting to MITRE Knowledge Base...", icon="🔗")
            mitre_transport = await stack.enter_async_context(stdio_client(mitre_server))
            mitre_session = await stack.enter_async_context(ClientSession(mitre_transport[0], mitre_transport[1]))
            await mitre_session.initialize()
        except Exception as e:
            yield f"Error establishing MCP connections: {str(e)}"
            return

        # --- RUN LANGGRAPH AGENT ---
        agent = build_react_agent(wazuh_session, mitre_session, selected_model)
        
        system_prompt = SystemMessage(content='''You are an elite Cybersecurity SOC Analyst Assistant.
        
You are equipped with tools to fetch alerts and playbooks.

YOUR OBJECTIVE:
1. First, call `fetch_wazuh_alerts` to see current incidents.
2. Read the returned alert CAREFULLY. Note the EXACT MITRE technique ID and the source IP given in the JSON.
3. Call `get_tier1_playbook` passing the precise technique ID discovered in step 2. You MUST NOT assume the ID is T1110. Use the one you just read.
4. If the Tier 1 playbook is NOT found (returns an error/not found message), you MUST call `get_tier2_mitre_data` with the technique ID to get the official MITRE mitigation steps.
5. Once you have the playbook or mitigation information from ANY tier, write a final comprehensive SOC report for the human analyst focusing on the exact technique ID and attack type returned.

CRITICAL RULES FOR TOOL CALLING:
- You must use the native tool calling capability.
- When calling ANY playbook or MITRE tool, you MUST use the exact parameter name: `technique_id`.
- DO NOT output a tool call as plain text or JSON in your response message.
- DO NOT say "I will now call the tool...". If you need to use a tool, invoke it directly without any conversational text.
- Your final report MUST be a standalone, complete document. You MUST rewrite the incident details, IP, and the playbook steps precisely inside your final message. DO NOT just say "see the playbook above".
- Once you have the playbook data from the tools, synthesize everything into a well-formatted Markdown report.
- If BOTH Tier 1 and Tier 2 tools fail to find data, and you must rely entirely on your own internal knowledge (Tier 3) to generate mitigations, you MUST add a clear WARNING to the report stating this. DO NOT add this warning if Tier 1 returned a valid playbook or Tier 2 returned valid MITRE data.
''')
        
        # State to trace logic
        state = {"messages": [system_prompt, HumanMessage(content=f"[{datetime.now()}] Start the autonomous triage process. You MUST call `fetch_wazuh_alerts` NOW to get the latest alert data, do not assume or invent anything.")]}
        
        # Stream the graph logic
        final_report = None
        
        # Increased recursion limit slightly to 15 to allow room for the new Reflection correction loops
        async for event in agent.astream(state, {"recursion_limit": 15}):
            for node, content in event.items():
                if node == "agent":
                    message = content["messages"][-1]
                    if getattr(message, "tool_calls", None):
                        for tc in message.tool_calls:
                            yield {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
                    else:
                        # Capture the agent's text output, but DO NOT yield it to the UI yet.
                        # If it hallucinated, this variable will be overwritten by its next attempt.
                        final_report = message.content
                elif node == "tools":
                    message = content["messages"][-1]
                    yield {"type": "tool_result", "name": message.name, "result": message.content}
        
        # Only yield the Final Triage Report to the UI once the LangGraph execution has completely finished.
        if final_report:
            yield {"type": "content", "content": final_report}

def start_triage():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(run_event_stream())

async def run_event_stream():
    events = []
    async for e in run_agentic_triage(selected_model):
        events.append(e)
    return events

# --- INTERFACE ---
st.title("🛡️ Wazuh AI Analyst")

if app_mode == "Agentic RAG (Autonomous)":
    st.caption("Architecture: Streamlit UI → LangGraph ReAct Agent → [Wazuh + MITRE MCP Servers]")
    
    if "agent_history" not in st.session_state:
        st.session_state["agent_history"] = []
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.subheader("Agent Control")
        if st.button("🚨 Autonomous Triage (Run Agent)", type="primary", use_container_width=True):
            st.session_state["agent_history"] = [] # clear previous run
            with st.spinner("Agent is thinking..."):
                events = start_triage()
                st.session_state["agent_history"] = events
        
        st.divider()
        st.subheader("Agent Thought Process")
        
        if st.session_state["agent_history"]:
            for event in st.session_state["agent_history"]:
                if isinstance(event, str):
                    st.error(event)
                elif event["type"] == "tool_call":
                    with st.status(f"Agent called tool: `{event['name']}`") as status:
                        st.json(event["args"])
                elif event["type"] == "tool_result":
                    with st.expander(f"Tool Output: `{event['name']}`"):
                        st.text(str(event["result"])[:500] + "... (truncated)" if len(str(event["result"])) > 500 else str(event["result"]))
        else:
            st.info("Click 'Autonomous Triage' to start the agent.")
    
    with col_right:
        st.subheader("Final Triage Report")
        
        has_report = False
        if st.session_state["agent_history"]:
            for event in st.session_state["agent_history"]:
                if isinstance(event, dict) and event.get("type") == "content" and event.get("content"):
                    st.info(event["content"])
                    has_report = True
                    
        if not has_report:
            st.info("The final generated triage report will appear here once the agent finishes its investigation.")

else:
    # --- STATIC RAG UI Mode ---
    st.caption("Architecture: Static Connect → Load Context → LLM Chat")
    
    col_dashboard, col_chat = st.columns([1.5, 1])

    with st.spinner("Fetching static context from MCP Servers..."):
        if "alert_data" not in st.session_state:
            data, context = run_static_logic()
            st.session_state["alert_data"] = data
            st.session_state["knowledge_context"] = context
        
        alert_data = st.session_state.get("alert_data")
        knowledge_context = st.session_state.get("knowledge_context")

    with col_dashboard:
        st.subheader("🚨 Static Alert Feed (Mock/Live)")
        if alert_data:
            st.info(f"**Rule:** {alert_data.get('rule', {}).get('description', 'Unknown Alert')}")
            with st.expander("🧠 Retrieved Context (From MITRE Server)", expanded=True):
                st.markdown(knowledge_context)
            with st.expander("🔍 Raw Alert Data"):
                st.json(alert_data)
        else:
            st.warning("No alerts received.")

    with col_chat:
        st.subheader("🤖 Static AI Chatbot")
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "I have loaded the data statically. How can I help?"}]

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask a question about the loaded alert..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                system_persona = """You are an elite Cybersecurity SOC Analyst Assistantizing in SIEM alert triage."""
                current_tier = st.session_state.get("intel_mode", "hybrid")
                tier_focus = {
                    "tier1": "Focus: Playbook actions.", "tier2": "Focus: Summarize.", "tier3": "Focus: Deep dive.", "hybrid": "Focus: Explain and remediate."
                }
                
                final_prompt = f"""{system_persona}\n{tier_focus[current_tier]}\n🚨 ALERT DATA:\n{json.dumps(alert_data)}\n📚 KNOWLEDGE BASE:\n{knowledge_context}\n❓ QUESTION: {prompt}"""
                
                stream = ollama_client.chat(model=selected_model, messages=[{'role': 'user', 'content': final_prompt}], stream=True)
                
                def stream_parser(raw_stream):
                    for chunk in raw_stream:
                        if 'message' in chunk and 'content' in chunk['message']:
                            yield chunk['message']['content']

                response = st.write_stream(stream_parser(stream))
            
            st.session_state.messages.append({"role": "assistant", "content": response})