#!/usr/bin/env python3
"""
TEST: Use simple click action to find and click OPEN button.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def main():
    print('='*70)
    print('TEST: Simple click on OPEN button')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    test_recipe = 'Topinambours au vinaigre'

    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')
    time.sleep(2)

    try:
        print(f'\n[2] Pressing Escape to clear state...')
        client.execute_action('key', text='Escape')
        time.sleep(1)

        print(f'\n[3] Clicking on recipe name "{test_recipe}" to trigger hover...')
        # This should position mouse over the recipe, which might trigger hover
        result = client.execute_action('click', text=test_recipe)

        if result.success:
            print(f'  ✓ Clicked (this should have triggered hover)')
        else:
            print(f'  ⚠️  Click failed')
            return

        time.sleep(1.5)  # Wait for hover effect

        print(f'\n[4] Now trying to click "Open" button...')
        # Now try clicking "Open" - the button should be visible after hover
        result2 = client.execute_action('click', text='Open')

        if result2.success:
            print(f'  ✓ Clicked "Open" button')
        else:
            print(f'  ⚠️  Could not find/click "Open" button')
            return

        time.sleep(2.5)

        print(f'\n[5] Checking if panel opened...')
        screenshot = client.take_screenshot(use_cache=False)

        verify_prompt = f"""Is there a RIGHT SIDEBAR PANEL open showing "{test_recipe}"?
Answer YES or NO, then explain."""

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

        result_text = response.content[0].text.strip()
        print(f'\n  {result_text}')

        print(f'\n{"="*70}')
        print('Did the panel open successfully?')
        print(f'{"="*70}')

    finally:
        print(f'\n[Cleanup] Switching back...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
