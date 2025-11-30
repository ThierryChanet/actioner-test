# Usage Examples

This document provides detailed examples of using the Notion AX Extractor.

## Basic Examples

### Extract a Single Page

```bash
# Extract with default settings (JSON output)
python -m src.cli extract "My Page"

# Extract with CSV output
python -m src.cli extract "My Page" --output csv

# Extract with both JSON and CSV
python -m src.cli extract "My Page" --output both
```

### Extract Multiple Pages

```bash
# Extract all pages from sidebar
python -m src.cli extract-all

# With verbose logging
python -m src.cli --verbose extract-all

# Save to custom directory
python -m src.cli --output-dir results extract-all
```

### Navigation Only

```bash
# Just navigate to a page (no extraction)
python -m src.cli navigate "Sprint Planning"

# Check what pages are available
python -m src.cli list-pages
```

### Extract from Database

Extract content from the first N pages of a Notion database (e.g., Recipe database):

```bash
# Set your Notion API token
export NOTION_TOKEN="secret_ABC123..."

# Extract first 10 pages from a database
python -m src.cli extract-database "your-database-id" --limit 10

# Extract first 5 pages with both JSON and CSV output
python -m src.cli extract-database "your-database-id" --limit 5 --output both

# With verbose logging
python -m src.cli --verbose extract-database "your-database-id" --limit 10
```

**Finding your Database ID:**
1. Open the database in Notion
2. Click "..." menu → "Copy link"
3. The URL looks like: `https://www.notion.so/workspace/DATABASE_ID?v=...`
4. Extract the `DATABASE_ID` part (32-character string)

## Advanced Examples

### Dry-Run Mode

Test what the tool will do without actually doing it:

```bash
# See what would be extracted
python -m src.cli extract "My Page" --mode dry-run

# See what pages would be extracted
python -m src.cli extract-all --mode dry-run
```

### Disable OCR

For pages with all accessible text, disable OCR for faster extraction:

```bash
python -m src.cli extract "Simple Page" --no-ocr
```

### Validation Workflow

Complete workflow to validate extraction accuracy:

```bash
# 1. Set your Notion API token
export NOTION_TOKEN="secret_ABC123..."

# 2. Extract a page normally
python -m src.cli extract "Project Roadmap"

# 3. Validate against API
python -m src.cli validate "Project Roadmap" --page-id "abc-123-def"

# 4. Check the comparison report in output/
```

## Batch Processing

### Extract Multiple Specific Pages

Create a script to extract specific pages:

```bash
#!/bin/bash
# extract_pages.sh

PAGES=(
  "Meeting Notes"
  "Project Roadmap"
  "Sprint Planning"
  "Team Wiki"
)

for page in "${PAGES[@]}"; do
  echo "Extracting: $page"
  python -m src.cli extract "$page"
done
```

### Scheduled Extraction

Use cron to extract pages daily:

```bash
# Add to crontab (crontab -e)
# Extract all pages every day at 2 AM
0 2 * * * cd /path/to/actioner-test && python -m src.cli extract-all
```

## Integration Examples

### Python Script Integration

```python
from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.extractor import NotionExtractor
from src.output.json_writer import JSONWriter

# Initialize
ax_client = AXClient()
detector = NotionDetector(ax_client)
extractor = NotionExtractor(detector)

# Ensure Notion is running
if detector.ensure_notion_active():
    # Extract current page
    result = extractor.extract_page()
    
    # Save to JSON
    writer = JSONWriter("output")
    filepath = writer.write_extraction(result)
    
    print(f"Extracted {len(result.blocks)} blocks")
    print(f"Saved to {filepath}")
```

### Validation Script

```python
from src.validation.notion_api import NotionAPIClient
from src.validation.comparator import Comparator
from src.validation.differ import Differ

# Initialize API client
api_client = NotionAPIClient(auth_token="your_token")

# Get gold standard
gold = api_client.page_to_extraction_result("page-id")

# Compare with extracted result
comparator = Comparator()
comparison = comparator.compare(gold, extracted_result)

# Generate report
differ = Differ()
report = differ.generate_report(comparison)
print(report)
```

### Database Extraction (Programmatic)

Extract content from multiple pages in a database using Python:

```python
from src.database_extractor import extract_database_pages

# Extract first 10 pages from a Recipe database
results = extract_database_pages(
    database_id="your-database-id",
    notion_token="secret_ABC123...",
    limit=10,
    output_dir='output',
    output_format='both',  # JSON and CSV
    verbose=True
)

# Process results
for result in results:
    print(f"\nRecipe: {result.title}")
    print(f"Blocks: {len(result.blocks)}")
    
    # Get all text content
    full_text = " ".join([b.content for b in result.blocks])
    print(f"Total characters: {len(full_text)}")
```

**Simple usage without saving files:**

```python
from src.database_extractor import extract_database_pages

# Just get the data (no file output)
results = extract_database_pages(
    database_id="your-db-id",
    notion_token="your-token",
    limit=10
)

# Access the content
for result in results:
    print(f"{result.title}:")
    for block in result.blocks:
        if block.block_type == "heading":
            print(f"  # {block.content}")
        else:
            print(f"  - {block.content}")
```

**Extract a single page:**

