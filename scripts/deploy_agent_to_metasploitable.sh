#!/bin/bash
# ================================================
# Deploy Wazuh Agent to Metasploitable Container
# ================================================
# This script installs and configures the Wazuh agent
# inside the Metasploitable container so it can send
# security logs to the Wazuh Manager.
#
# Usage: docker exec -it metasploitable-target bash < scripts/deploy_agent_to_metasploitable.sh
# Or: bash scripts/deploy_agent_to_metasploitable.sh

echo "[+] Installing Wazuh Agent on Metasploitable..."

# Step 1: Download Wazuh Agent DEB package
echo "[+] Downloading Wazuh Agent 4.7.2..."
wget https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.7.2-1_amd64.deb -O /tmp/wazuh-agent.deb

# Step 2: Install the agent
echo "[+] Installing Wazuh Agent..."
dpkg -i /tmp/wazuh-agent.deb

# Step 3: Configure the agent to connect to wazuh-manager
echo "[+] Configuring Wazuh Manager address..."
sed -i "s/<address>MANAGER_IP<\/address>/<address>wazuh-manager<\/address>/" /var/ossec/etc/ossec.conf

# Step 4: Start the Wazuh agent service
echo "[+] Starting Wazuh Agent..."
/var/ossec/bin/wazuh-control start

# Step 5: Verify agent is running
echo "[+] Verifying agent status..."
/var/ossec/bin/wazuh-control status

echo ""
echo "=========================================="
echo "✅ Wazuh Agent Deployment Complete!"
echo "=========================================="
echo "The Metasploitable container is now monitored."
echo "Check Wazuh Dashboard to see this agent appear."
echo ""
echo "Agent Name: metasploitable-target"
echo "Manager IP: wazuh-manager (172.20.0.x)"
echo "=========================================="
