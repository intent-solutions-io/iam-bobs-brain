#!/bin/bash
# IAM Department Template Installation Script
# Usage: ./install.sh /path/to/target/repo
#
# This script installs the IAM Department template into a new repository,
# replacing placeholders with your product-specific values.
#
# Prerequisites:
# - Target repo has basic Python setup
# - Git repository initialized
# - Write access to target directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}IAM Department Template Installer${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check arguments
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 /path/to/target/repo${NC}"
    echo ""
    echo "This script installs the IAM Department template into your repository."
    echo ""
    echo "Required parameters will be collected interactively:"
    echo "  - PRODUCT_NAME: lowercase product name (e.g., diagnosticpro)"
    echo "  - PRODUCT_DISPLAY_NAME: display name (e.g., DiagnosticPro)"
    echo "  - PROJECT_ID: GCP project ID"
    echo "  - LOCATION: GCP region (default: us-central1)"
    echo "  - REPO_OWNER: GitHub owner"
    echo "  - REPO_NAME: GitHub repository name"
    exit 1
fi

TARGET_DIR="$1"

# Validate target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Target directory does not exist: $TARGET_DIR${NC}"
    exit 1
fi

# Check if agents/ already exists
if [ -d "$TARGET_DIR/agents" ]; then
    echo -e "${YELLOW}Warning: agents/ directory already exists in target${NC}"
    read -p "Continue and merge? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

echo -e "${GREEN}Target directory: $TARGET_DIR${NC}"
echo ""

# Collect parameters
echo -e "${BLUE}Please provide the following parameters:${NC}"
echo ""

read -p "PRODUCT_NAME (lowercase, no spaces, e.g., diagnosticpro): " PRODUCT_NAME
read -p "PRODUCT_DISPLAY_NAME (e.g., DiagnosticPro): " PRODUCT_DISPLAY_NAME
read -p "PROJECT_ID (GCP project ID): " PROJECT_ID
read -p "LOCATION (GCP region, default: us-central1): " LOCATION
LOCATION=${LOCATION:-us-central1}
read -p "REPO_OWNER (GitHub owner): " REPO_OWNER
read -p "REPO_NAME (GitHub repo name): " REPO_NAME
read -p "ORCHESTRATOR_AGENT_NAME (default: ${PRODUCT_NAME}bot): " ORCHESTRATOR_AGENT_NAME
ORCHESTRATOR_AGENT_NAME=${ORCHESTRATOR_AGENT_NAME:-${PRODUCT_NAME}bot}
read -p "FOREMAN_AGENT_NAME (default: iam-senior-lead): " FOREMAN_AGENT_NAME
FOREMAN_AGENT_NAME=${FOREMAN_AGENT_NAME:-iam-senior-lead}

echo ""
echo -e "${BLUE}Configuration Summary:${NC}"
echo "  PRODUCT_NAME: $PRODUCT_NAME"
echo "  PRODUCT_DISPLAY_NAME: $PRODUCT_DISPLAY_NAME"
echo "  PROJECT_ID: $PROJECT_ID"
echo "  LOCATION: $LOCATION"
echo "  REPO_OWNER: $REPO_OWNER"
echo "  REPO_NAME: $REPO_NAME"
echo "  ORCHESTRATOR_AGENT_NAME: $ORCHESTRATOR_AGENT_NAME"
echo "  FOREMAN_AGENT_NAME: $FOREMAN_AGENT_NAME"
echo ""

read -p "Proceed with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo -e "${BLUE}Installing template...${NC}"

# Create directories
mkdir -p "$TARGET_DIR/agents/config"
mkdir -p "$TARGET_DIR/agents/shared_contracts"
mkdir -p "$TARGET_DIR/agents/a2a"
mkdir -p "$TARGET_DIR/agents/tools"
mkdir -p "$TARGET_DIR/agents/utils"
mkdir -p "$TARGET_DIR/agents/iam-foreman"
mkdir -p "$TARGET_DIR/agents/${ORCHESTRATOR_AGENT_NAME}"
mkdir -p "$TARGET_DIR/scripts"
mkdir -p "$TARGET_DIR/tests/data/synthetic_repo"

