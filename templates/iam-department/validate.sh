#!/bin/bash
# IAM Department Template Validation Script
# Usage: ./validate.sh /path/to/target/repo
#
# This script validates that the IAM Department template was installed correctly
# and all placeholders have been replaced.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}IAM Department Template Validator${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check arguments
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 /path/to/target/repo${NC}"
    exit 1
fi

TARGET_DIR="$1"

# Validate target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Target directory does not exist: $TARGET_DIR${NC}"
    exit 1
fi

echo -e "${BLUE}Validating: $TARGET_DIR${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Check 1: Required directories
echo -e "${BLUE}[1/5] Checking required directories...${NC}"

REQUIRED_DIRS=(
    "agents"
    "agents/config"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$TARGET_DIR/$dir" ]; then
        echo -e "  ${GREEN}✓${NC} $dir exists"
    else
        echo -e "  ${RED}✗${NC} $dir missing"
        ((ERRORS++))
    fi
done
echo ""

# Check 2: Core files
echo -e "${BLUE}[2/5] Checking core files...${NC}"

CORE_FILES=(
    "agents/config/repos.yaml"
    "agents/shared_contracts/__init__.py"
)

for file in "${CORE_FILES[@]}"; do
    if [ -f "$TARGET_DIR/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file exists"
    elif [ -f "$TARGET_DIR/$file.template" ]; then
        echo -e "  ${YELLOW}!${NC} $file.template exists (rename to remove .template)"
        ((WARNINGS++))
    else
        echo -e "  ${YELLOW}?${NC} $file missing (optional)"
    fi
done
echo ""

# Check 3: Unresolved placeholders
echo -e "${BLUE}[3/5] Checking for unresolved placeholders...${NC}"

PLACEHOLDER_COUNT=$(grep -r "{{" "$TARGET_DIR/agents" 2>/dev/null | grep -v ".template:" | wc -l || echo "0")

if [ "$PLACEHOLDER_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No unresolved placeholders found"
else
    echo -e "  ${RED}✗${NC} Found $PLACEHOLDER_COUNT unresolved placeholders:"
    grep -rn "{{" "$TARGET_DIR/agents" 2>/dev/null | grep -v ".template:" | head -10
    ((ERRORS++))
fi
echo ""

# Check 4: .template files that should be renamed
echo -e "${BLUE}[4/5] Checking for .template files to rename...${NC}"

TEMPLATE_COUNT=$(find "$TARGET_DIR" -name "*.template" -type f 2>/dev/null | wc -l)

if [ "$TEMPLATE_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No .template files to rename"
else
    echo -e "  ${YELLOW}!${NC} Found $TEMPLATE_COUNT .template files to rename:"
    find "$TARGET_DIR" -name "*.template" -type f 2>/dev/null | head -10
    echo ""
    echo "  Run: find $TARGET_DIR -name '*.template' | while read f; do mv \"\$f\" \"\${f%.template}\"; done"
    ((WARNINGS++))
fi
echo ""

# Check 5: Python syntax validation
echo -e "${BLUE}[5/5] Validating Python syntax...${NC}"

SYNTAX_ERRORS=0
for py_file in $(find "$TARGET_DIR/agents" -name "*.py" -type f 2>/dev/null); do
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        : # Silent success
    else
        echo -e "  ${RED}✗${NC} Syntax error in: $py_file"
        ((SYNTAX_ERRORS++))
    fi
done

if [ "$SYNTAX_ERRORS" -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} All Python files have valid syntax"
else
    echo -e "  ${RED}✗${NC} Found $SYNTAX_ERRORS files with syntax errors"
    ((ERRORS++))
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Customize agent system prompts for your product"
    echo "2. Implement product-specific tools"
    echo "3. Configure repos.yaml with your repositories"
    echo "4. Run: make check-arv-minimum"
    exit 0
elif [ "$ERRORS" -eq 0 ]; then
    echo -e "${YELLOW}Passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Address warnings and run validation again."
    exit 0
else
    echo -e "${RED}Failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Fix errors and run validation again."
    exit 1
fi
