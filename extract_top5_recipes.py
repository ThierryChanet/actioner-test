#!/usr/bin/env python3
"""Extract ingredients from top 5 recipes in Notion database."""

import sys
import time
import json
sys.path.insert(0, '.')

from src.agent.anthropic_computer_client import AnthropicComputerClient
from src.agent.screen_manager import NotionScreenManager

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
    print('='*60)

    for idx, recipe_name in enumerate(recipes, 1):
        print(f'\n[{idx}/5] Processing: {recipe_name}')

        try:
            # Switch to Notion
            with screen_mgr.for_action(f'extracting {recipe_name}'):
                # Click on recipe using vision
                result = client.execute_action('click', text=recipe_name)
                if not result.success:
                    print(f'  ⚠️  Could not find {recipe_name}')
                    all_ingredients[recipe_name] = []
                    continue

                time.sleep(2)

                # Take screenshot of open panel
                panel_screenshot = client.take_screenshot(use_cache=False)

                # Extract ingredients using vision
                prompt = f"""Look at this Notion page for "{recipe_name}".
Extract ONLY the ingredients list. Return as JSON:
{{"ingredients": ["ingredient 1", "ingredient 2", ...]}}"""

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

                # Parse JSON
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                try:
                    data = json.loads(response_text)
                    ingredients = data.get('ingredients', [])
                    all_ingredients[recipe_name] = ingredients
                    print(f'  ✓ Found {len(ingredients)} ingredients')
                except Exception as e:
                    print(f'  ⚠️  Could not parse ingredients: {e}')
                    all_ingredients[recipe_name] = []

                # Close panel with Escape
                client.execute_action('key', text='Escape')
                time.sleep(1)

        except Exception as e:
            print(f'  ❌ Error: {e}')
            all_ingredients[recipe_name] = []

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

if __name__ == "__main__":
    main()
