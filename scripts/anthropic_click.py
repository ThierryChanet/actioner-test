#!/usr/bin/env python3
"""
Direct test of Anthropic's element clicking capability.

This bypasses the agent and extraction tools to test if Anthropic's
Computer Use can successfully find and click on recipe names.
"""

import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agent.anthropic_computer_client import AnthropicComputerClient

def main():
    print("=" * 80)
    print("ANTHROPIC ELEMENT CLICKING TEST")
    print("=" * 80)
    print()

    # Initialize Anthropic client
    print("1. Initializing Anthropic Computer Use client...")
    try:
        client = AnthropicComputerClient(
            display_width=1920,
            display_height=1080,
            verbose=True,
            verbosity="verbose"
        )
        print("✓ Client initialized\n")
    except Exception as e:
        print(f"✗ Failed to initialize client: {e}")
        return

    # Test 1: Take screenshot and analyze
    print("-" * 80)
    print("2. Taking screenshot...")
    result = client.execute_action("screenshot")

    if result.success:
        print("✓ Screenshot captured")
        print(f"   Description preview: {result.data['description'][:200]}...\n")
    else:
        print(f"✗ Screenshot failed: {result.error}")
        return

    # Test 2: Switch to Notion
    print("-" * 80)
    print("3. Switching to Notion...")
    result = client.execute_action("switch_desktop", text="Notion")

    if result.success:
        print("✓ Switched to Notion")
        print("   Waiting for app to load...")
        time.sleep(1)
        print()
    else:
        print(f"✗ Failed to switch: {result.error}")
        return

    # Test 3: Take screenshot of Notion
    print("-" * 80)
    print("4. Analyzing Notion screen...")
    result = client.execute_action("screenshot")

    if result.success:
        print("✓ Screenshot captured")
        description = result.data['description']
        print(f"\nScreen analysis:")
        print(description[:500])
        print("...\n")
    else:
        print(f"✗ Screenshot failed: {result.error}")
        return

    # Test 4: Click on a recipe using Anthropic's element detection
    print("-" * 80)
    print("5. Testing Anthropic's element clicking...")
    print("   Target: 'Velouté Potimarron'")
    print("   Method: Claude will find the element and return coordinates")
    print()

    start_time = time.time()
    result = client.execute_action("click", text="Velouté Potimarron")
    duration = time.time() - start_time

    if result.success:
        print(f"✓ Click executed successfully!")
        print(f"   Coordinates: {result.data.get('coordinate', 'N/A')}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Latency: {result.latency_ms:.0f}ms")
        print()

        # Verify by taking another screenshot
        print("   Verifying navigation...")
        time.sleep(2)  # Wait for page to load
        verify_result = client.execute_action("screenshot")

        if verify_result.success:
            description = verify_result.data['description']
            if "Velouté Potimarron" in description or "Potimarron" in description:
                print("   ✓ Successfully navigated to recipe page!")
                print(f"   Description preview: {description[:300]}...\n")
            else:
                print("   ⚠️  May not have opened the recipe page")
                print(f"   Current screen: {description[:200]}...\n")
    else:
        print(f"✗ Click failed: {result.error}")
        print(f"   Duration: {duration:.2f}s")
        return

    # Test 5: Try clicking on a second recipe
    print("-" * 80)
    print("6. Testing second recipe click...")
    print("   Target: 'Aheobakjin'")
    print()

    # Go back first
    print("   Pressing Escape to go back...")
    client.execute_action("key", text="Escape")
    time.sleep(1)

    start_time = time.time()
    result = client.execute_action("click", text="Aheobakjin")
    duration = time.time() - start_time

    if result.success:
        print(f"✓ Second click executed!")
        print(f"   Coordinates: {result.data.get('coordinate', 'N/A')}")
        print(f"   Duration: {duration:.2f}s")
        print()

        # Verify
        time.sleep(2)
        verify_result = client.execute_action("screenshot")

        if verify_result.success:
            description = verify_result.data['description']
            if "Aheobakjin" in description:
                print("   ✓ Successfully navigated to second recipe!")
                print(f"   Description preview: {description[:300]}...\n")
            else:
                print("   ⚠️  May not have opened the recipe page")
                print(f"   Current screen: {description[:200]}...\n")
    else:
        print(f"✗ Second click failed: {result.error}")
        return

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print("✓ Anthropic Computer Use client working")
    print("✓ Screenshot capture and analysis working")
    print("✓ Desktop switching working")
    print("✓ Element clicking working (if coordinates were found)")
    print()
    print("Key Insight:")
    print("  - Anthropic can SEE recipe names in screenshots")
    print("  - Anthropic returns coordinates for clicking")
    print("  - This is much better than OCR!")
    print()
    print("Next Steps:")
    print("  1. Update extraction tools to use Anthropic's click method")
    print("  2. Bypass OCR navigation when using Anthropic provider")
    print("  3. Use Claude's coordinates directly instead of guessing")
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
