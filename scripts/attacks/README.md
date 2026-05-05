# 🎯 Attack Scripts for Kali Linux

This directory contains pre-built attack scripts for penetration testing against Metasploitable2.

## 📁 Available Scripts

- **`ssh_brute_force.sh`** - SSH credential brute force attack (T1110)
- **`network_scan.sh`** - Network reconnaissance with Nmap (T1595)
- **`exploit_vsftpd.sh`** - Exploit vulnerable FTP service (T1190)
- **`web_attack.sh`** - Web application vulnerability scanning (T1190)

## 🚀 Usage

### From Kali Linux Container:

```bash
# 1. Access Kali container
docker exec -it kali-attacker bash

# 2. Navigate to attack scripts
cd /root/attacks

# 3. Run a script
bash ssh_brute_force.sh
```

### Attack Workflow:

1. **Reconnaissance** - Scan the target
2. **Exploitation** - Execute vulnerability exploit
3. **Observe Wazuh** - Check Wazuh Dashboard for alerts
4. **AI Analysis** - Ask your SOC Assistant to analyze the alerts

## ⚠️ Important Notes

- **Target IP:** Metasploitable2 is accessible at its Docker service name (`metasploitable`) or check its IP with:
  ```bash
  docker inspect metasploitable-target | grep IPAddress
  ```

- **Lab Only:** These attacks should ONLY be run in isolated lab environments
- **Wazuh Alerts:** Most attacks generate alerts in 1-5 minutes
- **First Run:** Kali container takes 2-3 minutes to install tools on first startup

## 🔍 Checking Attack Results

**Via Wazuh Dashboard:**
```
https://localhost:443
Login: admin / SecretPassword
Navigate to: Security Events → Recent Alerts
```

**Via SOC Assistant:**
```
http://localhost:8501
Click "Fetch Latest Alerts" or ask: "Show me recent security events"
```

**Via Wazuh API:**
```bash
curl -k -u wazuh-wui:MyS3cr37P450r.*- \
  https://localhost:55000/security/users/authenticate
```
