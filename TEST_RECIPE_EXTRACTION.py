#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Extract ingredients from top 5 Notion recipes

This is the go-to test for validating the Notion automation system.
Run this script after making changes to verify everything still works.

WHAT THIS TEST VALIDATES:
========================
1. Screen switching (iTerm2 <-> Notion) without opening new terminals
2. Vision-based recipe clicking in Notion sidebar
3. Tab detection (recipe opens in new tab vs side panel)
4. Automatic tab closure and retry when tab opens unexpectedly
5. Vision-based ingredient extraction from recipe panels
6. JSON parsing with proper error handling and debug output
7. Panel closing with Escape key (with verification)
8. Retry logic for all operations (up to 2 attempts per recipe)
9. Sound notifications when returning to iTerm2

EXPECTED BEHAVIOR:
==================
- Script switches to Notion ONCE at start
- Processes all 5 recipes sequentially on Notion screen
- Detects and handles tab openings automatically
- Shows debug output for Claude vision responses
- Verifies panel closure after each recipe
- Switches back to iTerm2 ONCE at end with notification sound
- Prints summary of success/failure for each recipe

SUCCESS CRITERIA:
=================
- All 5 recipes should extract successfully (100% success rate)
- No new Terminal windows should open (stay in iTerm2)
- Panel should close after each recipe
- Total runtime: ~2-3 minutes for 5 recipes

KNOWN ISSUES TO WATCH FOR:
===========================
1. JSON parsing errors - check raw response output
2. Tab opening instead of side panel - should auto-detect and fix
3. Panel not closing - has retry logic with verification
4. Recipe not found - may need to scroll or verify Notion view

TROUBLESHOOTING:
================
If a recipe fails:
1. Check the raw response output (📝 Raw response)
2. Check if tab detection triggered (🔄 Detected new tab opened)
3. Check panel close verification (✓ Panel closed successfully)
4. Check retry attempts (🔄 Retry attempt X/2)

If script opens new Terminal:
1. Verify src/agent/screen_manager.py returns "iTerm2" for iTerm detection
2. Check that main() uses single switch_to() and switch_back()

USAGE:
======
    python3 TEST_RECIPE_EXTRACTION.py

Or with verbose output:
    python3 TEST_RECIPE_EXTRACTION.py 2>&1 | tee test_output.log

"""

import sys
import time
import json
import re
from datetime import datetime
sys.path.insert(0, '.')

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def detect_tab_change(client, recipe_name: str) -> bool:
    """
    Use Computer Vision to detect if clicking opened a new tab.

    This addresses the issue where clicking recipe title opens a new tab
    instead of the side panel, as requested by user.

    Returns:
        True if a new tab was opened, False if opened in side panel
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
    print(f'  Tab detection: {response_text[:80]}...')

    return response_text.upper().startswith('YES')


def close_tab_and_retry(client, recipe_name: str) -> bool:
    """
    Close the newly opened tab and retry clicking the recipe.

    Uses Cmd+W to close tab, then re-clicks the recipe to open in side panel.

    Returns:
        True if successfully opened in side panel after retry, False otherwise
    """
    print(f'  🔄 Tab opened instead of panel. Closing with Cmd+W and retrying...')

    # Close the tab with Cmd+W
    client.execute_action('key', text='Super+w')
    time.sleep(1.5)

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
    Extract ingredients from a recipe with comprehensive retry logic.

    Handles multiple failure modes:
    - Tab opening instead of side panel (auto-detects with vision, closes, retries)
    - JSON parsing failures (shows debug output, retries)
    - Panel closing failures (verifies with vision, retries)
    - Recipe not found (retries)

    Args:
        client: AnthropicComputerClient instance
        screen_mgr: NotionScreenManager instance
        recipe_name: Name of recipe to extract (visible text in Notion)
        max_retries: Maximum retry attempts (default: 2)

    Returns:
        List of ingredient strings, or empty list if all attempts fail

    Note: Assumes we're already on the Notion screen
    """
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                print(f'  🔄 Retry attempt {attempt + 1}/{max_retries}')

            # STEP 1: Click on recipe using vision
            print(f'  [1/6] Clicking on recipe "{recipe_name}"...')
            result = client.execute_action('click', text=recipe_name)
            if not result.success:
                print(f'  ⚠️  Could not find "{recipe_name}" in Notion')
                if attempt < max_retries - 1:
                    time.sleep(2)  # Wait before retry
                    continue
                return []

            time.sleep(2.5)  # Wait for panel to open

            # STEP 2: Check if it opened as a new tab (user-requested feature)
            print(f'  [2/6] Verifying panel opened (not tab)...')
            if detect_tab_change(client, recipe_name):
                if not close_tab_and_retry(client, recipe_name):
                    if attempt < max_retries - 1:
                        continue
                    return []

            # STEP 3: Verify the CORRECT recipe is showing
            print(f'  [3/5] Verifying correct recipe is displayed...')
            time.sleep(1)  # Wait for content to load

            verify_screenshot = client.take_screenshot(use_cache=False)
            verify_prompt = f"""Look at this Notion screenshot.

