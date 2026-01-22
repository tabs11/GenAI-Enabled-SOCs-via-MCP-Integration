# mitre_server.py
from mcp.server.fastmcp import FastMCP

# Define a second MCP server purely for Threat Intel
mcp = FastMCP("MITRE-Knowledge-Base")

# A small local database of playbooks for your demo scenarios
# Expanded KNOWLEDGE_BASE for mitre_server.py

KNOWLEDGE_BASE = {
    # PHASE 1: RECONNAISSANCE (Scanning)
    "T1595": """
    ### MITRE T1595: Active Scanning
    **Description:** Adversaries may execute active reconnaissance scans to gather information that can be used during targeting.
    **Mitigation / Playbook:**
    1. **Block:** Add source IP to the firewall blocklist immediately.
    2. **Analyze:** Check logs to see if the scan targeted specific open ports (e.g., 22, 80, 443).
    3. **Harden:** Ensure no unnecessary ports are exposed to the public internet.
    """,

    # PHASE 2: INITIAL ACCESS (Your current demo)
    "T1110": """
    ### MITRE T1110: Brute Force
    **Description:** Adversaries may use brute force techniques to gain access to accounts.
    **Mitigation / Playbook:**
    1. **Identity:** Check /var/log/auth.log for rapid failures.
    2. **Containment:** Block source IP immediately using iptables or firewall.
    3. **Remediation:** Reset passwords for affected accounts.
    4. **Detection:** Look for Event ID 4625 (Windows) or 'Failed password' (Linux).
    """,

    # PHASE 3: EXECUTION (The attacker got in and is running commands)
    "T1059": """
    ### MITRE T1059: Command and Scripting Interpreter
    **Description:** Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries.
    **Mitigation / Playbook:**
    1. **Monitor:** Enable auditd or PowerShell logging to capture command history.
    2. **Restrict:** Use AppLocker or sudo restrictions to limit what commands users can run.
    3. **Investigate:** Look for suspicious usage of curl, wget, or encoded PowerShell strings.
    """,

    # PHASE 4: PERSISTENCE (The attacker creates a backdoor)
    "T1098": """
    ### MITRE T1098: Account Manipulation
    **Description:** Adversaries may manipulate accounts to maintain access to victim systems (e.g., adding a new SSH key).
    **Mitigation / Playbook:**
    1. **Verify:** Audit ~/.ssh/authorized_keys for unknown entries.
    2. **Revoke:** Remove unauthorized keys and force password rotation.
    3. **Alert:** Configure Wazuh to alert on file changes in /etc/passwd or /home/*/.ssh/.
    """,
    
    # PHASE 5: IMPACT (Denial of Service - Your T1190 or T1498)
    "T1190": """
    ### MITRE T1190: Exploit Public-Facing Application
    **Description:** Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program.
    **Mitigation / Playbook:**
    1. **Analysis:** Check WAF logs for SQLi or XSS patterns.
    2. **Patching:** Ensure the application is updated to the latest version.
    3. **Isolation:** If confirmed, move the web server to a quarantine VLAN.
    """
}

@mcp.tool()
def mitigations(technique_id: str) -> str:
    """
    Retrieves the SOC Playbook and mitigation strategies for a specific MITRE Technique ID.
    Example Input: "T1110"
    """
    # Look up the ID in our local dictionary
    info = KNOWLEDGE_BASE.get(technique_id)
    
    if info:
        return info
    else:
        return f"No specific playbook found for technique ID: {technique_id}. Suggest manual investigation on attack.mitre.org."

if __name__ == "__main__":
    mcp.run()