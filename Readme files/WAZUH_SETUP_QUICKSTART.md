# 🚀 Wazuh Stack - Quick Start Summary

## ✅ What Was Added

Your docker-compose.yml now includes:

### New Services (3)
1. **wazuh-indexer** - Elasticsearch backend for log storage
2. **wazuh-manager** - SIEM core (API, alert processing, agent management)
3. **wazuh-dashboard** - Web UI for security monitoring

### Network
- **soc_network** (172.20.0.0/16) - All containers can communicate

### Environment Variables
- Your `soc-assistant` container now has:
  - `WAZUH_MANAGER_IP=wazuh-manager`
  - `WAZUH_API_PORT=55000`
  - `WAZUH_API_USER=wazuh-wui`
  - `WAZUH_API_PASSWORD=MyS3cr37P450r.*-`

---

## 🎯 How to Deploy

### Step 1: Start the Stack
```powershell
# Navigate to your project folder
cd "C:\Users\nunom\Desktop\Mestrado_IA\2º Ano\Proposta de tese\GenAI-Enabled-SOCs-via-MCP-Integration"

# Start all services
docker-compose up -d

# Wait 60 seconds for Wazuh to initialize
```

### Step 2: Verify Services
```powershell
# Check all containers are running
docker ps

# Should see 6 containers:
# - wazuh-mcp-agent (your app)
# - ollama-service
# - metasploitable-target
# - wazuh-indexer
# - wazuh-manager
# - wazuh-dashboard
```

### Step 3: Access Wazuh Dashboard
1. Open: **https://localhost:443**
2. Accept the security warning (self-signed certificate)
3. Login: **admin** / **admin**
4. Navigate to **"Agents"** - you'll see 0 agents (we'll add one next)

### Step 4: Test Wazuh API
```powershell
# Test API connection
curl -k -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/

# Expected response: JSON with api_version: "4.7.2"
```

### Step 5: Deploy Agent to Metasploitable (Optional)
```bash
# This makes Metasploitable send logs to Wazuh
docker exec -it metasploitable-target bash

# Inside the container:
wget https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.7.2-1_amd64.deb
dpkg -i wazuh-agent_4.7.2-1_amd64.deb
sed -i "s/<address>MANAGER_IP<\/address>/<address>wazuh-manager<\/address>/" /var/ossec/etc/ossec.conf
/var/ossec/bin/wazuh-control start
exit
```

### Step 6: Test Your App
1. Open: **http://localhost:8501**
2. Your Streamlit app now has access to Wazuh API
3. The `wazuh_server.py` has new tools:
   - `get_real_wazuh_alerts()` - Fetch live alerts
   - `get_wazuh_agents()` - List monitored systems

---

## 🔍 Verification Checklist

- [ ] All 6 containers running: `docker ps`
- [ ] Wazuh Dashboard accessible: https://localhost:443
- [ ] Wazuh API responding: `curl -k -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/`
- [ ] Streamlit app accessible: http://localhost:8501
- [ ] No errors in logs: `docker logs wazuh-manager`

---

## 📊 Service Map

```
Your Computer (Host)
│
├─ Port 8501  → Streamlit App (soc-assistant)
├─ Port 443   → Wazuh Dashboard (web UI)
├─ Port 55000 → Wazuh API (for your app)
├─ Port 9200  → Wazuh Indexer (Elasticsearch)
├─ Port 11434 → Ollama (AI engine)
└─ Port 2222  → Metasploitable SSH (victim)

Internal Network (172.20.0.x):
├─ wazuh-manager (SIEM Core)
├─ wazuh-indexer (Database)
├─ wazuh-dashboard (UI)
├─ wazuh-mcp-agent (Your App)
├─ ollama-service (AI)
└─ metasploitable-target (Victim)
```

---

## 🛠️ Useful Commands

```powershell
# View all logs
docker-compose logs

# Follow Wazuh Manager logs
docker logs -f wazuh-manager

# Restart Wazuh services
docker-compose restart wazuh-manager wazuh-indexer wazuh-dashboard

# Stop everything
docker-compose down

# Rebuild your app (if you changed code)
docker-compose up -d --build soc-assistant

# Check network connectivity
docker network inspect genai-enabled-socs-via-mcp-integration_soc_network
```

---

## 🐛 Common Issues

### Issue: Wazuh Manager won't start
**Symptom:** Container keeps restarting
**Solution:**
```powershell
docker logs wazuh-manager
# Look for errors, usually permission issues
# Fix: Reset volumes
docker-compose down -v
docker-compose up -d
```

### Issue: API returns 401 Unauthorized
**Symptom:** `curl` shows authentication error
**Solution:**
```powershell
# Check password matches in docker-compose.yml
# Both soc-assistant and wazuh-manager need same password
```

### Issue: Dashboard shows "No agents"
**Symptom:** Agents tab is empty
**Solution:** This is normal! You need to deploy agents manually (see Step 5)

### Issue: App can't connect to Wazuh
**Symptom:** `get_real_wazuh_alerts()` returns error
**Solution:**
```powershell
# Test from inside the container
docker exec -it wazuh-mcp-agent bash
curl -k -u wazuh-wui:MyS3cr37P450r.*- https://wazuh-manager:55000/
```

---

## 📚 Next Steps

1. ✅ **Current State:** Wazuh Stack is running, API is accessible
2. 🔄 **Next:** Deploy agent to Metasploitable (Step 5)
3. 🔄 **After That:** Simulate attacks (SSH brute force, port scans)
4. 🔄 **Finally:** See real alerts in Wazuh Dashboard AND your Streamlit app

---

## 📖 Detailed Documentation

For comprehensive guides, see:
- **Full Setup:** [scripts/setup_wazuh.md](setup_wazuh.md)
- **Main README:** [readme.md](../readme.md)

---

## 🎉 Success Indicators

You'll know everything is working when:
1. Wazuh Dashboard shows your deployed agent as "Active" (green)
2. Security Events appear in the Dashboard after simulating attacks
3. Your Streamlit app shows real alerts when you call `get_real_wazuh_alerts()`
4. The AI can analyze real security events from Wazuh + MITRE context

---

**Need Help?** Check the logs:
```powershell
docker logs wazuh-manager
docker logs wazuh-indexer
docker logs wazuh-dashboard
docker logs wazuh-mcp-agent
```
