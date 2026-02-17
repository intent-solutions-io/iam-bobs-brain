#!/usr/bin/env python3
"""
Org Storage Readiness Check (LIVE1-GCS)

Checks if org-wide knowledge hub storage is properly configured and accessible.
Run this before enabling org storage writes to ensure everything is set up correctly.

Usage:
    python3 scripts/check_org_storage_readiness.py
    python3 scripts/check_org_storage_readiness.py --env dev
    python3 scripts/check_org_storage_readiness.py --write-test  # Attempt test write
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path(__file__).parent.parent / "agents"))

from config.storage import (
    get_org_storage_bucket,
    is_org_storage_write_enabled,
)


def check_environment_variables():
    """Check if required environment variables are set."""
    print("\n" + "=" * 70)
    print("ENVIRONMENT VARIABLES")
    print("=" * 70)

    bucket = get_org_storage_bucket()
    write_enabled = is_org_storage_write_enabled()

    print(f"ORG_STORAGE_BUCKET: {bucket or '(not set)'}")
    print(f"ORG_STORAGE_WRITE_ENABLED: {write_enabled}")

    if not bucket:
        print("\n⚠️  WARNING: ORG_STORAGE_BUCKET not set")
        print("   Set with: export ORG_STORAGE_BUCKET=intent-org-knowledge-hub-{env}")
        return False

    if not write_enabled:
        print("\n📊 INFO: Org storage writes are DISABLED")
        print("   Enable with: export ORG_STORAGE_WRITE_ENABLED=true")
        return False

    print("\n✅ Environment variables configured correctly")
    return True


def check_gcs_library():
    """Check if google-cloud-storage library is installed."""
    print("\n" + "=" * 70)
    print("GCS CLIENT LIBRARY")
    print("=" * 70)

    try:
        from google.cloud import storage  # noqa: F401
        print("✅ google-cloud-storage is installed")
        return True
    except ImportError:
        print("❌ google-cloud-storage is NOT installed")
        print("   Install with: pip install google-cloud-storage")
        return False


def check_gcp_credentials():
    """Check if GCP credentials are available."""
    print("\n" + "=" * 70)
    print("GCP CREDENTIALS")
    print("=" * 70)

    # Check for Application Default Credentials
    adc_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if adc_path:
        print(f"GOOGLE_APPLICATION_CREDENTIALS: {adc_path}")
        if os.path.exists(adc_path):
            print("✅ Service account key file exists")
        else:
            print("❌ Service account key file not found")
            return False
    else:
        print("GOOGLE_APPLICATION_CREDENTIALS: (not set)")
        print("   Using Application Default Credentials (ADC)")
        print("   ADC will be used if available (e.g., from gcloud auth)")

    return True


def check_bucket_access():
    """Check if GCS bucket exists and is accessible."""
    print("\n" + "=" * 70)
    print("BUCKET ACCESS")
    print("=" * 70)

    bucket_name = get_org_storage_bucket()
    if not bucket_name:
        print("⚠️  Cannot check bucket access (ORG_STORAGE_BUCKET not set)")
        return False

    try:
        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Check if bucket exists
        if bucket.exists():
            print(f"✅ Bucket exists: gs://{bucket_name}/")

            # Try to list objects (tests read permissions)
            try:
                blobs = list(bucket.list_blobs(max_results=1))
                print(f"✅ Read access confirmed ({len(blobs)} object(s) found)")
            except Exception as e:
                print(f"⚠️  Read access test failed: {e}")

            return True
        else:
            print(f"❌ Bucket does NOT exist: gs://{bucket_name}/")
            print("   Create bucket with Terraform or gcloud:")
            print(f"   gcloud storage buckets create gs://{bucket_name}/ --location=US")
            return False

    except Exception as e:
        print(f"❌ Failed to check bucket access: {e}")
        print("   Check credentials and network connectivity")
        return False


def test_write_permissions():
    """Test write permissions by creating a test file."""
    print("\n" + "=" * 70)
    print("WRITE PERMISSIONS TEST")
    print("=" * 70)

    bucket_name = get_org_storage_bucket()
    if not bucket_name:
        print("⚠️  Cannot test write (ORG_STORAGE_BUCKET not set)")
        return False

    try:
        import json

        from google.cloud import storage

        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Create test file path
        test_path = f"_readiness_check/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        test_data = {
            "test": "org_storage_readiness_check",
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }

        # Upload test file
        blob = bucket.blob(test_path)
        blob.upload_from_string(
            json.dumps(test_data, indent=2),
            content_type="application/json"
        )

        print("✅ Write access confirmed")
        print(f"   Test file created: gs://{bucket_name}/{test_path}")

        # Clean up test file
        try:
            blob.delete()
            print("✅ Test file deleted successfully")
        except Exception as e:
            print(f"⚠️  Failed to delete test file: {e}")

        return True

    except Exception as e:
        print(f"❌ Write test failed: {e}")
        print("   Check IAM permissions for this service account")
        print("   Required role: roles/storage.objectAdmin")
        return False


def main():
    """Main readiness check entry point."""
    parser = argparse.ArgumentParser(
        description="Check org-wide storage configuration and readiness"
    )
    parser.add_argument(
        "--env",
        type=str,
        default=os.getenv("ENV", "dev"),
        help="Environment (dev, staging, prod). Default: dev"
    )
    parser.add_argument(
        "--write-test",
        action="store_true",
        help="Perform write test (creates and deletes test file)"
    )

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("ORG STORAGE READINESS CHECK (LIVE1-GCS)")
    print("=" * 70)
    print(f"Environment: {args.env}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all checks
    checks = {
        "Environment Variables": check_environment_variables(),
        "GCS Client Library": check_gcs_library(),
        "GCP Credentials": check_gcp_credentials(),
        "Bucket Access": check_bucket_access(),
    }

    # Optional write test
    if args.write_test:
        checks["Write Permissions"] = test_write_permissions()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    for check_name, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<50} {status}")

    print(f"\n{passed}/{total} checks passed")

    if passed == total:
        print("\n🎉 Org storage is READY for use!")
        print("   You can now enable writes with: export ORG_STORAGE_WRITE_ENABLED=true")
        sys.exit(0)
    else:
        print("\n⚠️  Org storage is NOT ready. Fix the failures above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
