# ================================================================
# Quick Test Script for Wazuh API Connection
# ================================================================
# This script tests the connection to the Wazuh API and displays
# basic information about the manager and registered agents.
#
# Usage: .\scripts\test_wazuh_connection.ps1
# ================================================================

Write-Host "🔍 Testing Wazuh API Connection" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$wazuhUrl = "https://localhost:55000"
$username = "wazuh-wui"
$password = "MyS3cr37P450r.*-"

# Create credentials
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($username, $securePassword)

# Test 1: Basic API Connection
Write-Host "[Test 1] Basic API Connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$wazuhUrl/" `
        -Method Get `
        -Credential $credential `
        -SkipCertificateCheck `
        -ErrorAction Stop
    
    Write-Host "✅ Connection successful!" -ForegroundColor Green
    Write-Host "   API Version: $($response.data.api_version)" -ForegroundColor Gray
    Write-Host "   Hostname: $($response.data.hostname)" -ForegroundColor Gray
    Write-Host "   License: $($response.data.license_name)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible issues:" -ForegroundColor Yellow
    Write-Host "   • Wazuh Manager not started yet (wait 30 more seconds)" -ForegroundColor Gray
    Write-Host "   • Docker container not running: docker ps | findstr wazuh-manager" -ForegroundColor Gray
    Write-Host "   • Check logs: docker logs wazuh-manager" -ForegroundColor Gray
    exit 1
}

# Test 2: List Agents
Write-Host "[Test 2] Listing Registered Agents..." -ForegroundColor Yellow
try {
    # Get JWT token first
    $authResponse = Invoke-RestMethod -Uri "$wazuhUrl/security/user/authenticate" `
        -Method Post `
        -Credential $credential `
        -SkipCertificateCheck `
        -ErrorAction Stop
    
    $token = $authResponse.data.token
    
    # Get agents
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    $agentsResponse = Invoke-RestMethod -Uri "$wazuhUrl/agents?select=id,name,ip,status,os.name" `
        -Method Get `
        -Headers $headers `
        -SkipCertificateCheck `
        -ErrorAction Stop
    
    $agents = $agentsResponse.data.affected_items
    
    if ($agents.Count -eq 0) {
        Write-Host "⚠️  No agents registered yet" -ForegroundColor Yellow
        Write-Host "   To register Metasploitable as an agent:" -ForegroundColor Gray
        Write-Host "   1. See scripts/setup_wazuh.md for instructions" -ForegroundColor Gray
        Write-Host "   2. Or run: bash scripts/deploy_agent_to_metasploitable.sh" -ForegroundColor Gray
    } else {
        Write-Host "✅ Found $($agents.Count) agent(s):" -ForegroundColor Green
        foreach ($agent in $agents) {
            $statusColor = if ($agent.status -eq "active") { "Green" } else { "Yellow" }
            Write-Host "   • $($agent.name) [$($agent.id)]" -ForegroundColor White
            Write-Host "     Status: $($agent.status) | IP: $($agent.ip) | OS: $($agent.os.name)" -ForegroundColor $statusColor
        }
    }
    Write-Host ""
} catch {
    Write-Host "⚠️  Could not fetch agents: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
}

# Test 3: Recent Alerts
Write-Host "[Test 3] Fetching Recent Alerts..." -ForegroundColor Yellow
try {
    $alertsResponse = Invoke-RestMethod -Uri "$wazuhUrl/alerts?limit=5&sort=-timestamp" `
        -Method Get `
        -Headers $headers `
        -SkipCertificateCheck `
        -ErrorAction Stop
    
    $alerts = $alertsResponse.data.affected_items
    
    if ($alerts.Count -eq 0) {
        Write-Host "ℹ️  No alerts in database yet" -ForegroundColor Cyan
        Write-Host "   Alerts will appear after:" -ForegroundColor Gray
        Write-Host "   • Deploying an agent to Metasploitable" -ForegroundColor Gray
        Write-Host "   • Simulating an attack (SSH brute force, port scan, etc.)" -ForegroundColor Gray
    } else {
        Write-Host "✅ Found $($alerts.Count) recent alert(s):" -ForegroundColor Green
        foreach ($alert in $alerts) {
            Write-Host "   • Rule $($alert.rule.id): $($alert.rule.description)" -ForegroundColor White
            Write-Host "     Level: $($alert.rule.level) | Agent: $($alert.agent.name) | Time: $($alert.timestamp)" -ForegroundColor Gray
        }
    }
    Write-Host ""
} catch {
    Write-Host "⚠️  Could not fetch alerts: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host ""
}

# Summary
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Wazuh API is operational and ready!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Deploy agent to Metasploitable (scripts/setup_wazuh.md)" -ForegroundColor White
Write-Host "   2. Open Streamlit App: http://localhost:8501" -ForegroundColor White
Write-Host "   3. Use 'get_real_wazuh_alerts' tool in your MCP client" -ForegroundColor White
Write-Host ""
