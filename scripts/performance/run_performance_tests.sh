#!/bin/bash
# Quick runner for catalog API performance tests

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
BASE_URL="${API_URL:-http://localhost:8000}"
RUNS=20
ENTITY_TYPE=""
VERBOSE=""
OUTPUT="performance-results.json"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --runs)
            RUNS="$2"
            shift 2
            ;;
        --entity-type)
            ENTITY_TYPE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --output)
            OUTPUT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --base-url URL          API base URL (default: http://localhost:8000)"
            echo "  --runs N                Number of runs per test (default: 20)"
            echo "  --entity-type TYPE      Test specific entity type (cpu, gpu, profile, etc.)"
            echo "  --verbose              Enable verbose output"
            echo "  --output FILE          Output file (default: performance-results.json)"
            echo "  --help                 Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Run all tests"
            echo "  $0 --entity-type cpu                  # Test CPU endpoints only"
            echo "  $0 --runs 50 --verbose                # 50 runs with verbose output"
            echo "  $0 --base-url http://staging-api:8000 # Test staging environment"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Catalog API Performance Tests${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Configuration:"
echo "  Base URL: $BASE_URL"
echo "  Runs: $RUNS"
echo "  Entity Type: ${ENTITY_TYPE:-all}"
echo "  Output: $OUTPUT"
echo ""

# Check if API is accessible
echo -n "Checking API health... "
if curl -sf "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo ""
    echo -e "${YELLOW}API is not accessible at $BASE_URL${NC}"
    echo "Please start the API with:"
    echo "  make up    # Docker Compose stack"
    echo "  make api   # Local API server"
    exit 1
fi

# Build command
CMD="poetry run python scripts/performance/catalog_performance_test.py"
CMD="$CMD --base-url $BASE_URL"
CMD="$CMD --runs $RUNS"
CMD="$CMD --output $OUTPUT"

if [ -n "$ENTITY_TYPE" ]; then
    CMD="$CMD --entity-type $ENTITY_TYPE"
fi

if [ -n "$VERBOSE" ]; then
    CMD="$CMD --verbose"
fi

# Run tests
echo ""
echo "Running tests..."
echo ""

if $CMD; then
    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}✓ All tests completed successfully${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo "Results saved to: $OUTPUT"
    echo ""
    echo "View detailed results:"
    echo "  cat $OUTPUT | jq '.summary'"
    echo ""
    echo "Update documentation:"
    echo "  docs/testing/performance-validation-results.md"
    exit 0
else
    echo ""
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}======================================${NC}"
    echo ""
    echo "Results saved to: $OUTPUT"
    echo ""
    echo "Review failed tests:"
    echo "  cat $OUTPUT | jq '.results[] | select(.passed == false)'"
    exit 1
fi
