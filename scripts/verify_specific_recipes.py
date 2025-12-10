#!/usr/bin/env python3
"""
Verify specific recipes by comparing Computer Use extraction vs API Gold Standard.

This tool extracts specified recipes using both methods and compares the results.
"""

import os
import sys
import subprocess
import json
from typing import List, Dict
from datetime import datetime

# Add src to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.validation.notion_api import NotionAPIClient

# Hardcoded Recipe database ID
RECIPE_DATABASE_ID = "5bb4c854c109480ebd7c6112e357b4e5"


def extract_recipe_with_computer_use(recipe_name: str) -> List[str]:
    """Extract ingredients using Computer Use agent."""
    print(f'\n  [Computer Use] Extracting: {recipe_name}')

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

        # Extract bullet points
        ingredients = []
        for line in output.split('\n'):
            if line.strip().startswith('- '):
                ingredient = line.strip()[2:].strip()
                if ingredient:
                    ingredients.append(ingredient)

        print(f'    ✅ Found {len(ingredients)} ingredients')
        return ingredients

    except subprocess.TimeoutExpired:
        print(f'    ❌ Timeout')
        return []
    except Exception as e:
        print(f'    ❌ Error: {e}')
        return []


def extract_recipe_with_api(recipe_name: str, notion_token: str) -> List[str]:
    """Extract ingredients using Notion API."""
    print(f'  [API] Extracting: {recipe_name}')

    try:
        client = NotionAPIClient(notion_token)

        # Query database for pages
        pages = client.query_database(RECIPE_DATABASE_ID, page_size=100)

        # Find matching recipe
        target_page = None
        for page in pages:
            properties = page.get('properties', {})
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_array = prop_data.get('title', [])
                    if title_array:
                        page_title = ''.join([t.get('plain_text', '') for t in title_array])
                        if page_title.strip() == recipe_name.strip():
                            target_page = page
                            break
            if target_page:
                break

        if not target_page:
            print(f'    ⚠️  Recipe not found in database')
            return []

        # Get all blocks
        blocks = client.get_all_blocks_recursive(target_page['id'])

        # Extract ingredients (bulleted list items)
        ingredients = []
        for block in blocks:
            block_type = block.get('type')
            if block_type in ['bulleted_list_item', 'numbered_list_item']:
                rich_text = block.get(block_type, {}).get('rich_text', [])
                text_parts = [rt.get('plain_text', '') for rt in rich_text]
                text = ''.join(text_parts).strip()
                if text:
                    ingredients.append(text)

        print(f'    ✅ Found {len(ingredients)} ingredients')
        return ingredients

    except Exception as e:
        print(f'    ❌ Error: {e}')
        return []


def compare_ingredients(
    recipe_name: str,
    cu_ingredients: List[str],
    api_ingredients: List[str]
) -> Dict:
    """Compare ingredients from both sources."""

    # Normalize for comparison
    def normalize(text):
        return text.lower().strip().replace('.', '').replace(',', '')

    cu_set = set(normalize(ing) for ing in cu_ingredients)
    api_set = set(normalize(ing) for ing in api_ingredients)

    matched = cu_set & api_set
    missing = api_set - cu_set  # In API but not in Computer Use
    extra = cu_set - api_set    # In Computer Use but not in API

    # Calculate metrics
    precision = len(matched) / len(cu_set) if cu_set else 0
    recall = len(matched) / len(api_set) if api_set else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'recipe_name': recipe_name,
        'cu_count': len(cu_ingredients),
        'api_count': len(api_ingredients),
        'matched': len(matched),
        'missing': len(missing),
        'extra': len(extra),
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'cu_ingredients': cu_ingredients,
        'api_ingredients': api_ingredients,
        'missing_list': list(missing),
        'extra_list': list(extra)
    }


def main():
    """Verify specific recipes against gold standard."""
    print("="*70)
    print("RECIPE VERIFICATION: Computer Use vs API Gold Standard")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get Notion token
    notion_token = os.environ.get('NOTION_TOKEN')
    if not notion_token or notion_token == 'your_notion_integration_token_here':
        print("❌ Error: NOTION_TOKEN not set in .env")
        sys.exit(1)

    # Recipes to verify (from Computer Use test)
    recipes_to_verify = [
        'Topinambours au vinaigre',
        'Velouté Potimarron',
        'Aheobakian',
        'Thai omelet',
        'Aubergines au sésame'
    ]

    print(f"Verifying {len(recipes_to_verify)} recipes:")
    for r in recipes_to_verify:
        print(f"  - {r}")
    print()

    results = []

    for idx, recipe_name in enumerate(recipes_to_verify, 1):
        print(f"\n[{idx}/{len(recipes_to_verify)}] {recipe_name}")
        print("-" * 70)

        # Extract with both methods
        cu_ingredients = extract_recipe_with_computer_use(recipe_name)
        api_ingredients = extract_recipe_with_api(recipe_name, notion_token)

        # Compare
        comparison = compare_ingredients(recipe_name, cu_ingredients, api_ingredients)
        results.append(comparison)

    # Print detailed comparison
    print("\n" + "="*70)
    print("DETAILED COMPARISON")
    print("="*70)

    for comp in results:
        f1 = comp['f1_score']
        status = '✅' if f1 >= 0.9 else '⚠️' if f1 >= 0.7 else '❌'

        print(f"\n{status} {comp['recipe_name']}")
        print(f"  Computer Use: {comp['cu_count']} ingredients")
        print(f"  API (Gold):   {comp['api_count']} ingredients")
        print(f"  Matched:      {comp['matched']}")
        print(f"  Precision:    {comp['precision']:.1%}")
        print(f"  Recall:       {comp['recall']:.1%}")
        print(f"  F1 Score:     {comp['f1_score']:.1%}")

        if comp['missing_list']:
            print(f"\n  Missing (in API but not extracted by Computer Use):")
            for ing in comp['missing_list']:
                print(f"    - {ing}")

        if comp['extra_list']:
            print(f"\n  Extra (extracted by Computer Use but not in API):")
            for ing in comp['extra_list']:
                print(f"    + {ing}")

    # Overall summary
    if results:
        avg_f1 = sum(r['f1_score'] for r in results) / len(results)
        avg_precision = sum(r['precision'] for r in results) / len(results)
        avg_recall = sum(r['recall'] for r in results) / len(results)

        print("\n" + "="*70)
        print("OVERALL METRICS")
        print("="*70)
        print(f"Recipes verified:   {len(results)}")
        print(f"Average Precision:  {avg_precision:.1%}")
        print(f"Average Recall:     {avg_recall:.1%}")
        print(f"Average F1 Score:   {avg_f1:.1%}")
        print("="*70)

        # Save results
        output_file = 'verification_results.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'verified_at': datetime.now().isoformat(),
                'recipes': results,
                'summary': {
                    'count': len(results),
                    'avg_precision': avg_precision,
                    'avg_recall': avg_recall,
                    'avg_f1': avg_f1
                }
            }, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Results saved to: {output_file}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)


if __name__ == "__main__":
    main()
