#!/bin/bash
# ================================================================
# Wazuh Stack Health Check Script (Linux/WSL/Git Bash)
# ================================================================
# This script validates the Wazuh stack deployment and connectivity
# Run this after docker-compose up to ensure everything is working
#
# Usage: bash scripts/validate_deployment.sh
# ================================================================

echo "🔍 Wazuh Stack Validation Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Test 1: Docker is running
echo -e "${YELLOW}[Test 1]${NC} Checking Docker daemon..."
if docker ps &>/dev/null; then
    echo -e "${GREEN}✅ Docker is running${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "   Please start Docker Desktop"
    ((FAILED++))
    exit 1
fi
echo ""

# Test 2: All containers are running
echo -e "${YELLOW}[Test 2]${NC} Checking container status..."
EXPECTED_CONTAINERS=("wazuh-mcp-agent" "ollama-service" "metasploitable-target" "wazuh-manager" "wazuh-indexer" "wazuh-dashboard")
for container in "${EXPECTED_CONTAINERS[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        STATUS=$(docker inspect -f '{{.State.Status}}' "$container")
        if [ "$STATUS" == "running" ]; then
            echo -e "   ${GREEN}✅ $container ($STATUS)${NC}"
            ((PASSED++))
        else
            echo -e "   ${RED}❌ $container ($STATUS)${NC}"
            ((FAILED++))
        fi
    else
        echo -e "   ${RED}❌ $container (not found)${NC}"
        ((FAILED++))
    fi
done
echo ""

# Test 3: Network connectivity
echo -e "${YELLOW}[Test 3]${NC} Checking Docker network..."
if docker network inspect genai-enabled-socs-via-mcp-integration_soc_network &>/dev/null; then
    SUBNET=$(docker network inspect genai-enabled-socs-via-mcp-integration_soc_network -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}')
    echo -e "${GREEN}✅ Network exists (Subnet: $SUBNET)${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ Network not found${NC}"
    ((FAILED++))
fi
echo ""

# Test 4: Wazuh Manager API
echo -e "${YELLOW}[Test 4]${NC} Testing Wazuh API connectivity..."
sleep 2  # Give API time to respond
API_RESPONSE=$(curl -k -s -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/ 2>/dev/null)
if echo "$API_RESPONSE" | grep -q "api_version"; then
    API_VERSION=$(echo "$API_RESPONSE" | grep -o '"api_version":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ Wazuh API is responding (Version: $API_VERSION)${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Wazuh API not ready yet${NC}"
    echo "   This is normal on first start. Wait 30 seconds and try again."
    ((FAILED++))
fi
echo ""

# Test 5: Wazuh Indexer
echo -e "${YELLOW}[Test 5]${NC} Testing Wazuh Indexer..."
INDEXER_RESPONSE=$(curl -s http://localhost:9200/_cluster/health 2>/dev/null)
if echo "$INDEXER_RESPONSE" | grep -q "cluster_name"; then
    CLUSTER_STATUS=$(echo "$INDEXER_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ Wazuh Indexer is healthy (Status: $CLUSTER_STATUS)${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Wazuh Indexer not responding${NC}"
    ((FAILED++))
fi
echo ""

# Test 6: Ollama Service
echo -e "${YELLOW}[Test 6]${NC} Testing Ollama service..."
OLLAMA_RESPONSE=$(docker exec ollama-service ollama list 2>&1)
if echo "$OLLAMA_RESPONSE" | grep -q "llama3.2"; then
    echo -e "${GREEN}✅ Ollama is running with llama3.2 model${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  llama3.2 model not installed${NC}"
    echo "   Run: docker exec -it ollama-service ollama pull llama3.2"
    ((FAILED++))
fi
echo ""

# Test 7: Streamlit App
echo -e "${YELLOW}[Test 7]${NC} Testing Streamlit application..."
STREAMLIT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null)
if [ "$STREAMLIT_RESPONSE" == "200" ] || [ "$STREAMLIT_RESPONSE" == "301" ]; then
    echo -e "${GREEN}✅ Streamlit app is accessible${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Streamlit app not responding (HTTP $STREAMLIT_RESPONSE)${NC}"
    ((FAILED++))
fi
echo ""

# Test 8: Metasploitable SSH
echo -e "${YELLOW}[Test 8]${NC} Testing Metasploitable SSH..."
if timeout 2 bash -c 'cat < /dev/null > /dev/tcp/localhost/2222' 2>/dev/null; then
    echo -e "${GREEN}✅ Metasploitable SSH is accessible (port 2222)${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  Metasploitable SSH not responding${NC}"
    ((FAILED++))
fi
echo ""

# Test 9: Check for Wazuh Agents
echo -e "${YELLOW}[Test 9]${NC} Checking registered Wazuh agents..."
AGENTS_RESPONSE=$(curl -k -s -u wazuh-wui:MyS3cr37P450r.*- https://localhost:55000/agents 2>/dev/null)
if echo "$AGENTS_RESPONSE" | grep -q "total_affected_items"; then
    AGENT_COUNT=$(echo "$AGENTS_RESPONSE" | grep -o '"total_affected_items":[0-9]*' | grep -o '[0-9]*')
    if [ "$AGENT_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ $AGENT_COUNT agent(s) registered${NC}"
        ((PASSED++))
    else
        echo -e "${BLUE}ℹ️  No agents registered yet (this is normal)${NC}"
        echo "   Deploy agent to Metasploitable: see scripts/setup_wazuh.md"
        ((PASSED++))
    fi
else
    echo -e "${YELLOW}⚠️  Could not fetch agent list${NC}"
    ((FAILED++))
fi
echo ""

# Summary
echo "========================================"
echo -e "${BLUE}Validation Summary${NC}"
echo "========================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Your Wazuh stack is ready.${NC}"
    echo ""
    echo "Next Steps:"
    echo "1. Open Wazuh Dashboard: https://localhost:443 (admin/admin)"
    echo "2. Open Streamlit App: http://localhost:8501"
    echo "3. Deploy agent to Metasploitable (optional, for real alerts)"
    echo "4. Start simulating attacks!"
    echo ""
elif [ $FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠️  Minor issues detected. System is mostly functional.${NC}"
    echo "Check the warnings above and refer to WAZUH_SETUP_QUICKSTART.md"
    echo ""
else
    echo -e "${RED}❌ Major issues detected. Please check the errors above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "• Wait 60 seconds for services to initialize"
    echo "• Check logs: docker logs wazuh-manager"
    echo "• Restart: docker-compose restart"
    echo ""
fi

echo "Documentation:"
echo "• Quick Start: WAZUH_SETUP_QUICKSTART.md"
echo "• Full Guide: scripts/setup_wazuh.md"
echo "• Architecture: ARCHITECTURE.md"
echo ""
