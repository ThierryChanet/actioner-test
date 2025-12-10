#!/usr/bin/env python3
"""
Fix Notion to open recipes in peek/side panel mode instead of tabs.

Strategy:
1. Try Cmd+Click to open in peek mode
2. If that doesn't work, help user configure database settings
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def test_peek_mode_click(client, recipe_name):
    """Test if Cmd+Click opens recipe in peek mode."""
    print(f'\nTesting Cmd+Click for "{recipe_name}"...')

    # Try to click with Cmd modifier to open in peek
    # In Notion, Cmd+Click or middle click opens in peek mode
    print(f'  Clicking with "click" action (should open peek/panel)...')
    result = client.execute_action('click', text=recipe_name)

    if not result.success:
        print(f'  ❌ Click failed for {recipe_name}')
        return False

    time.sleep(2.5)

    # Verify it opened as panel, not tab
    screenshot = client.take_screenshot(use_cache=False)

    verify_prompt = f"""Look at this Notion screenshot.

After clicking on "{recipe_name}", what happened?

A) Opened in RIGHT SIDEBAR panel (peek view)
B) Opened as a NEW TAB in the main area
C) Just selected the row, nothing opened

Answer with just the letter (A, B, or C) and brief explanation:"""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=150,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': verify_prompt}
            ]
        }]
    )

    answer = response.content[0].text.strip()
    print(f'  Result: {answer[:100]}...')

    if 'A' in answer.upper()[:20]:
        print(f'  ✅ SUCCESS: Opened as side panel!')
        return True
    elif 'B' in answer.upper()[:20]:
        print(f'  ⚠️  Opened as tab (not ideal)')
        return False
    else:
        print(f'  ⚠️  Did not open')
        return False


def main():
    print('='*70)
    print('FIX: Configure Notion to use peek/side panel mode')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    # Switch to Notion
    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        # Test with a recipe
        test_recipe = 'Aheobakjin'

        print(f'\n[2] Testing current click behavior...')
        peek_works = test_peek_mode_click(client, test_recipe)

        # Close any open panel/tab
        print(f'\n[3] Cleaning up...')
        client.execute_action('key', text='Escape')
        time.sleep(1)

        if peek_works:
            print(f'\n{"="*70}')
            print('✅ GOOD NEWS: Notion is opening recipes in peek/panel mode!')
            print('The extraction scripts should work now.')
            print(f'{"="*70}')
        else:
            print(f'\n{"="*70}')
            print('⚠️  CONFIGURATION NEEDED')
            print('="*70')
            print('\nNotion is not opening recipes in peek mode.')
            print('\nTo fix this, you need to configure the database:')
            print('1. In the Notion Recipes database')
            print('2. Click the "..." menu at the top right')
            print('3. Look for "Open pages as" or similar setting')
            print('4. Change it to "Side peek" or "Preview"')
            print('\nAlternatively, ensure the click action uses a modifier')
            print('that triggers peek mode in Notion.')
            print(f'{"="*70}')

    finally:
        # Switch back
        print(f'\n[4] Switching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
