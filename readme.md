# 🛡️ Wazuh AI Analyst – GenAI-Enabled SOC via MCP Integration

**Master's Thesis Prototype**  
**Student:** Nuno Martins  
**Supervisor:** Professor Nuno Lopes / Rui Fernandes  
**Institution:** Escola Superior de Tecnologia

---

## 🎯 Project Overview

This project demonstrates an intelligent SOC assistant that integrates a SIEM (Wazuh) and MITRE ATT&CK knowledge base with a Large Language Model (Llama 3.2) using the **Model Context Protocol (MCP)**. The system automates alert triage and provides context-aware mitigation advice, reducing analyst fatigue and grounding AI responses in official security frameworks.

### ✨ Key Features

- **Multi-Server MCP Orchestration:**  
  The Streamlit client (`app.py`) connects to two MCP servers:
  - `wazuh_server.py`: Retrieves security alerts from mock Wazuh data
  - `mitre_server.py`: Provides MITRE ATT&CK intelligence with three modes:
    - **Custom Playbooks:** Hardcoded SOC response procedures
    - **Official MITRE Data:** Live threat intelligence from MITRE ATT&CK repository
    - **Combined Mode:** Both custom playbooks and official data together

- **Real-Time MITRE ATT&CK Integration:**  
  Downloads and caches official MITRE ATT&CK data from the MITRE CTI repository, providing up-to-date threat intelligence with automatic 24-hour refresh.

- **Retrieval-Augmented Generation (RAG):**  
  Alerts are cross-referenced with MITRE mitigations before being sent to the LLM, ensuring responses are contextually accurate and actionable.

- **Attack Scenario Simulator:**  
  Inject different attack scenarios (SSH Brute Force, Network Scanning, Command Execution) to test the system's response capabilities.

- **Dockerized Deployment:**  
  Complete containerization with Docker Compose for easy deployment and consistent environments.

- **Modular & Extensible:**  
  Easily add new tools, data sources, or attack scenarios via MCP protocol.

---

## 🏗️ Architecture

```mermaid
graph TD
    User[SOC Analyst] -->|Interacts| Client[Streamlit Client / MCP Host]
    Client <-->|MCP Protocol| Wazuh["Wazuh MCP Server"]
    Client <-->|MCP Protocol| MITRE["MITRE MCP Server"]
    Wazuh <-->|Reads| Alerts[alert.json / Scenarios]
    MITRE <-->|Queries| KB[MITRE ATT&CK Knowledge Base]
    Client <-->|Prompt + Context| LLM["Llama 3.2 via Ollama"]
    
    subgraph Docker Environment
        Client
        LLM
        Wazuh
        MITRE
    end
```

---

## 🚀 Getting Started

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker & Docker Compose installed
- At least 8GB RAM available

#### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tabs11/GenAI-Enabled-SOCs-via-MCP-Integration.git
   cd GenAI-Enabled-SOCs-via-MCP-Integration
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Pull the Llama 3.2 model:**
   ```bash
   docker exec -it ollama-service ollama pull llama3.2
   ```

4. **Access the application:**
   - Open browser: http://localhost:8501
   - Optional: Vulnerable target at http://localhost:8080

5. **Stop all services:**
   ```bash
   docker-compose down
   ```

### Option 2: Local Installation

#### Prerequisites
- Python 3.10+
- Ollama installed locally

#### Installation Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install and configure Ollama:**
   ```bash
   # Download from https://ollama.com/
   ollama pull llama3.2
   ```

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

The application will:
- Automatically launch `wazuh_server.py` and `mitre_server.py` MCP servers
- Connect to both servers via the MCP protocol
- Present a dashboard with live alerts and an AI chat interface

---

## 📂 Project Structure

```
GenAI-Enabled-SOCs-via-MCP-Integration/
├── app.py                    # Main Streamlit application (MCP client)
├── wazuh_server.py          # MCP server for Wazuh alerts
├── mitre_server.py          # MCP server for MITRE ATT&CK knowledge
├── test_connection.py       # MCP connection testing utility
├── alert.json               # Current active alert
├── alert_Orig.json          # Original alert backup
├── mcp_config.json          # MCP configuration file
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── docker-compose.yml       # Multi-container orchestration
├── .gitignore              # Git ignore rules
├── .dockerignore           # Docker ignore rules (optional)
├── scenarios/              # Attack scenario templates
│   ├── alert_brute.json    # SSH Brute Force (T1110)
│   ├── alert_scan.json     # Network Scanning (T1595)
│   └── alert_exec.json     # Command Execution (T1059)
└── readme.md               # This file
```

