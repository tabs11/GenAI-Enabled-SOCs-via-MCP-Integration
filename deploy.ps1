#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy GenAI-Enabled SOC Environment

.DESCRIPTION
    Automated deployment script for the Wazuh AI Analyst project.
    Supports both full Wazuh stack deployment and simple mode (without Wazuh services).

.PARAMETER Mode
    Deployment mode: "full" (default) or "simple"
    - full: Deploys complete Wazuh stack (Manager, Indexer, Dashboard) with MCP integration
    - simple: Deploys only SOC Assistant, Ollama, and Metasploitable (no Wazuh services)

.PARAMETER SkipCertificates
    Skip certificate generation (use existing certificates)

.PARAMETER Clean
    Perform clean deployment (remove all volumes and rebuild)

.EXAMPLE
    .\deploy.ps1
    Deploy full Wazuh stack (default)

.EXAMPLE
    .\deploy.ps1 -Mode simple
    Deploy simple mode without Wazuh services

.EXAMPLE
    .\deploy.ps1 -Mode full -Clean
    Clean deployment of full stack (removes all data)

.EXAMPLE
    .\deploy.ps1 -SkipCertificates
    Deploy using existing certificates
#>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("full", "simple")]
    [string]$Mode = "full",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipCertificates,
    
    [Parameter(Mandatory=$false)]
    [switch]$Clean
)

