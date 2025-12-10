#!/usr/bin/env python3
"""Test closing panel by clicking neutral elements then pressing Escape."""

import sys
import os
import time
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient

def play_sound():
    try:
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                      check=False, capture_output=True)
    except:
        print('\a')

def main():
    print("="*60)
    print("TEST: Click neutral elements, then press Escape")
    print("="*60)

    client = AnthropicComputerClient()

    # Test different neutral click locations in the right panel
    # before pressing Escape
    test_locations = [
        ("Right panel background (middle)", (900, 400)),
        ("Right panel background (top)", (900, 200)),
        ("Right panel header area", (850, 100)),
        ("Right panel lower area", (900, 600)),
    ]

    for idx, (description, coords) in enumerate(test_locations, 1):
        print(f"\n{'='*60}")
        print(f"TEST {idx}: {description}")
        print(f"Click at {coords}, then press Escape")
        print('='*60)

        # Switch to Notion
        print("\n[1] Switching to Notion...")
        client.execute_action("switch_desktop", text="Notion")
        time.sleep(2)

        # Click neutral location to set focus
        print(f"[2] Clicking neutral location {coords}...")
        client.execute_action("left_click", coordinate=coords)
        time.sleep(0.5)

        # Press Escape
        print("[3] Pressing Escape...")
        client.execute_action("key", text="Escape")
        time.sleep(2)

        # Switch back to terminal
        print("[4] Switching back to terminal...")
        client.execute_action("switch_desktop", text="Terminal")
        time.sleep(1)
        play_sound()

        # Ask user if it worked
        print(f"\n📋 Did test {idx} close the panel?")
        print("   Check Notion to see if the right panel closed.")
        print("\nPress Enter when ready for next test...")
        try:
            input()
        except:
            print("(Continuing...)")
            time.sleep(2)

    print("\n" + "="*60)
    print("All tests complete!")
    print("="*60)
    play_sound()

if __name__ == "__main__":
    main()
