#!/usr/bin/env python3
"""
Example: Extract the first 10 pages from a Recipe database

This script demonstrates how to use the database extraction functionality
to retrieve and save content from a Notion database.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database_extractor import extract_database_pages


def main():
    # Get your Notion token from environment variable
    notion_token = os.environ.get('NOTION_TOKEN')
    if not notion_token:
        print("Error: NOTION_TOKEN environment variable not set")
        print("\nTo set it:")
        print("  export NOTION_TOKEN='your_secret_token_here'")
        sys.exit(1)
    
    # Your Recipe database ID
    # You can find this in the database URL: 
    # https://www.notion.so/workspace/DATABASE_ID?v=...
    database_id = input("Enter your Recipe database ID: ").strip()
    
    if not database_id:
        print("Error: Database ID is required")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("EXTRACTING RECIPE DATABASE")
    print("="*70 + "\n")
    
    try:
        # Extract first 10 pages from the database
        results = extract_database_pages(
            database_id=database_id,
            notion_token=notion_token,
            limit=10,
            output_dir='output',
            output_format='both',  # Save as both JSON and CSV
            verbose=True
        )
        
        # Display summary
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"\nSuccessfully extracted {len(results)} recipes:\n")
        
        for i, result in enumerate(results, 1):
            print(f"{i:2d}. {result.title}")
            print(f"    └─ {len(result.blocks)} content blocks")
        
        print(f"\n✓ Files saved to: output/")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

