#!/usr/bin/env python3
"""
SIMPLE TEST: Open just the first recipe with careful verification.
"""

import sys
import time
import base64
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def move_mouse_to(x: int, y: int) -> bool:
    """Move mouse cursor to specific coordinates."""
    try:
        import Quartz
        Quartz.CGWarpMouseCursorPosition((float(x), float(y)))
        return True
    except Exception as e:
        print(f'  ❌ Mouse move failed: {e}')
        return False


def save_screenshot(client, filename: str, description: str):
    """Save screenshot for inspection."""
    screenshot = client.take_screenshot(use_cache=False)
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(screenshot))
    print(f'  📸 Saved: {filename}')
    print(f'     {description}')


def main():
    print('='*70)
    print('SIMPLE TEST: Open first recipe panel')
    print('='*70)

    # Use Sonnet for better coordinate detection
    client = AnthropicComputerClient(model="claude-3-5-sonnet-20240620")
    screen_mgr = NotionScreenManager(client)

    test_recipe = 'Topinambours au vinaigre'

    # Switch to Notion
    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')
    time.sleep(2)

    try:
        # STEP 0: Press Escape to clear any state
        print(f'\n[2] Pressing Escape to clear state...')
        client.execute_action('key', text='Escape')
        time.sleep(1)

        # STEP 1: Find the recipe name
        print(f'\n[3] Finding "{test_recipe}"...')
        screenshot1 = client.take_screenshot(use_cache=False)
        save_screenshot(client, '/tmp/test_1_before_hover.png', 'Before hover')

        find_prompt = f"""Find the recipe "{test_recipe}" in this Notion database.

I need the PIXEL COORDINATES of where the recipe name appears.

Respond in this EXACT format:
COORDINATES: (x, y)

If not found, respond with: NOT_FOUND"""

        response = client.client.messages.create(
            model=client.model,
            max_tokens=150,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot1}},
                    {'type': 'text', 'text': find_prompt}
                ]
            }]
        )

        coord_text = response.content[0].text.strip()
        print(f'  Claude response: {coord_text[:150]}')

        if "NOT_FOUND" in coord_text:
            print(f'\n❌ Recipe not found')
            return

        match = re.search(r'(?:COORDINATES:?\s*(?:=\s*)?)?\(?(\d+),\s*(\d+)\)?', coord_text)
        if not match:
            print(f'\n❌ Could not parse coordinates')
            return

        x, y = int(match.group(1)), int(match.group(2))
        print(f'  ✓ Found at pixel coordinates: ({x}, {y})')

        # STEP 2: Hover over the recipe name
        print(f'\n[4] Hovering mouse at ({x}, {y})...')
        if not move_mouse_to(x, y):
            print(f'\n❌ Failed to move mouse')
            return

        print(f'  ✓ Mouse moved')

        # STEP 3: Wait for "OPEN" button to appear
        print(f'\n[5] Waiting 1.5 seconds for "OPEN" button to appear...')
        time.sleep(1.5)

        # STEP 4: Take screenshot to see if button appeared
        screenshot2 = client.take_screenshot(use_cache=False)
        save_screenshot(client, '/tmp/test_2_after_hover.png', 'After hover - OPEN button should be visible')

        # STEP 5: Look for "OPEN" button on the SAME horizontal line
        print(f'\n[6] Looking for "OPEN" button on same line as recipe...')

        open_prompt = f"""Look at this Notion screenshot near the recipe "{test_recipe}".

IMPORTANT: The "OPEN" button should be:
- On the SAME horizontal line as the recipe name (y-coordinate around {y})
- To the LEFT of the recipe name
- Small button with text "OPEN"

Find this button and provide its PIXEL COORDINATES.

Respond in EXACT format:
COORDINATES: (x, y)

If you cannot find an "OPEN" button on the same horizontal line, respond with: NOT_FOUND"""

        response2 = client.client.messages.create(
            model=client.model,
            max_tokens=200,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot2}},
                    {'type': 'text', 'text': open_prompt}
                ]
            }]
        )

        button_text = response2.content[0].text.strip()
        print(f'  Claude response: {button_text[:200]}')

        if "NOT_FOUND" in button_text:
            print(f'\n⚠️  "OPEN" button not found on same line')
            print(f'\nPlease check: /tmp/test_2_after_hover.png')
            print(f'Is the "OPEN" button visible? If yes, what are its coordinates?')
            return

        match2 = re.search(r'(?:COORDINATES:?\s*(?:=\s*)?)?\(?(\d+),\s*(\d+)\)?', button_text)
        if not match2:
            print(f'\n❌ Could not parse button coordinates')
            return

        btn_x, btn_y = int(match2.group(1)), int(match2.group(2))
        print(f'  ✓ Found "OPEN" button at: ({btn_x}, {btn_y})')

        # Verify it's on the same horizontal line (within 20 pixels)
        y_diff = abs(btn_y - y)
        if y_diff > 20:
            print(f'\n⚠️  WARNING: Button y-coordinate ({btn_y}) is {y_diff} pixels away from recipe ({y})')
            print(f'  This might not be the correct OPEN button!')

        # STEP 6: Click the "OPEN" button
        print(f'\n[7] Clicking "OPEN" button at ({btn_x}, {btn_y})...')
        result = client.execute_action('left_click', coordinate=(btn_x, btn_y))

        if not result.success:
            print(f'  ❌ Click failed')
            return

        print(f'  ✓ Clicked')

        # STEP 7: Wait and check if panel opened
        print(f'\n[8] Waiting for panel to open...')
        time.sleep(2.5)

        screenshot3 = client.take_screenshot(use_cache=False)
        save_screenshot(client, '/tmp/test_3_after_click.png', 'After clicking OPEN')

        # STEP 8: Verify panel opened
        print(f'\n[9] Checking if side panel opened...')

        verify_prompt = f"""Look at this Notion screenshot.

Is there a RIGHT SIDEBAR PANEL open showing the recipe "{test_recipe}"?

Answer:
- YES if you see a right sidebar panel with recipe content
- NO if no panel is open (just seeing the database table view)

Explain what you see."""

        response3 = client.client.messages.create(
            model=client.model,
            max_tokens=200,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot3}},
                    {'type': 'text', 'text': verify_prompt}
                ]
            }]
        )

        verify_text = response3.content[0].text.strip()
        print(f'\n  Claude says: {verify_text}')

        print(f'\n{"="*70}')
        print('VERIFICATION NEEDED')
        print(f'{"="*70}')
        print('Please check the screenshot: /tmp/test_3_after_click.png')
        print('')
        print('Question: Did the side panel for "Topinambours au vinaigre" open successfully?')
        print('')
        if 'YES' in verify_text[:20].upper():
            print('Claude thinks: YES - Panel opened ✓')
        else:
            print('Claude thinks: NO - Panel did not open')

    finally:
        print(f'\n[Cleanup] Switching back...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
