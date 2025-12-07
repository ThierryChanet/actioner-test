#!/usr/bin/env python3
"""Debug script to investigate Aheobakjin and Aubergines au sésame failures."""

import sys
import time
import json
import base64
sys.path.insert(0, '.')

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager


def save_screenshot(client, path, description):
    """Save screenshot to file for manual inspection."""
    screenshot = client.take_screenshot(use_cache=False)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(screenshot))
    print(f'  📸 Saved screenshot: {path}')
    print(f'     Description: {description}')


def debug_recipe(client, screen_mgr, recipe_name, recipe_num):
    """Debug a single recipe extraction with screenshots at each step."""
    print(f'\n{"="*70}')
    print(f'DEBUG RECIPE #{recipe_num}: {recipe_name}')
    print(f'{"="*70}')

    # STEP 1: Click on recipe
    print(f'\nSTEP 1: Clicking on recipe "{recipe_name}"...')
    result = client.execute_action('click', text=recipe_name)
    print(f'  Click result: {result.success}')
    time.sleep(2.5)

    save_screenshot(client, f'/tmp/debug_recipe{recipe_num}_1_after_click.png',
                   f'After clicking {recipe_name}')

    # STEP 2: Check tab detection
    print(f'\nSTEP 2: Tab detection...')
    screenshot = client.take_screenshot(use_cache=False)

    tab_prompt = f"""Look at this Notion screenshot.

Did clicking on "{recipe_name}" open a NEW TAB instead of opening in the side panel?

Look for these signs:
- Multiple tabs visible at the top (tab bar)
- The page opened in the main area instead of right sidebar
- No right sidebar panel visible

Answer with ONLY "YES" or "NO" on the first line, then explain briefly."""

    tab_response = client.client.messages.create(
        model=client.model,
        max_tokens=200,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': tab_prompt}
            ]
        }]
    )

    tab_text = tab_response.content[0].text.strip()
    is_tab = tab_text.upper().startswith('YES')

    print(f'  Tab detection result: {tab_text[:150]}...')
    print(f'  Is tab: {is_tab}')

    # STEP 3: Panel verification
    print(f'\nSTEP 3: Panel verification...')
    screenshot = client.take_screenshot(use_cache=False)

    panel_prompt = f"""Look at this Notion screenshot.

Is there a RIGHT SIDEBAR PANEL open showing the recipe "{recipe_name}"?

Answer with ONLY "YES" or "NO" on the first line, then explain what you see."""

    panel_response = client.client.messages.create(
        model=client.model,
        max_tokens=200,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': panel_prompt}
            ]
        }]
    )

    panel_text = panel_response.content[0].text.strip()
    panel_open = panel_text.upper().startswith('YES')

    print(f'  Panel verification result: {panel_text[:150]}...')
    print(f'  Panel showing recipe: {panel_open}')

    save_screenshot(client, f'/tmp/debug_recipe{recipe_num}_2_panel_verification.png',
                   f'Panel verification for {recipe_name}')

    # STEP 4: If tab, try to close it
    if is_tab:
        print(f'\nSTEP 4: Detected tab - attempting to close with Cmd+W...')
        client.execute_action('key', text='Super+w')
        time.sleep(2)

        save_screenshot(client, f'/tmp/debug_recipe{recipe_num}_3_after_close_tab.png',
                       f'After closing tab for {recipe_name}')

        # Verify tab closed
        screenshot = client.take_screenshot(use_cache=False)
        verify_response = client.client.messages.create(
            model=client.model,
            max_tokens=100,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                    {'type': 'text', 'text': 'Is there a tab bar with multiple tabs visible at the top? Answer YES or NO.'}
                ]
            }]
        )

        still_tab = verify_response.content[0].text.strip().upper().startswith('YES')
        print(f'  Tab still present after Cmd+W: {still_tab}')

        # Retry clicking
        if not still_tab:
            print(f'  Retrying click on {recipe_name}...')
            result = client.execute_action('click', text=recipe_name)
            time.sleep(2.5)

            save_screenshot(client, f'/tmp/debug_recipe{recipe_num}_4_after_retry_click.png',
                           f'After retry click on {recipe_name}')

    # STEP 5: Extract ingredients (if panel is showing)
    if panel_open or is_tab:
        print(f'\nSTEP 5: Attempting extraction...')
        screenshot = client.take_screenshot(use_cache=False)

        extract_prompt = f"""Look at this Notion page.

Extract ONLY the ingredients list for "{recipe_name}". Return as JSON:
{{"ingredients": ["ingredient 1", "ingredient 2", ...]}}

If you cannot find ingredients, return:
{{"ingredients": []}}"""

        extract_response = client.client.messages.create(
            model=client.model,
            max_tokens=500,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                    {'type': 'text', 'text': extract_prompt}
                ]
            }]
        )

        extract_text = extract_response.content[0].text.strip()
        print(f'  Extraction response ({len(extract_text)} chars): {extract_text[:200]}...')

        # Try to parse JSON
        import re
        json_match = re.search(r'\{[^{}]*"ingredients"[^{}]*\[[^\]]*\][^{}]*\}', extract_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                ingredients = data.get('ingredients', [])
                print(f'  ✓ Extracted {len(ingredients)} ingredients: {ingredients}')
            except:
                print(f'  ❌ JSON parsing failed')
        else:
            print(f'  ❌ No JSON found in response')

    # STEP 6: Close panel/tab
    print(f'\nSTEP 6: Closing panel/tab with Escape...')
    client.execute_action('key', text='Escape')
    time.sleep(2)

    save_screenshot(client, f'/tmp/debug_recipe{recipe_num}_5_after_escape.png',
                   f'After Escape for {recipe_name}')


def main():
    print('='*70)
    print('DEBUG: Investigating Aheobakjin and Aubergines au sésame failures')
    print('='*70)

    client = AnthropicComputerClient()
    screen_mgr = NotionScreenManager(client)

    # Switch to Notion once
    print('\n[SETUP] Switching to Notion...')
    screen_mgr.switch_to('Notion')

    try:
        # Debug Aheobakjin
        debug_recipe(client, screen_mgr, 'Aheobakjin', 1)

        # Wait between recipes
        print('\n\nWaiting 5 seconds before next recipe...\n')
        time.sleep(5)

        # Debug Aubergines au sésame
        debug_recipe(client, screen_mgr, 'Aubergines au sésame', 2)

    finally:
        # Switch back to iTerm2
        print(f'\n\n[TEARDOWN] Switching back to iTerm2...')
        screen_mgr.switch_back()
        screen_mgr.play_notification()

    print('\n' + '='*70)
    print('DEBUG COMPLETE')
    print('='*70)
    print('\nScreenshots saved to:')
    print('  /tmp/debug_recipe1_*.png (Aheobakjin)')
    print('  /tmp/debug_recipe2_*.png (Aubergines au sésame)')
    print('\nPlease review screenshots to understand the failures.')
    print('='*70)


if __name__ == "__main__":
    main()
