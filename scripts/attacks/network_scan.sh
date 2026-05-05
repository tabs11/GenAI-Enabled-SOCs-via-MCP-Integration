#!/bin/bash
# Network Scanning Attack - MITRE ATT&CK T1595
# Generates network reconnaissance alerts in Wazuh

echo "=========================================="
echo "Network Scanning Attack (T1595)"
echo "=========================================="
echo ""

# Get Metasploitable IP
TARGET=$(getent hosts metasploitable | awk '{ print $1 }')
if [ -z "$TARGET" ]; then
    echo "❌ Error: Cannot resolve 'metasploitable' hostname"
    echo "Falling back to common Docker subnet..."
    TARGET="172.20.0.100"
fi

echo "🎯 Target: $TARGET"
echo "📋 Attack Type: Active Scanning"
echo "🔧 Tool: Nmap"
echo ""

echo "🚀 Phase 1: Ping Sweep"
ping -c 5 $TARGET
echo ""

echo "🚀 Phase 2: Port Scan (Common Ports)"
echo "⏱️  This will take about 10 seconds..."
nmap -sS -p 21,22,23,25,80,443,3306,8080 $TARGET

echo ""
echo "🚀 Phase 3: Service Version Detection"
echo "⏱️  This will take about 20 seconds..."
nmap -sV -p 21,22,80 $TARGET

echo ""
echo "🚀 Phase 4: OS Detection"
nmap -O $TARGET 2>/dev/null || echo "OS detection requires root privileges"

echo ""
echo "✅ Scanning completed!"
echo ""
echo "📊 Expected Wazuh Alerts:"
echo "  - Multiple connection attempts detected"
echo "  - Port scanning activity (if Wazuh agent is on target)"
echo "  - MITRE Technique: T1595 - Active Scanning"
echo ""
echo "🔍 Discovered Services:"
echo "  - FTP (21): vsftpd 2.3.4 (backdoored version)"
echo "  - SSH (22): OpenSSH 4.7p1"
echo "  - Telnet (23): Linux telnetd"
echo "  - HTTP (80): Apache 2.2.8"
echo ""
echo "🔍 Check Wazuh Dashboard: https://localhost:443"
