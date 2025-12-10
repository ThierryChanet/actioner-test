#!/usr/bin/env python3
"""
TEST: Try different methods to open Notion recipe in side panel.

The diagnosis is clear: clicking is NOT opening the panel.
We need to find what action DOES open the panel.
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def check_panel_open(client, recipe_name: str) -> bool:
    """Check if a side panel is currently open using vision."""
    screenshot = client.take_screenshot(use_cache=False)

    prompt = f"""Look at this Notion screenshot.

Is there a RIGHT SIDEBAR PANEL currently open showing the recipe "{recipe_name}"?

Look for:
- A panel on the right side of the screen (not the main area)
- Recipe title "{recipe_name}" in the panel
- Recipe content/ingredients in the panel

Answer with ONLY "YES" or "NO" on the first line, then explain what you see."""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=200,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': prompt}
            ]
        }]
    )

    answer = response.content[0].text.strip()
    print(f'    Vision check: {answer[:100]}...')

    return answer.upper().startswith('YES')


def test_click_method(client, method_name: str, action_func):
    """Test a specific click method to see if it opens the panel."""
    print(f'\n{"="*70}')
    print(f'Testing: {method_name}')
    print(f'{"="*70}')

    test_recipe = 'Aheobakjin'

    try:
        # Execute the action
        print(f'  Executing action...')
        action_func()

        time.sleep(3)  # Wait for panel to open

        # Check if panel opened
        print(f'  Checking if panel opened...')
        panel_open = check_panel_open(client, test_recipe)

        if panel_open:
            print(f'  ✅ SUCCESS: Panel opened with {method_name}!')
            return True
        else:
            print(f'  ❌ FAILED: Panel did NOT open')
            return False

    except Exception as e:
        print(f'  ❌ ERROR: {e}')
        return False

    finally:
        # Clean up - press Escape
        print(f'  Cleaning up (Escape)...')
        client.execute_action('key', text='Escape')
        time.sleep(1)


def main():
    print('='*70)
    print('TEST: Find which method actually opens the side panel')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    test_recipe = 'Aheobakjin'

    # Switch to Notion
    print('\n[SETUP] Switching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        methods_to_test = [
            ('Regular click', lambda: client.execute_action('click', text=test_recipe)),
            ('Double click', lambda: client.execute_action('double_click', text=test_recipe)),
            ('Right click', lambda: client.execute_action('right_click', text=test_recipe)),
        ]

        results = {}

        for method_name, action_func in methods_to_test:
            success = test_click_method(client, method_name, action_func)
            results[method_name] = success

            # Wait between tests
            time.sleep(2)

        # Print results
        print(f'\n{"="*70}')
        print('RESULTS')
        print(f'{"="*70}')

        for method_name, success in results.items():
            status = '✅' if success else '❌'
            print(f'{status} {method_name}: {"WORKS" if success else "Does not work"}')

        # Find working method
        working_methods = [m for m, s in results.items() if s]

        if working_methods:
            print(f'\n✅ Found working method(s): {", ".join(working_methods)}')
            print(f'\nUpdate scripts/recipe_extraction_comprehensive.py to use this method!')
        else:
            print(f'\n❌ NO METHODS WORKED')
            print(f'\nThis means Notion database may need configuration:')
            print(f'  1. Click "..." menu on database')
            print(f'  2. Look for "Open pages as" setting')
            print(f'  3. Change to "Side peek" or "Preview"')

    finally:
        print(f'\n[TEARDOWN] Switching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
