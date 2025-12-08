#!/usr/bin/env python3
"""
GOLD STANDARD: Extract recipes using Notion API

This script extracts recipes directly from the Notion database using the API,
providing a gold standard baseline for comparison with Computer Use extraction.

Database ID: 5bb4c854c109480ebd7c6112e357b4e5
"""

import os
import sys
import json
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.validation.notion_api import NotionAPIClient


# Hardcoded Recipe database ID
RECIPE_DATABASE_ID = "5bb4c854c109480ebd7c6112e357b4e5"


def extract_ingredients_from_blocks(blocks: List[Dict[str, Any]]) -> List[str]:
    """Extract ingredients from Notion blocks.

    Looks for bulleted list items that contain ingredients.

    Args:
        blocks: List of Notion block objects

    Returns:
        List of ingredient strings
    """
    ingredients = []

    for block in blocks:
        block_type = block.get('type')

        # Check for bulleted list items (typical ingredient format)
        if block_type == 'bulleted_list_item':
            # Extract text from rich text
            rich_text = block.get(block_type, {}).get('rich_text', [])
            text_parts = [rt.get('plain_text', '') for rt in rich_text]
            text = ''.join(text_parts).strip()

            if text:
                ingredients.append(text)

        # Also check numbered lists
        elif block_type == 'numbered_list_item':
            rich_text = block.get(block_type, {}).get('rich_text', [])
            text_parts = [rt.get('plain_text', '') for rt in rich_text]
            text = ''.join(text_parts).strip()

            if text:
                ingredients.append(text)

    return ingredients


def get_recipe_name_from_page(page: Dict[str, Any]) -> str:
    """Extract recipe name from page properties.

    Args:
        page: Notion page object

    Returns:
        Recipe name as string
    """
    properties = page.get('properties', {})

    # Try common property names for recipe titles
    for prop_name in ['Name', 'NAME', 'Title', 'Recipe Name']:
        if prop_name in properties:
            prop = properties[prop_name]
            prop_type = prop.get('type')

            if prop_type == 'title':
                title_parts = prop.get('title', [])
                if title_parts:
                    return ''.join([t.get('plain_text', '') for t in title_parts])

    # Fallback: use page ID
    return f"Recipe {page.get('id', 'Unknown')[:8]}"


def extract_recipe_with_api(
    client: NotionAPIClient,
    page_id: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """Extract a single recipe using Notion API.

    Args:
        client: NotionAPIClient instance
        page_id: Notion page ID
        verbose: Print extraction progress

    Returns:
        Dictionary with recipe name and ingredients
    """
    try:
        # Get page metadata
        page = client.get_page(page_id)
        recipe_name = get_recipe_name_from_page(page)

        if verbose:
            print(f"  Extracting: {recipe_name}")

        # Get all blocks (including nested)
        blocks = client.get_all_blocks_recursive(page_id)

        # Extract ingredients
        ingredients = extract_ingredients_from_blocks(blocks)

        if verbose:
            print(f"    ✅ Found {len(ingredients)} ingredients")

        return {
            'name': recipe_name,
            'page_id': page_id,
            'ingredients': ingredients,
            'block_count': len(blocks)
        }

    except Exception as e:
        if verbose:
            print(f"    ❌ Error: {e}")

        return {
            'name': 'Unknown',
            'page_id': page_id,
            'ingredients': [],
            'error': str(e)
        }


def extract_all_recipes(
    notion_token: str,
    database_id: str = RECIPE_DATABASE_ID,
    limit: int = 10,
    verbose: bool = False
) -> List[Dict[str, Any]]:
    """Extract all recipes from the database using Notion API.

    Args:
        notion_token: Notion integration token
        database_id: Database ID (defaults to hardcoded Recipe DB)
        limit: Maximum number of recipes to extract
        verbose: Print progress information

    Returns:
        List of recipe dictionaries with name and ingredients
    """
    client = NotionAPIClient(notion_token)

    if verbose:
        print("Connecting to Notion API...")

    # Test connection
    try:
        # Get database metadata
        database = client.client.databases.retrieve(database_id=database_id)
        db_title = database.get('title', [{}])[0].get('plain_text', 'Unknown Database')
        if verbose:
            print(f"✓ Connected to database: {db_title}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Notion API: {e}")

    # Query database for pages
    if verbose:
        print(f"Querying for up to {limit} recipes...")

    try:
        response = client.client.databases.query(
            database_id=database_id,
            page_size=min(limit, 100)
        )

        pages = response.get('results', [])

        if verbose:
            print(f"✓ Found {len(pages)} recipes")
    except Exception as e:
        raise RuntimeError(f"Failed to query database: {e}")

    # Extract each recipe
    recipes = []

    for idx, page in enumerate(pages, 1):
        if verbose:
            print(f"\n[{idx}/{len(pages)}]", end=" ")

        recipe = extract_recipe_with_api(client, page['id'], verbose=verbose)
        recipes.append(recipe)

    return recipes


def save_gold_standard(
    recipes: List[Dict[str, Any]],
    output_file: str = 'gold_standard_recipes.json'
) -> None:
    """Save gold standard results to JSON file.

    Args:
        recipes: List of recipe dictionaries
        output_file: Output JSON filename
    """
    output_data = {
        'extraction_method': 'Notion API (Gold Standard)',
        'database_id': RECIPE_DATABASE_ID,
        'extracted_at': datetime.now().isoformat(),
        'recipe_count': len(recipes),
        'recipes': recipes
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved gold standard to: {output_file}")


def main():
    """Extract recipes using Notion API as gold standard."""
    print("="*70)
    print("GOLD STANDARD EXTRACTION: Notion API")
    print("="*70)
    print(f"Database ID: {RECIPE_DATABASE_ID}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get Notion token from environment
    notion_token = os.environ.get('NOTION_TOKEN')

    if not notion_token:
        print("❌ Error: NOTION_TOKEN environment variable not set")
        print("\nTo set it, add to .env file:")
        print("  NOTION_TOKEN=secret_your_token_here")
        print("\nOr export it:")
        print("  export NOTION_TOKEN='secret_your_token_here'")
        sys.exit(1)

    try:
        # Extract recipes (top 10 by default)
        recipes = extract_all_recipes(
            notion_token=notion_token,
            database_id=RECIPE_DATABASE_ID,
            limit=10,
            verbose=True
        )

        # Print results
        print("\n" + "="*70)
        print("EXTRACTION RESULTS")
        print("="*70)

        for recipe in recipes:
            status = '✅' if recipe['ingredients'] else '❌'
            print(f"\n{status} {recipe['name']}:")

            if recipe['ingredients']:
                for ing in recipe['ingredients']:
                    print(f"  • {ing}")
            else:
                if 'error' in recipe:
                    print(f"  (Error: {recipe['error']})")
                else:
                    print(f"  (No ingredients found)")

        # Summary
        success_count = sum(1 for r in recipe if r['ingredients'])
        total_ingredients = sum(len(r['ingredients']) for r in recipes)

        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Recipes extracted:      {len(recipes)}")
        print(f"Successful extractions: {success_count}")
        print(f"Total ingredients:      {total_ingredients}")
        print("="*70)

        # Save to JSON
        save_gold_standard(recipes)

        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
