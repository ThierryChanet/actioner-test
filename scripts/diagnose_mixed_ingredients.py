#!/usr/bin/env python3
"""
DIAGNOSTIC: Save screenshots during extraction to see what's actually showing.

This script extracts the first 3 recipes and saves screenshots at key points:
- After clicking each recipe
- Before extracting ingredients
- After pressing Escape

This will help us understand if:
1. The panel is opening correctly for each recipe
2. The panel is closing between recipes
3. The correct recipe is showing when we extract
"""

import sys
import time
import json
import re
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def save_screenshot(client, filename: str, description: str):
    """Save a screenshot to file for manual inspection."""
    screenshot = client.take_screenshot(use_cache=False)

    import base64
    with open(filename, 'wb') as f:
        f.write(base64.b64decode(screenshot))

    print(f'  📸 Saved screenshot: {filename}')
    print(f'     {description}')


def extract_with_screenshots(client, screen_mgr, recipe_name: str, recipe_num: int):
    """Extract ingredients while saving diagnostic screenshots."""
    print(f'\n{"="*70}')
    print(f'[{recipe_num}/3] DIAGNOSTIC: {recipe_name}')
    print(f'{"="*70}')

    try:
        # STEP 1: Click on recipe
        print(f'  [1/5] Clicking on recipe "{recipe_name}"...')
        result = client.execute_action('click', text=recipe_name)

        if not result.success:
            print(f'  ❌ Could not find "{recipe_name}"')
            return []

        time.sleep(2.5)

        # SCREENSHOT 1: After clicking (should show panel open)
        save_screenshot(
            client,
            f'/tmp/recipe{recipe_num}_1_after_click.png',
            f'After clicking "{recipe_name}" - panel should be open'
        )

        # STEP 2: Wait for content to load
        print(f'  [2/5] Waiting for content to load...')
        time.sleep(1)

        # SCREENSHOT 2: Before extraction (this is what we'll extract from)
        print(f'  [3/5] Taking screenshot for extraction...')
        panel_screenshot = client.take_screenshot(use_cache=False)

        # Save the extraction screenshot too
        save_screenshot(
            client,
            f'/tmp/recipe{recipe_num}_2_before_extraction.png',
            f'Before extracting from "{recipe_name}" - this is what Claude sees'
        )

        # STEP 3: Extract ingredients
        print(f'  [4/5] Extracting ingredients...')
        prompt = f"""Look at this Notion page for "{recipe_name}".

Extract ONLY the ingredients list. Return as JSON:
{{"ingredients": ["ingredient 1", "ingredient 2", ...]}}

If you cannot find ingredients, return:
{{"ingredients": []}}"""

        response = client.client.messages.create(
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
                            'data': panel_screenshot
                        }
                    },
                    {
                        'type': 'text',
                        'text': prompt
                    }
                ]
            }]
        )

        response_text = response.content[0].text.strip()

        # Extract JSON from response
        json_text = response_text

        if '```json' in response_text:
            json_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            json_text = response_text.split('```')[1].split('```')[0].strip()
        else:
            json_match = re.search(r'\{[^{}]*"ingredients"[^{}]*\[[^\]]*\][^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)

        # Parse JSON
        try:
            data = json.loads(json_text)
            ingredients = data.get('ingredients', [])
            print(f'  ✅ Extracted {len(ingredients)} ingredients')

            # STEP 4: Close with Escape
            print(f'  [5/5] Closing with Escape...')
            client.execute_action('key', text='Escape')
            time.sleep(2)

            # SCREENSHOT 3: After closing (panel should be closed)
            save_screenshot(
                client,
                f'/tmp/recipe{recipe_num}_3_after_escape.png',
                f'After pressing Escape - panel should be closed'
            )

            # Extra wait before next recipe
            time.sleep(1)

            return ingredients

        except json.JSONDecodeError as e:
            print(f'  ❌ JSON parse error: {e}')
            return []

    except Exception as e:
        print(f'  ❌ Unexpected error: {e}')
        return []


def main():
    """Diagnostic extraction with screenshots."""
    print("="*70)
    print("DIAGNOSTIC: Extract first 3 recipes with screenshots")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    # First 3 recipes
    recipes = [
        'Topinambours au vinaigre',
        'Velouté Potimarron',
        'Aheobakjin'
    ]

    all_ingredients = {}

    print('Configuration:')
    print(f'  - Recipes to extract: {len(recipes)}')
    print(f'  - Screenshots will be saved to: /tmp/recipe*.png')
    print(f'  - 3 screenshots per recipe (after click, before extraction, after escape)')
    print('='*70)

    # Switch to Notion
    print('\n[SETUP] Switching to Notion...')
    if not screen_mgr.switch_to('Notion'):
        print('❌ FATAL: Could not switch to Notion')
        return

    try:
        # Process each recipe
        for idx, recipe_name in enumerate(recipes, 1):
            ingredients = extract_with_screenshots(client, screen_mgr, recipe_name, idx)
            all_ingredients[recipe_name] = ingredients

            if ingredients:
                print(f'  ✅ SUCCESS')
            else:
                print(f'  ❌ FAILED')

    finally:
        # Switch back
        print(f'\n{"="*70}')
        print('[TEARDOWN] Switching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()

    # Print results
    print(f'\n{"="*70}')
    print('DIAGNOSTIC RESULTS')
    print(f'{"="*70}')

    for recipe_name, ingredients in all_ingredients.items():
        status = '✅' if ingredients else '❌'
        print(f'\n{status} {recipe_name}:')
        if ingredients:
            for ing in ingredients:
                print(f'  • {ing}')
        else:
            print('  (Extraction failed)')

    # Instructions
    print(f'\n{"="*70}')
    print('NEXT STEPS')
    print(f'{"="*70}')
    print('Screenshots saved to:')
    for i in range(1, len(recipes) + 1):
        print(f'\nRecipe {i}:')
        print(f'  /tmp/recipe{i}_1_after_click.png')
        print(f'  /tmp/recipe{i}_2_before_extraction.png')
        print(f'  /tmp/recipe{i}_3_after_escape.png')

    print('\nPlease check these screenshots to verify:')
    print('  1. Does _after_click show the correct recipe panel?')
    print('  2. Does _before_extraction show the right ingredients?')
    print('  3. Does _after_escape show the panel closed?')
    print('  4. Are recipes #1 and #2 showing different content?')
    print(f'{"="*70}')


if __name__ == "__main__":
    main()
