# 🛡️ GenAI-Enabled SOC via MCP Integration - Presentation Guide

## Presentation Structure (5-6 Slides)

---

## **SLIDE 1: Title & Overview**
**Title:** GenAI-Enabled Security Operations Center via Model Context Protocol

**Content:**
- Subtitle: Intelligent Threat Analysis with Multi-Agent Architecture
- Your Name & Institution: Mestrado IA - 2º Ano
- Date: February 2026

**Visual Elements:**
- Simple architecture diagram or system logo
- Tagline: "Bridging SIEM alerts with AI-powered threat intelligence"

---

## **SLIDE 2: The Problem & Solution**

**Problem Statement:**
- SOC analysts overwhelmed by alert fatigue
- Manual correlation between SIEM alerts and threat intelligence is time-consuming
- Need for contextualized, actionable responses

**Our Solution:**
- MCP-based multi-agent architecture
- Automated integration: Wazuh (SIEM) ↔ MITRE ATT&CK (Intel) ↔ LLM (Analysis)
- Real-time conversational interface for threat investigation

**Screenshot to Capture:**
- Architecture diagram (you can create a simple one or show the system components)
- OR: A split view of the dashboard showing both alert feed and chat interface

---

## **SLIDE 3: System Architecture**

**Key Components:**
1. **Wazuh MCP Server** - Alert ingestion and SIEM data retrieval
2. **MITRE MCP Server** - Threat intelligence with 3-tier knowledge system
3. **Streamlit Client** - Orchestration and UI
4. **Ollama LLM** - Natural language analysis and recommendations

**3-Tier Intelligence System:**
- Tier 1: Custom SOC Playbooks (hardcoded procedures)
- Tier 2: MITRE Summary (description + tactics)
- Tier 3: Deep Analysis (platforms, data sources, kill chain)
- Hybrid: Combined context for complete analysis

**Deployment Architecture:**
- 🐳 **Containerized with Docker Compose** - Production-ready deployment
- **3 Services:** SOC Assistant + Ollama (LLM) + Metasploitable (Test Target)
- Optional: Simple diagram showing Docker Compose architecture (3 containers)

**How to capture:** 
```
1. Run the app: streamlit run app.py
   OR using Docker: docker-compose up
2. Focus on the left sidebar showing configuration options
3. Capture the entire sidebar including model selection and intelligence tiers
```

**Talking Point for Docker:**
> "The system is deployed using Docker Compose, which orchestrates three services: our SOC application, the Ollama LLM engine, and a Metasploitable target for testing. This ensures consistent deployment across any environment and demonstrates production-ready architecture."
**How to capture:** 
```
1. Run the app: streamlit run app.py
2. Focus on the left sidebar showing configuration options
3. Capture the entire sidebar including model selection and intelligence tiers
```

---

## **SLIDE 4: Live Demo - Attack Scenario Injection**

**Demonstration Features:**
- Lab Controller for attack scenario simulation
- Three pre-configured attack vectors:
  - 🔒 SSH Brute Force (T1110)
  - 📡 Network Scanning (T1595)
  - 💻 Command Execution (T1059)

**Screenshot to Capture:**
1. **Before injection** - Sidebar showing scenario selector
2. **After injection** - Alert feed showing triggered alert with MITRE context

**How to capture:**
```
1. In the sidebar "Lab Controller" section
2. Select "SSH Brute Force" scenario
3. Click "Trigger Alert" button
4. Capture the success message and the updated dashboard
5. Show the "Retrieved Context (From MITRE Server)" expanded section
```

**Key Points to Highlight:**
- Dynamic scenario switching
- Automatic MITRE intelligence retrieval
- Real-time context enrichment

---

## **SLIDE 5: AI-Powered Analysis in Action**

**Interactive Capabilities:**
- Natural language queries about security alerts
- Context-aware responses using:
  - Alert metadata (source IP, rule details, severity)
  - MITRE ATT&CK intelligence
  - Historical conversation context

**Example Queries to Demonstrate:**
1. "What is this attack and how serious is it?"
2. "What should I do first to contain this threat?"
3. "Show me the mitigation steps for this technique"
4. "Is this a reconnaissance or an active attack?"

**Screenshot to Capture:**
- Chat interface showing a multi-turn conversation
- Example: User question + LLM response with detailed analysis
- Show the chat history with 2-3 exchanges

**How to capture:**
```
1. After triggering an alert, go to the chat interface (right column)
2. Ask: "What is this attack and what should I do?"
3. Wait for the LLM response
4. Ask a follow-up: "What are the specific mitigation steps?"
5. Capture the entire conversation thread
6. Make sure the response shows actionable recommendations
```

---

## **SLIDE 6: Results & Future Work**