---

## 🎮 Using Attack Scenarios

The Lab Controller in the sidebar allows you to inject different attack scenarios:

1. **SSH Brute Force (T1110):**  
   Simulates multiple failed authentication attempts from a single IP

2. **Network Scanning (T1595):**  
   Simulates reconnaissance activity with port scanning

3. **Command Execution (T1059):**  
   Simulates suspicious command execution after initial access

Click "Trigger Alert" to load the scenario and see how the AI analyst responds.

---

## 🎯 MITRE Intelligence Modes

The system offers three intelligence sources that can be selected from the sidebar:

### 📋 Custom Playbooks (Hardcoded)
- Step-by-step SOC response procedures
- Tailored for your organization's specific environment
- Includes actionable mitigation steps
- Example: T1110 playbook with auth.log checks and IP blocking

### 🌐 Official MITRE Data (Live)
- Downloads real-time data from [MITRE CTI Repository](https://github.com/mitre/cti)
- Provides official technique descriptions, tactics, and platforms
- Auto-cached for 24 hours to reduce API calls
- Includes direct links to MITRE ATT&CK website

### 🔄 Combined Mode (Recommended)
- Merges official MITRE intelligence with custom playbooks
- Gives analysts both threat context and actionable response steps
- Best for comprehensive incident analysis

---

## 🧠 How It Works

### Data Flow

1. **Alert Retrieval:** The client calls `wazuh_server.py` via MCP to fetch the latest security alert
2. **Context Enhancement:** The MITRE technique ID (e.g., T1110) is extracted from the alert
3. **Knowledge Retrieval:** The client calls `mitre_server.py` using the selected intelligence mode:
   - `get_playbook()` - Retrieves custom SOC playbooks
   - `get_mitre_technique()` - Downloads official MITRE ATT&CK data
   - `get_combined_intel()` - Merges both sources
4. **AI Analysis:** Both the alert and MITRE context are sent to Llama 3.2 via Ollama
5. **Interactive Response:** The SOC analyst can ask questions, and the AI responds with grounded, context-aware advice

### RAG Pipeline

The system implements Retrieval-Augmented Generation (RAG) by:
- **Retrieving** relevant security data from multiple sources (Wazuh alerts + MITRE intelligence)
- **Augmenting** the LLM prompt with this external context
- **Generating** responses that are factually grounded in official security frameworks

This approach reduces hallucinations and ensures recommendations are actionable and compliant with industry best practices.

### MITRE ATT&CK Data Management

The `mitre_server.py` automatically handles MITRE ATT&CK data:
- **Download:** Fetches STIX 2.0 JSON from the official MITRE CTI GitHub repository
- **Cache:** Stores data locally in `mitre_attack_data.json` for 24 hours
- **Parse:** Extracts technique details including descriptions, tactics, platforms, and references
- **Refresh:** Can be manually triggered using the `refresh_mitre_data()` tool

---

## 🔧 Technical Details

### MCP Server Configuration

Both servers are launched as `StdioServerParameters` in `app.py`:

```python
wazuh_server = StdioServerParameters(
    command=sys.executable, 
    args=["wazuh_server.py"]
)

mitre_server = StdioServerParameters(
    command=sys.executable, 
    args=["mitre_server.py"]
)
```

### MITRE Server Tools

The `mitre_server.py` exposes four MCP tools:

1. **`get_playbook(technique_id)`** - Retrieves custom SOC playbooks
2. **`get_mitre_technique(technique_id)`** - Fetches official MITRE ATT&CK data  
3. **`get_combined_intel(technique_id)`** - Returns both playbook and official data
4. **`refresh_mitre_data()`** - Forces download of latest MITRE data

### Docker Services

- **soc-assistant:** Streamlit app with MCP client orchestration
- **ollama:** Local LLM runtime (Llama 3.2)
- **victim-machine:** Optional vulnerable web app for demonstration (DVWA)

### Environment Variables

- `OLLAMA_HOST`: URL of Ollama service (default: `http://ollama:11434` in Docker)

### Adding New Attack Scenarios

Create a new JSON file in the `scenarios/` folder following this structure:

```json
{
  "rule": {
    "level": 10,
    "description": "Your attack description",
    "mitre": {
      "id": ["T1234"],
      "tactic": ["Tactic Name"],
      "technique": ["Technique Name"]
    }
  },
  "data": {
    "srcip": "192.168.1.100"
  }
}
```

---

## 🔧 Technical Details

### MCP Server Configuration

Both servers are launched as `StdioServerParameters` in `app.py`:

```python
wazuh_server = StdioServerParameters(
    command=sys.executable, 
    args=["wazuh_server.py"]
)

mitre_server = StdioServerParameters(
    command=sys.executable, 
    args=["mitre_server.py"]
)
```

### Docker Services

- **soc-assistant:** Streamlit app with MCP client orchestration
- **ollama:** Local LLM runtime (Llama 3.2)
- **victim-machine:** Optional vulnerable web app for demonstration (DVWA)

### Environment Variables

- `OLLAMA_HOST`: URL of Ollama service (default: `http://ollama:11434` in Docker)

### Adding New Attack Scenarios

Create a new JSON file in the `scenarios/` folder following this structure:

```json
{
  "rule": {
    "level": 10,
    "description": "Your attack description",
    "mitre": {
      "id": ["T1234"],
      "tactic": ["Tactic Name"],
      "technique": ["Technique Name"]
    }
  },
  "data": {
    "srcip": "192.168.1.100"
  }
}
```

### Extending the MITRE Knowledge Base

Edit `mitre_server.py` and add new entries to the `KNOWLEDGE_BASE` dictionary:

```python
KNOWLEDGE_BASE = {
    "T1234": """
    ### MITRE T1234: Your Technique
    **Description:** Technique description
    **Mitigation / Playbook:**
    1. Step one
    2. Step two
    """
}
```

---

## 🎯 Use Cases

- **Alert Triage:** Automatically explain security alerts in plain language with MITRE context
- **Incident Investigation:** Ask "What should I check next?" and get MITRE-based guidance
- **Playbook Assistance:** Retrieve step-by-step mitigation procedures for detected techniques
- **Training & Education:** Help junior analysts understand attack patterns and response strategies
- **Threat Hunting:** Explore different attack scenarios and their defensive measures

---

## 🐛 Troubleshooting

### Docker Issues

**Problem:** Containers fail to start  
**Solution:** Check Docker logs: `docker-compose logs`

**Problem:** Ollama model not found  
**Solution:** Pull the model manually:
```bash
docker exec -it ollama-service ollama pull llama3.2
```

**Problem:** Port already in use (8501)  
**Solution:** Stop conflicting services or change port in `docker-compose.yml`

### Local Installation Issues

**Problem:** MCP servers fail to connect  
**Solution:** Ensure Python path is correct and servers have execute permissions

**Problem:** Ollama connection failed  
**Solution:** Verify Ollama is running: `ollama list`

---

## 📊 Performance Considerations

- **Memory:** Llama 3.2 requires ~8GB RAM
- **Storage:** Model files ~4GB
- **Network:** Local deployment (no internet required after initial setup)

---

## 🔒 Security Notes

- This is a **prototype for educational purposes**
- The DVWA vulnerable target should **never be exposed to the internet**
- Use in isolated lab environments only
- Mock data is used instead of real security alerts

---

## 📖 References & Resources

- **[Wazuh SIEM](https://wazuh.com/)** – Open-source security monitoring and threat detection platform
- **[MITRE ATT&CK](https://attack.mitre.org/)** – Globally-accessible knowledge base of adversary tactics and techniques
- **[Ollama](https://ollama.com/)** – Run large language models locally
- **[Model Context Protocol (MCP)](https://modelcontext.github.io/)** – Open protocol for LLM-tool integration
- **[Streamlit](https://streamlit.io/)** – Python framework for building data applications
- **[FastMCP](https://github.com/jlowin/fastmcp)** – Pythonic framework for building MCP servers
- **[Docker](https://www.docker.com/)** – Containerization platform

---

## 🚧 Future Enhancements

- [ ] Real-time Wazuh API integration
- [ ] Multiple LLM model comparison (Mistral, Gemma, etc.)
- [ ] Advanced RAG with vector embeddings
- [ ] Alert correlation across multiple events
- [ ] Export incident reports to PDF/JSON
- [ ] Multi-language support
- [ ] Integration with ticketing systems (Jira, ServiceNow)

---

## 📝 License

This project is developed as part of a Master's thesis at Escola Superior de Tecnologia.  
For academic and educational use only.

---

## 👤 Author

**Nuno Martins**  
Master's in Artificial Intelligence  
Escola Superior de Tecnologia  

**Thesis Supervisors:**  
- Professor Nuno Lopes  
- Professor Rui Fernandes

---

## 🙏 Acknowledgments

Special thanks to the professors and the institution for supporting this research in applying GenAI to cybersecurity operations.

---

**For questions or collaboration opportunities, please contact via institutional channels.**