#!/bin/bash
# Find ALL data across ALL projects for consolidation

echo "======================================"
echo "COMPLETE DATA INVENTORY"
echo "======================================"
echo ""

PROJECTS=(
    "perception-with-intent"
    "bobs-brain"
    "pipelinepilot-prod"
    "brightstream-news"
    "cost-plus-db"
    "hustleapp-production"
    "ccpi-web-app-prod"
)

TOTAL_SIZE=0
TOTAL_ITEMS=0

echo "Scanning all projects for data..."
echo ""

for PROJECT in "${PROJECTS[@]}"; do
    echo "=== PROJECT: $PROJECT ==="

    # List all buckets in project
    BUCKETS=$(gsutil ls -p $PROJECT 2>/dev/null)

    if [ -z "$BUCKETS" ]; then
        echo "  No buckets found or no access"
    else
        for BUCKET in $BUCKETS; do
            # Get bucket size and item count
            SIZE=$(gsutil du -sh $BUCKET 2>/dev/null | awk '{print $1}' || echo "0")

            # Skip if empty
            if [ "$SIZE" != "0" ] && [ "$SIZE" != "0 B" ]; then
                echo "  📦 ${BUCKET}"
                echo "     Size: $SIZE"

                # Sample content types
                TYPES=$(gsutil ls -r $BUCKET 2>/dev/null | head -100 | xargs -n1 basename 2>/dev/null | rev | cut -d. -f1 | rev | sort -u | head -5 | tr '\n' ',' || echo "unknown")
                echo "     Types: ${TYPES%,}"
            fi
        done
    fi
    echo ""
done

echo "======================================"
echo "DATA CONSOLIDATION TARGETS"
echo "======================================"
echo ""
echo "Priority data to move to Vertex AI Search:"
echo ""
echo "1. Documentation (*.md, *.txt, *.pdf)"
echo "2. Code examples (*.py, *.js, *.ts)"
echo "3. Configuration (*.json, *.yaml)"
echo "4. Research papers"
echo "5. ADK patterns"
echo ""
echo "Target: bob-vertex-agent-datastore (Vertex AI Search)"
echo "Current: 8,718 documents"
echo ""
echo "This will become the SINGLE source of truth for ALL agents!"