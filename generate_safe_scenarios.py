import os
import json
import random
from datetime import datetime, timedelta

# A list of MITRE ATT&CK techniques tailored for safe (virus-free) simulation
TECHNIQUES = [
    {"id": "T1110.001", "name": "Password Guessing", "desc": "Failed login attempts (Brute Force)", "log": "Failed password for user {user} from {ip} port 22 ssh2"},
    {"id": "T1059.001", "name": "PowerShell", "desc": "Suspicious PowerShell execution", "log": "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -Command Write-Host 'Safe Simulation'"},
    {"id": "T1003.001", "name": "LSASS Memory", "desc": "Attempted memory dump of LSASS", "log": "procdump.exe -ma lsass.exe lsass.dmp (Safe Simulation)"},
    {"id": "T1047", "name": "Windows Management Instrumentation", "desc": "WMI execution", "log": "wmic process call create 'calc.exe'"},
    {"id": "T1078", "name": "Valid Accounts", "desc": "Unusual login time or location", "log": "Successful interactive logon by {user} at uncommon hour"},
    {"id": "T1190", "name": "Exploit Public-Facing Application", "desc": "Web exploit or SQLi attempt", "log": "GET /login.php?user=admin' OR '1'='1 (Safe Simulated SQLi)"},
    {"id": "T1053.005", "name": "Scheduled Task", "desc": "Suspicious scheduled task creation", "log": "schtasks /create /tn 'UpdaterTasks' /tr 'cmd.exe /c echo Safe' /sc daily"},
    {"id": "T1082", "name": "System Information Discovery", "desc": "System info collection", "log": "systeminfo.exe > info.txt"},
    {"id": "T1105", "name": "Ingress Tool Transfer", "desc": "Suspicious file download", "log": "certutil.exe -urlcache -split -f http://example.com/safe_file.txt test.txt"},
    {"id": "T1049", "name": "System Network Connections Discovery", "desc": "Network connection enumeration", "log": "netstat -ano | findstr ESTABLISHED"},
]

def generate_safe_scenarios(count=100):
    scenarios_dir = "scenarios"
    os.makedirs(scenarios_dir, exist_ok=True)
    
    users = ["admin", "root", "jdoe", "asmith", "guest", "svc_account"]
    
    print(f"[*] Generating {count} safe, synthesized mock alerts...")
    
    for i in range(1, count + 1):
        tech = random.choice(TECHNIQUES)
        src_ip = f"{random.randint(10, 192)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}"
        user = random.choice(users)
        
        # Safely format the log string
        log_str = tech["log"].replace("{user}", user).replace("{ip}", src_ip)
        
        fake_alert = {
            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 1440))).strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
            "rule": {
                "level": random.randint(5, 14),
                "description": f"Simulation: {tech['desc']}",
                "mitre": {
                    "id": [tech["id"]],
                    "technique": [tech["name"]]
                }
            },
            "src_ip": src_ip,
            "full_log": log_str
        }
        
        # Save each to a unique file
        file_name = os.path.join(scenarios_dir, f"alert_safe_{i:03d}_{tech['id'].replace('.', '_')}.json")
        with open(file_name, "w") as f:
            json.dump(fake_alert, f, indent=2)
            
    print(f"[+] Successfully generated {count} AV-friendly mock scenarios in '{scenarios_dir}'.")

if __name__ == "__main__":
    # Remove old MORDOR corrupted files if they exist to prevent evaluation script crashes
    for file in os.listdir("scenarios"):
        if file.startswith("alert_mordor_"):
            try:
                os.remove(os.path.join("scenarios", file))
            except:
                pass
                
    generate_safe_scenarios(100)