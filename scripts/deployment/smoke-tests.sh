#!/bin/bash
set -e

##############################################################################
# Entity CRUD Deployment Smoke Tests
#
# Automated smoke tests for entity CRUD functionality deployment.
# Tests critical API paths for all catalog entities.
#
# Usage:
#   ./scripts/deployment/smoke-tests.sh
#   API_URL=https://api.yourdomain.com ./scripts/deployment/smoke-tests.sh
#
# Environment Variables:
#   API_URL - Base URL for API (default: http://localhost:8000)
#
# Exit Codes:
#   0 - All tests passed
#   1 - One or more tests failed
##############################################################################

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
VERBOSE="${VERBOSE:-0}"
CLEANUP="${CLEANUP:-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Cleanup tracking
CREATED_ENTITIES=()

##############################################################################
# Utility Functions
##############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

log_failure() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_verbose() {
    if [ "$VERBOSE" -eq 1 ]; then
        echo -e "${NC}       $1"
    fi
}

# Execute HTTP request and check response
http_request() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local expected_status="$4"
    local description="$5"

    local url="${API_URL}${endpoint}"
    local response
    local http_code

    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$url" 2>&1)
    fi

    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')

    log_verbose "Request: $method $endpoint"
    log_verbose "Expected: $expected_status, Got: $http_code"

    if [ "$http_code" -eq "$expected_status" ]; then
        log_success "$description"
        echo "$response_body"
        return 0
    else
        log_failure "$description (Expected HTTP $expected_status, got $http_code)"
        log_verbose "Response: $response_body"
        return 1
    fi
}

# Track created entity for cleanup
track_entity() {
    local entity_type="$1"
    local entity_id="$2"
    CREATED_ENTITIES+=("$entity_type:$entity_id")
}

# Cleanup created test entities
cleanup_entities() {
    if [ "$CLEANUP" -eq 0 ]; then
        log_info "Skipping cleanup (CLEANUP=0)"
        return 0
    fi

    log_info "Cleaning up test entities..."

    for entity in "${CREATED_ENTITIES[@]}"; do
        IFS=':' read -r type id <<< "$entity"

        case "$type" in
            cpu)
                endpoint="/v1/catalog/cpus/$id"
                ;;
            gpu)
                endpoint="/v1/catalog/gpus/$id"
                ;;
            profile)
                endpoint="/v1/catalog/profiles/$id"
                ;;
            ports-profile)
                endpoint="/v1/catalog/ports-profiles/$id"
                ;;
            ram-spec)
                endpoint="/v1/catalog/ram-specs/$id"
                ;;
            storage-profile)
                endpoint="/v1/catalog/storage-profiles/$id"
                ;;
            *)
                log_warning "Unknown entity type: $type"
                continue
                ;;
        esac

        curl -s -X DELETE "${API_URL}${endpoint}" > /dev/null 2>&1
        log_verbose "Deleted $type:$id"
    done
}

# Extract ID from JSON response
extract_id() {
    echo "$1" | jq -r '.id'
}

##############################################################################
# Test Suites
##############################################################################

test_health_check() {
    log_info "Test Suite: Health Check"
    http_request "GET" "/health" "" 200 "API health endpoint responds" > /dev/null
}

test_cpu_crud() {
    log_info "Test Suite: CPU CRUD Operations"

    # List CPUs
    http_request "GET" "/v1/catalog/cpus?limit=10" "" 200 "List CPUs" > /dev/null

    # Get CPU detail (using first CPU)
    local cpu_list
    cpu_list=$(curl -s "${API_URL}/v1/catalog/cpus?limit=1")
    local cpu_id
    cpu_id=$(echo "$cpu_list" | jq -r '.[0].id')

    if [ -n "$cpu_id" ] && [ "$cpu_id" != "null" ]; then
        http_request "GET" "/v1/catalog/cpus/$cpu_id" "" 200 "Get CPU detail" > /dev/null

        # Update CPU (PATCH)
        local patch_data='{"notes":"Smoke test update"}'
        http_request "PATCH" "/v1/catalog/cpus/$cpu_id" "$patch_data" 200 "Update CPU (PATCH)" > /dev/null

        # Get CPU usage
        http_request "GET" "/v1/catalog/cpus/$cpu_id/listings?limit=10" "" 200 "Get CPU usage (listings)" > /dev/null
    else
        log_warning "No CPUs found in database for detailed testing"
    fi
}

