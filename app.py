import streamlit as st
import asyncio
import json
import ollama
import sys
import os
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import shutil

# Configure Ollama client to use Docker service if OLLAMA_HOST is set
ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="Wazuh AI Assistant", page_icon="🛡️")


def get_installed_models():
    """
    Fetches the list of available models from the local Ollama instance.
    Returns a default list if connection fails.
    """
    try:
        models_info = ollama_client.list()
        # return format --> {'models': [{'model': 'llama3.2:latest', ...}]}
        return [m['model'] for m in models_info['models']]
    except Exception as e:
        # Fallback: If Ollama fails, show these by default
        return ["llama3.2", "llama3.1", "mistral", "gemma2"]

with st.sidebar:
    st.header("🎮 Lab Controller")
    st.caption("Inject a specific attack scenario into the mock environment.")
    
    # 1. Define available scenarios
    scenarios = {
        "ssh_brute": "🔒 SSH Brute Force (T1110)",
        "net_scan": "📡 Network Scanning (T1595)",
        "cmd_exec": "💻 Command Execution (T1059)"
    }
    
    # 2. Dropdown to select
    selected_scenario = st.selectbox(
        "Select Attack Vector:",
        options=list(scenarios.keys()),
        format_func=lambda x: scenarios[x]
    )

    st.divider() # visual separator
    
    st.header("🧠 AI Configuration")
    
    #detect models automatically
    available_models = get_installed_models()
    
    selected_model = st.selectbox(
        "Select LLM Model:",
        options=available_models,
        index=0, # the
        help="Switch models to compare speed vs. accuracy."
    )
    
    # Shows which model is active (optional, but good for debugging)
    st.caption(f"Active Model: `{selected_model}`")
    
    st.divider() # visual separator
    
    st.header("🎯 MITRE Intelligence Source")
    
    intel_options = {
        "playbook": "📋 Custom Playbooks (Hardcoded)",
        "mitre": "🌐 Official MITRE Data (Live)",
        "combined": "🔄 Combined (Both Sources)"
    }
    
    intel_mode = st.selectbox(
        "Intelligence Mode:",
        options=list(intel_options.keys()),
        format_func=lambda x: intel_options[x],
        index=2,  # Default to combined
        help="Choose between hardcoded playbooks, real MITRE data, or both."
    )
    
    # Store in session state for use in async function
    st.session_state["intel_mode"] = intel_mode
    
    # 3. Button to Apply
    if st.button("🚨 Trigger Alert", type="primary"):
        source_file = f"scenarios/alert_{selected_scenario.replace('ssh_brute', 'brute').replace('net_scan', 'scan').replace('cmd_exec', 'exec')}.json"
        
        # Overwrite the main alert.json
        try:
            shutil.copy(source_file, "alert.json")
            st.success(f"Injected: {scenarios[selected_scenario]}")
            
            # Clear session state to force a re-run of the MCP pipeline
            if "alert_data" in st.session_state:
                del st.session_state["alert_data"]
            if "knowledge_context" in st.session_state:
                del st.session_state["knowledge_context"]
            if "messages" in st.session_state:
                st.session_state.messages = [] # Reset chat history too
                
            st.rerun() # Refresh the app immediately
            
        except FileNotFoundError:
            st.error(f"Missing file: {source_file}. Did you create the 'scenarios' folder?")


# --- MCP SERVERS (Windows Configuration) ---

# 1. Wazuh Server
# Using sys.executable to ensure the correct Python environment is called
wazuh_server = StdioServerParameters(
    command=sys.executable, 
    args=["wazuh_server.py"]
)

# 2. MITRE Server (Local Python Version - More stable on Windows)
mitre_server = StdioServerParameters(
    command=sys.executable, 
    args=["mitre_server.py"]
)

# --- ORCHESTRATION FUNCTIONS (Async) ---

