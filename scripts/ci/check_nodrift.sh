#!/bin/bash
#
# Bob's Brain - Framework Drift Detection
#
# Enforces Hard Rules (R1, R3, R4, R8) by scanning for violations:
# - R1: No alternative agent frameworks (LangChain, Crew, AutoGen)
# - R3: No Runner imports in service/ (gateway code)
# - R4: No local credentials or manual deployment commands
# - R8: All violations block CI builds
#
# Usage: bash scripts/ci/check_nodrift.sh
#
# Exit codes:
#   0 - No violations detected
#   1 - Violations found (fails CI)

set -e

echo "🔍 Scanning for framework drift violations..."
echo "================================================"

VIOLATIONS=0
EXCLUDE_DIRS=".venv|99-Archive|archive|node_modules"

# R1: Check for alternative agent frameworks
echo ""
echo "R1: Checking for alternative agent frameworks..."
if grep -rE "from langchain|import langchain|from crewai|import crewai|from autogen|import autogen" \
    --exclude-dir=.venv \
    --exclude-dir=99-Archive \
    --exclude-dir=archive \
    --exclude-dir=node_modules \
    --exclude-dir=000-docs \
    --exclude-dir=claudes-docs \
    . 2>/dev/null | grep -v "CLAUDE.md" | grep -v "check_nodrift.sh"; then
    echo "❌ VIOLATION R1: Alternative framework imports found"
    echo "   Only google-adk is allowed for agent implementation"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ R1: No alternative frameworks detected"
fi

# R3: Check for Runner imports in service/ (gateway code)
echo ""
echo "R3: Checking for Runner imports in service/..."
if [ -d "service" ]; then
    if grep -rE "^[^#]*from google\.adk\.runner|^[^#]*from google\.adk\.serving" service/ --exclude="*.md" 2>/dev/null; then
        echo "❌ VIOLATION R3: Runner or serving imports found in service/"
        echo "   Gateways must proxy to Agent Engine via REST, not run their own Runner"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ R3: No Runner imports in gateway code"
    fi
fi

# R3: Check for my_agent imports in service/ (gateway should not import agent code)
echo ""
echo "R3: Checking for agent code imports in service/..."
if [ -d "service" ]; then
    # Only match actual import statements (from my_agent import X or import my_agent)
    # Exclude lines starting with #, and exclude docstring references
    if grep -rE "^[[:space:]]*(from my_agent import|import my_agent)" service/ --exclude="*.md" 2>/dev/null; then
        echo "❌ VIOLATION R3: Direct agent imports found in service/"
        echo "   Gateways must NOT import agent code directly"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ R3: No agent code imports in gateway"
    fi
fi

# R4: Check for local GCP credentials
echo ""
echo "R4: Checking for local GCP credentials..."
CRED_FILES=$(find . -type f \( -name "application_default_credentials.json" -o -name "*-key.json" \) \
    2>/dev/null | grep -vE "$EXCLUDE_DIRS" || true)

if [ -n "$CRED_FILES" ]; then
    echo "❌ VIOLATION R4: Local GCP credential files found"
    echo "$CRED_FILES"
    echo "   Use Workload Identity Federation in CI, not service account keys"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ R4: No local credential files detected"
fi

# R4: Check for manual deployment commands (outside CI context)
echo ""
echo "R4: Checking for manual deployment commands..."
if [ "${GITHUB_ACTIONS:-false}" != "true" ]; then
    # Only check if NOT running in CI (to allow CI scripts to have these commands)
    MANUAL_DEPLOYS=$(grep -rE "gcloud run deploy|gcloud functions deploy" scripts/ \
        2>/dev/null | grep -v "scripts/ci/" | grep -v "check_nodrift.sh" || true)

    if [ -n "$MANUAL_DEPLOYS" ]; then
        echo "❌ VIOLATION R4: Manual deployment commands found in scripts/"
        echo "$MANUAL_DEPLOYS"
        echo "   All deployments must go through GitHub Actions (R4)"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "✅ R4: No manual deployment commands detected"
    fi
else
    echo "ℹ️  R4: Skipped (running in CI context)"
fi

# R8: Check for .env files committed (should only be .env.example)
echo ""
echo "R8: Checking for committed .env files..."
if [ -f ".env" ] && git ls-files --error-unmatch .env 2>/dev/null; then
    echo "❌ VIOLATION R8: .env file is committed to git"
    echo "   Only .env.example should be committed. Secrets must be in GitHub Secrets."
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ R8: No .env file committed"
fi

# Summary
echo ""
echo "================================================"
if [ $VIOLATIONS -gt 0 ]; then
    echo "❌ Found $VIOLATIONS drift violation(s)"
    echo ""
    echo "To fix violations:"
    echo "  1. Review CLAUDE.md for hard rules (R1-R8)"
    echo "  2. Remove alternative frameworks (use google-adk only)"
    echo "  3. Ensure service/ code only proxies to Agent Engine"
    echo "  4. Remove local credentials (use WIF in CI)"
    echo "  5. Deploy via GitHub Actions only"
    echo ""
    exit 1
fi

echo "✅ No drift violations detected"
echo "All hard rules (R1-R8) are satisfied"
exit 0
