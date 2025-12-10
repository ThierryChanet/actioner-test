#!/usr/bin/env python3
"""
DEBUG: Test the hover → "Open" button pattern with detailed output.
"""

import sys
import time
import base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def save_screenshot(client, filename: str):
    """Save screenshot."""
    screenshot = client.take_screenshot(use_cache=False)
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(screenshot))
    print(f'  📸 Saved: {filename}')
    return screenshot


def main():
    print('='*70)
    print('DEBUG: Test hover → "Open" button pattern')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    test_recipe = 'Aheobakjin'

    # Switch to Notion
    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')
    time.sleep(2)

    try:
        # STEP 1: Take initial screenshot
        print(f'\n[2] Taking screenshot before hover...')
        screenshot1 = save_screenshot(client, '/tmp/hover_test_1_before.png')

        # STEP 2: Ask Claude to find the recipe
        print(f'\n[3] Asking Claude to find "{test_recipe}"...')

        find_prompt = f"""Look at this Notion database screenshot.

Find the recipe titled "{test_recipe}" in the visible rows.

Provide:
1. Is the recipe visible? (YES/NO)
2. If yes, what are the EXACT pixel coordinates of the recipe NAME text?
3. Format: COORDINATES: (x, y)

Be precise - the coordinates will be used for mouse hovering."""

        response1 = client.client.messages.create(
            model=client.model,
            max_tokens=200,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot1}},
                    {'type': 'text', 'text': find_prompt}
                ]
            }]
        )

        claude_response1 = response1.content[0].text.strip()
        print(f'\nClaude response:')
        print(f'{"-"*70}')
        print(claude_response1)
        print(f'{"-"*70}')

        # STEP 3: If found, try to hover (manually trigger for this test)
        print(f'\n[4] Now MANUALLY hover your mouse over "{test_recipe}" and wait 2 seconds...')
        print(f'    (This simulates the hover action)')
        time.sleep(4)  # Give time to manually hover

        # STEP 4: Take screenshot after hover
        print(f'\n[5] Taking screenshot after hover...')
        screenshot2 = save_screenshot(client, '/tmp/hover_test_2_after_hover.png')

        # STEP 5: Ask Claude to find the "Open" button
        print(f'\n[6] Asking Claude to find "Open" button...')

        button_prompt = f"""Look at this Notion screenshot.

The mouse was just hovered over the recipe "{test_recipe}".
An "Open" button should have appeared near the recipe name.

Questions:
1. Do you see an "Open" button near "{test_recipe}"? (YES/NO)
2. If yes, what does it look like? (describe color, icon, text)
3. If yes, what are its EXACT pixel coordinates?
4. Format: COORDINATES: (x, y)

Be specific about what you see."""

        response2 = client.client.messages.create(
            model=client.model,
            max_tokens=300,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot2}},
                    {'type': 'text', 'text': button_prompt}
                ]
            }]
        )

        claude_response2 = response2.content[0].text.strip()
        print(f'\nClaude response:')
        print(f'{"-"*70}')
        print(claude_response2)
        print(f'{"-"*70}')

        print(f'\n{"="*70}')
        print('CONCLUSIONS')
        print(f'{"="*70}')
        print('Check the screenshots:')
        print('  /tmp/hover_test_1_before.png')
        print('  /tmp/hover_test_2_after_hover.png')
        print('')
        print('Questions to answer:')
        print('1. Did the "Open" button appear when you hovered?')
        print('2. Does Claude vision recognize it?')
        print('3. If yes, can we automate the hover action?')

    finally:
        print(f'\n[7] Cleaning up...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
