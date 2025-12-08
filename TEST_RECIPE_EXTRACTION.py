#!/usr/bin/env python3
"""
COMPREHENSIVE TEST: Extract ingredients from top 5 Notion recipes

This test uses the official Anthropic Computer Use agent which properly
handles hover interactions to reveal and click the "OPEN" button in Notion.

WORKING IMPLEMENTATION:
- Uses: python -m src.agent
- Hover triggers the OPEN button to appear
- Click OPEN button opens side panel
- Extract ingredients from panel
- Close panel with Escape

SUCCESS CRITERIA:
- All 5 recipes should extract successfully (100% success rate)
- Ingredients should be unique per recipe (no mixing)
"""

import subprocess
import sys
import json
import re
from datetime import datetime


def extract_recipe_with_agent(recipe_name: str) -> list:
    """
    Extract ingredients from a recipe using the official Computer Use agent.

    Args:
        recipe_name: Name of the recipe in Notion

    Returns:
        List of ingredient strings
    """
    print(f'\n{"="*70}')
    print(f'Extracting: {recipe_name}')
    print(f'{"="*70}')

    # Construct the agent prompt - WORKING IMPLEMENTATION
    # Key: Don't press Escape at start (interrupts agent in terminal)
    # Agent handles switching to Notion automatically
    prompt = (
        f'Switch to Notion application. '
        f'In the Recipes database table, find "{recipe_name}" in the NAME column. '
        f'Hover over the recipe name to reveal the OPEN button to the left. '
        f'Click the OPEN button to open the side panel. '
        f'Extract ALL ingredients from the panel and list them. '
        f'Then close the panel.'
    )

    try:
        # Run the agent
        result = subprocess.run(
            ['python', '-m', 'src.agent', prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Parse the output to extract ingredients
        output = result.stdout

        # Look for JSON in the output
        # The agent returns ingredients in its response
        # Try to extract them

        # First, look for explicit JSON format
        json_match = re.search(r'\{[^{}]*"ingredients"[^{}]*\[[^\]]*\][^{}]*\}', output, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                ingredients = data.get('ingredients', [])
                print(f'  ✅ Extracted {len(ingredients)} ingredients')
                for ing in ingredients:
                    print(f'    • {ing}')
                return ingredients
            except json.JSONDecodeError:
                pass

        # Fallback: Look for bullet points in agent response
        # The agent typically lists ingredients as bullet points
        ingredients = []
        for line in output.split('\n'):
            # Look for lines that start with "- " (bullet points)
            if line.strip().startswith('- '):
                ingredient = line.strip()[2:].strip()
                if ingredient:
                    ingredients.append(ingredient)

        if ingredients:
            print(f'  ✅ Extracted {len(ingredients)} ingredients (from bullet points)')
            for ing in ingredients:
                print(f'    • {ing}')
            return ingredients

        print(f'  ⚠️  No ingredients found in output')
        print(f'  Output preview: {output[:200]}...')
        return []

    except subprocess.TimeoutExpired:
        print(f'  ❌ Timeout after 120 seconds')
        return []
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return []


def main():
    """Extract ingredients from top 5 recipes using the official agent."""
    print("="*70)
    print("COMPREHENSIVE TEST: Top 5 Recipe Ingredient Extraction")
    print("Using: Official Anthropic Computer Use Agent")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # List of top 5 recipes to extract
    recipes = [
        'Topinambours au vinaigre',
        'Velouté Potimarron',
        'Aheobakian',
        'Thai omelet',
        'Aubergines au sésame'
    ]

    all_ingredients = {}

    print('Configuration:')
    print(f'  - Recipes to extract: {len(recipes)}')
    print(f'  - Method: Official Computer Use Agent')
    print(f'  - Hover + OPEN button pattern')
    print('='*70)

    # Process each recipe
    for idx, recipe_name in enumerate(recipes, 1):
        print(f'\n[{idx}/5] Processing: {recipe_name}')
        ingredients = extract_recipe_with_agent(recipe_name)
        all_ingredients[recipe_name] = ingredients

    # Print final results
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
    print(f'Recipes processed:      {len(recipes)}')
    print(f'Successful extractions: {success_count}')
    print(f'Failed extractions:     {len(recipes) - success_count}')
    print(f'Success rate:           {success_count/len(recipes)*100:.1f}%')
    print(f'Total ingredients:      {total_ingredients}')
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