What is the TITLE/NAME of the recipe currently displayed (in panel or main area)?

Answer in this format:
RECIPE: [exact recipe name you see]"""

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

            displayed_recipe = verify_response.content[0].text.strip()
            print(f'  Claude sees: {displayed_recipe}')

            # Check if the displayed recipe matches what we clicked
            if recipe_name.lower() not in displayed_recipe.lower():
                print(f'  ⚠️  Wrong recipe showing! Expected "{recipe_name}"')
                print(f'  Closing current panel and retrying...')

                # Close the wrong panel
                client.execute_action('key', text='Escape')
                time.sleep(2)

                if attempt < max_retries - 1:
                    continue
                return []

            print(f'  ✓ Correct recipe confirmed: {recipe_name}')

            # STEP 4: Take screenshot for extraction
            print(f'  [4/5] Taking screenshot for extraction...')
            panel_screenshot = client.take_screenshot(use_cache=False)

            # STEP 5: Extract ingredients using vision
            print(f'  [5/5] Extracting ingredients...')
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

            # STEP 5: DEBUG OUTPUT - Show what Claude vision returned
            print(f'  📝 Raw response ({len(response_text)} chars):')
            if len(response_text) > 0:
                print(f'     "{response_text[:200]}..."')
            else:
                print(f'     (EMPTY RESPONSE - this causes JSON parse errors!)')

            # STEP 6: Extract JSON from response - handle multiple formats
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
            if len(json_text) > 0:
                print(f'     "{json_text[:200]}..."')
            else:
                print(f'     (EMPTY - will fail to parse!)')

            # STEP 7: Parse JSON and extract ingredients
            try:
                data = json.loads(json_text)
                ingredients = data.get('ingredients', [])
                print(f'  ✓ Parsed successfully: {len(ingredients)} ingredients')

                # STEP 6: Close with Escape (with verification)
                print(f'  [6/6] Closing panel...')

                # Try Escape up to 3 times
                for close_attempt in range(3):
                    client.execute_action('key', text='Escape')
                    time.sleep(1.5)

                    # Verify it actually closed
                    check_screenshot = client.take_screenshot(use_cache=False)
                    check_prompt = """Is there a recipe panel/page open on the right side or main area?
