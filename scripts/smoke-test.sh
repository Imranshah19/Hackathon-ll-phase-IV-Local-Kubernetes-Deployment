#!/bin/bash
# =============================================================================
# Smoke Test Script for Todo App Deployment
# =============================================================================
# Verifies that the deployed application is functioning correctly
#
# Usage:
#   ./scripts/smoke-test.sh [BASE_URL]
#
# Examples:
#   ./scripts/smoke-test.sh https://todo.example.com
#   ./scripts/smoke-test.sh http://localhost:8000
# =============================================================================

set -e

# Configuration
BASE_URL="${1:-http://localhost:8000}"
TIMEOUT=10
RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

# HTTP request with retry
http_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected_status="$4"
    local retry=0

    while [ $retry -lt $RETRIES ]; do
        if [ -n "$data" ]; then
            response=$(curl -s -w "\n%{http_code}" -X "$method" \
                -H "Content-Type: application/json" \
                -d "$data" \
                --connect-timeout "$TIMEOUT" \
                "${BASE_URL}${endpoint}" 2>/dev/null || echo "000")
        else
            response=$(curl -s -w "\n%{http_code}" -X "$method" \
                --connect-timeout "$TIMEOUT" \
                "${BASE_URL}${endpoint}" 2>/dev/null || echo "000")
        fi

        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        if [ "$status_code" = "$expected_status" ]; then
            echo "$body"
            return 0
        fi

        ((retry++))
        sleep 2
    done

    echo "Expected $expected_status, got $status_code"
    return 1
}

# =============================================================================
# Test Functions
# =============================================================================

test_health_live() {
    log_info "Testing liveness endpoint..."
    if http_request "GET" "/health/live" "" "200" > /dev/null; then
        log_success "Liveness check passed"
    else
        log_error "Liveness check failed"
    fi
}

test_health_ready() {
    log_info "Testing readiness endpoint..."
    if http_request "GET" "/health/ready" "" "200" > /dev/null; then
        log_success "Readiness check passed"
    else
        log_error "Readiness check failed"
    fi
}

test_api_root() {
    log_info "Testing API root endpoint..."
    if http_request "GET" "/" "" "200" > /dev/null; then
        log_success "API root accessible"
    else
        log_error "API root not accessible"
    fi
}

test_openapi_docs() {
    log_info "Testing OpenAPI docs..."
    if http_request "GET" "/docs" "" "200" > /dev/null; then
        log_success "OpenAPI docs accessible"
    else
        log_error "OpenAPI docs not accessible"
    fi
}

test_metrics_endpoint() {
    log_info "Testing metrics endpoint..."
    if http_request "GET" "/metrics" "" "200" > /dev/null; then
        log_success "Metrics endpoint accessible"
    else
        log_error "Metrics endpoint not accessible (may not be enabled)"
    fi
}

test_auth_register() {
    log_info "Testing user registration..."
    local email="smoke-test-$(date +%s)@example.com"
    local response

    response=$(http_request "POST" "/api/auth/register" \
        "{\"email\":\"$email\",\"password\":\"SmokeTest123!\"}" "201" 2>&1)

    if echo "$response" | grep -q "access_token"; then
        log_success "User registration works"
    else
        log_error "User registration failed: $response"
    fi
}

test_tasks_unauthorized() {
    log_info "Testing tasks endpoint requires auth..."
    local response

    response=$(curl -s -w "\n%{http_code}" -X GET \
        "${BASE_URL}/api/tasks" 2>/dev/null || echo "000")
    status_code=$(echo "$response" | tail -n1)

    if [ "$status_code" = "401" ] || [ "$status_code" = "403" ]; then
        log_success "Tasks endpoint properly secured"
    else
        log_error "Tasks endpoint not properly secured (got $status_code)"
    fi
}

test_response_time() {
    log_info "Testing response time..."
    local start_time=$(date +%s%3N)

    curl -s -o /dev/null --connect-timeout "$TIMEOUT" "${BASE_URL}/health/live"

    local end_time=$(date +%s%3N)
    local duration=$((end_time - start_time))

    if [ "$duration" -lt 1000 ]; then
        log_success "Response time acceptable (${duration}ms)"
    else
        log_error "Response time too slow (${duration}ms)"
    fi
}

# =============================================================================
# Main
# =============================================================================

echo ""
echo "=============================================="
echo "  Todo App Smoke Tests"
echo "=============================================="
echo "  Target: $BASE_URL"
echo "  Timeout: ${TIMEOUT}s"
echo "  Retries: $RETRIES"
echo "=============================================="
echo ""

# Run tests
test_health_live
test_health_ready
test_api_root
test_openapi_docs
test_metrics_endpoint
test_auth_register
test_tasks_unauthorized
test_response_time

# Summary
echo ""
echo "=============================================="
echo "  Test Summary"
echo "=============================================="
echo -e "  ${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "  ${RED}Failed:${NC} $TESTS_FAILED"
echo "=============================================="

if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
fi
