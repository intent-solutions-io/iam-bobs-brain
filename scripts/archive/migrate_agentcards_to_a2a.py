#!/usr/bin/env python3
"""
Migration script to update AgentCards to A2A Protocol v0.3.0 compliance.

Phase 1: Add missing required fields (backward compatible)
- Adds protocol_version, preferred_transport, provider, etc.
- Keeps existing custom fields for now
- Non-breaking additive changes only

Usage:
    python scripts/migrate_agentcards_to_a2a.py [--dry-run]
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict


def load_agentcard(path: Path) -> Dict[str, Any]:
    """Load an AgentCard JSON file."""
    with open(path) as f:
        return json.load(f)


def save_agentcard(path: Path, data: Dict[str, Any], dry_run: bool = False) -> None:
    """Save an AgentCard JSON file."""
    if dry_run:
        print(f"[DRY RUN] Would update: {path}")
        print(json.dumps(data, indent=2))
        print("-" * 60)
    else:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")  # Add trailing newline
        print(f"✅ Updated: {path}")


def migrate_agentcard_phase1(card: Dict[str, Any], agent_name: str) -> Dict[str, Any]:
    """
    Phase 1 migration: Add A2A v0.3.0 required fields.

    This is backward compatible - only adds new fields.
    """
    # Add protocol version
    if "protocol_version" not in card:
        card["protocol_version"] = "0.3.0"

    # Add transport settings
    if "preferred_transport" not in card:
        card["preferred_transport"] = "JSONRPC"

    # Add provider information
    if "provider" not in card:
        card["provider"] = {
            "organization": "Intent Solutions",
            "url": "https://intent.solutions",
        }

    # Add security fields (empty for now)
    if "security" not in card:
        card["security"] = None  # Will be list of security requirements when needed

    if "security_schemes" not in card:
        card["security_schemes"] = None  # Will be dict of schemes when needed

    # Add documentation URL
    if "documentation_url" not in card:
        card["documentation_url"] = "https://github.com/jeremylongshore/bobs-brain"

    # Add icon URL (null for now)
    if "icon_url" not in card:
        card["icon_url"] = None

    # Add extended card support flag
    if "supports_authenticated_extended_card" not in card:
        card["supports_authenticated_extended_card"] = False

    # Add additional interfaces (supporting both JSONRPC and potential future transports)
    if "additional_interfaces" not in card:
        # For now, just declare JSONRPC at the main URL
        card["additional_interfaces"] = [
            {
                "url": card.get("url", f"https://{agent_name}.intent.solutions"),
                "transport": "JSONRPC",
            }
        ]

    # Update capabilities structure if needed
    # Phase 1: Keep as array for backward compatibility
    # Phase 2 will convert to proper AgentCapabilities object

    # Fix skill field names (Phase 1.5 - low risk rename)
    if "skills" in card:
        for skill in card["skills"]:
            # Rename skill_id to id if present
            if "skill_id" in skill and "id" not in skill:
                skill["id"] = skill.pop("skill_id")

            # Add required tags field if missing
            if "tags" not in skill:
                # Generate tags from skill id
                skill_parts = skill.get("id", "").split(".")
                skill["tags"] = [part for part in skill_parts if part]

            # Add examples if missing
            if "examples" not in skill:
                skill["examples"] = []  # Will be populated in Phase 2

    # Ensure field ordering for readability
    ordered_card = {}

    # Core identity fields first
    field_order = [
        "protocol_version",
        "name",
        "version",
        "description",
        "url",
        "preferred_transport",
        "additional_interfaces",
        "provider",
        "documentation_url",
        "icon_url",
        "capabilities",
        "default_input_modes",
        "default_output_modes",
        "skills",
        "security",
        "security_schemes",
        "supports_authenticated_extended_card",
        "spiffe_id",  # Keep custom field at end for now
    ]

    for field in field_order:
        if field in card:
            ordered_card[field] = card[field]

    # Add any remaining fields not in our order list
    for field, value in card.items():
        if field not in ordered_card:
            ordered_card[field] = value

    return ordered_card


def find_agentcard_files() -> list[Path]:
    """Find all agent-card.json files in the agents directory."""
    agents_dir = Path(__file__).parent.parent / "agents"
    return list(agents_dir.glob("*/.well-known/agent-card.json"))


def main():
    """Run the migration."""
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
        print("=" * 60)

    # Find all AgentCard files
    card_files = find_agentcard_files()

    if not card_files:
        print("❌ No agent-card.json files found in agents/*/.well-known/")
        return 1

    print(f"Found {len(card_files)} AgentCard(s) to migrate")
    print("-" * 60)

    success_count = 0
    error_count = 0

    for card_path in card_files:
        agent_name = card_path.parent.parent.name
        print(f"\n📋 Processing: {agent_name}")

        try:
            # Load current card
            card = load_agentcard(card_path)

            # Check if already migrated
            if card.get("protocol_version") == "0.3.0":
                print("  ✓ Already at v0.3.0")
                success_count += 1
                continue

            # Migrate to Phase 1
            migrated_card = migrate_agentcard_phase1(card, agent_name)

            # Save updated card
            save_agentcard(card_path, migrated_card, dry_run=dry_run)
            success_count += 1

        except Exception as e:
            print(f"  ❌ Error: {e}")
            error_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 Migration Summary:")
    print(f"  ✅ Success: {success_count}")
    print(f"  ❌ Errors: {error_count}")

    if dry_run:
        print("\n⚠️  This was a dry run. Run without --dry-run to apply changes.")
    else:
        print("\n✨ Migration complete!")
        print("\nNext steps:")
        print("  1. Run tests: pytest tests/unit/test_agentcard_json.py")
        print("  2. Validate with A2A inspector (when available)")
        print(
            "  3. Commit changes: git add -A && git commit -m 'feat(agents): migrate AgentCards to A2A v0.3.0 Phase 1'"
        )

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
