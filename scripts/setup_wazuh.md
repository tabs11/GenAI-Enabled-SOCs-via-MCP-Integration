# 🛡️ Wazuh Stack Setup Guide

This guide will help you configure and verify the Wazuh Stack in your Docker environment.

---

## 📋 Architecture Overview

Your Docker environment now includes:

```
┌─────────────────────────────────────────────────────────────┐
│                      SOC Network (172.20.0.0/16)            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ SOC Assistant│  │   Ollama     │  │ Metasploitable  │   │
│  │ (Streamlit)  │  │  (Llama 3.2) │  │   (Target)      │   │
│  │  :8501       │  │  :11434      │  │   :22, :80      │   │
│  └──────┬───────┘  └──────────────┘  └────────┬────────┘   │
│         │                                      │            │
│         │ MCP Protocol                         │ Logs       │
│         │                                      │            │
│  ┌──────▼──────────────────────────────────────▼────────┐   │
│  │              Wazuh Manager :55000                     │   │
│  │         (SIEM Core + API + Agent Collector)           │   │
│  └──────┬────────────────────────────────────────────────┘   │
│         │ Filebeat                                           │
│  ┌──────▼────────┐           ┌────────────────────────┐     │
│  │Wazuh Indexer  │◄──────────┤  Wazuh Dashboard       │     │
│  │(Elasticsearch)│           │   (Web UI) :443        │     │
│  │    :9200      │           └────────────────────────┘     │
│  └───────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Step 1: Start the Stack

```bash
# Start all services
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

You should see 6 containers:
- ✅ wazuh-mcp-agent (soc-assistant)
- ✅ ollama-service
- ✅ metasploitable-target
- ✅ wazuh-indexer
- ✅ wazuh-manager
- ✅ wazuh-dashboard

---

## 🔍 Step 2: Verify Wazuh Services

### Check Wazuh Manager Logs
```bash
docker logs wazuh-manager
```

Look for:
- ✅ `Started (pid: XXXX)`
- ✅ `Listening on port 1514` (agent connection)
- ✅ `API ready on port 55000`

### Check Wazuh Indexer
```bash
docker logs wazuh-indexer
```

Look for:
- ✅ `Node started`
- ✅ `Cluster health status: GREEN`

### Check Wazuh Dashboard
```bash
docker logs wazuh-dashboard
```

Look for:
- ✅ `Server running at https://0.0.0.0:5601`

---

## 🌐 Step 3: Access Wazuh Dashboard

Open your browser and navigate to:
```
https://localhost:443
```

**⚠️ Security Warning:** Your browser will show a certificate warning (self-signed cert). Click "Advanced" → "Proceed to localhost".

**Default Credentials:**
- Username: `admin`
- Password: `admin`

**Post-Login:**
1. Navigate to **Server Management** → **Endpoints Summary**
2. You should see the Wazuh Manager listed
3. Currently, no agents are enrolled yet

---

## 🤖 Step 4: Test Wazuh API Connection

The Wazuh Manager exposes a RESTful API on port **55000**. Your `app.py` will use this to fetch real alerts.

### Test from Host Machine:
```bash
curl -k -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/
```

Expected Response:
```json
{
  "data": {
    "title": "Wazuh API REST",
    "api_version": "4.7.2",
    "revision": 40720,
    "license_name": "GPL 2.0",
    "license_url": "https://github.com/wazuh/wazuh/blob/master/LICENSE",
    "hostname": "wazuh-manager",
    "timestamp": "2026-02-13T12:34:56+0000"
  }
}
```

### Test from Inside soc-assistant Container:
```bash
docker exec -it wazuh-mcp-agent bash
curl -k -u wazuh-wui:MyS3cr37P450r.*- https://wazuh-manager:55000/
```

---

## 📡 Step 5: Deploy Wazuh Agent to Metasploitable (Optional - For Real Alerts)

To generate **real security alerts**, install the Wazuh agent on the Metasploitable container.

### Option A: Manual Installation
```bash
# Enter the Metasploitable container
docker exec -it metasploitable-target bash

# Download Wazuh Agent
wget https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.7.2-1_amd64.deb

# Install
dpkg -i wazuh-agent_4.7.2-1_amd64.deb

# Configure manager address
sed -i "s/<address>MANAGER_IP<\/address>/<address>wazuh-manager<\/address>/" /var/ossec/etc/ossec.conf

# Start agent
/var/ossec/bin/wazuh-control start
```

