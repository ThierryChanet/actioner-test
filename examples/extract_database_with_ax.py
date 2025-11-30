#!/usr/bin/env python3
"""
Example: Extract database pages using AX navigation (no API needed!)

This script navigates through database rows in the Notion desktop app
and extracts content by actually clicking on rows and reading the pages.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.navigator import NotionNavigator
from src.notion.extractor import NotionExtractor
from src.notion.database_ax_extractor import DatabaseAXExtractor
from src.ocr.fallback import OCRHandler
from src.output.json_writer import JSONWriter


def main():
    print("\n" + "="*70)
    print("DATABASE EXTRACTION WITH AX NAVIGATION")
    print("="*70)
    print("\nThis will extract pages by clicking through database rows")
    print("Make sure you have a database view open in Notion\n")
    
    # Ask for confirmation
    response = input("Ready to start? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        return
    
    # Initialize components
    print("\nInitializing...")
    ax_client = AXClient()
    detector = NotionDetector(ax_client)
    navigator = NotionNavigator(detector)
    extractor = NotionExtractor(detector)
    
    # Setup OCR
    ocr_handler = OCRHandler()
    if ocr_handler.is_available():
        extractor.set_ocr_handler(ocr_handler)
        print(f"✓ OCR enabled: {ocr_handler.get_active_handler()}")
    
    # Find Notion
    if not detector.ensure_notion_active():
        print("❌ Notion app not found. Please start Notion and open a database.")
        sys.exit(1)
    
    print("✓ Notion app found")
    
    # Check current page
    current_title = detector.get_page_title()
    print(f"✓ Current view: {current_title}")
    
    # Initialize database extractor
    db_extractor = DatabaseAXExtractor(detector, navigator, extractor)
    
    # Preview rows
    print("\nScanning database rows...")
    preview = db_extractor.preview_database(limit=10)
    
    if not preview:
        print("❌ No database rows found.")
        print("   Make sure you're viewing a database (table, board, gallery, etc.)")
        sys.exit(1)
    
    print(f"\nFound {len(preview)} rows:")
    for item in preview:
        print(f"  {item['index']+1}. {item['title']}")
    
    # Ask how many to extract
    limit = input(f"\nHow many pages to extract? (1-{len(preview)}, default: 10): ").strip()
    if not limit:
        limit = 10
    else:
        try:
            limit = int(limit)
            limit = min(max(1, limit), len(preview))
        except ValueError:
            limit = 10
    
    print(f"\nExtracting {limit} pages...")
    print("="*70 + "\n")
    
    # Extract
    results = db_extractor.extract_database_pages(
        limit=limit,
        use_ocr=True,
        navigation_delay=1.0
    )
    
    # Save results
    print("\nSaving results...")
    json_writer = JSONWriter("output")
    
    for result in results:
        json_path = json_writer.write_extraction(result)
        print(f"  ✓ Saved: {json_path}")
    
    # Summary
    total_blocks = sum(len(r.blocks) for r in results)
    
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE!")
    print("="*70)
    print(f"Pages extracted: {len(results)}")
    print(f"Total blocks: {total_blocks}")
    print(f"Output directory: output/")
    print("="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

