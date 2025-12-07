#!/usr/bin/env python3
"""Test different methods to close Notion panel and save screenshots."""

import sys
import os
import time
import base64
import subprocess
sys.path.insert(0, os.path.dirname(__file__))

from src.agent.anthropic_computer_client import AnthropicComputerClient

def play_sound():
    """Play notification sound."""
    try:
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                      check=False, capture_output=True)
    except:
        print('\a')

def save_screenshot(client, path):
    """Save screenshot to file."""
    screenshot = client.take_screenshot(use_cache=False)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(screenshot))
    print(f"   Saved: {path}")

def main():
    print("="*60)
    print("TESTING CLOSE METHODS: Will try clicking different locations")
    print("="*60)

    client = AnthropicComputerClient()

    # Methods to test
    methods = [
        ("Close button (X)", (1792, 16)),
        ("Chevron button", (1792, 82)),
        ("Escape key", None),
    ]

    for idx, (method_name, coords) in enumerate(methods, 1):
        print(f"\n{'='*60}")
        print(f"TEST {idx}: {method_name}")
        if coords:
            print(f"Coordinates: {coords}")
        print('='*60)

        # Switch to Notion
        print("\n[1] Switching to Notion...")
        client.execute_action("switch_desktop", text="Notion")
        time.sleep(2.0)

        # Take before screenshot
        print("[2] Taking BEFORE screenshot...")
        save_screenshot(client, f"/tmp/before_method_{idx}.png")

        # Apply method
        if coords:
            print(f"[3] Clicking at {coords}...")
            client.execute_action("left_click", coordinate=coords)
        else:
            print("[3] Pressing Escape...")
            client.execute_action("key", text="Escape")

        time.sleep(2.0)

        # Take after screenshot
        print("[4] Taking AFTER screenshot...")
        save_screenshot(client, f"/tmp/after_method_{idx}.png")

        # Switch back to terminal
        print("[5] Switching back to terminal...")
        client.execute_action("switch_desktop", text="iTerm")
        time.sleep(1.0)
        play_sound()

        print(f"\n✅ Test {idx} complete!")
        print(f"   BEFORE: /tmp/before_method_{idx}.png")
        print(f"   AFTER:  /tmp/after_method_{idx}.png")
        print("\n📋 Please check if the panel closed")

        # Wait before next test to let user check
        if idx < len(methods):
            print("\nWaiting 3 seconds before next test...")
            time.sleep(3)

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nScreenshots saved:")
    for idx in range(1, len(methods) + 1):
        print(f"\nMethod {idx}:")
        print(f"  BEFORE: /tmp/before_method_{idx}.png")
        print(f"  AFTER:  /tmp/after_method_{idx}.png")

    play_sound()

if __name__ == "__main__":
    main()
