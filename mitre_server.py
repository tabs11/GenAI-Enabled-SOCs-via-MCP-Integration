# mitre_server.py
from mcp.server.fastmcp import FastMCP
import requests
import json
import os
from pathlib import Path

# Define a second MCP server purely for Threat Intel
mcp = FastMCP("MITRE-Knowledge-Base")

# MITRE ATT&CK STIX data URL
MITRE_ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
CACHE_FILE = Path("mitre_attack_data.json")

# Cache duration in seconds (24 hours)
CACHE_DURATION = 86400

def download_mitre_data():
    """Download the latest MITRE ATT&CK data from the official repository."""
    try:
        response = requests.get(MITRE_ATTACK_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Cache the data locally
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f)
        
        return data
    except Exception as e:
        return None

def load_mitre_data():
    """Load MITRE data from cache or download if not available."""
    # Check if cache exists and is recent
    if CACHE_FILE.exists():
        cache_age = os.path.getmtime(CACHE_FILE)
        if (os.path.getmtime(CACHE_FILE) - cache_age) < CACHE_DURATION:
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
    
    # Download fresh data
    return download_mitre_data()

def get_technique_from_mitre(technique_id: str):
    """Extract technique details from MITRE STIX data."""
    data = load_mitre_data()
    if not data:
        return None
    
    # STIX format: look for attack-pattern objects
    for obj in data.get('objects', []):
        if obj.get('type') == 'attack-pattern':
            # Check if this is the technique we're looking for
            external_refs = obj.get('external_references', [])
            for ref in external_refs:
                if ref.get('source_name') == 'mitre-attack' and ref.get('external_id') == technique_id:
                    return {
                        'id': technique_id,
                        'name': obj.get('name', 'Unknown'),
                        'description': obj.get('description', 'No description available'),
                        'url': ref.get('url', ''),
                        'tactics': [phase['phase_name'] for phase in obj.get('kill_chain_phases', [])],
                        'platforms': obj.get('x_mitre_platforms', [])
                    }
    
    return None

# A small local database of playbooks for your demo scenarios
# Expanded KNOWLEDGE_BASE for mitre_server.py

KNOWLEDGE_BASE = {
    # PHASE 1: RECONNAISSANCE (Scanning)
    "T1595": """### MITRE T1595: Active Scanning
**Description:** Adversaries may execute active reconnaissance scans to gather information that can be used during targeting.

**Mitigation / Playbook:**
1. **Block:** Add source IP to the firewall blocklist immediately.
2. **Analyze:** Check logs to see if the scan targeted specific open ports (e.g., 22, 80, 443).
3. **Harden:** Ensure no unnecessary ports are exposed to the public internet.""",

    # PHASE 2: INITIAL ACCESS (Your current demo)
    "T1110": """### MITRE T1110: Brute Force
**Description:** Adversaries may use brute force techniques to gain access to accounts.

**Mitigation / Playbook:**
1. **Identity:** Check /var/log/auth.log for rapid failures.
2. **Containment:** Block source IP immediately using iptables or firewall.
3. **Remediation:** Reset passwords for affected accounts.
4. **Detection:** Look for Event ID 4625 (Windows) or 'Failed password' (Linux).""",

    # PHASE 3: EXECUTION (The attacker got in and is running commands)
    "T1059": """### MITRE T1059: Command and Scripting Interpreter
**Description:** Adversaries may abuse command and script interpreters to execute commands, scripts, or binaries.

**Mitigation / Playbook:**
1. **Monitor:** Enable auditd or PowerShell logging to capture command history.
2. **Restrict:** Use AppLocker or sudo restrictions to limit what commands users can run.
3. **Investigate:** Look for suspicious usage of curl, wget, or encoded PowerShell strings.""",

    # PHASE 4: PERSISTENCE (The attacker creates a backdoor)
    "T1098": """### MITRE T1098: Account Manipulation
**Description:** Adversaries may manipulate accounts to maintain access to victim systems (e.g., adding a new SSH key).

**Mitigation / Playbook:**
1. **Verify:** Audit ~/.ssh/authorized_keys for unknown entries.
2. **Revoke:** Remove unauthorized keys and force password rotation.
3. **Alert:** Configure Wazuh to alert on file changes in /etc/passwd or /home/*/.ssh/.""",
    
    # PHASE 5: IMPACT (Denial of Service - Your T1190 or T1498)
    "T1190": """### MITRE T1190: Exploit Public-Facing Application
**Description:** Adversaries may attempt to take advantage of a weakness in an Internet-facing computer or program.

**Mitigation / Playbook:**
1. **Analysis:** Check WAF logs for SQLi or XSS patterns.
2. **Patching:** Ensure the application is updated to the latest version.
3. **Isolation:** If confirmed, move the web server to a quarantine VLAN."""
}

@mcp.tool()
def get_playbook(technique_id: str) -> str:
    """
    Retrieves the SOC Playbook and mitigation strategies for a specific MITRE Technique ID.
    This returns hardcoded playbooks with step-by-step response procedures.
    Example Input: "T1110"
    """
    # Look up the ID in our local dictionary
    info = KNOWLEDGE_BASE.get(technique_id)
    
    if info:
        return info
    else:
        return f"No specific playbook found for technique ID: {technique_id}. Suggest manual investigation on attack.mitre.org."

@mcp.tool()
def get_mitre_technique(technique_id: str) -> str:
    """
    Retrieves official MITRE ATT&CK data for a specific technique ID.
    This downloads real data from the MITRE ATT&CK repository.
    Example Input: "T1110"
    """
    technique = get_technique_from_mitre(technique_id)
    
    if technique:
        output = f"""### MITRE {technique['id']}: {technique['name']}

**Description:** {technique['description']}

**Tactics:** {', '.join(technique['tactics'])}

**Platforms:** {', '.join(technique['platforms'])}

**Reference:** {technique['url']}
"""
        return output
    else:
        return f"Technique {technique_id} not found in MITRE ATT&CK database. Please verify the ID is correct."

@mcp.tool()
def get_combined_intel(technique_id: str) -> str:
    """
    Retrieves both official MITRE ATT&CK data AND the custom SOC playbook.
    This combines real threat intelligence with actionable response procedures.
    Example Input: "T1110"
    """
    # Get official MITRE data
    mitre_data = get_mitre_technique(technique_id)
    
    # Get custom playbook
    playbook = KNOWLEDGE_BASE.get(technique_id)
    
    if playbook:
        # Remove leading/trailing whitespace from playbook
        playbook_clean = playbook.strip()
        return f"{mitre_data}\n\n---\n\n{playbook_clean}"
    else:
        return f"{mitre_data}\n\n---\n\n*No custom playbook available for this technique*"

@mcp.tool()
def refresh_mitre_data() -> str:
    """
    Forces a refresh of the MITRE ATT&CK database from the official repository.
    Use this to get the latest threat intelligence updates.
    """
    # Delete cache file if it exists
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    
    # Download fresh data
    data = download_mitre_data()
    
    if data:
        num_techniques = sum(1 for obj in data.get('objects', []) if obj.get('type') == 'attack-pattern')
        return f"Successfully refreshed MITRE ATT&CK data. Loaded {num_techniques} techniques."
    else:
        return "Failed to refresh MITRE data. Check your internet connection."

if __name__ == "__main__":
    mcp.run()