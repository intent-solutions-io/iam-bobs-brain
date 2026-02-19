#!/bin/bash
# Verify No Duplicate Data Across Buckets

set -e

echo "========================================="
echo "DUPLICATE DATA CHECK"
echo "========================================="
echo ""

MAIN_BUCKET="bobs-brain-knowledge"
TEMP_DIR="/tmp/bucket_inventory"

# Create temp directory for inventory
mkdir -p ${TEMP_DIR}

echo "Creating inventory of all buckets..."
echo ""

# Inventory each bucket
echo "1. Inventory of bobs-brain-knowledge:"
gsutil ls -r gs://bobs-brain-knowledge/** 2>/dev/null > ${TEMP_DIR}/knowledge.txt || echo "Empty or no access"
wc -l ${TEMP_DIR}/knowledge.txt 2>/dev/null || echo "0 files"

echo ""
echo "2. Inventory of bobs-brain-bob-vertex-agent-rag:"
gsutil ls -r gs://bobs-brain-bob-vertex-agent-rag/** 2>/dev/null > ${TEMP_DIR}/rag.txt || echo "Empty or no access"
wc -l ${TEMP_DIR}/rag.txt 2>/dev/null || echo "0 files"

echo ""
echo "3. Inventory of bobs-brain-adk-staging:"
gsutil ls -r gs://bobs-brain-adk-staging/** 2>/dev/null > ${TEMP_DIR}/staging.txt || echo "Empty or no access"
wc -l ${TEMP_DIR}/staging.txt 2>/dev/null || echo "0 files"

echo ""
echo "4. Inventory of bobs-brain-bob-vertex-agent-logs:"
gsutil ls -r gs://bobs-brain-bob-vertex-agent-logs/** 2>/dev/null > ${TEMP_DIR}/logs.txt || echo "Empty or no access"
wc -l ${TEMP_DIR}/logs.txt 2>/dev/null || echo "0 files"

echo ""
echo "========================================="
echo "CHECKING FOR DUPLICATES"
echo "========================================="
echo ""

# Extract just filenames (not full paths) and check for duplicates
cat ${TEMP_DIR}/*.txt 2>/dev/null | xargs -n1 basename 2>/dev/null | sort | uniq -d > ${TEMP_DIR}/duplicates.txt || true

if [ -s ${TEMP_DIR}/duplicates.txt ]; then
    echo "⚠️  WARNING: Potential duplicate filenames found:"
    cat ${TEMP_DIR}/duplicates.txt
else
    echo "✅ No duplicate filenames found across buckets"
fi

echo ""
echo "========================================="
echo "SIZE ANALYSIS"
echo "========================================="
echo ""

echo "Checking bucket sizes..."
echo ""

for bucket in bobs-brain-knowledge bobs-brain-bob-vertex-agent-rag bobs-brain-adk-staging bobs-brain-bob-vertex-agent-logs; do
    echo "Size of gs://${bucket}:"
    gsutil du -sh gs://${bucket} 2>/dev/null || echo "  Empty or no access"
    echo ""
done

echo "========================================="
echo "RECOMMENDATIONS"
echo "========================================="
echo ""
echo "1. Consolidate all data into gs://${MAIN_BUCKET}"
echo "2. Use organized subdirectories for different data types"
echo "3. Delete empty buckets after consolidation"
echo "4. Keep logs separate if they're auto-generated"
echo ""
echo "Total unique files to consolidate: $(cat ${TEMP_DIR}/*.txt 2>/dev/null | sort -u | wc -l)"

# Cleanup
rm -rf ${TEMP_DIR}