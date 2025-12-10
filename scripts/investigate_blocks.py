#!/usr/bin/env python3
"""Investigate block types in a recipe to improve API extraction."""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from src.validation.notion_api import NotionAPIClient

recipe_name = sys.argv[1] if len(sys.argv) > 1 else "Velouté Potimarron"

notion_token = os.getenv('NOTION_TOKEN')
client = NotionAPIClient(notion_token)

# Find the recipe
pages = client.query_database("5bb4c854c109480ebd7c6112e357b4e5", page_size=100)

target_page = None
for page in pages:
    properties = page.get('properties', {})
    for prop_name, prop_data in properties.items():
        if prop_data.get('type') == 'title':
            title_array = prop_data.get('title', [])
            if title_array:
                title = ''.join([t.get('plain_text', '') for t in title_array])
                if title.strip() == recipe_name.strip():
                    target_page = page
                    break
    if target_page:
        break

if target_page:
    print(f"Found recipe: {title}")
    print(f"Page ID: {target_page['id']}")

    # Show properties first
    print("\n" + "="*70)
    print("DATABASE PROPERTIES")
    print("="*70)

    properties = target_page.get('properties', {})
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get('type')
        print(f"\n{prop_name} ({prop_type}):")

        # Extract value based on type
        if prop_type == 'title':
            title_array = prop_data.get('title', [])
            value = ''.join([t.get('plain_text', '') for t in title_array])
            print(f"  Value: '{value}'")

        elif prop_type == 'multi_select':
            options = prop_data.get('multi_select', [])
            values = [opt.get('name', '') for opt in options]
            print(f"  Values: {values}")

        elif prop_type == 'select':
            option = prop_data.get('select')
            if option:
                print(f"  Value: '{option.get('name', '')}'")

        elif prop_type == 'relation':
            relations = prop_data.get('relation', [])
            print(f"  Related pages: {len(relations)}")
            for rel in relations[:3]:  # Show first 3
                print(f"    - {rel.get('id', '')}")

        elif prop_type == 'rich_text':
            rich_text = prop_data.get('rich_text', [])
            text = ''.join([t.get('plain_text', '') for t in rich_text])
            print(f"  Value: '{text[:100]}'")

        else:
            print(f"  (type not displayed)")

    print("\n" + "="*70)
    print("BLOCK ANALYSIS")
    print("="*70)

    blocks = client.get_all_blocks_recursive(target_page['id'])

    print(f"\nTotal blocks: {len(blocks)}")

    block_types = {}
    for idx, block in enumerate(blocks):
        block_type = block.get('type')
        block_types[block_type] = block_types.get(block_type, 0) + 1

        # Show details for each block
        print(f"\n[Block {idx+1}] Type: {block_type}")
        print(f"  ID: {block.get('id')}")
        print(f"  Has children: {block.get('has_children', False)}")

        # Try to extract text
        text = client.extract_text_from_block(block)
        if text:
            print(f"  Text: '{text[:100]}'")
        else:
            print(f"  Text: (none)")

        # Show block data structure
        block_data = block.get(block_type, {})
        if 'rich_text' in block_data:
            rt = block_data['rich_text']
            print(f"  Rich text items: {len(rt)}")
            if rt:
                print(f"  First rich text: '{rt[0].get('plain_text', '')[:50]}'")

        # Check for children
        if block.get('has_children'):
            print(f"  ⚠️  This block has children that might contain ingredients!")

    print(f"\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    for btype, count in sorted(block_types.items()):
        print(f"  {btype}: {count}")

else:
    print(f"Recipe '{recipe_name}' not found")