```python
from src.database_extractor import extract_single_page

result = extract_single_page(
    page_id="page-id-here",
    notion_token="your-token",
    verbose=True
)

print(f"Title: {result.title}")
print(f"Blocks: {len(result.blocks)}")
```

**Preview database pages (without full extraction):**

```python
from src.database_extractor import get_database_pages_list

# Get list of pages in database (lightweight)
pages = get_database_pages_list(
    database_id="your-db-id",
    notion_token="your-token",
    limit=10
)

# Show titles
for page in pages:
    props = page.get('properties', {})
    # Database title property name varies - common ones:
    title_prop = props.get('Name') or props.get('Title') or props.get('title')
    if title_prop:
        title_data = title_prop.get('title', [])
        if title_data:
            title = title_data[0].get('plain_text', 'Untitled')
            print(f"- {title} (ID: {page['id']})")
```

## Troubleshooting Examples

### Debug Mode

```bash
# Enable verbose logging to see what's happening
python -m src.cli --verbose extract "My Page"

# This will show:
# - AX tree traversal
# - Scroll actions
# - Block detection
# - OCR decisions
```

### Check Notion State

```python
from src.ax.client import AXClient
from src.notion.detector import NotionDetector

ax_client = AXClient()
detector = NotionDetector(ax_client)

if detector.find_notion():
    state = detector.get_state()
    print(f"Notion running: {state['notion_running']}")
    print(f"Current page: {state['page_title']}")
    print(f"Loading: {state['is_loading']}")
    print(f"Sidebar visible: {state['sidebar_visible']}")
```

### Test Navigation

```python
from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.navigator import NotionNavigator

ax_client = AXClient()
detector = NotionDetector(ax_client)
navigator = NotionNavigator(detector)

# Ensure Notion is active
detector.ensure_notion_active()

# List available pages
pages = navigator.get_sidebar_pages()
for i, page in enumerate(pages):
    print(f"{i+1}. {page['name']}")

# Navigate to first page
if pages:
    success = navigator.navigate_to_page(pages[0]['name'])
    print(f"Navigation: {'Success' if success else 'Failed'}")
```

## Output Processing Examples

### Parse JSON Output

```python
import json

# Read extraction result
with open('output/My_Page_extraction.json') as f:
    data = json.load(f)

# Process blocks
for block in data['blocks']:
    print(f"[{block['type']}] {block['content'][:50]}...")
    print(f"  Source: {block['source']}")
    print()

# Show metadata
print(f"Total blocks: {data['metadata']['block_count']}")
```

### Convert to Markdown

```python
import json

def json_to_markdown(json_file):
    with open(json_file) as f:
        data = json.load(f)
    
    lines = [f"# {data['title']}", ""]
    
    for block in data['blocks']:
        content = block['content']
        block_type = block['type']
        
        if block_type == 'heading':
            lines.append(f"## {content}")
        elif block_type == 'list':
            lines.append(f"- {content}")
        else:
            lines.append(content)
        lines.append("")
    
    return "\n".join(lines)

# Convert
markdown = json_to_markdown('output/My_Page_extraction.json')
with open('output/My_Page.md', 'w') as f:
    f.write(markdown)
```

### CSV Analysis

```python
import csv
import pandas as pd

# Load CSV
df = pd.read_csv('output/My_Page_extraction.csv')

# Analysis
print(f"Total blocks: {len(df)}")
print(f"Block types: {df['Type'].value_counts()}")
print(f"Sources: {df['Source'].value_counts()}")

# Filter OCR blocks
ocr_blocks = df[df['Source'] == 'ocr']
print(f"OCR used for {len(ocr_blocks)} blocks")
```

## Environment Setup Examples

### Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd actioner-test

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest

# Format code
black src/

# Lint
flake8 src/
```

## Performance Tuning

### Fast Extraction (Skip OCR)

```bash
# For text-only pages, skip OCR
python -m src.cli extract "Text Page" --no-ocr
```

### Batch with Delays

```bash
#!/bin/bash
# Extract with delays to avoid overwhelming Notion

for page in "Page1" "Page2" "Page3"; do
  python -m src.cli extract "$page"
  sleep 2  # Wait 2 seconds between extractions
done
```

### Custom Scroll Settings

```python
from src.notion.extractor import NotionExtractor

# Adjust scroll settings for faster/slower scrolling
result = extractor.extract_page(
    scroll_delay=0.1,  # Faster scrolling
    max_scrolls=50     # Limit scroll iterations
)
```

## Error Handling Examples

### Graceful Failure Handling

```python
from src.errors import (
    NotionNotFoundError,
    NavigationError,
    ExtractionError,
    handle_exception
)

try:
    # Your extraction code
    result = extractor.extract_page()
except NotionNotFoundError:
    print("Please start Notion app first")
except NavigationError as e:
    print(f"Could not find page: {e.page_name}")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except Exception as e:
    print(handle_exception(e))
```

### Retry Logic

```python
from src.errors import retry_on_failure
from src.notion.navigator import NavigationError

@retry_on_failure(max_attempts=3, delay=1.0)
def navigate_with_retry(navigator, page_name):
    if not navigator.navigate_to_page(page_name):
        raise NavigationError(page_name)
    return True

# Will retry up to 3 times
navigate_with_retry(navigator, "My Page")
```

---

For more examples and use cases, check the test suite in `tests/` directory.

