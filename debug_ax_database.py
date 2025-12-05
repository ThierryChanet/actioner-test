#!/usr/bin/env python3
"""
Debug script to diagnose AX database navigation issues.
This will help identify why database rows aren't being detected.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.navigator import NotionNavigator
from src.ax.utils import find_elements_by_role


def debug_database_structure():
    """Debug the structure of the current Notion database view."""
    print("\n" + "="*70)
    print("AX DATABASE STRUCTURE DEBUGGER")
    print("="*70 + "\n")
    
    # Initialize
    ax_client = AXClient()
    detector = NotionDetector(ax_client)
    navigator = NotionNavigator(detector)
    
    # Find Notion app
    print("1. Looking for Notion app...")
    if not detector.ensure_notion_active(debug=True):
        print("❌ Notion app not found or not accessible")
        print("\nTroubleshooting:")
        print("  - Make sure Notion desktop app is running")
        print("  - Make sure you've granted Accessibility permissions")
        return
    
    print("✅ Notion app found and activated\n")
    
    # Get current page info
    print("2. Current page information:")
    current_title = detector.get_page_title()
    is_loading = detector.is_loading()
    print(f"   Title: {current_title}")
    print(f"   Loading: {is_loading}")
    print()
    
    # Check content area
    print("3. Checking content area...")
    content_area = detector.get_content_area(debug=True)
    if not content_area:
        print("❌ No content area found!")
        print("\nTroubleshooting:")
        print("  - Make sure you're viewing a database (table/board/gallery)")
        print("  - Try clicking into the database view")
        return
    
    print(f"✅ Content area found: {content_area}")
    print(f"   Role: {content_area.role}")
    print(f"   Title: {content_area.title}")
    print()
    
    # Look for AXRow elements
    print("4. Searching for AXRow elements...")
    row_elements = find_elements_by_role(content_area, "AXRow", max_depth=20)
    print(f"   Found {len(row_elements)} AXRow elements")
    
    if row_elements:
        print("\n   First 5 rows:")
        for i, row in enumerate(row_elements[:5]):
            title = row.title or row.get_text_content() or "(no title)"
            actions = row.get_actions()
            print(f"   {i+1}. {title[:50]}")
            print(f"      Actions: {actions}")
            print(f"      Role: {row.role}")
    else:
        print("   ℹ️  No AXRow elements found")
    print()
    
    # Look for links
    print("5. Searching for AXLink elements (fallback)...")
    links = find_elements_by_role(content_area, "AXLink", max_depth=15)
    print(f"   Found {len(links)} AXLink elements")
    
    if links:
        print("\n   First 10 links:")
        for i, link in enumerate(links[:10]):
            title = link.title or link.get_text_content() or "(no title)"
            print(f"   {i+1}. {title[:50]}")
    else:
        print("   ℹ️  No AXLink elements found")
    print()
    
    # Look for buttons
    print("6. Searching for AXButton elements...")
    buttons = find_elements_by_role(content_area, "AXButton", max_depth=15)
    print(f"   Found {len(buttons)} AXButton elements")
    
    if buttons:
        print("\n   First 10 buttons:")
        for i, button in enumerate(buttons[:10]):
            title = button.title or button.get_text_content() or "(no title)"
            print(f"   {i+1}. {title[:50]}")
    print()
    
    # Try the actual get_database_rows method
    print("7. Testing get_database_rows() method...")
    rows = navigator.get_database_rows()
    print(f"   Result: {len(rows)} rows found")
    
    if rows:
        print("\n   Detected rows:")
        for i, row in enumerate(rows[:10]):
            print(f"   {i+1}. {row['title'][:50]}")
    else:
        print("\n   ❌ No rows detected!")
        print("\n   Possible issues:")
        print("   - The current view is not a database")
        print("   - The database structure has changed")
        print("   - Elements are not clickable/accessible")
    print()
    
    # Try to find all elements with certain roles
    print("8. Scanning for all common element types...")
    for role in ["AXTable", "AXGroup", "AXScrollArea", "AXCell", "AXStaticText"]:
        elements = find_elements_by_role(content_area, role, max_depth=10)
        if elements:
            print(f"   - {role}: {len(elements)} found")
    
    print("\n" + "="*70)
    print("DIAGNOSIS COMPLETE")
    print("="*70)
    print("\nNext steps:")
    print("1. If no rows found, try switching to a different database view")
    print("2. Make sure you're viewing a table/board/gallery (not a page)")
    print("3. Try clicking on the database to ensure it's in focus")
    print("4. Share the output above for further debugging")


if __name__ == '__main__':
    try:
        debug_database_structure()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