test_gpu_crud() {
    log_info "Test Suite: GPU CRUD Operations"

    # List GPUs
    http_request "GET" "/v1/catalog/gpus?limit=10" "" 200 "List GPUs" > /dev/null

    # Get GPU detail (using first GPU)
    local gpu_list
    gpu_list=$(curl -s "${API_URL}/v1/catalog/gpus?limit=1")
    local gpu_id
    gpu_id=$(echo "$gpu_list" | jq -r '.[0].id')

    if [ -n "$gpu_id" ] && [ "$gpu_id" != "null" ]; then
        http_request "GET" "/v1/catalog/gpus/$gpu_id" "" 200 "Get GPU detail" > /dev/null

        # Update GPU (PATCH)
        local patch_data='{"notes":"Smoke test update"}'
        http_request "PATCH" "/v1/catalog/gpus/$gpu_id" "$patch_data" 200 "Update GPU (PATCH)" > /dev/null

        # Get GPU usage
        http_request "GET" "/v1/catalog/gpus/$gpu_id/listings?limit=10" "" 200 "Get GPU usage (listings)" > /dev/null
    else
        log_warning "No GPUs found in database for detailed testing"
    fi
}

test_profile_crud() {
    log_info "Test Suite: Profile CRUD Operations"

    # List Profiles
    http_request "GET" "/v1/catalog/profiles" "" 200 "List Profiles" > /dev/null

    # Get Profile detail (using first profile)
    local profile_list
    profile_list=$(curl -s "${API_URL}/v1/catalog/profiles?limit=1")
    local profile_id
    profile_id=$(echo "$profile_list" | jq -r '.[0].id')

    if [ -n "$profile_id" ] && [ "$profile_id" != "null" ]; then
        http_request "GET" "/v1/catalog/profiles/$profile_id" "" 200 "Get Profile detail" > /dev/null

        # Update Profile (PATCH)
        local patch_data='{"description":"Smoke test update"}'
        http_request "PATCH" "/v1/catalog/profiles/$profile_id" "$patch_data" 200 "Update Profile (PATCH)" > /dev/null

        # Get Profile usage
        http_request "GET" "/v1/catalog/profiles/$profile_id/listings?limit=10" "" 200 "Get Profile usage (listings)" > /dev/null
    else
        log_warning "No Profiles found in database for detailed testing"
    fi
}

test_ports_profile_crud() {
    log_info "Test Suite: PortsProfile CRUD Operations"

    # List PortsProfiles
    http_request "GET" "/v1/catalog/ports-profiles" "" 200 "List PortsProfiles" > /dev/null

    # Get PortsProfile detail (using first profile)
    local profile_list
    profile_list=$(curl -s "${API_URL}/v1/catalog/ports-profiles?limit=1")
    local profile_id
    profile_id=$(echo "$profile_list" | jq -r '.[0].id')

    if [ -n "$profile_id" ] && [ "$profile_id" != "null" ]; then
        http_request "GET" "/v1/catalog/ports-profiles/$profile_id" "" 200 "Get PortsProfile detail" > /dev/null

        # Update PortsProfile (PATCH)
        local patch_data='{"notes":"Smoke test update"}'
        http_request "PATCH" "/v1/catalog/ports-profiles/$profile_id" "$patch_data" 200 "Update PortsProfile (PATCH)" > /dev/null

        # Get PortsProfile usage
        http_request "GET" "/v1/catalog/ports-profiles/$profile_id/listings?limit=10" "" 200 "Get PortsProfile usage (listings)" > /dev/null
    else
        log_warning "No PortsProfiles found in database for detailed testing"
    fi
}

