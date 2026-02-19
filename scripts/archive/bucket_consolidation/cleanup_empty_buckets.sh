#!/bin/bash
# Cleanup Empty Buckets - Run AFTER data is imported to Vertex AI Search

set -e

echo "============================================"
echo "BUCKET CLEANUP - REMOVE EMPTY BUCKETS"
echo "============================================"
echo ""
echo "⚠️  WARNING: This will DELETE buckets!"
echo "Only run AFTER verifying data is in Vertex AI Search"
echo ""

# Safety check
read -p "Have you verified all data is in bob-vertex-agent-datastore? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborting cleanup. Verify data first."
    exit 1
fi

echo ""
echo "Checking bucket contents one more time..."
echo ""

# Check each bucket is actually empty
for bucket in bobs-brain-knowledge bobs-brain-adk-staging bobs-brain-bob-vertex-agent-logs; do
    echo "Checking gs://${bucket}..."
    size=$(gsutil du -s gs://${bucket} 2>/dev/null | awk '{print $1}' || echo "0")

    if [ "$size" == "0" ]; then
        echo "  ✅ Empty (${size} bytes) - safe to delete"
    else
        echo "  ⚠️  NOT EMPTY (${size} bytes) - will skip"
    fi
done

echo ""
echo "Special check for RAG bucket (has data to migrate first):"
echo "gs://bobs-brain-bob-vertex-agent-rag..."
rag_size=$(gsutil du -sh gs://bobs-brain-bob-vertex-agent-rag 2>/dev/null || echo "unknown")
echo "  Size: ${rag_size}"
echo "  ⚠️  Import this to Vertex AI Search FIRST"

echo ""
read -p "Delete empty buckets now? (yes/no): " delete_confirm
if [ "$delete_confirm" != "yes" ]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Deleting empty buckets..."
echo ""

# Delete only if empty
for bucket in bobs-brain-knowledge bobs-brain-adk-staging bobs-brain-bob-vertex-agent-logs; do
    size=$(gsutil du -s gs://${bucket} 2>/dev/null | awk '{print $1}' || echo "0")

    if [ "$size" == "0" ]; then
        echo "Deleting gs://${bucket}..."
        gsutil rm -r gs://${bucket} && echo "  ✅ Deleted" || echo "  ❌ Failed to delete"
    else
        echo "Skipping gs://${bucket} (not empty)"
    fi
done

echo ""
echo "============================================"
echo "FINAL STATUS"
echo "============================================"
echo ""
echo "Remaining buckets:"
gsutil ls | grep "bobs-brain" || echo "None with 'bobs-brain' prefix"

echo ""
echo "✅ Empty buckets cleaned up"
echo "📊 All data should now be in: bob-vertex-agent-datastore"
echo ""
echo "Next step for RAG bucket:"
echo "1. Run: python3 import_to_vertex_search.py"
echo "2. Verify import in Vertex AI Search console"
echo "3. Then delete: gsutil rm -r gs://bobs-brain-bob-vertex-agent-rag"