async def orchestrate_investigation():
    """
    Connects to both servers, retrieves data, and cross-references information.
    """
    async with AsyncExitStack() as stack:
        # --- A. CONNECT TO WAZUH ---
        st.toast("🔌 Connecting to Wazuh MCP Server...", icon="🔗")
        try:
            wazuh_transport = await stack.enter_async_context(stdio_client(wazuh_server))
            wazuh_session = await stack.enter_async_context(ClientSession(wazuh_transport[0], wazuh_transport[1]))
            await wazuh_session.initialize()
        except Exception as e:
            st.error(f"Failed to connect to Wazuh Server: {e}")
            return None, None
        
        # --- B. CONNECT TO MITRE ---
        st.toast("🔌 Connecting to MITRE Knowledge Base...", icon="🔗")
        try:
            mitre_transport = await stack.enter_async_context(stdio_client(mitre_server))
            mitre_session = await stack.enter_async_context(ClientSession(mitre_transport[0], mitre_transport[1]))
            await mitre_session.initialize()
        except Exception as e:
            st.error(f"Failed to connect to MITRE Server (Check Node.js installation): {e}")
            return None, None

        # --- C. EXECUTION (The RAG Flow) ---
        
        # 1. Get Alerts (Wazuh Tool)
        try:
            alerts_result = await wazuh_session.call_tool("get_latest_alerts", arguments={})
            # The server returns a JSON string, we need to parse it
            alerts_data = json.loads(alerts_result.content[0].text)
        except Exception as e:
            st.error(f"Error fetching alerts: {e}")
            return None, None
        
        if not alerts_data:
            return None, "No alerts found."

        target_alert = alerts_data[0]
        
        # Extract technique ID (e.g., T1110)
        # Protection in case the alert has no MITRE ID
        try:
            mitre_id = target_alert['rule']['mitre']['id'][0]
        except KeyError:
            mitre_id = None
        
        context_text = "No MITRE ID found in alert."
        
        # 2. Get Intelligence (MITRE Tool)
        if mitre_id:
            try:
                # Get the selected intelligence mode from session state
                intel_mode = st.session_state.get("intel_mode", "combined")
                
                # Map mode to tool name
                tool_map = {
                    "playbook": "get_playbook",
                    "mitre": "get_mitre_technique",
                    "combined": "get_combined_intel"
                }
                
                tool_name = tool_map.get(intel_mode, "get_combined_intel")
                
                # Call the appropriate tool
                mitigation_result = await mitre_session.call_tool(tool_name, arguments={"technique_id": mitre_id})
                context_text = mitigation_result.content[0].text
            except Exception as e:
                context_text = f"Could not retrieve MITRE data for ID {mitre_id}: {str(e)}"

        return target_alert, context_text

def run_async_logic():
    """Helper to run async code in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    return loop.run_until_complete(orchestrate_investigation())

# --- INTERFACE (Dashboard) ---

st.title("🛡️ Wazuh AI Analyst (MCP Architecture)")
st.caption("Architecture: Streamlit Client <-> [Wazuh Server + MITRE Server]")

col_dashboard, col_chat = st.columns([1.5, 1])

# Load data (Now via MCP)
with st.spinner("Orchestrating MCP Servers..."):
    # Execute logic only once or when necessary
    if "alert_data" not in st.session_state:
        data, context = run_async_logic()
        st.session_state["alert_data"] = data
        st.session_state["knowledge_context"] = context
    
    alert_data = st.session_state["alert_data"]
    knowledge_context = st.session_state["knowledge_context"]

with col_dashboard:
    st.subheader("🚨 Live Alert Feed (via MCP)")
    if alert_data:
        st.info(f"**Rule:** {alert_data.get('rule', {}).get('description', 'Unknown Alert')}")
        
        # Show evidence that the MITRE Server worked
        with st.expander("🧠 Retrieved Context (From MITRE Server)", expanded=True):
            st.markdown(knowledge_context)
            
        with st.expander("🔍 Raw Alert Data"):
            st.json(alert_data)
    else:
        st.warning("No alerts received from Wazuh Server.")

# --- INTERFACE (Chatbot) ---
with col_chat:
    st.subheader("🤖 AI Assistant")
    
    # 1. INITIALIZE SESSION STATE
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "I have connected to the Wazuh and MITRE nodes. How can I help?"})

    # 2. DISPLAY CHAT HISTORY
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 3. HANDLE USER INPUT
    if prompt := st.chat_input("Ask a question..."):
        # Add user message to state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Response (Corrected JSON Parser Logic)
        with st.chat_message("assistant"):
            final_prompt = f"""
            CONTEXT: {knowledge_context}
            ALERT: {json.dumps(alert_data)}
            QUESTION: {prompt}
            """
            
            # Create stream
            stream = ollama_client.chat(
                model=selected_model, 
                messages=[{'role': 'user', 'content': final_prompt}], 
                stream=True
            )
            
            # Parser function to extract text from JSON chunks
            def stream_parser(raw_stream):
                for chunk in raw_stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        yield chunk['message']['content']

            # Write clean text to stream
            response = st.write_stream(stream_parser(stream))
        
        # Add assistant response to state
        st.session_state.messages.append({"role": "assistant", "content": response})