Answer YES or NO:"""

                    check_response = client.client.messages.create(
                        model=client.model,
                        max_tokens=50,
                        messages=[{
                            'role': 'user',
                            'content': [
                                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': check_screenshot}},
                                {'type': 'text', 'text': check_prompt}
                            ]
                        }]
                    )

                    still_open = check_response.content[0].text.strip().upper().startswith('YES')

                    if not still_open:
                        print(f'  ✓ Panel closed successfully')
                        break
                    elif close_attempt < 2:
                        print(f'  ⚠️  Panel still open, pressing Escape again ({close_attempt+2}/3)...')
                    else:
                        print(f'  ⚠️  WARNING: Panel may still be open after 3 Escape attempts!')

                # Extra wait before next recipe
                time.sleep(1)

                return ingredients

            except json.JSONDecodeError as e:
                print(f'  ❌ JSON parse error: {e}')
                print(f'  ❌ Failed to parse JSON on attempt {attempt + 1}')
                if attempt < max_retries - 1:
                    # Try closing panel before retry
                    print(f'  🔄 Closing panel and retrying...')
                    client.execute_action('key', text='Escape')
                    time.sleep(1)
                    continue
                return []

        except Exception as e:
            print(f'  ❌ Unexpected error on attempt {attempt + 1}: {e}')
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
    """
    Main test function - extracts ingredients from top 5 recipes.
    """
    print("="*70)
    print("COMPREHENSIVE TEST: Top 5 Recipe Ingredient Extraction")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    # List of top 5 recipes to extract
    recipes = [
        'Topinambours au vinaigre',
        'Velouté Potimarron',
        'Aheobakjin',
        'Thai omelet',
        'Aubergines au sésame'
    ]

    all_ingredients = {}
    start_time = time.time()

    print('Test Configuration:')
    print(f'  - Recipes to extract: {len(recipes)}')
    print(f'  - Max retries per recipe: 2')
    print(f'  - Tab detection: Enabled')
    print(f'  - Panel close verification: Enabled')
    print(f'  - Debug logging: Enabled')
    print('='*70)

    # Switch to Notion once and stay there for all extractions
    print('\n[SETUP] Switching to Notion...')
    if not screen_mgr.switch_to('Notion'):
        print('❌ FATAL: Could not switch to Notion. Aborting test.')
        return

    try:
        # Process each recipe
        for idx, recipe_name in enumerate(recipes, 1):
            print(f'\n{"="*70}')
            print(f'[{idx}/5] Processing: {recipe_name}')
            print(f'{"="*70}')

            recipe_start = time.time()
            ingredients = extract_ingredients_with_retry(client, screen_mgr, recipe_name)
            recipe_duration = time.time() - recipe_start

            all_ingredients[recipe_name] = ingredients

            if ingredients:
                print(f'  ✅ SUCCESS ({recipe_duration:.1f}s)')
            else:
                print(f'  ❌ FAILED ({recipe_duration:.1f}s)')

    finally:
        # Switch back to iTerm2 at the end
        print(f'\n{"="*70}')
        print('[TEARDOWN] Switching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()

    # Print results
    total_duration = time.time() - start_time

    print(f'\n{"="*70}')
    print('TEST RESULTS: INGREDIENTS FOR TOP 5 RECIPES')
    print(f'{"="*70}')

    for recipe_name, ingredients in all_ingredients.items():
        status = '✅' if ingredients else '❌'
        print(f'\n{status} {recipe_name}:')
        if ingredients:
            for ing in ingredients:
                print(f'  • {ing}')
        else:
            print('  (Extraction failed)')

    # Summary statistics
    success_count = sum(1 for ing in all_ingredients.values() if ing)
    total_ingredients = sum(len(ing) for ing in all_ingredients.values())

    print(f'\n{"="*70}')
    print('SUMMARY STATISTICS')
    print(f'{"="*70}')
    print(f'Recipes processed:     {len(recipes)}')
    print(f'Successful extractions: {success_count}')
    print(f'Failed extractions:     {len(recipes) - success_count}')
    print(f'Success rate:          {success_count/len(recipes)*100:.1f}%')
    print(f'Total ingredients:     {total_ingredients}')
    print(f'Total duration:        {total_duration:.1f}s')
    print(f'Avg per recipe:        {total_duration/len(recipes):.1f}s')
    print(f'{"="*70}')

    # Test verdict
    if success_count == len(recipes):
        print('✅ TEST PASSED: All recipes extracted successfully!')
    elif success_count >= len(recipes) * 0.8:
        print(f'⚠️  TEST PARTIAL: {success_count}/{len(recipes)} recipes extracted')
    else:
        print(f'❌ TEST FAILED: Only {success_count}/{len(recipes)} recipes extracted')

    print(f'\nCompleted at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'{"="*70}')

    return success_count == len(recipes)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
