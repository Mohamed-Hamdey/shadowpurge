#!/usr/bin/env python3
"""
ShadowPurge Initialization Script

This script initializes a ShadowPurge project with configuration files,
platform registry, and test data. Run this script to set up your project.
"""

import os
import json
from pathlib import Path

def create_project_structure():
    """Create the basic ShadowPurge project structure."""
    directories = [
        "shadowpurge/core",
        "shadowpurge/discovery",
        "shadowpurge/deleter",
        "shadowpurge/ui",
        "data",
        "tests",
        "docs",
        "examples"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"[OK] Created directory: {directory}")

def create_init_files():
    """Create essential __init__.py files for Python packages."""
    packages = [
        "shadowpurge",
        "shadowpurge/core",
        "shadowpurge/discovery",
        "shadowpurge/deleter",
        "shadowpurge/ui"
    ]

    for package in packages:
        init_file = Path(f"{package}/__init__.py")
        init_file.write_text("")
        print(f"[OK] Created: {init_file}")

def create_platform_registry():
    """Create initial platform registry with popular platforms."""
    platforms = [
        {
            "name": "GitHub",
            "url_template": "https://github.com/{}",
            "category": "Developer",
            "deletion_url": "https://github.com/settings/admin",
            "removal_instructions": "Log in to GitHub, go to Settings > Account > Delete Account at the bottom of the page.",
            "automation_supported": True
        },
        {
            "name": "Twitter/X",
            "url_template": "https://twitter.com/{}",
            "category": "Social",
            "deletion_url": "https://twitter.com/settings/deactivate",
            "removal_instructions": "Go to Settings and privacy > Your account > Deactivate your account.",
            "automation_supported": True
        },
        {
            "name": "Reddit",
            "url_template": "https://www.reddit.com/user/{}",
            "category": "Social",
            "deletion_url": "https://www.reddit.com/settings/account",
            "removal_instructions": "Go to User Settings > Account and click Deactivate Account at the bottom.",
            "automation_supported": True
        },
        {
            "name": "Instagram",
            "url_template": "https://www.instagram.com/{}/",
            "category": "Social",
            "deletion_url": "https://www.instagram.com/accounts/remove/request/permanent/",
            "removal_instructions": "Log in and follow the permanent deletion request form.",
            "automation_supported": True
        },
        {
            "name": "LinkedIn",
            "url_template": "https://www.linkedin.com/in/{}",
            "category": "Social",
            "deletion_url": "https://www.linkedin.com/psettings/member-delete-profile",
            "removal_instructions": "Go to Privacy settings, scroll to bottom and click 'Delete your LinkedIn account'.",
            "automation_supported": False
        },
        {
            "name": "Facebook",
            "url_template": "https://www.facebook.com/{}",
            "category": "Social",
            "deletion_url": "https://www.facebook.com/settings",
            "removal_instructions": "Log in, go to Settings > Account Settings > Deactivate/Close your account at the bottom.",
            "automation_supported": False
        },
        {
            "name": "Twitch",
            "url_template": "https://www.twitch.tv/{}",
            "category": "Social",
            "deletion_url": "https://www.twitch.tv/settings/delete",
            "removal_instructions": "Go to Settings > Advanced > Delete Account, follow the confirmation process.",
            "automation_supported": True
        },
        {
            "name": "Spotify",
            "url_template": "https://open.spotify.com/user/{}",
            "category": "Entertainment",
            "deletion_url": "https://www.spotify.com/account/settings",
            "removal_instructions": "Log in, go to Account Settings and click Delete Account, follow the prompts.",
            "automation_supported": True
        },
        {
            "name": "Steam",
            "url_template": "https://steamcommunity.com/profiles/{}",
            "category": "Gaming",
            "deletion_url": "https://steamcommunity.com/profile/delete",
            "removal_instructions": "Log in, go to Profile settings, click Delete Account, complete the survey and verification.",
            "automation_supported": False
        }
    ]

    platform_data = {"platforms": platforms}

    with open("data/platforms.json", "w", encoding="utf-8") as f:
        json.dump(platform_data, f, indent=2, ensure_ascii=False)

    print("[OK] Created: data/platforms.json")

def create_example_script():
    """Create an example script to demonstrate ShadowPurge usage."""
    example_code = '''"""
Example script demonstrating ShadowPurge functionality.

This script shows how to use ShadowPurge to discover and manage digital footprints.
"""

import asyncio
from shadowpurge.discovery.engine import DiscoveryEngine
from shadowpurge.discovery.osint import OSINTScanner

async def example_discovery():
    """Example of discovering usernames across platforms."""
    print("=== ShadowPurge Discovery Example ===\\n")

    engine = DiscoveryEngine()
    targets = ["johndoe", "jane.smith", "tech.enthusiast"]

    for target in targets:
        print(f"\\nScanning for: {target}")
        results = await engine.scan(target)

        found = [r for r in results if r.get("found", False)]
        print(f"   Found {len(found)} active profiles")

        for result in found[:3]:
            print(f"   * {result['name']}: {result['url']}")

    print("\\n=== Discovery Complete ===\\n")

async def example_osint():
    """Example of email and phone footprint discovery."""
    print("=== ShadowPurge OSINT Example ===\\n")

    scanner = OSINTScanner()

    email = "test.user@example.com"
    print(f"Checking breach database for: {email}")
    breaches = await scanner.check_email_breaches(email)
    print(f"   Found {len(breaches)} breaches")

    phone = "+15551234567"
    print(f"\\nChecking phone footprint for: {phone}")
    phone_records = await scanner.check_phone_footprint(phone)
    print(f"   Found {len(phone_records)} public records")

    print("\\n=== OSINT Complete ===\\n")

def main():
    """Main example function."""
    print("ShadowPurge Usage Examples\\n")
    asyncio.run(example_discovery())
    asyncio.run(example_osint())

if __name__ == "__main__":
    main()
'''

    with open("examples/demo_shadowpurge.py", "w", encoding="utf-8") as f:
        f.write(example_code)

    print("[OK] Created: examples/demo_shadowpurge.py")

def create_requirements_files():
    """Create requirements files for development and production."""
    requirements = [
        "httpx>=0.25.0",
        "rich>=13.5.0",
        "questionary>=2.0.0",
        "pydantic>=2.4.0",
        "python-dotenv>=1.0.0",
        "playwright>=1.40.0"
    ]

    with open("requirements.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(requirements))

    print("[OK] Created: requirements.txt")

    dev_requirements = requirements + [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "black>=23.0.0",
        "flake8>=6.0.0",
        "mypy>=1.0.0"
    ]

    with open("requirements-dev.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(dev_requirements))

    print("[OK] Created: requirements-dev.txt")

def main():
    """Main initialization function."""
    print("ShadowPurge Initialization Script\\n")
    create_project_structure()
    create_init_files()
    create_platform_registry()
    create_example_script()
    create_requirements_files()
    print("\\n[OK] PROJECT INITIALIZATION COMPLETE!")

if __name__ == "__main__":
    main()
