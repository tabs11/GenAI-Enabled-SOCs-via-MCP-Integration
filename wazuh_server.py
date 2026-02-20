# wazuh_server.py
import sys
import os
import json
import requests
from mcp.server.fastmcp import FastMCP
import urllib3

# Disable SSL warnings for lab environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Initialize the server
mcp = FastMCP("Wazuh-Local-Mock")

@mcp.tool()
def get_latest_alerts() -> str:
    """
    Retrieves the latest high-severity alerts from the SIEM.
    In a real scenario, this would query the Wazuh API.
    """
    sys.stderr.write("\n[SERVER LOG] MCP Client just called get_latest_alerts!\n") # Debug log to stderr
    try:
        with open('alert.json', 'r') as f:
            data = json.load(f)
            # Return as a stringified JSON list to be safe for MCP transport
            return json.dumps([data]) 
    except FileNotFoundError:
        return "[]"

@mcp.tool()
def get_real_wazuh_alerts(limit: int = 10) -> str:
    """
    Fetches real security alerts from the Wazuh Manager API.
    Requires Wazuh Manager to be running and agents to be deployed.
    
    Args:
        limit: Maximum number of alerts to retrieve (default: 10)
    
    Returns:
        JSON string containing recent security alerts from Wazuh
    """
    sys.stderr.write(f"\n[SERVER LOG] Fetching real alerts from Wazuh Manager (limit={limit})...\n")
    
    # Get Wazuh connection details from environment
    wazuh_host = os.getenv("WAZUH_MANAGER_IP", "wazuh-manager")
    wazuh_port = os.getenv("WAZUH_API_PORT", "55000")
    wazuh_user = os.getenv("WAZUH_API_USER", "wazuh-wui")
    wazuh_pass = os.getenv("WAZUH_API_PASSWORD", "MyS3cr37P450r.*-")
    
    base_url = f"https://{wazuh_host}:{wazuh_port}"
    
    try:
        # Step 1: Authenticate and get JWT token
        sys.stderr.write(f"[SERVER LOG] Authenticating to {base_url}...\n")
        auth_response = requests.post(
            f"{base_url}/security/user/authenticate",
            auth=(wazuh_user, wazuh_pass),
            verify=False,
            timeout=10
        )
        auth_response.raise_for_status()
        token = auth_response.json()['data']['token']
        
        # Step 2: Fetch alerts
        sys.stderr.write("[SERVER LOG] Fetching alerts...\n")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        alerts_response = requests.get(
            f"{base_url}/alerts",
            headers=headers,
            params={
                "limit": limit,
                "sort": "-timestamp",
                "select": "rule.id,rule.description,rule.level,rule.mitre,agent.name,timestamp,data"
            },
            verify=False,
            timeout=10
        )
        alerts_response.raise_for_status()
        
        alerts_data = alerts_response.json()
        sys.stderr.write(f"[SERVER LOG] Successfully fetched {len(alerts_data.get('data', {}).get('affected_items', []))} alerts\n")
        
        return json.dumps(alerts_data)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to connect to Wazuh API: {str(e)}"
        sys.stderr.write(f"[SERVER ERROR] {error_msg}\n")
        return json.dumps({
            "error": error_msg,
            "hint": "Make sure Wazuh Manager is running and environment variables are set correctly"
        })
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        sys.stderr.write(f"[SERVER ERROR] {error_msg}\n")
        return json.dumps({"error": error_msg})

@mcp.tool()
def get_wazuh_agents() -> str:
    """
    Lists all registered Wazuh agents and their status.
    Useful for checking if Metasploitable or other targets are being monitored.
    
    Returns:
        JSON string containing agent information (name, IP, status, OS)
    """
    sys.stderr.write("\n[SERVER LOG] Fetching Wazuh agent list...\n")
    
    wazuh_host = os.getenv("WAZUH_MANAGER_IP", "wazuh-manager")
    wazuh_port = os.getenv("WAZUH_API_PORT", "55000")
    wazuh_user = os.getenv("WAZUH_API_USER", "wazuh-wui")
    wazuh_pass = os.getenv("WAZUH_API_PASSWORD", "MyS3cr37P450r.*-")
    
    base_url = f"https://{wazuh_host}:{wazuh_port}"
    
    try:
        # Authenticate
        auth_response = requests.post(
            f"{base_url}/security/user/authenticate",
            auth=(wazuh_user, wazuh_pass),
            verify=False,
            timeout=10
        )
        auth_response.raise_for_status()
        token = auth_response.json()['data']['token']
        
        # Get agents
        headers = {"Authorization": f"Bearer {token}"}
        agents_response = requests.get(
            f"{base_url}/agents",
            headers=headers,
            params={"select": "id,name,ip,status,os.name,os.version"},
            verify=False,
            timeout=10
        )
        agents_response.raise_for_status()
        
        agents_data = agents_response.json()
        sys.stderr.write(f"[SERVER LOG] Found {agents_data.get('data', {}).get('total_affected_items', 0)} registered agents\n")
        
        return json.dumps(agents_data)
        
    except Exception as e:
        error_msg = f"Failed to fetch agents: {str(e)}"
        sys.stderr.write(f"[SERVER ERROR] {error_msg}\n")
        return json.dumps({"error": error_msg})

if __name__ == "__main__":
    mcp.run()