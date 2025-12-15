#!/usr/bin/env python3
"""Debug script to test OPEN button detection and clicking."""

import sys
import time
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.agent.anthropic_computer_client import AnthropicComputerClient


def main():
    print("="*60)
    print("DEBUG: OPEN BUTTON COORDINATE TEST")
    print("="*60)

    # Initialize
    client = AnthropicComputerClient(verbose=True)

    # Calibrate Claude Vision dimensions
    print("\n1. Calibrating Claude Vision dimensions...")
    screenshot = client.take_screenshot(use_cache=False)
    client._detect_claude_vision_dimensions(screenshot)
    print(f"   Claude sees: {client._claude_vision_width}x{client._claude_vision_height}")
    print(f"   Actual screenshot: {client.pixel_width}x{client.pixel_height}")
    print(f"   Logical display: {client.logical_width}x{client.logical_height}")

    # Switch to Notion
    print("\n2. Switching to Notion...")
    client.execute_action("switch_desktop", text="Notion")
    time.sleep(2)

    # Press Escape to close any open dialogs
    print("\n3. Pressing Escape to close any dialogs...")
    client.execute_action("key", text="Escape")
    time.sleep(0.5)
    client.execute_action("key", text="Escape")
    time.sleep(1)

    # Take fresh screenshot
    print("\n4. Taking screenshot...")
    screenshot = client.take_screenshot(use_cache=False)

    # Save it
    with open("/tmp/debug_notion.png", "wb") as f:
        f.write(base64.b64decode(screenshot))
    print("   Saved to /tmp/debug_notion.png")

    # Find first recipe
    print("\n5. Finding first recipe on screen...")
    response = client.client.messages.create(
        model=client.model,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot}},
                {"type": "text", "text": """Find the FIRST recipe name in this Notion database.

Return:
RECIPE: <recipe name>
COORDINATES: (x, y) - center of the recipe name text"""}
            ]
        }],
        temperature=0
    )
    print(f"   Response: {response.content[0].text}")

    import re
    recipe_match = re.search(r'RECIPE:\s*(.+)', response.content[0].text)
    coord_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response.content[0].text)

    if not coord_match:
        print("   ERROR: Could not find recipe coordinates")
        client.execute_action("switch_desktop", text="iTerm")
        return

    recipe_name = recipe_match.group(1).strip() if recipe_match else "Unknown"
    claude_x = int(coord_match.group(1))
    claude_y = int(coord_match.group(2))

    print(f"\n   Recipe: {recipe_name}")
    print(f"   Claude coords: ({claude_x}, {claude_y})")

    # Scale to screenshot coords
    screenshot_x, screenshot_y = client._scale_claude_vision_coordinates(claude_x, claude_y)
    print(f"   Screenshot coords: ({screenshot_x}, {screenshot_y})")

    # Scale to logical coords for mouse
    move_x, move_y = client._scale_coordinates_for_click(screenshot_x, screenshot_y)
    print(f"   Logical/Move coords: ({move_x}, {move_y})")

    # Hover over the recipe
    print(f"\n6. Hovering over '{recipe_name}'...")
    client._execute_mouse_move(move_x, move_y)
    time.sleep(1)

    # Take screenshot to find OPEN button
    print("\n7. Taking screenshot to find OPEN button...")
    screenshot2 = client.take_screenshot(use_cache=False)

    with open("/tmp/debug_after_hover.png", "wb") as f:
        f.write(base64.b64decode(screenshot2))
    print("   Saved to /tmp/debug_after_hover.png")

    # Find OPEN button
    print("\n8. Finding OPEN button...")
    response2 = client.client.messages.create(
        model=client.model,
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": screenshot2}},
                {"type": "text", "text": f"""I hovered over "{recipe_name}". Find the "OPEN" button that appeared.

The OPEN button should be:
- On the SAME ROW as the recipe name
- Usually to the LEFT of the recipe name
- A small button with text "OPEN"

Return:
FOUND: YES or NO
COORDINATES: (x, y) - center of the OPEN button
Y_SAME_AS_RECIPE: YES or NO (is the Y coordinate close to the recipe's Y={claude_y}?)"""}
            ]
        }],
        temperature=0
    )
    print(f"   Response: {response2.content[0].text}")

    coord_match2 = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response2.content[0].text)

    if coord_match2:
        open_claude_x = int(coord_match2.group(1))
        open_claude_y = int(coord_match2.group(2))

        print(f"\n   OPEN button Claude coords: ({open_claude_x}, {open_claude_y})")

        # Check Y alignment
        y_diff = abs(open_claude_y - claude_y)
        print(f"   Y difference from recipe: {y_diff} pixels")

        # Scale
        open_screenshot_x, open_screenshot_y = client._scale_claude_vision_coordinates(open_claude_x, open_claude_y)
        print(f"   OPEN button screenshot coords: ({open_screenshot_x}, {open_screenshot_y})")

        open_click_x, open_click_y = client._scale_coordinates_for_click(open_screenshot_x, open_screenshot_y)
        print(f"   OPEN button click coords: ({open_click_x}, {open_click_y})")

        # Click the OPEN button
        print(f"\n9. Clicking OPEN button at ({open_click_x}, {open_click_y})...")
        client._execute_click(open_click_x, open_click_y)
        time.sleep(1.5)

        # Take final screenshot
        print("\n10. Taking screenshot after click...")
        screenshot3 = client.take_screenshot(use_cache=False)
        with open("/tmp/debug_after_click.png", "wb") as f:
            f.write(base64.b64decode(screenshot3))
        print("   Saved to /tmp/debug_after_click.png")

    # Switch back
    print("\n11. Switching back to iTerm...")
    client.execute_action("switch_desktop", text="iTerm")

    print("\n" + "="*60)
    print("DEBUG COMPLETE")
    print("="*60)
    print("\nCheck the screenshots:")
    print("  /tmp/debug_notion.png - Initial state")
    print("  /tmp/debug_after_hover.png - After hovering")
    print("  /tmp/debug_after_click.png - After clicking OPEN")


if __name__ == "__main__":
    main()
