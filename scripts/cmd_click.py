#!/usr/bin/env python3
"""
TEST: Try Cmd+Click to open Notion panel in peek mode.

In macOS/Notion, Cmd+Click often opens items in preview/peek mode.
"""

import sys
import time
import base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def save_screenshot(client, filename: str):
    """Save screenshot for inspection."""
    screenshot = client.take_screenshot(use_cache=False)
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(screenshot))
    print(f'  📸 Saved: {filename}')


def check_panel_open(client) -> str:
    """Check what's currently on screen."""
    screenshot = client.take_screenshot(use_cache=False)

    prompt = """Look at this Notion screenshot.

Describe what you see:
1. Is there a RIGHT SIDEBAR PANEL open? (not the left sidebar with recipe list)
2. If yes, what recipe is showing in the panel?
3. If no panel, just describe the main view

Be concise."""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=150,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': prompt}
            ]
        }]
    )

    return response.content[0].text.strip()


def main():
    print('='*70)
    print('TEST: Cmd+Click to open panel')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    test_recipe = 'Aheobakjin'

    # Switch to Notion
    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        # Take initial screenshot
        print(f'\n[2] Initial state:')
        state = check_panel_open(client)
        print(f'    {state}')
        save_screenshot(client, '/tmp/test_cmd_click_1_before.png')

        # METHOD 1: Click while holding Cmd using vision to find coordinates
        print(f'\n[3] Getting coordinates for "{test_recipe}"...')
        screenshot = client.take_screenshot(use_cache=False)

        coord_prompt = f"""Find "{test_recipe}" in this Notion screenshot.
Provide ONLY the coordinates in this format: COORDINATES: (x, y)
If not found, respond with: NOT_FOUND"""

        response = client.client.messages.create(
            model=client.model,
            max_tokens=150,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                    {'type': 'text', 'text': coord_prompt}
                ]
            }]
        )

        coord_text = response.content[0].text.strip()
        print(f'    Claude response: {coord_text}')

        # Parse coordinates
        if "NOT_FOUND" in coord_text:
            print(f'    ❌ Recipe not found')
            return

        import re
        match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', coord_text)
        if not match:
            print(f'    ❌ Could not parse coordinates')
            return

        x, y = int(match.group(1)), int(match.group(2))
        print(f'    Coordinates: ({x}, {y})')

        # Now try clicking with Cmd held down using cliclick
        print(f'\n[4] Attempting Cmd+Click at ({x}, {y})...')

        # Use cliclick tool if available (or pyautogui)
        import subprocess

        # Try using cliclick (macOS command-line tool for clicking)
        try:
            # Cmd+Click using cliclick: kd:cmd (key down), c:x,y (click), ku:cmd (key up)
            subprocess.run(['cliclick', f'kd:cmd', f'c:{x},{y}', 'ku:cmd'], check=True)
            print(f'    ✅ Executed Cmd+Click')
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f'    ⚠️  cliclick not available, trying alternative method')

            # Alternative: Use AppleScript
            applescript = f'''
tell application "System Events"
    key down command
    delay 0.1
    tell application "Notion" to activate
    do shell script "/usr/bin/cliclick c:{x},{y}"
    delay 0.1
    key up command
end tell
            '''
            try:
                subprocess.run(['osascript', '-e', applescript], check=True)
                print(f'    ✅ Executed Cmd+Click via AppleScript')
            except Exception as e2:
                print(f'    ❌ Failed: {e2}')
                return

        time.sleep(3)

        # Check result
        print(f'\n[5] After Cmd+Click:')
        state = check_panel_open(client)
        print(f'    {state}')
        save_screenshot(client, '/tmp/test_cmd_click_2_after.png')

        # Check if it worked
        if 'panel' in state.lower() and 'open' in state.lower():
            print(f'\n✅ SUCCESS: Cmd+Click opened the panel!')
            print(f'\nNext step: Update scripts/recipe_extraction_comprehensive.py to use Cmd+Click')
        else:
            print(f'\n❌ FAILED: Panel did not open')
            print(f'\nNotion database may need configuration for peek mode.')

    finally:
        print(f'\n[6] Cleaning up and switching back...')
        client.execute_action('key', text='Escape')
        time.sleep(1)
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
