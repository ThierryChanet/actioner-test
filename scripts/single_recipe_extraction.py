#!/usr/bin/env python3
"""Quick test for a single recipe."""

import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from src.validation.notion_api import NotionAPIClient

recipe_name = sys.argv[1] if len(sys.argv) > 1 else "Velouté de Potimarron"
RECIPE_DATABASE_ID = "5bb4c854c109480ebd7c6112e357b4e5"

print("="*70)
print(f"TESTING: {recipe_name}")
print("="*70)

# Extract with Computer Use
print("\n[1/2] Computer Use Extraction")
print("-"*70)

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

    cu_ingredients = []
    for line in result.stdout.split('\n'):
        if line.strip().startswith('- '):
            ingredient = line.strip()[2:].strip()
            if ingredient:
                cu_ingredients.append(ingredient)

    print(f"✅ Found {len(cu_ingredients)} ingredients:")
    for ing in cu_ingredients:
        print(f"  • {ing}")

except Exception as e:
    print(f"❌ Error: {e}")
    cu_ingredients = []

# Extract with API
print(f"\n[2/2] API Extraction")
print("-"*70)

notion_token = os.getenv('NOTION_TOKEN')
if notion_token:
    try:
        client = NotionAPIClient(notion_token)
        pages = client.query_database(RECIPE_DATABASE_ID, page_size=100)

        # Find recipe
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

        if target_page:
            blocks = client.get_all_blocks_recursive(target_page['id'])
            api_ingredients = []
            for block in blocks:
                block_type = block.get('type')
                if block_type in ['bulleted_list_item', 'numbered_list_item']:
                    rich_text = block.get(block_type, {}).get('rich_text', [])
                    text = ''.join([rt.get('plain_text', '') for rt in rich_text]).strip()
                    if text:
                        api_ingredients.append(text)

            print(f"✅ Found {len(api_ingredients)} ingredients:")
            for ing in api_ingredients:
                print(f"  • {ing}")
        else:
            print(f"⚠️  Recipe not found in database")
            api_ingredients = []

    except Exception as e:
        print(f"❌ Error: {e}")
        api_ingredients = []
else:
    print("❌ NOTION_TOKEN not set")
    api_ingredients = []

# Compare
print(f"\n" + "="*70)
print("COMPARISON")
print("="*70)

if cu_ingredients and api_ingredients:
    def normalize(text):
        return text.lower().strip().replace('.', '').replace(',', '')

    cu_set = set(normalize(ing) for ing in cu_ingredients)
    api_set = set(normalize(ing) for ing in api_ingredients)

    matched = cu_set & api_set
    missing = api_set - cu_set
    extra = cu_set - api_set

    precision = len(matched) / len(cu_set) if cu_set else 0
    recall = len(matched) / len(api_set) if api_set else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    print(f"Computer Use:  {len(cu_ingredients)} ingredients")
    print(f"API (Gold):    {len(api_ingredients)} ingredients")
    print(f"Matched:       {len(matched)}")
    print(f"Precision:     {precision:.1%}")
    print(f"Recall:        {recall:.1%}")
    print(f"F1 Score:      {f1:.1%}")

    if missing:
        print(f"\nMissing from Computer Use:")
        for ing in missing:
            print(f"  - {ing}")

    if extra:
        print(f"\nExtra in Computer Use:")
        for ing in extra:
            print(f"  + {ing}")

    if f1 >= 0.9:
        print(f"\n✅ EXCELLENT: F1 Score {f1:.1%}")
    elif f1 >= 0.7:
        print(f"\n⚠️  GOOD: F1 Score {f1:.1%}")
    else:
        print(f"\n❌ NEEDS IMPROVEMENT: F1 Score {f1:.1%}")
else:
    print("⚠️  Cannot compare - one or both extractions failed")

print("="*70)
