import os
import io
import json
import zipfile
import requests
from datetime import datetime

# URLs atualizados e testados do repositório OTRF/Security-Datasets (formato .zip)
MORDOR_URLS = {
    "T1059.001": {
        "name": "PowerShell Command Execution",
        "url": "https://raw.githubusercontent.com/OTRF/Security-Datasets/master/datasets/atomic/windows/execution/host/empire_launcher_vbs.zip"
    },
    "T1003.001": {
        "name": "OS Credential Dumping: Mimikatz",
        "url": "https://raw.githubusercontent.com/OTRF/Security-Datasets/master/datasets/atomic/windows/credential_access/host/empire_mimikatz_extract_keys.zip"
    },
    "T1021.006": {
        "name": "Lateral Movement: Windows Remote Management",
        "url": "https://raw.githubusercontent.com/OTRF/Security-Datasets/master/datasets/atomic/windows/lateral_movement/host/empire_psremoting_stager.zip"
    },
    "T1569.002": {
        "name": "System Services: Service Execution",
        "url": "https://raw.githubusercontent.com/OTRF/Security-Datasets/master/datasets/atomic/windows/lateral_movement/host/empire_psexec_dcerpc_tcp_svcctl.zip"
    }
}

def download_and_extract():
    scenarios_dir = "scenarios"
    if not os.path.exists(scenarios_dir):
        os.makedirs(scenarios_dir)
        print(f"[+] Diretório criado: {scenarios_dir}")

    for technique_id, info in MORDOR_URLS.items():
        print(f"[*] A transferir {info['name']} ({technique_id})...")
        try:
            # Transferir o ficheiro zip
            response = requests.get(info['url'], timeout=15)
            if response.status_code == 200:
                print("    [+] Transferência concluída. A extrair...")
                
                # Abrir e extrair o ZIP na memória
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    # Encontrar o primeiro ficheiro .json dentro do zip
                    json_filename = next((name for name in z.namelist() if name.endswith('.json')), None)
                    
                    if json_filename:
                        with z.open(json_filename) as f:
                            # Ler apenas a primeira linha (formato JSONL)
                            first_line = f.readline().decode('utf-8')
                            first_event = json.loads(first_line)
                            
                            # Converter e injetar o formato de alerta do Wazuh
                            wazuh_alert = {
                                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000+0000"),
                                "rule": {
                                    "level": 12,
                                    "description": f"MORDOR Simulation: {info['name']}",
                                    "mitre": {
                                        "id": [technique_id],
                                        "technique": [info['name']]
                                    }
                                },
                                "src_ip": first_event.get("SourceIP", "10.0.0.50"), # Fallback IP se não existir
                                "full_log": json.dumps(first_event)
                            }
                            
                            # Guardar na pasta scenarios
                            out_path = os.path.join(scenarios_dir, f"alert_mordor_{technique_id.replace('.', '_')}.json")
                            with open(out_path, "w") as out_f:
                                json.dump(wazuh_alert, out_f, indent=2)
                            print(f"    [+] Guardado com sucesso em {out_path}")
                    else:
                        print("    [-] Nenhum ficheiro .json encontrado dentro do zip.")
            else:
                print(f"    [-] Falha ao transferir: HTTP {response.status_code}")
        except Exception as e:
            print(f"    [-] Erro a processar a tática {technique_id}: {str(e)}")

if __name__ == "__main__":
    download_and_extract()