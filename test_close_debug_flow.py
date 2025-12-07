#!/usr/bin/env python3
"""Debug test with explicit screen switching and sound notifications."""

import sys
import os
import time
import base64
import subprocess
sys.path.insert(0, os.path.dirname(__file__))

from src.agent.anthropic_computer_client import AnthropicComputerClient

def play_sound():
    """Play notification sound for iTerm2 users."""
    try:
        # macOS system sound
        subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                      check=False, capture_output=True)
    except:
        print('\a')  # Terminal bell fallback

def main():
    print("="*60)
    print("DEBUG MODE: Testing Notion panel close with screen switching")
    print("="*60)

    client = AnthropicComputerClient()

    # Step 1: Switch to Notion
    print("\n[1] Switching to NOTION screen...")
    result = client.execute_action("switch_desktop", text="Notion")
    print(f"    Result: {result.success}")
    if not result.success:
        print(f"    ERROR: {result.error}")
        return
    time.sleep(2.0)

    # Step 2: Take BEFORE screenshot
    print("\n[2] Taking BEFORE screenshot (should show Notion)...")
    before_screenshot = client.take_screenshot(use_cache=False)
    with open("/tmp/debug_before.png", "wb") as f:
        f.write(base64.b64decode(before_screenshot))
    print("    Saved: /tmp/debug_before.png")

    # Verify we're on Notion
    print("\n[3] Verifying we're on Notion screen...")
    verify_prompt = "Is this a Notion application window? Answer YES or NO."
    response = client.client.messages.create(
        model=client.model,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": before_screenshot
                    }
                },
                {
                    "type": "text",
                    "text": verify_prompt
                }
            ]
        }]
    )
    is_notion = response.content[0].text.strip()
    print(f"    Claude says: {is_notion}")

    if not is_notion.upper().startswith("YES"):
        print("\n❌ ERROR: Not on Notion screen!")
        print("Switching back to terminal...")
        play_sound()
        return

    # Step 4: Check if right panel is open
    print("\n[4] Checking if right panel is open...")
    panel_prompt = "Is there a right sidebar/panel open in this Notion window showing recipe details? Answer YES or NO."
    response = client.client.messages.create(
        model=client.model,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": before_screenshot
                    }
                },
                {
                    "type": "text",
                    "text": panel_prompt
                }
            ]
        }]
    )
    has_panel = response.content[0].text.strip()
    print(f"    Claude says: {has_panel}")

    if not has_panel.upper().startswith("YES"):
        print("\n⚠️  No right panel open to close!")
        print("Switching back to terminal...")
        play_sound()
        return

    # Step 5: Press Escape
    print("\n[5] Pressing ESCAPE to close panel...")
    client.execute_action("key", text="Escape")
    time.sleep(1.5)

    # Step 6: Take AFTER screenshot
    print("\n[6] Taking AFTER screenshot...")
    after_screenshot = client.take_screenshot(use_cache=False)
    with open("/tmp/debug_after.png", "wb") as f:
        f.write(base64.b64decode(after_screenshot))
    print("    Saved: /tmp/debug_after.png")

    # Step 7: Verify result
    print("\n[7] Verifying panel closed...")
    verify_prompt = """Compare these images.

BEFORE should show: Notion with right panel open (showing recipe details)
AFTER should show: Notion with NO right panel (left database list full width)

Did the right panel close? Answer:
SUCCESS - Panel closed
FAILED - Panel still open
UNCLEAR - Can't determine"""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "BEFORE:"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": before_screenshot
                    }
                },
                {
                    "type": "text",
                    "text": "AFTER:"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": after_screenshot
                    }
                },
                {
                    "type": "text",
                    "text": verify_prompt
                }
            ]
        }]
    )

    result_text = response.content[0].text.strip()

    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(result_text)
    print("="*60)

    # Step 8: Switch back to terminal and notify user
    print("\n[8] Switching back to TERMINAL screen...")
    # Note: We don't have a direct "switch to terminal" action
    # But we can click on iTerm2 or terminal
    client.execute_action("switch_desktop", text="iTerm")
    time.sleep(1.0)

    print("\n🔔 PLAYING SOUND - Test complete, switched back to terminal")
    play_sound()

    if "SUCCESS" in result_text:
        print("\n✅ TEST PASSED - Panel closed successfully!")
    elif "FAILED" in result_text:
        print("\n❌ TEST FAILED - Panel still open")
    else:
        print("\n⚠️  TEST UNCLEAR - Check screenshots")

    print("\nScreenshots saved:")
    print("  BEFORE: /tmp/debug_before.png")
    print("  AFTER:  /tmp/debug_after.png")

if __name__ == "__main__":
    main()
