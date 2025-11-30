# Database Extraction Implementation Summary

## What Was Built

I've successfully implemented a complete solution to extract the content of the first N pages from a Notion database (e.g., Recipe database). The implementation includes:

### 1. Core Functionality (`src/database_extractor.py`)

Three main functions:

- **`extract_database_pages()`** - Main function to extract content from multiple database pages
- **`extract_single_page()`** - Extract a single page by ID
- **`get_database_pages_list()`** - Lightweight query to preview pages without full extraction

### 2. API Enhancement (`src/validation/notion_api.py`)

Added three new methods to the `NotionAPIClient` class:

- **`query_database()`** - Query a database with pagination and filtering
- **`get_database()`** - Get database metadata
- **`extract_database_pages()`** - Extract content from multiple database pages

### 3. CLI Command (`src/cli.py`)

New command: `extract-database`

```bash
python -m src.cli extract-database DATABASE_ID --limit 10 --output both
```

### 4. Example Script (`examples/extract_recipe_database.py`)

An interactive Python script demonstrating usage:

```bash
export NOTION_TOKEN="your-token"
python examples/extract_recipe_database.py
```

### 5. Comprehensive Tests (`tests/test_database_extractor.py`)

8 test cases covering:
- Basic extraction
- Connection failures
- Page listing
- Single page extraction
- JSON/CSV output
- Verbose mode
- Empty databases

**All tests pass! ✅**

### 6. Documentation

- **`DATABASE_EXTRACTION.md`** - Complete guide with examples and troubleshooting
- **`USAGE_EXAMPLES.md`** - Updated with database extraction examples
- **`README.md`** - Updated to include the new feature

## Usage Examples

### Command Line

```bash
# Set your Notion API token
export NOTION_TOKEN="secret_ABC123..."

# Extract first 10 pages from a Recipe database
python -m src.cli extract-database "abc123def456" --limit 10 --output both
```

### Python API

```python
from src.database_extractor import extract_database_pages

# Extract with file output
results = extract_database_pages(
    database_id="abc123def456",
    notion_token="secret_ABC123...",
    limit=10,
    output_dir='output',
    output_format='both',
    verbose=True
)

# Process the results
for result in results:
    print(f"{result.title}: {len(result.blocks)} blocks")
    for block in result.blocks:
        print(f"  - {block.content}")
```

### Simple Usage (No File Output)

```python
from src.database_extractor import extract_database_pages

# Just get the data in memory
results = extract_database_pages(
    database_id="your-db-id",
    notion_token="your-token",
    limit=10
)

# Access immediately
for result in results:
    print(result.title)
```

## Features

✅ **Extract up to 100 pages** (Notion API limit) from any database  
✅ **Flexible output** - JSON, CSV, or both formats  
✅ **Programmatic access** - Use as a Python library or CLI tool  
✅ **Progress tracking** - Verbose mode shows detailed progress  
✅ **Error handling** - Graceful handling of API failures  
✅ **Well tested** - 8 comprehensive unit tests  
✅ **Fully documented** - Multiple documentation files and examples  

## Output Format

### JSON
Each page saved as a separate JSON file with complete structure:

```json
{
  "page_id": "abc123",
  "title": "Chocolate Chip Cookies",
  "blocks": [
    {
      "type": "heading",
      "content": "Ingredients",
      "source": "api",
      "order": 0,
      "metadata": {...}
    }
  ],
  "metadata": {
    "source": "notion_api",
    "block_count": 15
  }
}
```

### CSV
Tabular format for easy analysis:

| Order | Type    | Content     | Source | Block ID |
|-------|---------|-------------|--------|----------|
| 0     | heading | Ingredients | api    | xyz789   |
| 1     | list    | 2 cups flour| api    | def456   |

## Files Created/Modified

### New Files
1. `src/database_extractor.py` - Main implementation
2. `examples/extract_recipe_database.py` - Example script
3. `tests/test_database_extractor.py` - Test suite
4. `DATABASE_EXTRACTION.md` - Complete guide
5. `IMPLEMENTATION_SUMMARY.md` - This file

### Modified Files
1. `src/validation/notion_api.py` - Added database query methods
2. `src/cli.py` - Added extract-database command
3. `USAGE_EXAMPLES.md` - Added database extraction examples
4. `README.md` - Updated features and quick start

## How to Get Started

### Step 1: Get Your Notion API Token

1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the token (starts with `secret_`)
4. Share your database with the integration

### Step 2: Get Your Database ID

1. Open database in Notion
2. Copy the URL
3. Extract the ID: `https://www.notion.so/workspace/DATABASE_ID?v=...`

### Step 3: Run the Extraction

```bash
export NOTION_TOKEN="secret_..."
python -m src.cli extract-database "DATABASE_ID" --limit 10
```

## Advanced Use Cases

### 1. Export to Markdown

```python
from src.database_extractor import extract_database_pages

results = extract_database_pages(db_id, token, limit=10)

for result in results:
    with open(f"{result.title}.md", 'w') as f:
        f.write(f"# {result.title}\n\n")
        for block in result.blocks:
            if block.block_type == "heading":
                f.write(f"## {block.content}\n\n")
            else:
                f.write(f"{block.content}\n\n")
```

### 2. Build Search Index

```python
import json
from src.database_extractor import extract_database_pages

results = extract_database_pages(db_id, token, limit=100)

index = {
    page.title: [b.content for b in page.blocks]
    for page in results
}

with open('search_index.json', 'w') as f:
    json.dump(index, f)
```

### 3. Content Analysis

```python
from src.database_extractor import extract_database_pages

results = extract_database_pages(db_id, token, limit=50)

# Find recipes with chocolate
for recipe in results:
    content = " ".join([b.content for b in recipe.blocks])
    if "chocolate" in content.lower():
        print(f"Found: {recipe.title}")
```

## Testing

Run the test suite:

```bash
pytest tests/test_database_extractor.py -v
```

Result: **8/8 tests passed ✅**

## Documentation

- **README.md** - Main project documentation
- **DATABASE_EXTRACTION.md** - Complete database extraction guide
- **USAGE_EXAMPLES.md** - Detailed usage examples
- **IMPLEMENTATION_SUMMARY.md** - This file

## Architecture

The implementation follows the existing codebase patterns:

```
User Request
    ↓
database_extractor.py (high-level interface)
    ↓
notion_api.py (API client)
    ↓
Notion API (official API)
    ↓
ExtractionResult objects
    ↓
json_writer.py / csv_writer.py
    ↓
Output files
```

## Limitations

- Maximum 100 pages per request (Notion API limit)
- Text content only (no images, files, embeds)
- Requires Notion API token and database sharing
- Database must be shared with your integration

## Future Enhancements

Potential improvements:
- Batch processing with rate limiting
- Support for database filters and sorts
- Parallel page extraction
- Progress bars for large databases
- Resume interrupted extractions
- Database schema extraction

## Summary

✅ **Fully functional** - Ready to use  
✅ **Well tested** - All tests pass  
✅ **Well documented** - Multiple guides and examples  
✅ **Easy to use** - CLI and Python API  
✅ **Flexible** - Multiple output formats  
✅ **Production ready** - Error handling and validation  

The implementation provides a complete, robust solution for extracting content from Notion databases, with both command-line and programmatic interfaces, comprehensive documentation, and full test coverage.

