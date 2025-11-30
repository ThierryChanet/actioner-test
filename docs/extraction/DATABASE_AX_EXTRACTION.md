# Database Extraction with AX Navigation

Extract database pages using **direct Accessibility actions** - no API token needed! This method actually navigates through your database by clicking on rows, just like you would manually.

## 🎯 Key Differences

| Feature | AX Navigation (This Guide) | API Method |
|---------|---------------------------|------------|
| **Token Required** | ❌ No | ✅ Yes |
| **Works Offline** | ✅ Yes | ❌ No |
| **Notion App Required** | ✅ Yes (desktop) | ❌ No |
| **Speed** | Slower (navigates UI) | Faster (direct API) |
| **Use Case** | Local extraction, no API access | Bulk extraction, automation |

## Quick Start

### Method 1: Command Line (Simplest)

```bash
# 1. Open your database in Notion desktop app
# 2. Make sure you're viewing the database (table/board/gallery view)
# 3. Run:

python -m src.cli extract-database-ax --limit 10
```

### Method 2: Interactive Script

```bash
python examples/extract_database_with_ax.py
```

### Method 3: Python API

```python
from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.navigator import NotionNavigator
from src.notion.extractor import NotionExtractor
from src.notion.database_ax_extractor import DatabaseAXExtractor

# Initialize
ax_client = AXClient()
detector = NotionDetector(ax_client)
navigator = NotionNavigator(detector)
extractor = NotionExtractor(detector)

# Create database extractor
db_extractor = DatabaseAXExtractor(detector, navigator, extractor)

# Extract 10 pages
results = db_extractor.extract_database_pages(limit=10)
```

## How It Works

The AX-based extractor:

1. **Scans** the current database view to find clickable rows
2. **Clicks** on each row to open the page
3. **Extracts** content using Accessibility APIs
4. **Navigates back** to the database
5. **Repeats** for the next row

This mimics how you would manually extract pages, but automated!

## Requirements

- ✅ Notion desktop app running
- ✅ Accessibility permissions enabled
- ✅ A database open in Notion
- ❌ No API token needed!

## Setup

### 1. Enable Accessibility Permissions

```bash
# Check permissions
python -m src.cli check-permissions

# If not enabled:
# System Settings > Privacy & Security > Accessibility
# Add your Terminal app
```

### 2. Open Your Database

1. Open Notion desktop app
2. Navigate to your database (Recipe, Projects, etc.)
3. Make sure you're in a list/table/board view (not a single page)

### 3. Run Extraction

```bash
python -m src.cli extract-database-ax --limit 10
```

## Command Line Usage

### Basic Extraction

```bash
# Extract first 10 pages
python -m src.cli extract-database-ax --limit 10
```

### Options

```bash
# Specify number of pages
--limit 20                    # Extract 20 pages

# Output format
--output json                 # JSON only (default)
--output csv                  # CSV only
--output both                 # Both formats

# OCR settings
--no-ocr                      # Disable OCR fallback

# Navigation timing
--navigation-delay 2.0        # Wait 2s after each navigation

# Verbose output
--verbose                     # Show detailed logging
```

### Complete Example

```bash
python -m src.cli extract-database-ax \
  --limit 10 \
  --output both \
  --navigation-delay 1.5 \
  --verbose
```

## List Database Rows

Preview what pages are in the database before extracting:

```bash
python -m src.cli list-database-rows
```

Output:
```
=======================================================================
DATABASE ROWS: Recipe Database
=======================================================================

  1. Chocolate Chip Cookies
  2. Banana Bread
  3. Pasta Carbonara
  4. Thai Green Curry
  ...

=======================================================================
Total rows: 45
=======================================================================
```

## Python API Usage

### Full Extraction

```python
from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.navigator import NotionNavigator
from src.notion.extractor import NotionExtractor
from src.notion.database_ax_extractor import DatabaseAXExtractor

# Initialize components
ax_client = AXClient()
detector = NotionDetector(ax_client)
navigator = NotionNavigator(detector)
extractor = NotionExtractor(detector)

# Activate Notion
detector.ensure_notion_active()

# Create database extractor
db_extractor = DatabaseAXExtractor(detector, navigator, extractor)

# Extract pages
results = db_extractor.extract_database_pages(
    limit=10,
    use_ocr=True,
    scroll_delay=0.3,
    navigation_delay=1.0
)

# Process results
for result in results:
    print(f"{result.title}: {len(result.blocks)} blocks")
```

### Preview Before Extracting

```python
# List available rows
rows = db_extractor.list_database_rows()
print(f"Found {len(rows)} rows:")
for row in rows:
    print(f"  - {row}")

# Preview with details
preview = db_extractor.preview_database(limit=10)
for item in preview:
    print(f"{item['index']}. {item['title']}")
```

### Extract Specific Pages

```python
# Extract specific pages by title
page_titles = [
    "Chocolate Chip Cookies",
    "Banana Bread",
    "Thai Green Curry"
]

results = db_extractor.extract_database_pages_by_titles(
    page_titles=page_titles,
    use_ocr=True
)
```

### Save Results

```python
from src.output.json_writer import JSONWriter
from src.output.csv_writer import CSVWriter

# Extract pages
results = db_extractor.extract_database_pages(limit=10)

# Save as JSON
json_writer = JSONWriter("output")
for result in results:
    json_writer.write_extraction(result)

# Save as CSV
csv_writer = CSVWriter("output")
for result in results:
    csv_writer.write_extraction(result)
```

## Output Format

Same as regular extraction:

