#!/usr/bin/env python3
"""
Bob's Brain Version Selector
Interactive tool to explore and run different Bob versions
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class BobVersionSelector:
    """Interactive version selector for Bob's Brain"""

    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.versions_dir = self.root_dir / "versions"

        self.versions = {
            "1": {
                "name": "v1-basic",
                "title": "Basic Bob",
                "description": "Simple CLI interface with ChromaDB knowledge base",
                "features": [
                    "Local CLI interface",
                    "ChromaDB integration",
                    "Basic conversation",
                    "Knowledge retrieval",
                ],
                "run_command": "python3 run_bob.py",
                "requirements": ["chromadb", "python-dotenv"],
            },
            "2": {
                "name": "v2-unified",
                "title": "Unified Bob v2",
                "description": "Professional Slack bot with enterprise features",
                "features": [
                    "Slack integration",
                    "Duplicate response prevention",
                    "Smart conversation memory",
                    "970+ knowledge items",
                    "Professional communication",
                ],
                "run_command": "python3 bob_unified_v2.py",
                "requirements": ["slack_sdk", "chromadb", "python-dotenv"],
            },
            "current": {
                "name": "current",
                "title": "Current Version (Symlink)",
                "description": "Points to the latest stable version",
                "features": ["Same as v2-unified"],
                "run_command": "python3 bob_unified_v2.py",
                "requirements": ["slack_sdk", "chromadb", "python-dotenv"],
            },
        }

    def display_header(self):
        """Display welcome header"""
        print("\n" + "=" * 60)
        print("🤖 Bob's Brain - Version Selector")
        print("=" * 60)
        print("\nExplore Bob's evolution through different versions!")
        print("Each version represents a milestone in Bob's development.\n")

    def display_versions(self):
        """Display available versions"""
        print("Available Versions:")
        print("-" * 40)

        for key, version in self.versions.items():
            print(f"\n[{key}] {version['title']}")
            print(f"    {version['description']}")
            print("    Features:")
            for feature in version["features"]:
                print(f"      • {feature}")

    def check_requirements(self, version: Dict) -> bool:
        """Check if requirements are installed"""
        print(f"\nChecking requirements for {version['title']}...")

        missing = []
        for req in version["requirements"]:
            try:
                __import__(req.replace("-", "_"))
                print(f"  ✅ {req}")
            except ImportError:
                print(f"  ❌ {req} (missing)")
                missing.append(req)

        if missing:
            print(f"\n⚠️  Missing requirements: {', '.join(missing)}")
            install = input("Would you like to install them? (y/n): ").lower()
            if install == "y":
                self.install_requirements(missing)
                return True
            return False

        print("\n✅ All requirements satisfied!")
        return True

    def install_requirements(self, packages: List[str]):
        """Install missing packages"""
        print("\nInstalling requirements...")
        for package in packages:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=False)
        print("✅ Installation complete!")

    def setup_version(self, version: Dict):
        """Setup and run selected version"""
        version_path = self.versions_dir / version["name"]

        if not version_path.exists():
            print(f"\n❌ Version directory not found: {version_path}")
            return

        print(f"\n🚀 Setting up {version['title']}...")
        print(f"   Directory: {version_path}")

        # Check for .env file
        env_file = version_path / ".env"
        if not env_file.exists():
            template = self.root_dir / ".env.template"
            if template.exists():
                print("\n⚠️  No .env file found. Creating from template...")
                subprocess.run(["cp", str(template), str(env_file)], check=False)
                print(f"   Please edit: {env_file}")
                edit = input("Would you like to edit it now? (y/n): ").lower()
                if edit == "y":
                    editor = os.environ.get("EDITOR", "nano")
                    subprocess.run([editor, str(env_file)], check=False)

        # Run the version
        print(f"\n▶️  Running: {version['run_command']}")
        print("-" * 40)

        os.chdir(version_path)
        subprocess.run(version["run_command"].split(), check=False)

    def run_interactive(self):
        """Run interactive version selector"""
        self.display_header()

        while True:
            self.display_versions()

            print("\n" + "-" * 40)
            print("Options:")
            print("  [1-2] Select a version to run")
            print("  [c]   Use current version")
            print("  [d]   View detailed documentation")
            print("  [q]   Quit")

            choice = input("\nYour choice: ").lower().strip()

            if choice == "q":
                print("\n👋 Goodbye!")
                break

            elif choice == "d":
                self.show_documentation()

            elif choice in self.versions:
                version = self.versions[choice]
                if self.check_requirements(version):
                    self.setup_version(version)
                    break

            elif choice == "c":
                version = self.versions["current"]
                if self.check_requirements(version):
                    self.setup_version(version)
                    break

            else:
                print("\n❌ Invalid choice. Please try again.")

    def show_documentation(self):
        """Display documentation"""
        print("\n" + "=" * 60)
        print("📚 Bob's Brain Documentation")
        print("=" * 60)

        docs = [
            ("README.md", "General overview and setup"),
            ("CLAUDE.md", "Development guidance"),
            ("VERSIONS.md", "Version changelog"),
            ("docs/evolution.md", "Bob's evolution story"),
        ]

        for doc, description in docs:
            doc_path = self.root_dir / doc
            if doc_path.exists():
                print(f"\n✅ {doc}")
                print(f"   {description}")
                view = input("   View this file? (y/n): ").lower()
                if view == "y":
                    with open(doc_path) as f:
                        content = f.read()
                    print("\n" + content[:1000] + "...\n")
                    input("Press Enter to continue...")

    def run_docker(self, version_name: str):
        """Run version in Docker"""
        print(f"\n🐳 Running {version_name} in Docker...")
        docker_file = self.root_dir / "docker" / f"{version_name}.Dockerfile"

        if docker_file.exists():
            # Build image
            subprocess.run(
                [
                    "docker",
                    "build",
                    "-f",
                    str(docker_file),
                    "-t",
                    f"bobs-brain:{version_name}",
                    ".",
                ], check=False
            )

            # Run container
            subprocess.run(
                ["docker", "run", "-it", "--rm", f"bobs-brain:{version_name}"], check=False
            )
        else:
            print(f"❌ Docker file not found: {docker_file}")


def main():
    """Main entry point"""
    selector = BobVersionSelector()

    # Check for command line arguments
    if len(sys.argv) > 1:
        version_key = sys.argv[1]
        if version_key in selector.versions:
            version = selector.versions[version_key]
            if selector.check_requirements(version):
                selector.setup_version(version)
        else:
            print(f"❌ Unknown version: {version_key}")
            print(f"Available: {', '.join(selector.versions.keys())}")
    else:
        # Run interactive mode
        selector.run_interactive()


if __name__ == "__main__":
    main()
