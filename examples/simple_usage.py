#!/usr/bin/env python3
"""
Simple example showing the easiest way to extract database pages.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database_extractor import extract_database_pages


# Get credentials
notion_token = os.environ.get('NOTION_TOKEN', 'your-token-here')
database_id = 'your-database-id'

# Extract 10 pages
results = extract_database_pages(
    database_id=database_id,
    notion_token=notion_token,
    limit=10,
    verbose=True
)

# Print results
print(f"\n✅ Extracted {len(results)} pages:")
for i, result in enumerate(results, 1):
    print(f"{i}. {result.title} ({len(result.blocks)} blocks)")