### JSON
```json
{
  "title": "Chocolate Chip Cookies",
  "blocks": [
    {
      "type": "heading",
      "content": "Ingredients",
      "source": "ax",
      "order": 0
    }
  ],
  "metadata": {
    "source": "ax_navigation",
    "database_row_index": 0,
    "block_count": 15
  }
}
```

### CSV
| Order | Type    | Content     | Source | Role        |
|-------|---------|-------------|--------|-------------|
| 0     | heading | Ingredients | ax     | AXHeading   |
| 1     | text    | 2 cups flour| ax     | AXStaticText|

## Troubleshooting

### "No database rows found"

**Problem**: The extractor can't find any clickable rows.

**Solutions**:
1. Make sure you're viewing a database (not a single page)
2. Try switching to table view: View options > Table
3. Ensure the database isn't empty
4. The database might be loading - wait a few seconds

### "Failed to navigate to row"

**Problem**: Clicking on a row doesn't open the page.

**Solutions**:
1. Increase navigation delay: `--navigation-delay 2.0`
2. Check if Notion is responding (not frozen)
3. Try clicking manually first to verify it works
4. Some database views might not support navigation

### "Failed to navigate back to database"

**Problem**: Can't return to database after extracting a page.

**Solutions**:
1. Increase navigation delay
2. The extractor will try to navigate directly by database title
3. Make sure browser back navigation works (Cmd+[)

### Extraction is slow

**Expected**: AX navigation is slower than API extraction.

**Tips**:
- Reduce `navigation-delay` (but may cause errors)
- Disable OCR with `--no-ocr` if not needed
- Extract in smaller batches
- Use API method for bulk extraction

### Missing content

**Problem**: Some blocks aren't extracted.

**Solutions**:
1. Enable OCR (default)
2. Increase scroll delay: `--scroll-delay 0.5`
3. Check if content is in collapsed sections
4. Some content types might not be accessible via AX

## Performance

Typical extraction times (per page):
- Navigation: 1-3 seconds
- Content extraction: 2-10 seconds (depending on page size)
- Total: **3-13 seconds per page**

For 10 pages: **30-130 seconds** (0.5-2 minutes)

💡 **Tip**: For bulk extraction (100+ pages), use the API method instead!

## Comparison with API Method

### When to use AX Navigation:
- ✅ No API token available
- ✅ Working offline/locally
- ✅ Small batch extraction (< 20 pages)
- ✅ Need to verify visual layout
- ✅ Learning/testing purposes

### When to use API Method:
- ✅ Have API token
- ✅ Bulk extraction (50+ pages)
- ✅ Automated workflows
- ✅ Speed is important
- ✅ Working with databases regularly

## Examples

### Extract Recipe Database

```bash
# Open Recipe database in Notion
# Then run:
python -m src.cli extract-database-ax --limit 10 --output both
```

### Extract with Progress Tracking

```python
from src.notion.database_ax_extractor import DatabaseAXExtractor

# ... initialize components ...

db_extractor = DatabaseAXExtractor(detector, navigator, extractor)

# Preview first
preview = db_extractor.preview_database(limit=20)
print(f"Will extract {len(preview)} pages")

# Extract with custom handling
results = []
for i in range(len(preview)):
    print(f"Progress: {i+1}/{len(preview)}")
    
    # Navigate to row
    success = navigator.navigate_to_database_row(i)
    if success:
        # Extract
        result = extractor.extract_page()
        results.append(result)
        
        # Navigate back
        navigator.navigate_back()
        time.sleep(1)
```

### Extract Specific Recipes

```python
# Extract only specific recipes
recipes_to_extract = [
    "Chocolate Chip Cookies",
    "Banana Bread"
]

results = db_extractor.extract_database_pages_by_titles(
    page_titles=recipes_to_extract,
    use_ocr=True,
    navigation_delay=1.5
)

for result in results:
    print(f"Extracted: {result.title}")
```

## Advanced Usage

### Custom Navigation Timing

```python
# Slower, more reliable
results = db_extractor.extract_database_pages(
    limit=10,
    navigation_delay=2.0,  # Wait 2s after navigation
    scroll_delay=0.5       # Slower scrolling
)

# Faster, might be less reliable
results = db_extractor.extract_database_pages(
    limit=10,
    navigation_delay=0.5,  # Minimal delay
    scroll_delay=0.1       # Fast scrolling
)
```

### Error Recovery

```python
results = []
for i in range(10):
    try:
        # Try to navigate
        if navigator.navigate_to_database_row(i):
            result = extractor.extract_page()
            results.append(result)
            navigator.navigate_back()
        else:
            print(f"Skipped row {i}")
    except Exception as e:
        print(f"Error on row {i}: {e}")
        # Try to recover - go back to database
        navigator.navigate_to_page("Database Name")
        continue
```

## Tips & Best Practices

1. **Start with list view**: `list-database-rows` to see what's available
2. **Test with small limit**: Try `--limit 3` first to test
3. **Use verbose mode**: `--verbose` for debugging
4. **Save incremental**: Save after each page to avoid losing data
5. **Monitor Notion**: Keep an eye on the Notion app while extracting
6. **Close other apps**: Free up memory for smoother navigation
7. **Stable connection**: Although offline-capable, stable system helps

## Limitations

- ⚠️ Slower than API method
- ⚠️ Requires Notion desktop app
- ⚠️ May not work with all database view types
- ⚠️ Can't filter or sort (uses current view)
- ⚠️ Limited to visible rows in current view
- ⚠️ May miss linked databases or relations

## See Also

- **[DATABASE_EXTRACTION.md](DATABASE_EXTRACTION.md)** - API-based extraction
- **[USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)** - More examples
- **[README.md](README.md)** - Main documentation
- **[DEBUGGING.md](DEBUGGING.md)** - Troubleshooting guide

