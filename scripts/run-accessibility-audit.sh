#!/bin/bash

# Accessibility Audit Test Runner
# Runs automated accessibility tests and generates report

set -e

echo "🔍 Starting Accessibility Audit..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if web server is running
echo "📡 Checking if web server is running..."
if curl -s http://localhost:3020 > /dev/null; then
    echo -e "${GREEN}✓ Web server is running${NC}"
else
    echo -e "${RED}✗ Web server is NOT running${NC}"
    echo ""
    echo "Please start the web server with:"
    echo "  make web"
    echo "  or"
    echo "  pnpm --filter web dev"
    exit 1
fi

echo ""
echo "🧪 Running accessibility tests..."
echo ""

# Run accessibility audit tests
pnpm test:e2e tests/e2e/accessibility-audit.spec.ts --reporter=list

echo ""
echo "✅ Accessibility audit complete!"
echo ""
echo "📊 View detailed report:"
echo "  pnpm test:e2e:report"
echo ""
echo "📄 Review audit documentation:"
echo "  docs/testing/accessibility-audit-report.md"
echo "  docs/testing/accessibility-checklist.md"
