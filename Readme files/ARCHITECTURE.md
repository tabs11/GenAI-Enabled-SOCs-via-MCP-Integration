# 📐 Wazuh Stack Architecture Diagram

## Complete System Architecture

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                                    HOST MACHINE                                    │
│                                   (Your Windows)                                   │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                    │
│  Browser                    Browser                    Terminal                   │
│  http://localhost:8501      https://localhost:443      ssh localhost:2222        │
│       │                            │                           │                  │
│       ▼                            ▼                           ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐     │
│  │                     Docker Network: soc_network (172.20.0.0/16)         │     │
│  │                                                                          │     │
│  │  ┌────────────────────┐        ┌────────────────────┐                   │     │
│  │  │  soc-assistant     │        │   ollama-service   │                   │     │
│  │  │   (Streamlit)      │◄──────►│    (Llama 3.2)     │                   │     │
│  │  │    :8501           │        │     :11434         │                   │     │
│  │  └──────┬─────────────┘        └────────────────────┘                   │     │
│  │         │                                                                │     │
│  │         │ MCP Protocol (stdio)                                           │     │
│  │         │                                                                │     │
│  │  ┌──────▼─────────────────────────────────────────────────────────┐     │     │
│  │  │            MCP Servers (Python subprocesses)                   │     │     │
│  │  │  ┌──────────────────┐     ┌─────────────────────────────┐     │     │     │
│  │  │  │ wazuh_server.py  │     │    mitre_server.py          │     │     │     │
│  │  │  │ • get_alerts     │     │ • get_playbook (Tier 1)     │     │     │     │
│  │  │  │ • get_real_alerts│     │ • get_summary (Tier 2)      │     │     │     │
│  │  │  │ • get_agents     │     │ • get_deep_analysis (Tier 3)│     │     │     │
│  │  │  └────────┬─────────┘     └─────────────────────────────┘     │     │     │
│  │  └───────────┼────────────────────────────────────────────────────┘     │     │
│  │              │                                                            │     │
│  │              │ HTTPS API (Port 55000)                                    │     │
│  │              │                                                            │     │
│  │  ┌───────────▼────────────────────────────────────────────────────┐     │     │
│  │  │                     wazuh-manager                              │     │     │
│  │  │                    (SIEM Core Engine)                          │     │     │
│  │  │  • REST API (:55000)                                           │     │     │
│  │  │  • Agent Management (:1514, :1515)                             │     │     │
│  │  │  • Alert Processing & Correlation                              │     │     │
│  │  │  • Rule Engine                                                 │     │     │
│  │  └───┬─────────────────────────────────────────────┬──────────────┘     │     │
│  │      │ Filebeat                                    │ Agent Logs         │     │
│  │      │                                             │ (:1514 syslog)     │     │
│  │      │                                             │                    │     │
│  │      ▼                                             ▼                    │     │
│  │  ┌───────────────────────┐              ┌─────────────────────────┐    │     │
│  │  │  wazuh-indexer        │              │  metasploitable-target  │    │     │
│  │  │  (Elasticsearch)      │              │   (Vulnerable VM)       │    │     │
│  │  │  • Log Storage        │              │  • SSH :22 → :2222      │    │     │
│  │  │  • Search & Query     │              │  • HTTP :80 → :8080     │    │     │
│  │  │  :9200                │              │  • FTP :21              │    │     │
│  │  └───────────┬───────────┘              │  • Telnet :23           │    │     │
│  │              │                          │  [Wazuh Agent Installed]│    │     │
│  │              │ Query                    └─────────────────────────┘    │     │
│  │              │                                                          │     │
│  │              ▼                                                          │     │
│  │  ┌───────────────────────┐                                             │     │
│  │  │  wazuh-dashboard      │                                             │     │
│  │  │   (Web UI)            │                                             │     │
│  │  │   :5601 → :443        │                                             │     │
│  │  │  • Visualization      │                                             │     │
│  │  │  • Agent Management   │                                             │     │
│  │  │  • Security Events    │                                             │     │
│  │  └───────────────────────┘                                             │     │
│  │                                                                          │     │
│  └──────────────────────────────────────────────────────────────────────────┘     │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

### Alert Processing Flow

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                            ALERT LIFECYCLE                                     │
└───────────────────────────────────────────────────────────────────────────────┘

1. Attack Occurs
   ↓
   metasploitable-target
   (SSH failed login, port scan, etc.)
   ↓
2. Wazuh Agent Detects Event
   ↓
   /var/log/auth.log → Wazuh Agent
   ↓
3. Agent Sends to Manager
   ↓
   TCP 1514 → wazuh-manager
   ↓
4. Manager Processes Alert
   ↓
   Rule Engine → Alert Generation
   ↓
5. Store in Indexer
   ↓
   Filebeat → wazuh-indexer (Elasticsearch)
   ↓
