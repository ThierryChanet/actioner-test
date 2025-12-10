#!/usr/bin/env python3
"""Interactive test to find the best way to close Notion panel."""

import sys
import os
import time
import subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient

def play_sound():
    """Play notification sound."""
    try:
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                      check=False, capture_output=True)
    except:
        print('\a')

def ask_user(question: str) -> str:
    """Ask user a question and get response."""
    play_sound()
    response = input(f"\n🔔 {question} (yes/no): ").strip().lower()
    return response

def main():
    print("="*60)
    print("INTERACTIVE TEST: Finding best way to close Notion panel")
    print("="*60)

    client = AnthropicComputerClient()

    # Step 1: Switch to Notion
    print("\n[1] Switching to Notion...")
    client.execute_action("switch_desktop", text="Notion")
    time.sleep(2.0)

    # Step 2: Take screenshot to analyze
    print("\n[2] Analyzing Notion screen...")
    screenshot = client.take_screenshot(use_cache=False)

    # Ask Claude to find potential close buttons
    analysis_prompt = """Analyze this Notion screenshot.

Describe this Notion screen in detail.

Is there a right sidebar/panel open? Answer YES or NO first.

If YES, identify ALL possible ways to close it:
   - Close button (X)
   - Chevron buttons (>, >>, ←)
   - Back buttons
   - Any other clickable elements

For EACH option, provide:
   - Description of the element
   - Approximate coordinates (x, y)
   - Confidence level (high/medium/low)

Format:
Panel open: YES/NO

OPTION 1: [description]
  Coordinates: (x, y)
  Confidence: [high/medium/low]

OPTION 2: [description]
  Coordinates: (x, y)
  Confidence: [high/medium/low]"""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": screenshot
                    }
                },
                {
                    "type": "text",
                    "text": analysis_prompt
                }
            ]
        }]
    )

    analysis = response.content[0].text.strip()
    print("\n" + "="*60)
    print("CLAUDE'S ANALYSIS:")
    print("="*60)
    print(analysis)
    print("="*60)

    if not ("YES" in analysis.upper() and "PANEL OPEN" in analysis.upper()):
        print("\n⚠️  No panel detected to close!")
        client.execute_action("switch_desktop", text="Terminal")
        play_sound()
        return

    # Step 3: Extract coordinates from analysis
    import re
    coord_pattern = r'Coordinates:\s*\((\d+),\s*(\d+)\)'
    coordinates = re.findall(coord_pattern, analysis)

    if coordinates:
        print(f"\n[3] Found {len(coordinates)} potential close options")

        # Try each coordinate
        for idx, (x, y) in enumerate(coordinates, 1):
            print(f"\n--- Testing Option {idx}: ({x}, {y}) ---")

            # Click the coordinate
            print(f"Clicking at ({x}, {y})...")
            client.execute_action("left_click", coordinate=(int(x), int(y)))
            time.sleep(2.0)

            # Switch back to terminal and ask user
            client.execute_action("switch_desktop", text="Terminal")
            time.sleep(1.0)

            result = ask_user(f"Did clicking ({x}, {y}) close the panel?")

            if result.startswith('y'):
                print(f"\n✅ SUCCESS! Clicking ({x}, {y}) works!")
                print(f"\nSolution: Click at coordinates ({x}, {y}) to close panel")
                play_sound()
                return
            else:
                print(f"   ❌ Clicking ({x}, {y}) didn't work")
                # Switch back to Notion for next attempt
                print("   Switching back to Notion for next attempt...")
                client.execute_action("switch_desktop", text="Notion")
                time.sleep(2.0)

    # Step 4: Try Escape key
    print("\n--- Testing Escape Key ---")
    print("Pressing Escape...")

    # Make sure we're on Notion
    client.execute_action("switch_desktop", text="Notion")
    time.sleep(2.0)

    client.execute_action("key", text="Escape")
    time.sleep(2.0)

    # Switch back and ask
    client.execute_action("switch_desktop", text="Terminal")
    time.sleep(1.0)

    result = ask_user("Did pressing Escape close the panel?")

    if result.startswith('y'):
        print("\n✅ SUCCESS! Escape key works!")
        print("\nSolution: Press Escape to close panel")
    else:
        print("\n❌ FAILED! None of the methods worked")
        print("\nPlease manually close the panel and let me know what worked")

    play_sound()

if __name__ == "__main__":
    main()
