#!/bin/bash
# SAFE Migration Plan - Wire Bob to datahub WITHOUT breaking existing search

set -e

echo "============================================"
echo "SAFE MIGRATION PLAN - NO BREAKAGE"
echo "============================================"
echo ""
echo "CURRENT STATE:"
echo "  - Bob uses: bob-vertex-agent-datastore (8,718 docs)"
echo "  - Location: bobs-brain project"
echo "  - Status: WORKING - DO NOT BREAK!"
echo ""
echo "MIGRATION APPROACH: GRADUAL WITH FALLBACK"
echo ""

# Step 1: TEST FIRST - Don't change production
echo "Phase 1: PARALLEL SETUP (Safe)"
echo "================================"
echo "1. Create datahub-intent project ✅"
echo "2. Set up NEW datastore there"
echo "3. Copy data to new location"
echo "4. Bob STILL uses old datastore"
echo "5. TEST new datastore separately"
echo ""

# Step 2: Add dual search capability
echo "Phase 2: DUAL SEARCH (With Fallback)"
echo "====================================="
cat << 'EOF'
# In Bob's search tools, add fallback:

def search_knowledge(query):
    try:
        # Try new datahub first
        results = search_datahub_datastore(query)
        if results:
            return results
    except:
        pass

    # FALLBACK to existing datastore
    return search_original_datastore(query)
EOF
echo ""

# Step 3: Update environment variables
echo "Phase 3: GRADUAL SWITCH"
echo "========================"
echo "Environment variables to update:"
echo ""
cat << 'EOF'
# In .env files - ADD but don't remove old ones:
VERTEX_SEARCH_DATASTORE_ID=bob-vertex-agent-datastore  # KEEP THIS
DATAHUB_DATASTORE_ID=universal-knowledge-store         # ADD THIS
DATAHUB_PROJECT_ID=datahub-intent                      # ADD THIS

# Feature flag to control which to use:
USE_DATAHUB=false  # Start with false, switch to true when ready
EOF
echo ""

# Step 4: Update Bob's tools
echo "Phase 4: UPDATE BOB'S TOOLS (Carefully)"
echo "========================================"
cat << 'EOF'
# In agents/shared_tools/custom_tools.py:

def get_vertex_search_tools():
    """Get search tools with datahub support."""

    use_datahub = os.getenv("USE_DATAHUB", "false") == "true"

    if use_datahub:
        # Use new datahub
        project_id = os.getenv("DATAHUB_PROJECT_ID", "datahub-intent")
        datastore_id = os.getenv("DATAHUB_DATASTORE_ID")
    else:
        # Use existing Bob datastore
        project_id = os.getenv("PROJECT_ID", "bobs-brain")
        datastore_id = os.getenv("VERTEX_SEARCH_DATASTORE_ID")

    return create_search_tool(project_id, datastore_id)
EOF
echo ""

# Step 5: Testing plan
echo "Phase 5: TESTING BEFORE SWITCH"
echo "==============================="
echo "1. Deploy with USE_DATAHUB=false (uses old datastore)"
echo "2. Test that Bob still works normally"
echo "3. Set USE_DATAHUB=true in dev environment only"
echo "4. Test search works with new datahub"
echo "5. Compare results between old and new"
echo "6. Only switch production when confident"
echo ""

echo "============================================"
echo "ROLLBACK PLAN (If anything breaks)"
echo "============================================"
echo "1. Set USE_DATAHUB=false immediately"
echo "2. Bob reverts to original datastore"
echo "3. No data lost, no downtime"
echo "4. Fix issues in datahub"
echo "5. Try again when ready"
echo ""

echo "============================================"
echo "COMMANDS TO EXECUTE (Safe order)"
echo "============================================"
echo ""
echo "# 1. Check current datastore (don't modify)"
echo "gcloud ai search datastores describe bob-vertex-agent-datastore \\"
echo "    --location=us --project=bobs-brain"
echo ""
echo "# 2. Create new datastore in datahub (separate)"
echo "gcloud ai search datastores create universal-knowledge-store \\"
echo "    --location=us \\"
echo "    --project=datahub-intent \\"
echo "    --type=unstructured"
echo ""
echo "# 3. Export data from old datastore (read-only)"
echo "gcloud ai search documents export \\"
echo "    --datastore=bob-vertex-agent-datastore \\"
echo "    --location=us \\"
echo "    --project=bobs-brain \\"
echo "    --gcs-uri=gs://datahub-intent/migration/export/"
echo ""
echo "# 4. Import to new datastore (doesn't affect old one)"
echo "gcloud ai search documents import \\"
echo "    --datastore=universal-knowledge-store \\"
echo "    --location=us \\"
echo "    --project=datahub-intent \\"
echo "    --gcs-uri=gs://datahub-intent/migration/export/"
echo ""

echo "============================================"
echo "SAFETY CHECKLIST"
echo "============================================"
echo "[ ] Old datastore still exists and unchanged"
echo "[ ] Bob can still search old datastore"
echo "[ ] New datastore created separately"
echo "[ ] Data copied (not moved) to new location"
echo "[ ] Feature flag controls which to use"
echo "[ ] Fallback mechanism in place"
echo "[ ] Tested in dev before production"
echo "[ ] Rollback takes < 30 seconds"
echo ""
echo "✅ This approach CANNOT break Bob!"