**Key Achievements:**
✅ Production-ready containerized deployment (Docker)
✅ Successful MCP-based multi-agent integration
✅ Real-time MITRE ATT&CK intelligence retrieval (3-tier system)
✅ Model-agnostic LLM interface (Ollama support)
✅ Interactive threat investigation workflow
✅ Scenario-based testing environment

**Performance Metrics (if available):**
- Response time for alert analysis
- Accuracy of threat identification
- Number of supported MITRE techniques (state the count from your database)

**Future Enhancements:**
- Integration with real Wazuh API (currently mock data)
- Automated response actions (e.g., firewall rule creation)
- Multi-language support
- Historical alert correlation
- Custom playbook editor

**Optional Screenshot:**
- A comparison showing different intelligence tiers (side by side)
- OR: Performance dashboard if you have metrics

---

## **HOW TO CAPTURE ALL SCREENSHOTS**

### Step-by-Step Guide:

**1. Start the Application:**
```powershell
# Open PowerShell in your project directory
cd "c:\Users\nunom\Desktop\Mestrado_IA\2º Ano\Proposta de tese\GenAI-Enabled-SOCs-via-MCP-Integration"

# Make sure Ollama is running (if using Docker)
docker-compose up -d ollama

# Start Streamlit
streamlit run app.py
```

**2. Capture Screenshot 1 - Initial Dashboard:**
- Full window view showing both columns (alert feed + chat)
- Sidebar visible with all configuration options
- Save as: `screenshot_1_dashboard_overview.png`

**3. Capture Screenshot 2 - Sidebar Configuration:**
- Focus on sidebar showing:
  - Lab Controller with scenario selection
  - AI Configuration with model selection
  - MITRE Intelligence tiers
- Save as: `screenshot_2_sidebar_config.png`

**4. Capture Screenshot 3 - Attack Injection:**
- Select "SSH Brute Force" scenario
- Click "Trigger Alert"
- Capture the success message and updated alert feed
- Make sure "Retrieved Context" section is expanded
- Save as: `screenshot_3_attack_injection.png`

**5. Capture Screenshot 4 - MITRE Context Display:**
- Full view of the expanded "Retrieved Context (From MITRE Server)" section
- Should show the intelligence data based on selected tier
- Save as: `screenshot_4_mitre_context.png`

**6. Capture Screenshot 5 - Chat Interaction:**
- Ask: "What is this attack and how should I respond?"
- Wait for complete LLM response
- Capture the conversation showing question + detailed answer
- Save as: `screenshot_5_chat_interaction.png`

**7. Capture Screenshot 6 - Multi-turn Conversation:**
- Ask follow-up: "What are the specific commands I should run?"
- Capture showing the full conversation thread (2-3 exchanges)
- Save as: `screenshot_6_conversation_flow.png`

**8. Optional - Capture Screenshot 7 - Different Tiers:**
- Switch between intelligence tiers (Tier 1, 2, 3, Hybrid)
- Capture the different outputs for comparison
- Save as: `screenshot_7_tier_comparison.png`

---

## **PRESENTATION TIPS**

### Visual Design:
- Use a dark theme for screenshots (looks more professional for security tools)
- Highlight important UI elements with boxes or arrows
- Keep text minimal - let the screenshots tell the story

### Narrative Flow:
1. Start with the problem (alert fatigue, manual work)
2. Introduce your solution (MCP architecture)
3. Show the architecture clearly
4. Demonstrate with live screenshots
5. End with impact and future vision

### Key Messages:
- **Innovation:** First implementation of MCP for SOC automation
- **Flexibility:** Model-agnostic, tier-based intelligence
- **Practicality:** Real attack scenarios, actionable responses
- **Scalability:** Modular architecture ready for expansion

---

## **ADDITIONAL RESOURCES TO INCLUDE**

### In Appendix or Backup Slides:
- Code snippet showing MCP tool definitions
- Sample JSON alert structure
- MITRE technique coverage
- Docker Compose architecture diagram (3-service setup) statistics
- Technology stack diagram

### Demo Video (Optional):
Consider recording a 2-3 minute video showing:
1. Selecting a scenario
2. Triggering an alert
3. Asking questions to the AI
4. Switching intelligence tiers
5. Showing different attack scenarios

---

## **FINAL CHECKLIST**

Before your presentation:
- [ ] Test all three attack scenarios
- [ ] Verify Ollama/LLM is responding correctly
- [ ] Prepare backup screenshots in case of technical issues
- [ ] Have the application running during presentation (if doing live demo)
- [ ] Prepare 1-2 example questions to ask the AI
- [ ] Know your MITRE technique IDs (T1110, T1595, T1059)
- [ ] Have the repository link ready if asked about code

---

Good luck with your presentation! 🚀
