"""
Example script demonstrating ShadowPurge functionality.

This script shows how to use ShadowPurge to discover and manage digital footprints.
"""

import asyncio
from shadowpurge.discovery.engine import DiscoveryEngine
from shadowpurge.discovery.osint import OSINTScanner

async def example_discovery():
    """Example of discovering usernames across platforms."""
    print("=== ShadowPurge Discovery Example ===\n")

    engine = DiscoveryEngine()
    targets = ["johndoe", "jane.smith", "tech.enthusiast"]

    for target in targets:
        print(f"\nScanning for: {target}")
        results = await engine.scan(target)

        found = [r for r in results if r.get("found", False)]
        print(f"   Found {len(found)} active profiles")

        for result in found[:3]:
            print(f"   * {result['name']}: {result['url']}")

    print("\n=== Discovery Complete ===\n")

async def example_osint():
    """Example of email and phone footprint discovery."""
    print("=== ShadowPurge OSINT Example ===\n")

    scanner = OSINTScanner()

    email = "test.user@example.com"
    print(f"Checking breach database for: {email}")
    breaches = await scanner.check_email_breaches(email)
    print(f"   Found {len(breaches)} breaches")

    phone = "+15551234567"
    print(f"\nChecking phone footprint for: {phone}")
    phone_records = await scanner.check_phone_footprint(phone)
    print(f"   Found {len(phone_records)} public records")

    print("\n=== OSINT Complete ===\n")

def main():
    """Main example function."""
    print("ShadowPurge Usage Examples\n")
    asyncio.run(example_discovery())
    asyncio.run(example_osint())

if __name__ == "__main__":
    main()