# Function to copy and replace
copy_and_replace() {
    local src="$1"
    local dest="$2"

    # Copy file
    cp "$src" "$dest"

    # Replace placeholders
    sed -i "s/{{PRODUCT_NAME}}/$PRODUCT_NAME/g" "$dest"
    sed -i "s/{{PRODUCT_DISPLAY_NAME}}/$PRODUCT_DISPLAY_NAME/g" "$dest"
    sed -i "s/{{PROJECT_ID}}/$PROJECT_ID/g" "$dest"
    sed -i "s/{{LOCATION}}/$LOCATION/g" "$dest"
    sed -i "s/{{REPO_OWNER}}/$REPO_OWNER/g" "$dest"
    sed -i "s/{{REPO_NAME}}/$REPO_NAME/g" "$dest"
    sed -i "s/{{ORCHESTRATOR_AGENT_NAME}}/$ORCHESTRATOR_AGENT_NAME/g" "$dest"
    sed -i "s/{{FOREMAN_AGENT_NAME}}/$FOREMAN_AGENT_NAME/g" "$dest"

    # Remove .template extension if present
    if [[ "$dest" == *.template ]]; then
        mv "$dest" "${dest%.template}"
        dest="${dest%.template}"
    fi

    echo "  Created: $dest"
}

# Copy template files
echo -e "${GREEN}Copying template files...${NC}"

# Core contracts
if [ -f "$SCRIPT_DIR/agents/shared_contracts/__init__.py.template" ]; then
    copy_and_replace "$SCRIPT_DIR/agents/shared_contracts/__init__.py.template" \
        "$TARGET_DIR/agents/shared_contracts/__init__.py.template"
fi

# Config
if [ -f "$SCRIPT_DIR/agents/config/repos.yaml.template" ]; then
    copy_and_replace "$SCRIPT_DIR/agents/config/repos.yaml.template" \
        "$TARGET_DIR/agents/config/repos.yaml.template"
fi

# Bob/Orchestrator
if [ -f "$SCRIPT_DIR/agents/bob/agent.py.template" ]; then
    copy_and_replace "$SCRIPT_DIR/agents/bob/agent.py.template" \
        "$TARGET_DIR/agents/${ORCHESTRATOR_AGENT_NAME}/agent.py.template"
fi
if [ -f "$SCRIPT_DIR/agents/bob/system-prompt.md.template" ]; then
    copy_and_replace "$SCRIPT_DIR/agents/bob/system-prompt.md.template" \
        "$TARGET_DIR/agents/${ORCHESTRATOR_AGENT_NAME}/system-prompt.md.template"
fi

# Foreman
if [ -f "$SCRIPT_DIR/agents/iam-foreman/orchestrator.py.template" ]; then
    copy_and_replace "$SCRIPT_DIR/agents/iam-foreman/orchestrator.py.template" \
        "$TARGET_DIR/agents/iam-foreman/orchestrator.py.template"
fi

# Makefile snippet
if [ -f "$SCRIPT_DIR/Makefile.snippet" ]; then
    echo ""
    echo -e "${YELLOW}Makefile targets available in: $SCRIPT_DIR/Makefile.snippet${NC}"
    echo "  Add these targets to your Makefile manually."
fi

echo ""
echo -e "${GREEN}Template installation complete!${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Review created files in $TARGET_DIR/agents/"
echo "2. Rename any .template extensions: find . -name '*.template' | while read f; do mv \"\$f\" \"\${f%.template}\"; done"
echo "3. Customize agent system prompts for your product domain"
echo "4. Implement product-specific tools"
echo "5. Run validation: ./validate.sh $TARGET_DIR"
echo "6. Run tests: cd $TARGET_DIR && make check-arv-minimum"
echo ""
echo -e "${GREEN}Done!${NC}"
