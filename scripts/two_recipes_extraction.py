#!/usr/bin/env python3
"""
TEST: Extract two recipes successively to verify the working implementation.
"""

import subprocess
import sys
import re
from datetime import datetime


def extract_recipe(recipe_name: str) -> list:
    """Extract ingredients using the official agent."""
    print(f'\n{"="*70}')
    print(f'Extracting: {recipe_name}')
    print(f'{"="*70}')

    prompt = (
        f'Switch to Notion application. '
        f'In the Recipes database table, find "{recipe_name}" in the NAME column. '
        f'Hover over the recipe name to reveal the OPEN button to the left. '
        f'Click the OPEN button to open the side panel. '
        f'Extract ALL ingredients from the panel and list them. '
        f'IMPORTANT: Press Escape key to close the side panel. '
        f'Verify the panel is closed before finishing.'
    )

    try:
        result = subprocess.run(
            ['python', '-m', 'src.agent', prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        output = result.stdout

        # Extract bullet points (agent lists ingredients this way)
        ingredients = []
        for line in output.split('\n'):
            if line.strip().startswith('- '):
                ingredient = line.strip()[2:].strip()
                if ingredient:
                    ingredients.append(ingredient)

        if ingredients:
            print(f'  ✅ Extracted {len(ingredients)} ingredients:')
            for ing in ingredients:
                print(f'    • {ing}')
            return ingredients
        else:
            print(f'  ⚠️  No ingredients found')
            print(f'  Output: {output[:300]}...')
            return []

    except subprocess.TimeoutExpired:
        print(f'  ❌ Timeout')
        return []
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return []


def main():
    """Test extraction on two recipes."""
    print("="*70)
    print("TEST: Extract Two Recipes Successively")
    print("Using: Official Anthropic Computer Use Agent")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Test with first two recipes
    recipes = [
        'Topinambours au vinaigre',
        'Velouté Potimarron'
    ]

    results = {}

    for idx, recipe in enumerate(recipes, 1):
        print(f'\n[{idx}/2] Processing: {recipe}')
        ingredients = extract_recipe(recipe)
        results[recipe] = ingredients

    # Print summary
    print(f'\n{"="*70}')
    print('RESULTS')
    print(f'{"="*70}')

    for recipe, ingredients in results.items():
        status = '✅' if ingredients else '❌'
        print(f'\n{status} {recipe}:')
        if ingredients:
            for ing in ingredients:
                print(f'  • {ing}')
        else:
            print('  (Failed)')

    # Verify success
    success_count = sum(1 for ing in results.values() if ing)

    print(f'\n{"="*70}')
    print(f'Success: {success_count}/2 recipes')
    print(f'{"="*70}')

    if success_count == 2:
        print('✅ TEST PASSED: Both recipes extracted successfully!')
        return True
    else:
        print(f'❌ TEST FAILED: Only {success_count}/2 succeeded')
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
