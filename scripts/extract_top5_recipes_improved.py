#!/usr/bin/env python3
"""Extract ingredients from top N recipes with retry logic and tab detection.

This script dynamically extracts recipe names from the visible Notion screen
and uses fuzzy matching to handle minor spelling variations.
"""

import sys
import time
import json
import re
import os
from pathlib import Path
from difflib import SequenceMatcher
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Direct imports to avoid langchain_classic dependency in __init__.py
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'agent'))
from anthropic_computer_client import AnthropicComputerClient
from screen_manager import NotionScreenManager


def fuzzy_match(text1: str, text2: str, threshold: float = 0.8) -> bool:
    """
    Check if two strings are similar enough using fuzzy matching.

    Args:
        text1: First string to compare
        text2: Second string to compare
        threshold: Minimum similarity ratio (0.0 to 1.0), default 0.8 (80% similar)

    Returns:
        True if strings are similar enough, False otherwise
    """
    # Normalize strings for comparison
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()

    # Exact match
    if t1 == t2:
        return True

    # Check if one contains the other
    if t1 in t2 or t2 in t1:
        return True

    # Use SequenceMatcher for fuzzy comparison
    ratio = SequenceMatcher(None, t1, t2).ratio()
    return ratio >= threshold


def extract_recipe_names_from_screen(client, count: int = 5) -> list[str]:
    """
    Extract recipe names from the current Notion screen using vision.

    Args:
        client: AnthropicComputerClient instance
        count: Number of recipes to extract (default 5)

    Returns:
        List of recipe names visible on screen
    """
    print(f'  Scanning screen for recipe names...')
    screenshot = client.take_screenshot(use_cache=False)

    prompt = f"""Look at this Notion screenshot showing a recipe database.

List the FIRST {count} recipe names you can see in the table/list, in order from top to bottom.

Return ONLY a JSON array of recipe names, nothing else:
["Recipe 1", "Recipe 2", "Recipe 3", ...]

If you see fewer than {count} recipes, return all that you can see."""

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
    print(f'  Raw response: {response_text[:200]}...')

    # Parse JSON array from response
    try:
        # Try direct parse first
        if response_text.startswith('['):
            recipes = json.loads(response_text)
        else:
            # Extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                recipes = json.loads(json_match.group(0))
            else:
                print(f'  ⚠️ Could not parse recipe names from response')
                return []

        print(f'  ✓ Found {len(recipes)} recipes: {recipes}')
        return recipes[:count]

    except json.JSONDecodeError as e:
        print(f'  ⚠️ JSON parse error: {e}')
        return []

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

            # STEP 3: Verify the recipe page is visible (side panel OR main view)
            print(f'  [3/5] Verifying recipe "{recipe_name}" is displayed...')
            verify_screenshot = client.take_screenshot(use_cache=False)
            verify_prompt = f"""Look at this Notion screenshot.

Is there a recipe page/detail view visible? It could be in:
- A RIGHT SIDEBAR PANEL, or
- The MAIN content area

What recipe title is currently displayed (either in panel or main view)?

Answer in this format:
RECIPE_VISIBLE: YES or NO
RECIPE_TITLE: <the title if visible, or UNKNOWN>
VIEW_TYPE: PANEL or MAIN or UNKNOWN"""

            verify_response = client.client.messages.create(
                model=client.model,
                max_tokens=200,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': verify_screenshot}},
                        {'type': 'text', 'text': verify_prompt}
                    ]
                }]
            )

            response_text = verify_response.content[0].text.strip()
            recipe_visible = 'RECIPE_VISIBLE: YES' in response_text.upper()

            # Extract the recipe title from the response for fuzzy matching
            title_match = re.search(r'RECIPE_TITLE:\s*(.+)', response_text, re.IGNORECASE)
            detected_title = title_match.group(1).strip() if title_match else ""

            # Check view type
            view_type = "unknown"
            if 'VIEW_TYPE: PANEL' in response_text.upper():
                view_type = "panel"
            elif 'VIEW_TYPE: MAIN' in response_text.upper():
                view_type = "main"

            # Use fuzzy matching to verify the correct recipe is displayed
            if recipe_visible and detected_title and detected_title.upper() != 'UNKNOWN':
                if fuzzy_match(recipe_name, detected_title):
                    print(f'  ✓ Recipe confirmed: "{detected_title}" (view: {view_type})')
                else:
                    print(f'  ⚠️  Shows "{detected_title}" instead of "{recipe_name}" (view: {view_type})')
                    # Still proceed - we can extract whatever is shown
                    print(f'  ℹ️  Proceeding with extraction anyway')
            elif not recipe_visible:
                print(f'  ⚠️  Recipe not visible')
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return []
            else:
                print(f'  ✓ Recipe appears to be displayed (view: {view_type})')

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

                # STEP 5: Go back to recipe list
                # Use Cmd+[ (browser back) or Escape depending on how it opened
                print(f'  [5/5] Returning to recipe list...')
                # Try Escape first (works for panels)
                client.execute_action('key', text='Escape')
                time.sleep(1)
                # Also try Cmd+[ (back navigation) for main view
                client.execute_action('key', text='Super+bracketleft')
                time.sleep(1.5)
                print(f'  ✓ Navigated back')

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


def main(num_recipes: int = 5):
    """
    Extract ingredients from the first N recipes visible on screen.

    Args:
        num_recipes: Number of recipes to extract (default 5)
    """
    client = AnthropicComputerClient(verbose=True)
    screen_mgr = NotionScreenManager(client)

    print(f'Client: model={client.model}, display={client.display_width}x{client.display_height}, scale={client.retina_scale}')

    all_ingredients = {}

    print(f'Extracting ingredients from top {num_recipes} recipes...')
    print('With dynamic recipe detection, fuzzy matching, and retry logic')
    print('='*60)

    # Switch to Notion once and stay there for all extractions
    print('\nSwitching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        # Dynamically extract recipe names from the screen
        print('\nStep 1: Detecting recipe names from screen...')
        recipes = extract_recipe_names_from_screen(client, count=num_recipes)

        if not recipes:
            print('❌ Could not detect any recipes on screen. Make sure Notion is showing the recipe database.')
            return

        print(f'\n✓ Will extract ingredients from {len(recipes)} recipes:')
        for i, r in enumerate(recipes, 1):
            print(f'  {i}. {r}')

        print('\nStep 2: Extracting ingredients from each recipe...')

        for idx, recipe_name in enumerate(recipes, 1):
            print(f'\n[{idx}/{len(recipes)}] Processing: {recipe_name}')
            ingredients = extract_ingredients_with_retry(client, screen_mgr, recipe_name)
            all_ingredients[recipe_name] = ingredients
    finally:
        # Switch back to iTerm2 at the end
        print('\n\nSwitching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()

    print('\n' + '='*60)
    print(f'INGREDIENTS FOR {len(all_ingredients)} RECIPES')
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
    print(f'SUMMARY: {success_count}/{len(all_ingredients)} recipes extracted successfully')
    print(f'{"="*60}')

if __name__ == "__main__":
    main()
