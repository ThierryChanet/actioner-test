#!/usr/bin/env python3
"""Extract ingredients from top 5 recipes with retry logic and tab detection."""

import sys
import time
import json
import re
sys.path.insert(0, '.')

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager

def detect_tab_change(client, recipe_name: str) -> bool:
    """
    Use Computer Vision to detect if clicking opened a new tab.
    Returns True if a new tab was opened, False otherwise.
    """
    screenshot = client.take_screenshot(use_cache=False)

    prompt = f"""Look at this Notion screenshot.

Did clicking on "{recipe_name}" open a NEW TAB instead of opening in the side panel?

Look for these signs:
- Multiple tabs visible at the top (tab bar)
- The page opened in the main area instead of right sidebar
- No right sidebar panel visible

Answer with ONLY "YES" or "NO" on the first line, then explain briefly."""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=200,
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

    response_text = response.content[0].text.strip()
    print(f'  Tab detection response: {response_text[:100]}...')

    return response_text.upper().startswith('YES')


def close_tab_and_retry(client, recipe_name: str) -> bool:
    """
    Close the newly opened tab and retry clicking the recipe.
    Returns True if successful, False otherwise.
    """
    print(f'  🔄 Detected new tab opened. Closing tab and retrying...')

    # Close the tab with Cmd+W
    client.execute_action('key', text='Super+w')
    time.sleep(1)

    # Now retry clicking the recipe
    result = client.execute_action('click', text=recipe_name)
    time.sleep(2)

    # Check again if it opened in side panel this time
    if detect_tab_change(client, recipe_name):
        print(f'  ❌ Still opening as tab after retry')
        return False

    print(f'  ✅ Successfully opened in side panel after retry')
    return True


def extract_ingredients_with_retry(client, screen_mgr, recipe_name: str, max_retries: int = 2):
    """
    Extract ingredients from a recipe with retry logic.

    Handles:
    - Tab opening instead of side panel
    - JSON parsing failures
    - Panel closing failures

    Note: Assumes we're already on the Notion screen
    """
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f'  🔄 Retry attempt {attempt + 1}/{max_retries}')

            # STEP 1: Click on recipe using vision (we're already on Notion)
            print(f'  [1/5] Clicking on recipe "{recipe_name}"...')
            result = client.execute_action('click', text=recipe_name)
            if not result.success:
                print(f'  ⚠️  Could not find {recipe_name}')
                if attempt < max_retries - 1:
                    continue
                return []

            time.sleep(2.5)  # Wait for panel to open

            # STEP 2: Check if it opened as a new tab
            print(f'  [2/5] Verifying panel opened (not tab)...')
            if detect_tab_change(client, recipe_name):
                if not close_tab_and_retry(client, recipe_name):
                    if attempt < max_retries - 1:
                        continue
                    return []

            # STEP 3: Verify the side panel is actually open for THIS recipe
            print(f'  [3/5] Verifying side panel shows "{recipe_name}"...')
            verify_screenshot = client.take_screenshot(use_cache=False)
            verify_prompt = f"""Look at this Notion screenshot.

Is there a RIGHT SIDEBAR PANEL open showing the recipe "{recipe_name}"?

Answer with ONLY "YES" or "NO" on the first line."""

            verify_response = client.client.messages.create(
                model=client.model,
                max_tokens=100,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': verify_screenshot}},
                        {'type': 'text', 'text': verify_prompt}
                    ]
                }]
            )

            panel_open = verify_response.content[0].text.strip().upper().startswith('YES')
            if not panel_open:
                print(f'  ⚠️  Side panel not showing "{recipe_name}"')
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return []

            print(f'  ✓ Side panel confirmed for "{recipe_name}"')

            # STEP 4: Take screenshot of open panel for extraction
            print(f'  [4/5] Extracting ingredients from panel...')
            panel_screenshot = client.take_screenshot(use_cache=False)

            # Extract ingredients using vision
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

            # DEBUG: Print raw response
            print(f'  📝 Raw response ({len(response_text)} chars):')
            print(f'     "{response_text[:200]}..."')

            # Parse JSON - handle multiple formats
            json_text = response_text

            # Try extracting from code blocks first
            if '```json' in response_text:
                json_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_text = response_text.split('```')[1].split('```')[0].strip()
            else:
                # Look for JSON object in the response (starts with { and ends with })
                json_match = re.search(r'\{[^{}]*"ingredients"[^{}]*\[[^\]]*\][^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    # Try to find any JSON object
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(0)

            print(f'  📝 Extracted JSON ({len(json_text)} chars):')
            print(f'     "{json_text[:200]}..."')

            try:
                data = json.loads(json_text)
                ingredients = data.get('ingredients', [])
                print(f'  ✓ Parsed successfully: {len(ingredients)} ingredients')

                # STEP 5: Close panel with Escape (trust it works)
                print(f'  [5/5] Closing side panel for "{recipe_name}"...')
                client.execute_action('key', text='Escape')
                time.sleep(2)  # Wait for panel to close
                print(f'  ✓ Panel closed (Escape pressed)')

                # Extra wait to ensure panel fully closed before next recipe
                time.sleep(1)

                return ingredients

            except json.JSONDecodeError as e:
                print(f'  ⚠️  JSON parse error: {e}')
                print(f'  ⚠️  Failed to parse JSON on attempt {attempt + 1}')
                if attempt < max_retries - 1:
                    # Try closing panel before retry
                    client.execute_action('key', text='Escape')
                    time.sleep(1)
                    continue
                return []

        except Exception as e:
            print(f'  ❌ Error on attempt {attempt + 1}: {e}')
            if attempt < max_retries - 1:
                # Try to recover by pressing Escape
                try:
                    client.execute_action('key', text='Escape')
                    time.sleep(1)
                except:
                    pass
                continue
            return []

    return []


def main():
    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    # List of recipes to extract
    recipes = [
        'Topinambours au vinaigre',
        'Velouté Potimarron',
        'Aheobakjin',
        'Thai omelet',
        'Aubergines au sésame'
    ]

    all_ingredients = {}

    print('Extracting ingredients from top 5 recipes...')
    print('With retry logic and tab detection')
    print('='*60)

    # Switch to Notion once and stay there for all extractions
    print('\nSwitching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        for idx, recipe_name in enumerate(recipes, 1):
            print(f'\n[{idx}/5] Processing: {recipe_name}')
            ingredients = extract_ingredients_with_retry(client, screen_mgr, recipe_name)
            all_ingredients[recipe_name] = ingredients
    finally:
        # Switch back to iTerm2 at the end
        print('\n\nSwitching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()

    print('\n' + '='*60)
    print('INGREDIENTS FOR TOP 5 RECIPES')
    print('='*60)

    for recipe_name, ingredients in all_ingredients.items():
        print(f'\n📋 {recipe_name}:')
        if ingredients:
            for ing in ingredients:
                print(f'  • {ing}')
        else:
            print('  (Could not extract)')

    # Summary statistics
    success_count = sum(1 for ing in all_ingredients.values() if ing)
    print(f'\n{"="*60}')
    print(f'SUMMARY: {success_count}/{len(recipes)} recipes extracted successfully')
    print(f'{"="*60}')

if __name__ == "__main__":
    main()