# Color output functions
function Write-Step {
    param([string]$Message)
    Write-Host "`n▶ $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "  ⚠ $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

# Display banner
Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🛡️  GenAI-Enabled SOC Deployment Script                    ║
║                                                               ║
║   Mode: $($Mode.ToUpper().PadRight(52))║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Determine which compose file to use
$composeFile = if ($Mode -eq "simple") { "docker-compose-simple.yml" } else { "docker-compose.yml" }

# Check if compose file exists
if (-not (Test-Path $composeFile)) {
    Write-Error-Custom "Compose file not found: $composeFile"
    exit 1
}

Write-Success "Using compose file: $composeFile"

# Step 1: Configure WSL2 (only for full mode)
if ($Mode -eq "full") {
    Write-Step "Step 1/8: Configuring WSL2 memory settings..."
    try {
        $currentValue = wsl -d docker-desktop sysctl vm.max_map_count 2>&1 | Select-String -Pattern '\d+' | ForEach-Object { $_.Matches.Value }
        if ($currentValue -lt 262144) {
            wsl -d docker-desktop sysctl -w vm.max_map_count=262144 | Out-Null
            Write-Success "Set vm.max_map_count=262144"
        } else {
            Write-Success "vm.max_map_count already configured ($currentValue)"
        }
    } catch {
        Write-Warning-Custom "Could not configure WSL2. If indexer fails to start, run: wsl -d docker-desktop sysctl -w vm.max_map_count=262144"
    }
} else {
    Write-Step "Step 1/8: Skipping WSL2 configuration (simple mode)"
}

# Step 2: Stop existing containers
Write-Step "Step 2/8: Stopping existing containers..."
docker-compose -f $composeFile down 2>&1 | Out-Null
Write-Success "Containers stopped"

# Step 3: Clean volumes if requested
if ($Clean) {
    Write-Step "Step 3/8: Cleaning volumes (clean deployment)..."
    
    $volumes = @(
        "genai-enabled-socs-via-mcp-integration_wazuh_indexer_data",
        "genai-enabled-socs-via-mcp-integration_wazuh_api_configuration",
        "genai-enabled-socs-via-mcp-integration_wazuh_etc",
        "genai-enabled-socs-via-mcp-integration_wazuh_logs",
        "genai-enabled-socs-via-mcp-integration_wazuh_queue",
        "genai-enabled-socs-via-mcp-integration_wazuh_var_multigroups",
        "genai-enabled-socs-via-mcp-integration_wazuh_integrations",
        "genai-enabled-socs-via-mcp-integration_wazuh_active_response",
        "genai-enabled-socs-via-mcp-integration_wazuh_agentless",
        "genai-enabled-socs-via-mcp-integration_wazuh_wodles",
        "genai-enabled-socs-via-mcp-integration_filebeat_etc",
        "genai-enabled-socs-via-mcp-integration_filebeat_var",
        "genai-enabled-socs-via-mcp-integration_wazuh_dashboard_config",
        "genai-enabled-socs-via-mcp-integration_wazuh_dashboard_custom"
    )
    
    $removedCount = 0
    foreach ($volume in $volumes) {
        $result = docker volume rm $volume 2>&1
        if ($LASTEXITCODE -eq 0) {
            $removedCount++
        }
    }
    
    Write-Success "Removed $removedCount volumes"
} else {
    Write-Step "Step 3/8: Skipping volume cleanup (use -Clean to remove all data)"
}

# Step 4: Generate certificates (only for full mode)
if ($Mode -eq "full" -and -not $SkipCertificates) {
    Write-Step "Step 4/8: Generating SSL certificates..."
    
    if (Test-Path "generate-indexer-certs.yml") {
        docker-compose -f generate-indexer-certs.yml run --rm generator 2>&1 | Out-Null
        
        $certCount = (Get-ChildItem "config\wazuh_indexer_ssl_certs\*.pem" -ErrorAction SilentlyContinue).Count
        if ($certCount -ge 10) {
            Write-Success "Generated $certCount certificate files"
        } else {
            Write-Error-Custom "Certificate generation may have failed (only $certCount files found)"
        }
    } else {
        Write-Warning-Custom "Certificate generator not found, skipping..."
    }
} elseif ($Mode -eq "full" -and $SkipCertificates) {
    Write-Step "Step 4/8: Skipping certificate generation (using existing certificates)"
    
    $certCount = (Get-ChildItem "config\wazuh_indexer_ssl_certs\*.pem" -ErrorAction SilentlyContinue).Count
    if ($certCount -lt 10) {
        Write-Error-Custom "Existing certificates not found! Remove -SkipCertificates flag."
        exit 1
    }
    Write-Success "Using $certCount existing certificate files"
} else {
    Write-Step "Step 4/8: Skipping certificate generation (simple mode)"
}

# Step 5: Start all services
Write-Step "Step 5/8: Starting all services..."
docker-compose -f $composeFile up -d

if ($LASTEXITCODE -eq 0) {
    Write-Success "All services started"
} else {
    Write-Error-Custom "Failed to start services"
    exit 1
}

# Step 6: Wait for services to initialize
if ($Mode -eq "full") {
    Write-Step "Step 6/8: Waiting for Wazuh Indexer to initialize (45 seconds)..."
    
    for ($i = 45; $i -gt 0; $i--) {
        Write-Host "`r  Waiting... $i seconds remaining " -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds 1
    }
    Write-Host "`r" -NoNewline
    Write-Success "Indexer initialization wait complete"
} else {
    Write-Step "Step 6/8: Waiting for services to initialize (10 seconds)..."
    Start-Sleep -Seconds 10
    Write-Success "Services ready"
}

# Step 7: Initialize security plugin (only for full mode)
if ($Mode -eq "full") {
    Write-Step "Step 7/8: Initializing Wazuh security plugin..."
    
    $securityCmd = @'
export OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk && 
chmod +x /usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh && 
/usr/share/wazuh-indexer/plugins/opensearch-security/tools/securityadmin.sh 
-cd /usr/share/wazuh-indexer/opensearch-security/ 
-icl 
-key /usr/share/wazuh-indexer/certs/admin-key.pem 
-cert /usr/share/wazuh-indexer/certs/admin.pem 
-cacert /usr/share/wazuh-indexer/certs/root-ca.pem 
-h 127.0.0.1 
-nhnv
'@ -replace "`n", " "
    
    $output = docker exec wazuh-indexer bash -c $securityCmd 2>&1
    
    if ($output -match "Done with success") {
        Write-Success "Security plugin initialized successfully"
    } else {
        Write-Warning-Custom "Security initialization may have issues. Check logs: docker logs wazuh-indexer"
    }
} else {
    Write-Step "Step 7/8: Skipping security initialization (simple mode)"
}

# Step 8: Verify deployment
Write-Step "Step 8/8: Verifying deployment..."

$containers = docker ps --format "{{.Names}}" 2>&1
$runningCount = ($containers | Measure-Object).Count

if ($runningCount -gt 0) {
    Write-Success "Running containers: $runningCount"
    Write-Host ""
    docker ps --format "table {{.Names}}\t{{.Status}}" | ForEach-Object { 
        Write-Host "  $_" -ForegroundColor Gray 
    }
} else {
    Write-Error-Custom "No containers are running!"
    exit 1
}

# Display access information
Write-Host @"

╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ✅ DEPLOYMENT SUCCESSFUL                                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Green

if ($Mode -eq "full") {
    Write-Host @"
🌐 Access URLs:
   ┌──────────────────────────────────────────────────────────┐
   │ Wazuh Dashboard:  https://localhost:443                  │
   │   Username: admin                                        │
   │   Password: admin                                        │
   │                                                          │
   │ SOC Assistant:    http://localhost:8501                  │
   │                                                          │
   │ Wazuh API:        https://localhost:55000                │
   │   Username: wazuh-wui                                    │
   │   Password: MyS3cr37P450r.*-                             │
   └──────────────────────────────────────────────────────────┘

📋 Next Steps:
   1. Open Wazuh Dashboard: Start-Process "https://localhost:443"
   2. Open SOC Assistant:   Start-Process "http://localhost:8501"
   3. Deploy agent to Metasploitable (see DEPLOYMENT_SUCCESS.md)

⚠️  Note: Accept the SSL certificate warning (self-signed for lab use)

"@ -ForegroundColor White
} else {
    Write-Host @"
🌐 Access URLs:
   ┌──────────────────────────────────────────────────────────┐
   │ SOC Assistant:    http://localhost:8501                  │
   │ Ollama LLM:       http://localhost:11434                 │
   │ Metasploitable:   ssh://localhost:2222 (msfadmin/msfadmin)│
   └──────────────────────────────────────────────────────────┘

📋 Next Steps:
   1. Open SOC Assistant: Start-Process "http://localhost:8501"
   2. Test with mock alerts (no Wazuh stack in simple mode)

ℹ️  Running in SIMPLE MODE - Wazuh services not deployed
   To deploy full stack, run: .\deploy.ps1 -Mode full

"@ -ForegroundColor White
}

Write-Host "📚 Documentation: See README.md and DEPLOYMENT_SUCCESS.md" -ForegroundColor Cyan
Write-Host ""
