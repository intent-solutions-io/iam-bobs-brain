#!/usr/bin/env bash
set -euo pipefail

REPO="intent-solutions-io/bobs-brain"
DEFAULT_BRANCH="main"
ARCHIVE_PREFIX="archive"

echo ">>> Branch cleanup for ${REPO}"
echo ">>> Default branch: ${DEFAULT_BRANCH}"
echo ">>> Archive tag prefix: ${ARCHIVE_PREFIX}/<branch-name>"
echo

# Ensure we're on the default branch and up to date
git checkout "${DEFAULT_BRANCH}"
git fetch origin
git pull origin "${DEFAULT_BRANCH}"

echo ">>> Listing remote branches (excluding ${DEFAULT_BRANCH})..."
BRANCHES=$(git branch -r | sed 's#origin/##' | grep -v "^${DEFAULT_BRANCH}$" | grep -v "HEAD" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//' || true)

if [ -z "${BRANCHES}" ]; then
  echo "No non-main branches found. Nothing to do."
  exit 0
fi

echo "The following remote branches will be archived and then deleted:"
echo "${BRANCHES}"
echo
read -r -p "Type 'ARCHIVE' to continue: " CONFIRM
if [ "${CONFIRM}" != "ARCHIVE" ]; then
  echo "Aborting."
  exit 1
fi

# 1) Create archive tags for each branch tip
for BR in ${BRANCHES}; do
  TAG_NAME="${ARCHIVE_PREFIX}/${BR}"
  echo ">>> Creating tag ${TAG_NAME} from origin/${BR}..."
  git fetch origin "${BR}:${BR}" || true
  git tag -f "${TAG_NAME}" "origin/${BR}" || git tag -f "${TAG_NAME}" "${BR}"
done

echo ">>> Pushing archive tags to origin..."
git push origin --tags

# 2) Optionally create GitHub Releases for each tag (manual step later)

# 3) Delete remote branches
for BR in ${BRANCHES}; do
  echo ">>> Deleting remote branch origin/${BR}..."
  git push origin --delete "${BR}" || true
done

# 4) Prune local branches
echo ">>> Pruning local tracking branches..."
git fetch --prune

echo ">>> Branch cleanup complete."
echo "Archived tags:"
git tag | grep "^${ARCHIVE_PREFIX}/" || true

echo
echo "REMINDERS:"
echo "- Update 000-docs/ARCHIVED_BRANCHES.md with the list of archive/* tags."
echo "- In GitHub repo settings:"
echo "  * Make '${DEFAULT_BRANCH}' the default branch."
echo "  * Protect '${DEFAULT_BRANCH}'."
echo "  * Enable 'Automatically delete head branches' after merge."
