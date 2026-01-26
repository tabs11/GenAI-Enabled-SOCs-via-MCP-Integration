# mitre_server.py
from mcp.server.fastmcp import FastMCP
import requests
import json
import sys
from typing import Optional, Dict, Any

# Define MCP server for Threat Intel
mcp = FastMCP("MITRE-Knowledge-Base")

# MITRE ATT&CK STIX data URL (Official MITRE STIX repository)
MITRE_ATTACK_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"

# Global in-memory cache for MITRE data
MITRE_CACHE: Optional[Dict[str, Any]] = None

def download_and_cache_mitre_data() -> bool:
    """
    Downloads the official MITRE ATT&CK STIX JSON on server startup.
    Caches the data in memory for fast access.
    Returns True if successful, False otherwise.
    """
    global MITRE_CACHE
    
    sys.stderr.write("[MITRE SERVER] Downloading MITRE ATT&CK STIX data...\n")
    
    try:
        response = requests.get(MITRE_ATTACK_URL, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        # Build a fast lookup dictionary: technique_id -> technique_object
        MITRE_CACHE = {}
        
        for obj in data.get('objects', []):
            if obj.get('type') == 'attack-pattern':
                # Extract the technique ID (e.g., T1110)
                external_refs = obj.get('external_references', [])
                for ref in external_refs:
                    if ref.get('source_name') == 'mitre-attack':
                        technique_id = ref.get('external_id')
                        if technique_id:
                            MITRE_CACHE[technique_id] = {
                                'id': technique_id,
                                'name': obj.get('name', 'Unknown'),
                                'description': obj.get('description', 'No description available'),
                                'url': ref.get('url', ''),
                                'tactics': [phase['phase_name'] for phase in obj.get('kill_chain_phases', [])],
                                'platforms': obj.get('x_mitre_platforms', []),
                                'data_sources': obj.get('x_mitre_data_sources', [])
                            }
                        break
        
        sys.stderr.write(f"[MITRE SERVER] Successfully loaded {len(MITRE_CACHE)} techniques into memory.\n")
        return True
        
    except Exception as e:
        sys.stderr.write(f"[MITRE SERVER] Failed to download MITRE data: {str(e)}\n")
        MITRE_CACHE = {}
        return False

def get_technique_from_cache(technique_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve technique data from in-memory cache."""
    if MITRE_CACHE is None:
        return None
    return MITRE_CACHE.get(technique_id)

# =============================================================================
# TIER 1: LOCAL PLAYBOOKS (Hardcoded SOC Response Procedures)
# =============================================================================

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

# =============================================================================
# MCP TOOLS - 3-TIER ARCHITECTURE
# =============================================================================

@mcp.tool()
def get_playbook(technique_id: str) -> str:
    """
    TIER 1: Local Playbook (Hardcoded SOC Response Procedures)
    
    Retrieves custom SOC playbooks with step-by-step mitigation procedures.
    These are organization-specific response procedures maintained locally.
    
    Example Input: "T1110"
    """
    playbook = KNOWLEDGE_BASE.get(technique_id)
    
    if playbook:
        return playbook
    else:
        return f"❌ No custom playbook found for technique ID: {technique_id}.\n\nSuggestion: Create a playbook or use Tier 2/3 for official MITRE data."

@mcp.tool()
def get_summary(technique_id: str) -> str:
    """
    TIER 2: Official MITRE Summary (Description + Tactics)
    
    Retrieves a concise summary from the official MITRE ATT&CK database.
    Includes the official description and associated tactics (kill chain phases).
    
    Example Input: "T1110"
    """
    technique = get_technique_from_cache(technique_id)
    
    if not technique:
        return f"❌ Technique {technique_id} not found in MITRE ATT&CK database.\n\nEnsure the server has downloaded the MITRE data successfully."
    
    output = f"""### {technique['id']}: {technique['name']}

**Description:** {technique['description']}

**Tactics:** {', '.join(technique['tactics']) if technique['tactics'] else 'None specified'}

**Reference:** {technique['url']}
"""
    return output

@mcp.tool()
def get_deep_analysis(technique_id: str) -> str:
    """
    TIER 3: Deep Dive Analysis (Full MITRE Intelligence)
    
    Retrieves comprehensive details from the official MITRE ATT&CK database.
    Includes description, tactics, platforms, data sources, and references.
    Use this for in-depth incident investigation.
    
    Example Input: "T1110"
    """
    technique = get_technique_from_cache(technique_id)
    
    if not technique:
        return f"❌ Technique {technique_id} not found in MITRE ATT&CK database.\n\nEnsure the server has downloaded the MITRE data successfully."
    
    output = f"""### {technique['id']}: {technique['name']}

**Description:** {technique['description']}

**Tactics (Kill Chain Phases):** {', '.join(technique['tactics']) if technique['tactics'] else 'None specified'}

**Platforms:** {', '.join(technique['platforms']) if technique['platforms'] else 'None specified'}

**Data Sources:** {', '.join(technique['data_sources']) if technique['data_sources'] else 'None specified'}

**Official Reference:** {technique['url']}

---

*This data is sourced from the official MITRE ATT&CK STIX repository.*
"""
    return output

@mcp.tool()
def get_full_context(technique_id: str) -> str:
    """
    HYBRID: Full Context (Tier 1 Playbook + Tier 3 Deep Analysis)
    
    Combines custom SOC playbooks with comprehensive MITRE ATT&CK intelligence.
    Provides both actionable response procedures and detailed threat context.
    Recommended for complete incident analysis.
    
    Example Input: "T1110"
    """
    # Get Tier 3 (Deep Analysis)
    deep_analysis = get_deep_analysis(technique_id)
    
    # Get Tier 1 (Playbook)
    playbook = KNOWLEDGE_BASE.get(technique_id)
    
    if playbook:
        return f"{deep_analysis}\n\n---\n\n## 🔧 CUSTOM SOC PLAYBOOK\n\n{playbook}"
    else:
        return f"{deep_analysis}\n\n---\n\n*No custom playbook available for this technique. Consider creating one based on your organization's procedures.*"

@mcp.tool()
def refresh_mitre_data() -> str:
    """
    Forces a refresh of the MITRE ATT&CK database from the official repository.
    Use this to get the latest threat intelligence updates.
    """
    success = download_and_cache_mitre_data()
    
    if success and MITRE_CACHE:
        return f"✅ Successfully refreshed MITRE ATT&CK data. Loaded {len(MITRE_CACHE)} techniques into memory."
    else:
        return "❌ Failed to refresh MITRE data. Check your internet connection and server logs."

# =============================================================================
# SERVER INITIALIZATION
# =============================================================================

# Download MITRE data on server startup
sys.stderr.write("[MITRE SERVER] Initializing...\n")
download_and_cache_mitre_data()
sys.stderr.write("[MITRE SERVER] Ready to serve requests.\n")

if __name__ == "__main__":
    mcp.run()