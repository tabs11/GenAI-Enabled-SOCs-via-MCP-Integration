# wazuh_server.py
import sys
from mcp.server.fastmcp import FastMCP
import json

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

if __name__ == "__main__":
    mcp.run()