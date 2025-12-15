#!/usr/bin/env python3
"""Calibration setup for Claude Vision coordinate system using Notion.

This script tests coordinate calibration by:
1. Opening Notion
2. Taking a screenshot and identifying a clickable target using vision
3. Clicking the target
4. Asking the user to confirm if the click landed correctly

Usage:
    python scripts/setup_calibration.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient


def ask_user_confirmation(prompt: str) -> bool:
    """Ask user for yes/no confirmation."""
    try:
        while True:
            response = input(f"\n{prompt} (y/n): ").strip().lower()
            if response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                print("Please enter 'y' or 'n'")
    except EOFError:
        # Non-interactive mode - return None to indicate no input
        return None


def run_calibration():
    """Run the calibration test using Notion."""
    print("=" * 60)
    print("CLAUDE VISION CALIBRATION SETUP")
    print("Using Notion as calibration target")
    print("=" * 60)

    # Initialize client
    print("\n1. Initializing AnthropicComputerClient...")
    client = AnthropicComputerClient(verbose=True)

    print(f"\n   Display info:")
    print(f"   - Logical size: {client.logical_width}x{client.logical_height}")
    print(f"   - Screenshot size: {client.pixel_width}x{client.pixel_height}")
    print(f"   - Retina scale: {client.retina_scale}")

    # Switch to Notion
    print("\n2. Switching to Notion...")
    result = client.execute_action("switch_desktop", text="Notion")
    if not result.success:
        print(f"   ERROR: Could not switch to Notion: {result.error}")
        print("   Please make sure Notion is running.")
        return False

    time.sleep(2.0)  # Wait for switch

    # Take screenshot and find a clickable element
    print("\n3. Taking screenshot and analyzing with Claude Vision...")
    screenshot_b64 = client.take_screenshot(use_cache=False)

    # Save screenshot for debugging
    import base64
    debug_path = "/tmp/calibration_screenshot.png"
    with open(debug_path, "wb") as f:
        f.write(base64.b64decode(screenshot_b64))
    print(f"   Screenshot saved to: {debug_path}")

    # Ask Claude to find a good clickable target in Notion
    # NOTE: Anthropic API resizes images to ~1400px wide. We need to scale coordinates.
    prompt = f"""Look at this Notion screenshot.

First, tell me: what are the pixel dimensions of this image as you see it?

Then find the "Share" button in the top-right corner of the Notion window.
Give me the EXACT pixel coordinates of the center of the Share button.

Format your response as:
IMAGE_SIZE: (width, height)
ELEMENT: Share button
COORDINATES: (x, y)"""

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
                        "data": screenshot_b64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        temperature=0
    )

    response_text = response.content[0].text
    print(f"\n   Claude's response:\n{response_text}")

    # Parse the response
    import re

    # Get image size Claude sees
    size_match = re.search(r'IMAGE_SIZE:\s*\((\d+),\s*(\d+)\)', response_text)
    element_match = re.search(r'ELEMENT:\s*(.+)', response_text)
    coord_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response_text)

    if not coord_match:
        print("\n   ERROR: Could not parse coordinates from Claude's response")
        return False

    # Claude's coordinates in the scaled-down image it sees
    claude_x = int(coord_match.group(1))
    claude_y = int(coord_match.group(2))
    element_desc = element_match.group(1).strip() if element_match else "Unknown element"

    # Calculate scale factor between what Claude sees and actual screenshot
    if size_match:
        claude_width = int(size_match.group(1))
        claude_height = int(size_match.group(2))
        scale_x = client.pixel_width / claude_width
        scale_y = client.pixel_height / claude_height
        print(f"\n4. Coordinate scaling:")
        print(f"   - Claude sees:     {claude_width}x{claude_height}")
        print(f"   - Actual screenshot: {client.pixel_width}x{client.pixel_height}")
        print(f"   - Scale factors:   X={scale_x:.2f}, Y={scale_y:.2f}")
    else:
        # Default assumption: Claude resizes to ~1400px width
        scale_x = client.pixel_width / 1400
        scale_y = client.pixel_height / 875  # Assuming 16:10 aspect ratio
        print(f"\n4. Using default scale factors: X={scale_x:.2f}, Y={scale_y:.2f}")

    # Scale Claude's coordinates to actual screenshot coordinates
    x = int(claude_x * scale_x)
    y = int(claude_y * scale_y)

    print(f"\n5. Target identified:")
    print(f"   - Element: {element_desc}")
    print(f"   - Claude's coordinates: ({claude_x}, {claude_y})")
    print(f"   - Scaled to screenshot: ({x}, {y})")

    # Scale coordinates for click (screenshot space -> logical space)
    click_x, click_y = client._scale_coordinates_for_click(x, y)
    print(f"   - Scaled for click: ({click_x}, {click_y})")

    # Execute the click
    print(f"\n6. Clicking on '{element_desc}'...")
    print("   Watch the Notion window!")
    client._execute_click(click_x, click_y)
    time.sleep(1.0)

    print("\n" + "-" * 40)
    print("CLICK EXECUTED")
    print("-" * 40)
    print(f"Target:      {element_desc}")
    print(f"Screenshot:  ({x}, {y})")
    print(f"Click point: ({click_x}, {click_y})")
    print("-" * 40)
    # Switch back to iTerm for user interaction
    print("\n6. Switching back to iTerm...")
    client.execute_action("switch_desktop", text="iTerm")
    time.sleep(0.5)

    print("\n" + "=" * 60)
    print("CALIBRATION TEST COMPLETE")
    print("=" * 60)
    print(f"\nTarget:      {element_desc}")
    print(f"Screenshot:  ({x}, {y})")
    print(f"Click point: ({click_x}, {click_y})")
    print("\nPlease confirm: Did the click hit the target correctly?")

    return True


def show_coordinate_info():
    """Display coordinate system information."""
    print("\n" + "=" * 60)
    print("COORDINATE SYSTEM INFO")
    print("=" * 60)

    client = AnthropicComputerClient(verbose=False)

    print(f"\nDisplay Configuration:")
    print(f"  Logical resolution:    {client.logical_width}x{client.logical_height}")
    print(f"  Screenshot resolution: {client.pixel_width}x{client.pixel_height}")
    print(f"  Retina scale factor:   {client.retina_scale}x")

    print(f"\nCoordinate Spaces:")
    print(f"  1. Screenshot space: 0-{client.pixel_width} x 0-{client.pixel_height}")
    print(f"     - Used by Claude Vision for element detection")
    print(f"     - Coordinates returned by vision analysis")
    print(f"")
    print(f"  2. Logical space:    0-{client.logical_width} x 0-{client.logical_height}")
    print(f"     - Used by macOS for mouse clicks")
    print(f"     - Screenshot coords divided by {client.retina_scale}")

    print(f"\nConversion Examples:")
    test_coords = [
        (0, 0),
        (client.pixel_width // 2, client.pixel_height // 2),
        (client.pixel_width - 1, client.pixel_height - 1),
        (500, 500),
    ]
    for x, y in test_coords:
        sx, sy = client._scale_coordinates_for_click(x, y)
        print(f"  Screenshot ({x:4d}, {y:4d}) -> Click ({sx:4d}, {sy:4d})")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--info":
        show_coordinate_info()
    else:
        run_calibration()