6. Multiple Consumers
   ├─► wazuh-dashboard (Human Analyst)
   │   └─► https://localhost:443
   │
   └─► wazuh_server.py (AI Analyst)
       └─► MCP Tool: get_real_wazuh_alerts()
           ├─► Fetch via REST API (:55000)
           ├─► Cross-reference with MITRE (mitre_server.py)
           └─► Send to LLM (Llama 3.2 via Ollama)
               └─► Generate contextual analysis
                   └─► Display in Streamlit UI
```

## MCP Communication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCP CLIENT-SERVER ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────────┘

Streamlit App (MCP Host/Client)
│
├─► Launch MCP Servers via stdio
│   ├─► python wazuh_server.py
│   └─► python mitre_server.py
│
├─► Connect via ClientSession
│   ├─► stdio_client(wazuh_server)
│   └─► stdio_client(mitre_server)
│
├─► Call Tools via MCP Protocol
│   │
│   ├─► wazuh_session.call_tool("get_latest_alerts")
│   │   └─► Returns: JSON array of alerts
│   │
│   ├─► wazuh_session.call_tool("get_real_wazuh_alerts", {"limit": 10})
│   │   └─► Returns: Live alerts from Wazuh API
│   │
│   ├─► wazuh_session.call_tool("get_wazuh_agents")
│   │   └─► Returns: List of registered agents
│   │
│   └─► mitre_session.call_tool("get_full_context", {"technique_id": "T1110"})
│       └─► Returns: Playbook + Deep MITRE intelligence
│
└─► Combine Context + Send to LLM
    └─► ollama.chat(model="llama3.2", messages=[...])
        └─► AI-generated response with MITRE grounding
```

## Network Ports Summary

| Service | Container Port | Host Port | Protocol | Purpose |
|---------|----------------|-----------|----------|---------|
| Streamlit App | 8501 | 8501 | HTTP | Web UI for SOC Analyst |
| Wazuh Dashboard | 5601 | 443 | HTTPS | Wazuh Web UI |
| Wazuh API | 55000 | 55000 | HTTPS | REST API for automation |
| Wazuh Agent Port | 1514 | - | TCP | Agent log collection |
| Wazuh Enrollment | 1515 | - | TCP | Agent registration |
| Wazuh Indexer | 9200 | 9200 | HTTP | Elasticsearch API |
| Ollama | 11434 | 11434 | HTTP | LLM inference |
| Metasploitable SSH | 22 | 2222 | SSH | Vulnerable target |
| Metasploitable HTTP | 80 | 8080 | HTTP | Vulnerable web server |
| Metasploitable FTP | 21 | 21 | FTP | Vulnerable FTP |
| Metasploitable Telnet | 23 | 23 | Telnet | Vulnerable Telnet |

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                         SECURITY ZONES                       │
└─────────────────────────────────────────────────────────────┘

Internet
   ↕ (CLOSED - Lab Environment Only)
───────────────────────────────────────────
Host Machine (Windows)
   │
   ├─► Port Forwarding (Controlled)
   │   ├─► 8501 → soc-assistant
   │   ├─► 443 → wazuh-dashboard
   │   └─► 2222 → metasploitable (SSH)
   │
   └─► Docker Internal Network (172.20.0.0/16)
       │
       ├─► SOC Services (Trusted)
       │   ├─► soc-assistant
       │   ├─► ollama-service
       │   ├─► wazuh-manager
       │   ├─► wazuh-indexer
       │   └─► wazuh-dashboard
       │
       └─► Victim Services (Isolated)
           └─► metasploitable-target
               • Monitored by Wazuh Agent
               • Intentionally vulnerable
               • Never exposed to internet
```

## Volume Persistence

```
Docker Volumes (Data Persistence)
├─► ollama_data
│   └─► /root/.ollama (Model files ~4GB)
│
├─► wazuh_indexer_data
│   └─► /var/lib/wazuh-indexer (Security events)
│
├─► wazuh_logs
│   └─► /var/ossec/logs (Manager logs)
│
├─► wazuh_etc
│   └─► /var/ossec/etc (Configuration)
│
└─► wazuh_dashboard_config
    └─► /usr/share/wazuh-dashboard/data (Dashboard settings)
```

---

## Key Integration Points

1. **App ↔ Wazuh:** HTTP REST API on port 55000
2. **App ↔ Ollama:** HTTP on port 11434
3. **App ↔ MCP Servers:** stdio (stdin/stdout pipes)
4. **Wazuh Manager ↔ Indexer:** Filebeat (port 9200)
5. **Wazuh Manager ↔ Agents:** Syslog (port 1514)
6. **Dashboard ↔ Indexer:** Elasticsearch Query API
7. **Dashboard ↔ Manager:** Wazuh API (port 55000)

---

**This architecture enables:**
- ✅ Real-time security monitoring
- ✅ AI-powered alert analysis
- ✅ MITRE ATT&CK knowledge integration
- ✅ Isolated lab environment for safe testing
- ✅ Complete observability via logs and dashboards
