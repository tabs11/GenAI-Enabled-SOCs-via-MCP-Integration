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
        global MITRE_CACHE
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
# TIER 1: LOCAL PLAYBOOKS (Loaded from Config)
# =============================================================================

PLAYBOOKS_FILE = "config/playbooks.json"

def load_playbooks() -> Dict[str, str]:
    """Loads the custom playbooks from the JSON config file."""
    try:
        with open(PLAYBOOKS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        sys.stderr.write(f"[MITRE SERVER] Warning: Could not load playbooks from {PLAYBOOKS_FILE}: {e}\n")
        return {}

KNOWLEDGE_BASE = load_playbooks()

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
def get_tier2_mitre_data(technique_id: str) -> str:
    """
    TIER 2: Official MITRE Data (Full Intelligence)
    
    Retrieves comprehensive details from the official MITRE ATT&CK database.
    Includes description, tactics, platforms, data sources, and references.
    Use this if Tier 1 (playbook) lacks information.
    
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
    HYBRID: Full Context (Tier 1 Playbook + Tier 2 MITRE Data)
    
    Combines custom SOC playbooks with comprehensive MITRE ATT&CK intelligence.
    Provides both actionable response procedures and detailed threat context.
    Recommended for complete incident analysis.
    
    Example Input: "T1110"
    """
    # Get Tier 2 (MITRE Data)
    mitre_data = get_tier2_mitre_data(technique_id)
    
    # Get Tier 1 (Playbook)
    playbook = KNOWLEDGE_BASE.get(technique_id)
    
    if playbook:
        return f"{mitre_data}\n\n---\n\n## 🔧 CUSTOM SOC PLAYBOOK\n\n{playbook}"
    else:
        return f"{mitre_data}\n\n---\n\n*No custom playbook available for this technique. Consider creating one based on your organization's procedures.*"

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