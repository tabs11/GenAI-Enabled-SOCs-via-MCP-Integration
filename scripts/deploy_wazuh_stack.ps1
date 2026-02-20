# ================================================================
# Wazuh Stack Deployment & Validation Script
# ================================================================
# This PowerShell script automates the deployment of the Wazuh
# stack and validates that all components are working correctly.
#
# Usage: .\scripts\deploy_wazuh_stack.ps1
# ================================================================

Write-Host "🛡️  Wazuh Stack Deployment Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker is running
Write-Host "[1/7] Checking Docker status..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Step 2: Stop existing containers (if any)
Write-Host ""
Write-Host "[2/7] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down
Write-Host "✅ Cleanup complete" -ForegroundColor Green

# Step 3: Start all services
Write-Host ""
Write-Host "[3/7] Starting all services (this may take 2-3 minutes)..." -ForegroundColor Yellow
docker-compose up -d

# Step 4: Wait for services to be healthy
Write-Host ""
Write-Host "[4/7] Waiting for services to initialize..." -ForegroundColor Yellow
Write-Host "    This can take up to 60 seconds for Wazuh components..." -ForegroundColor Gray

Start-Sleep -Seconds 30

# Check each service
$services = @("wazuh-indexer", "wazuh-manager", "wazuh-dashboard", "ollama-service", "metasploitable-target", "wazuh-mcp-agent")
foreach ($service in $services) {
    $status = docker inspect -f '{{.State.Status}}' $service 2>$null
    if ($status -eq "running") {
        Write-Host "    ✅ $service" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  $service - $status" -ForegroundColor Yellow
    }
}

# Step 5: Test Wazuh API
Write-Host ""
Write-Host "[5/7] Testing Wazuh API connectivity..." -ForegroundColor Yellow
Start-Sleep -Seconds 10  # Give API time to fully start

try {
    $response = Invoke-RestMethod -Uri "https://localhost:55000/" `
        -Method Get `
        -Credential (New-Object System.Management.Automation.PSCredential("wazuh-wui", (ConvertTo-SecureString "MyS3cr37P450r.*-" -AsPlainText -Force))) `
        -SkipCertificateCheck `
        -ErrorAction Stop
    
    Write-Host "✅ Wazuh API is responding" -ForegroundColor Green
    Write-Host "    Version: $($response.data.api_version)" -ForegroundColor Gray
    Write-Host "    Hostname: $($response.data.hostname)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Wazuh API not ready yet (this is normal on first start)" -ForegroundColor Yellow
    Write-Host "    Try again in 30 seconds with: curl -k -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/" -ForegroundColor Gray
}

# Step 6: Check Ollama model
Write-Host ""
Write-Host "[6/7] Checking Ollama models..." -ForegroundColor Yellow
$ollamaModels = docker exec ollama-service ollama list 2>$null

if ($ollamaModels -like "*llama3.2*") {
    Write-Host "✅ Llama 3.2 model is installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Llama 3.2 model not found" -ForegroundColor Yellow
    Write-Host "    Run: docker exec -it ollama-service ollama pull llama3.2" -ForegroundColor Gray
}

# Step 7: Display access information
Write-Host ""
Write-Host "[7/7] Deployment Summary" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Service URLs:" -ForegroundColor Cyan
Write-Host "   • Streamlit App:     http://localhost:8501" -ForegroundColor White
Write-Host "   • Wazuh Dashboard:   https://localhost:443" -ForegroundColor White
Write-Host "   • Wazuh API:         https://localhost:55000" -ForegroundColor White
Write-Host "   • Metasploitable:    ssh://localhost:2222 (HTTP: :8080)" -ForegroundColor White
Write-Host ""
Write-Host "🔐 Default Credentials:" -ForegroundColor Cyan
Write-Host "   • Wazuh Dashboard:   admin / admin" -ForegroundColor White
Write-Host "   • Wazuh API:         wazuh-wui / MyS3cr37P450r.*-" -ForegroundColor White
Write-Host "   • Metasploitable:    msfadmin / msfadmin" -ForegroundColor White
Write-Host ""
Write-Host "📊 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Open Wazuh Dashboard: https://localhost:443" -ForegroundColor White
Write-Host "   2. Login with admin/admin" -ForegroundColor White
Write-Host "   3. Deploy agent to Metasploitable (see setup_wazuh.md)" -ForegroundColor White
Write-Host "   4. Open Streamlit App: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation: scripts/setup_wazuh.md" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