test_ram_spec_crud() {
    log_info "Test Suite: RamSpec CRUD Operations"

    # List RamSpecs
    http_request "GET" "/v1/catalog/ram-specs?limit=10" "" 200 "List RamSpecs" > /dev/null

    # Get RamSpec detail (using first spec)
    local spec_list
    spec_list=$(curl -s "${API_URL}/v1/catalog/ram-specs?limit=1")
    local spec_id
    spec_id=$(echo "$spec_list" | jq -r '.[0].id')

    if [ -n "$spec_id" ] && [ "$spec_id" != "null" ]; then
        http_request "GET" "/v1/catalog/ram-specs/$spec_id" "" 200 "Get RamSpec detail" > /dev/null

        # Update RamSpec (PATCH)
        local patch_data='{"notes":"Smoke test update"}'
        http_request "PATCH" "/v1/catalog/ram-specs/$spec_id" "$patch_data" 200 "Update RamSpec (PATCH)" > /dev/null

        # Get RamSpec usage
        http_request "GET" "/v1/catalog/ram-specs/$spec_id/listings?limit=10" "" 200 "Get RamSpec usage (listings)" > /dev/null
    else
        log_warning "No RamSpecs found in database for detailed testing"
    fi
}

test_storage_profile_crud() {
    log_info "Test Suite: StorageProfile CRUD Operations"

    # List StorageProfiles
    http_request "GET" "/v1/catalog/storage-profiles?limit=10" "" 200 "List StorageProfiles" > /dev/null

    # Get StorageProfile detail (using first profile)
    local profile_list
    profile_list=$(curl -s "${API_URL}/v1/catalog/storage-profiles?limit=1")
    local profile_id
    profile_id=$(echo "$profile_list" | jq -r '.[0].id')

    if [ -n "$profile_id" ] && [ "$profile_id" != "null" ]; then
        http_request "GET" "/v1/catalog/storage-profiles/$profile_id" "" 200 "Get StorageProfile detail" > /dev/null

        # Update StorageProfile (PATCH)
        local patch_data='{"notes":"Smoke test update"}'
        http_request "PATCH" "/v1/catalog/storage-profiles/$profile_id" "$patch_data" 200 "Update StorageProfile (PATCH)" > /dev/null

        # Get StorageProfile usage
        http_request "GET" "/v1/catalog/storage-profiles/$profile_id/listings?limit=10" "" 200 "Get StorageProfile usage (listings)" > /dev/null
    else
        log_warning "No StorageProfiles found in database for detailed testing"
    fi
}

test_fields_data_api() {
    log_info "Test Suite: Fields Data API"

    # List entities
    http_request "GET" "/v1/fields-data/entities" "" 200 "List available entities" > /dev/null

    # Get entity schemas
    http_request "GET" "/v1/fields-data/cpu/schema" "" 200 "Get CPU schema" > /dev/null
    http_request "GET" "/v1/fields-data/gpu/schema" "" 200 "Get GPU schema" > /dev/null
    http_request "GET" "/v1/fields-data/profile/schema" "" 200 "Get Profile schema" > /dev/null
}

##############################################################################
# Main Execution
##############################################################################

main() {
    echo "============================================================"
    echo "Entity CRUD Deployment Smoke Tests"
    echo "============================================================"
    echo ""
    log_info "API URL: $API_URL"
    log_info "Verbose: $VERBOSE"
    log_info "Cleanup: $CLEANUP"
    echo ""

    # Check dependencies
    if ! command -v curl &> /dev/null; then
        log_failure "curl is not installed"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_failure "jq is not installed"
        exit 1
    fi

    # Run test suites
    test_health_check
    test_cpu_crud
    test_gpu_crud
    test_profile_crud
    test_ports_profile_crud
    test_ram_spec_crud
    test_storage_profile_crud
    test_fields_data_api

    # Cleanup
    cleanup_entities

    # Summary
    echo ""
    echo "============================================================"
    echo "Test Summary"
    echo "============================================================"
    echo "Total Tests:  $TOTAL_TESTS"
    echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
    echo ""

    if [ "$FAILED_TESTS" -eq 0 ]; then
        echo -e "${GREEN}✅ All smoke tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}❌ Some tests failed. See details above.${NC}"
        exit 1
    fi
}

# Trap cleanup on exit
trap cleanup_entities EXIT

# Run main
main "$@"
