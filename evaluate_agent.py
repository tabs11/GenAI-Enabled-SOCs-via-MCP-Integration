import os
import sys
import json
import shutil
import asyncio
import pandas as pd
from datetime import datetime
from contextlib import AsyncExitStack

# Agent and MCP imports mirroring app.py
from agent import build_react_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.messages import SystemMessage, HumanMessage

wazuh_server_params = StdioServerParameters(command=sys.executable, args=["wazuh_server.py"])
mitre_server_params = StdioServerParameters(command=sys.executable, args=["mitre_server.py"])

async def evaluate_agent():
    scenarios_dir = "scenarios"
    results = []
    selected_model = "llama3.1:latest"  # Matches the Streamlit UI screenshot to ensure identical behavior
    
    print("[*] Initializing MCP connections...")
    async with AsyncExitStack() as stack:
        try:
            wazuh_transport = await stack.enter_async_context(stdio_client(wazuh_server_params))
            wazuh_session = await stack.enter_async_context(ClientSession(wazuh_transport[0], wazuh_transport[1]))
            await wazuh_session.initialize()
            
            mitre_transport = await stack.enter_async_context(stdio_client(mitre_server_params))
            mitre_session = await stack.enter_async_context(ClientSession(mitre_transport[0], mitre_transport[1]))
            await mitre_session.initialize()
        except Exception as e:
            print(f"[-] Could not connect to MCP servers: {e}")
            return
            
        agent = build_react_agent(wazuh_session, mitre_session, selected_model)
        
        # System prompt EXACTLY mirroring app.py
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

        for file in os.listdir(scenarios_dir):
            if not file.endswith(".json"):
                continue
                
            filepath = os.path.join(scenarios_dir, file)
            print(f"[*] Evaluating scenario: {file}")
            
            # Inject into alert.json so 'fetch_wazuh_alerts' MCP tool picks it up
            shutil.copy(filepath, "alert.json")
            
            with open(filepath, 'r') as f:
                injected_log = json.load(f)
                
            # Prepare state mimicking app.py interaction
            state = {
                "messages": [
                    system_prompt, 
                    HumanMessage(content=f"[{datetime.now()}] Start the autonomous triage process. You MUST call `fetch_wazuh_alerts` NOW to get the latest alert data, do not assume or invent anything.")
                ]
            }
            
            final_report = "ERROR_NO_RESPONSE"
            agent_steps = []
            
            # Run LangGraph execution using ainvoke to capture the exact final outcome directly
            print(f"    - Running agent stream...")
            try:
                final_state = await agent.ainvoke(state, {"recursion_limit": 15})
                
                # Parse the final state strictly to pull the actual history and the final report
                for message in final_state["messages"][2:]: # Skip system prompt and human start prompt
                    if getattr(message, "tool_calls", None):
                        for tc in message.tool_calls:
                            step = f"Tool Call: {tc['name']} (args: {tc['args']})"
                            print(f"      > {step}")
                            agent_steps.append(step)
                    elif message.type == "tool":
                        step = f"Tool Result: {message.name} => {str(message.content)[:100]}..."
                        print(f"      > {step}")
                        agent_steps.append(step)
                    elif message.type == "human" and message.content.startswith("System Error"):
                        step = f"Correction Triggered: {message.content}"
                        print(f"      > {step}")
                        agent_steps.append(step)
                
                # The final message is guaranteed to be the AI's last report before graph __end__
                final_report = final_state["messages"][-1].content
                            
            except Exception as e:
                final_report = f"EXECUTION_ERROR: {str(e)}"
                print(f"      > ERROR: {e}")
                
            results.append({
                "Filename": file,
                "Injected Rule": str(injected_log.get("rule", {}).get("description", "Unknown")),
                "Agent Steps": "\n".join(agent_steps),
                "Final Agent Output": final_report
            })
            
    # Exporting
    out_file = "evaluation_results_month6.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print(f"[+] Evaluation complete. Results saved to {out_file}")

if __name__ == "__main__":
    if not os.path.exists("scenarios"):
        print("Scenarios directory not found.")
        sys.exit(1)
        
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(evaluate_agent())
    except KeyboardInterrupt:
        pass
