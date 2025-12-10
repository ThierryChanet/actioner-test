#!/usr/bin/env python3
"""
AUTOMATED FIX: Configure Notion database to open recipes in peek/side panel mode.

Steps:
1. Click "..." menu at top right of database
2. Look for "Open pages as" or similar setting
3. Change to "Side peek" or "Preview" mode
"""

import sys
import time
import base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def save_screenshot(client, filename: str, description: str):
    """Save screenshot with description."""
    screenshot = client.take_screenshot(use_cache=False)
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(screenshot))
    print(f'  📸 {filename}: {description}')


def main():
    print('='*70)
    print('AUTOMATED FIX: Configure Notion peek mode')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        # STEP 1: Take initial screenshot
        print(f'\n[2] Finding database menu ("...")...')
        save_screenshot(client, '/tmp/config_1_initial.png', 'Initial view')

        # STEP 2: Click "..." menu
        screenshot = client.take_screenshot(use_cache=False)

        menu_prompt = """Look at this Notion database screenshot.

Find the database menu button (usually "..." or three dots) at the top right of the database.

Provide coordinates in this format: COORDINATES: (x, y)
If not found, respond with: NOT_FOUND"""

        response = client.client.messages.create(
            model=client.model,
            max_tokens=150,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                    {'type': 'text', 'text': menu_prompt}
                ]
            }]
        )

        coord_text = response.content[0].text.strip()
        print(f'  Claude response: {coord_text[:100]}...')

        if "NOT_FOUND" in coord_text:
            print(f'\n❌ Could not find database menu')
            print(f'\nPlease manually configure Notion:')
            print(f'1. Click "..." menu at top right of Recipes database')
            print(f'2. Look for "Open pages as" or "Layout" setting')
            print(f'3. Change to "Side peek" or "Preview"')
            return

        # Parse coordinates
        import re
        match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', coord_text)
        if not match:
            print(f'\n⚠️  Could not parse coordinates')
            print(f'Manual configuration required (see above)')
            return

        x, y = int(match.group(1)), int(match.group(2))
        print(f'  Menu button at: ({x}, {y})')

        # Click menu
        print(f'\n[3] Clicking database menu...')
        result = client.execute_action('left_click', coordinate=(x, y))

        if not result.success:
            print(f'  ❌ Click failed: {result.error}')
            return

        time.sleep(2)
        save_screenshot(client, '/tmp/config_2_menu_open.png', 'After clicking menu')

        # STEP 3: Look for "Open pages as" or similar option
        print(f'\n[4] Looking for peek mode setting...')
        screenshot = client.take_screenshot(use_cache=False)

        settings_prompt = """Look at this Notion menu that just opened.

Find ANY option related to how pages open, such as:
- "Open pages as"
- "Layout"
- "Preview"
- "Side peek"
- "Center peek"

Describe what you see:
1. Is there an option for controlling how pages open?
2. What is it called?
3. What are the available choices?
4. Which option would open pages in a SIDE PANEL (not full page)?

Be specific about the menu items you see."""

        response = client.client.messages.create(
            model=client.model,
            max_tokens=500,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                    {'type': 'text', 'text': settings_prompt}
                ]
            }]
        )

        menu_analysis = response.content[0].text.strip()

        print(f'\n{"="*70}')
        print('MENU ANALYSIS')
        print(f'{"="*70}')
        print(menu_analysis)
        print(f'{"="*70}')

        # STEP 4: Ask Claude to identify the specific option to click
        if 'open' in menu_analysis.lower() and ('side' in menu_analysis.lower() or 'peek' in menu_analysis.lower()):
            print(f'\n[5] Found peek mode option! Looking for coordinates...')

            coord_prompt2 = f"""Based on this menu, what should I click to enable SIDE PANEL/PEEK mode?

Provide ONLY the coordinates of the option to click: COORDINATES: (x, y)
If unclear, respond with: UNCLEAR"""

            response2 = client.client.messages.create(
                model=client.model,
                max_tokens=150,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                        {'type': 'text', 'text': coord_prompt2}
                    ]
                }]
            )

            coord_text2 = response2.content[0].text.strip()
            print(f'  Claude response: {coord_text2}')

            match2 = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', coord_text2)
            if match2:
                x2, y2 = int(match2.group(1)), int(match2.group(2))
                print(f'\n[6] Clicking peek mode option at ({x2}, {y2})...')

                result2 = client.execute_action('left_click', coordinate=(x2, y2))
                time.sleep(2)

                save_screenshot(client, '/tmp/config_3_after_setting.png', 'After configuring peek mode')

                if result2.success:
                    print(f'\n✅ Successfully configured peek mode!')
                    print(f'\nNext step: Run scripts/recipe_extraction_comprehensive.py to verify it works')
                else:
                    print(f'\n⚠️  Click may have failed, check screenshots')
            else:
                print(f'\n⚠️  Could not determine which option to click')
                print(f'Please check /tmp/config_2_menu_open.png and configure manually')
        else:
            print(f'\n⚠️  Could not find peek mode option in menu')
            print(f'\nMANUAL CONFIGURATION REQUIRED:')
            print(f'1. Check screenshot: /tmp/config_2_menu_open.png')
            print(f'2. Look for option to control how pages open')
            print(f'3. Change to "Side peek" or similar')
            print(f'\nIf no such option exists, Notion may not support peek mode for this database type.')

    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()

    finally:
        # Close any open menus
        print(f'\n[Cleanup] Closing menus (Escape)...')
        client.execute_action('key', text='Escape')
        time.sleep(1)

        print(f'\n[Teardown] Switching back...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()

        print(f'\nScreenshots saved to:')
        print(f'  /tmp/config_1_initial.png')
        print(f'  /tmp/config_2_menu_open.png')
        print(f'  /tmp/config_3_after_setting.png (if successful)')


if __name__ == "__main__":
    main()