### Option B: Automated Script (Coming Soon)
```bash
# Run the deployment script
bash scripts/deploy_agent_to_metasploitable.sh
```

### Verify Agent Registration:
1. Go to **Wazuh Dashboard** → **Agents**
2. You should see a new agent: `metasploitable-target`
3. Status should be **Active** (green)

---

## 🔗 Step 6: Update Your App to Use Real Wazuh API

Your `wazuh_server.py` currently reads from `alert.json` (mock data). To connect to the real Wazuh API:

### Create a new tool in `wazuh_server.py`:
```python
import requests
import os

@mcp.tool()
def get_real_wazuh_alerts() -> str:
    """
    Fetches real alerts from the Wazuh API.
    """
    wazuh_api_url = f"https://{os.getenv('WAZUH_MANAGER_IP', 'wazuh-manager')}:55000"
    auth = (os.getenv('WAZUH_API_USER'), os.getenv('WAZUH_API_PASSWORD'))
    
    try:
        response = requests.get(
            f"{wazuh_api_url}/alerts",
            auth=auth,
            verify=False,  # Ignore SSL for lab environment
            params={"limit": 10, "sort": "-timestamp"}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return json.dumps({"error": str(e)})
```

---

## 🧪 Step 7: Test the Full Pipeline

### Trigger a Simulated Attack:
```bash
# SSH Brute Force from your host to Metasploitable
ssh msfadmin@localhost -p 2222
# Password: msfadmin
# Try wrong passwords 5+ times to trigger alert
```

### Check Wazuh Dashboard:
1. Navigate to **Security Events**
2. Look for Rule ID `5712` (SSH authentication failure)
3. You should see multiple failed login attempts

### Check Your Streamlit App:
1. Open http://localhost:8501
2. Click "🚨 Trigger Alert" → Select "SSH Brute Force"
3. Ask the AI: "What just happened?"
4. The AI should cross-reference with MITRE ATT&CK T1110

---

## 🔧 Troubleshooting

### Issue: Wazuh Manager won't start
```bash
# Check logs
docker logs wazuh-manager

# Common fix: Reset permissions
docker-compose down
docker volume rm $(docker volume ls -q | grep wazuh)
docker-compose up -d
```

### Issue: Agent not connecting
```bash
# Check firewall
docker exec wazuh-manager /var/ossec/bin/wazuh-control status

# Check agent config
docker exec metasploitable-target cat /var/ossec/etc/ossec.conf | grep address
```

### Issue: API authentication fails
```bash
# Reset API password
docker exec wazuh-manager /var/ossec/api/scripts/wazuh-api-password.sh -u wazuh-wui -p MyS3cr37P450r.*-
```

---

## 📊 Next Steps

1. ✅ **Network Visibility:** All containers can communicate via `soc_network`
2. ✅ **Wazuh Ports:** 1514 (agents), 55000 (API) are exposed internally
3. ✅ **Environment Variables:** Your app knows where Wazuh is (`wazuh-manager`)
4. 🔄 **Agent Deployment:** Install agent on Metasploitable for real logs
5. 🔄 **Kali Linux:** Add attacker machine (next phase)

---

## 📚 Useful Commands

```bash
# View all container IPs
docker network inspect genai-enabled-socs-via-mcp-integration_soc_network

# Restart just Wazuh services
docker-compose restart wazuh-manager wazuh-indexer wazuh-dashboard

# View real-time Wazuh logs
docker logs -f wazuh-manager

# Access Wazuh CLI
docker exec -it wazuh-manager /var/ossec/bin/wazuh-control
```

---

## 🎯 Validation Checklist

- [ ] All 6 containers running
- [ ] Wazuh Dashboard accessible at https://localhost:443
- [ ] Wazuh API responds on port 55000
- [ ] Wazuh Manager shows in Dashboard
- [ ] Metasploitable agent registered (if installed)
- [ ] Your app can reach wazuh-manager service
- [ ] No Docker network errors in logs

---

**🎉 Congratulations!** Your Wazuh Stack is ready for SOC operations.
