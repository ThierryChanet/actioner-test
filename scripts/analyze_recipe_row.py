#!/usr/bin/env python3
"""
DIAGNOSTIC: Analyze a recipe row to find ALL clickable elements.

Maybe there's a specific icon or button (not the recipe name) that opens the panel.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def main():
    print('='*70)
    print('DIAGNOSTIC: Analyze recipe row UI elements')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    test_recipe = 'Aheobakjin'

    # Switch to Notion
    print('\n[1] Switching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        # Take screenshot
        print(f'\n[2] Analyzing recipe row for "{test_recipe}"...')
        screenshot = client.take_screenshot(use_cache=False)

        # Ask Claude to identify ALL clickable elements in that row
        prompt = f"""Look at this Notion database screenshot.

Find the row for the recipe "{test_recipe}" and identify ALL clickable elements in that row.

For each clickable element, describe:
1. What it is (recipe name, icon, button, etc.)
2. What clicking it might do
3. The visual appearance (color, icon shape, etc.)
4. Approximate location in the row (left, middle, right)

Also, tell me:
- Is there a specific icon/button that might open the recipe in a side panel/peek view?
- What's the typical pattern in Notion databases for opening items in peek mode vs full page?

Be detailed - I'm trying to figure out which element to click to open the panel."""

        response = client.client.messages.create(
            model=client.model,
            max_tokens=1000,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': 'image/png',
                            'data': screenshot
                        }
                    },
                    {
                        'type': 'text',
                        'text': prompt
                    }
                ]
            }]
        )

        analysis = response.content[0].text.strip()

        print(f'\n{"="*70}')
        print('CLAUDE VISION ANALYSIS')
        print(f'{"="*70}')
        print(analysis)
        print(f'{"="*70}')

        # Also ask specifically about peek mode configuration
        prompt2 = """Looking at this Notion database, can you tell:

1. Is there a database menu (usually "..." at top right) visible?
2. Are there any settings or configurations visible that control how recipes open?
3. Do you see any indication of how items are configured to open (full page vs peek/side panel)?

This will help me understand if the database needs configuration changes."""

        response2 = client.client.messages.create(
            model=client.model,
            max_tokens=500,
            messages=[{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': 'image/png',
                            'data': screenshot
                        }
                    },
                    {
                        'type': 'text',
                        'text': prompt2
                    }
                ]
            }]
        )

        config_analysis = response2.content[0].text.strip()

        print(f'\nCONFIGURATION ANALYSIS')
        print(f'{"="*70}')
        print(config_analysis)
        print(f'{"="*70}')

        print('\n\nNEXT STEPS:')
        print('-----------')
        print('Based on the analysis above:')
        print('1. Try clicking different elements if icons are identified')
        print('2. Configure database if settings are visible')
        print('3. Consider manual Notion configuration changes')

    finally:
        print(f'\n[3] Switching back...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()


if __name__ == "__main__":
    main()
