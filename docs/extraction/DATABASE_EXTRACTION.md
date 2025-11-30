# Database Extraction Guide

Extract content from the first N pages of any Notion database (e.g., Recipe database, Project tracker, etc.)

## Quick Start

### Method 1: Command Line

```bash
# Set your Notion API token
export NOTION_TOKEN="secret_ABC123..."

# Extract first 10 pages from your database
python -m src.cli extract-database "your-database-id" --limit 10 --output both
```

### Method 2: Python Script

```python
from src.database_extractor import extract_database_pages

results = extract_database_pages(
    database_id="your-database-id",
    notion_token="secret_ABC123...",
    limit=10,
    output_dir='output',
    output_format='both',
    verbose=True
)

# Access the data
for result in results:
    print(f"{result.title}: {len(result.blocks)} blocks")
```

### Method 3: Use the Example Script

```bash
export NOTION_TOKEN="secret_ABC123..."
python examples/extract_recipe_database.py
```

## Getting Your Database ID

1. Open your database in Notion (web or desktop)
2. Click the "..." menu in the top right
3. Select "Copy link"
4. The URL looks like:
   ```
   https://www.notion.so/workspace/abc123def456?v=xyz...
   ```
5. The database ID is the part after the workspace name: `abc123def456`

Alternatively, look at the URL when viewing the database:
```
https://www.notion.so/workspace/DATABASE_ID?v=VIEW_ID
```

## Getting Your Notion API Token

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Give it a name (e.g., "Database Extractor")
4. Select the workspace
5. Click "Submit"
6. Copy the "Internal Integration Token" (starts with `secret_`)
7. **Important**: Share the database with your integration:
   - Open the database in Notion
   - Click "Share" in the top right
   - Click "Invite"
   - Select your integration
   - Click "Invite"

## Command Line Usage

### Basic extraction

```bash
python -m src.cli extract-database DATABASE_ID
```

### Options

```bash
# Specify number of pages (default: 10)
python -m src.cli extract-database DATABASE_ID --limit 20

# Choose output format
python -m src.cli extract-database DATABASE_ID --output json    # JSON only
python -m src.cli extract-database DATABASE_ID --output csv     # CSV only
python -m src.cli extract-database DATABASE_ID --output both    # Both formats

# Use token from environment variable
export NOTION_TOKEN="secret_..."
python -m src.cli extract-database DATABASE_ID

# Or provide directly
python -m src.cli extract-database DATABASE_ID --notion-token "secret_..."

# Verbose output
python -m src.cli --verbose extract-database DATABASE_ID
```

## Python API Usage

### Extract database pages

```python
from src.database_extractor import extract_database_pages

# Full featured extraction
results = extract_database_pages(
    database_id="abc123def456",
    notion_token="secret_...",
    limit=10,                    # Max pages to extract
    output_dir='output',         # Save files here
    output_format='both',        # 'json', 'csv', or 'both'
    verbose=True                 # Print progress
)

# Each result is an ExtractionResult object
for result in results:
    print(result.title)              # Page title
    print(len(result.blocks))        # Number of content blocks
    print(result.metadata)           # Additional metadata
    
    # Access blocks
    for block in result.blocks:
        print(block.content)         # Text content
        print(block.block_type)      # Type: text, heading, list, etc.
        print(block.source)          # Source: 'api'
```

### Extract without saving files

```python
from src.database_extractor import extract_database_pages

# Don't specify output_dir to skip file writing
results = extract_database_pages(
    database_id="your-db-id",
    notion_token="your-token",
    limit=10
)

# Process in memory
for result in results:
    # Do something with the data
    pass
```

### Extract a single page

```python
from src.database_extractor import extract_single_page

result = extract_single_page(
    page_id="page-id-here",
    notion_token="your-token",
    output_dir='output',
    output_format='json',
    verbose=True
)

print(f"Title: {result.title}")
print(f"Blocks: {len(result.blocks)}")
```

### Preview database without full extraction

```python
from src.database_extractor import get_database_pages_list

# Lightweight query - just get page list
pages = get_database_pages_list(
    database_id="your-db-id",
    notion_token="your-token",
    limit=10
)

# Each page is a dictionary with properties
for page in pages:
    page_id = page['id']
    properties = page['properties']
    # Extract title (property name varies by database)
    # Common names: 'Name', 'Title', 'title'
```

## Output Format

### JSON Output

Each page is saved as a separate JSON file:

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
      "metadata": {
        "block_id": "xyz789",
        "type": "heading_1"
      }
    },
    {
      "type": "list",
      "content": "2 cups flour",
      "source": "api",
      "order": 1,
      "metadata": {
        "block_id": "def456",
        "type": "bulleted_list_item"
      }
    }
  ],
  "metadata": {
    "source": "notion_api",
    "block_count": 15
  }
}
```

### CSV Output

Each page is saved as a CSV with columns:

| Order | Type    | Content              | Source | Block ID |
|-------|---------|----------------------|--------|----------|
| 0     | heading | Ingredients          | api    | xyz789   |
| 1     | list    | 2 cups flour         | api    | def456   |
| 2     | list    | 1 cup sugar          | api    | ghi123   |

## Use Cases

### Extract Recipe Database

```python
from src.database_extractor import extract_database_pages

recipes = extract_database_pages(
    database_id="your-recipe-db-id",
    notion_token=token,
    limit=10,
    output_dir='recipes',
    verbose=True
)

# Find recipes with specific ingredients
for recipe in recipes:
    content = " ".join([b.content for b in recipe.blocks])
    if "chocolate" in content.lower():
        print(f"Found chocolate recipe: {recipe.title}")
```

### Build a Search Index

```python
from src.database_extractor import extract_database_pages
import json

# Extract all pages
pages = extract_database_pages(
    database_id=db_id,
    notion_token=token,
    limit=100
)

# Build search index
index = {}
for page in pages:
    index[page.title] = {
        'content': [b.content for b in page.blocks],
        'block_count': len(page.blocks)
    }

# Save index
with open('search_index.json', 'w') as f:
    json.dump(index, f, indent=2)
```

### Export to Markdown

```python
from src.database_extractor import extract_database_pages

pages = extract_database_pages(db_id, token, limit=10)

for page in pages:
    # Create markdown file
    with open(f"{page.title}.md", 'w') as f:
        f.write(f"# {page.title}\n\n")
        
        for block in page.blocks:
            if block.block_type == "heading":
                f.write(f"## {block.content}\n\n")
            elif block.block_type == "list":
                f.write(f"- {block.content}\n")
            else:
                f.write(f"{block.content}\n\n")
```

## Limitations

- Maximum 100 pages per request (Notion API limit)
- Requires Notion API token and database permissions
- Extracts text content only (no images, files, or embeds)
- Database must be shared with your integration

## Troubleshooting

### "Failed to connect to Notion API"

- Check that your token is correct and starts with `secret_`
- Verify the token hasn't expired
- Ensure you have internet connectivity

### "Failed to retrieve database"

- Verify the database ID is correct
- Make sure the database is shared with your integration:
  1. Open database in Notion
  2. Click "Share"
  3. Add your integration

### "No pages found"

- The database might be empty
- Try increasing the `limit` parameter
- Check if there are any filters on the database view

### Rate Limits

If extracting many pages:
- Add delays between requests
- Use smaller batch sizes
- Consider the Notion API rate limits (3 requests per second)

## Examples

See the `examples/` directory for complete working examples:

- `extract_recipe_database.py` - Interactive script for Recipe databases

## API Reference

### extract_database_pages()

Main function to extract content from a database.

**Parameters:**
- `database_id` (str): Notion database ID
- `notion_token` (str): Notion API integration token
- `limit` (int): Maximum number of pages to extract (default: 10)
- `output_dir` (str, optional): Directory to save files
- `output_format` (str): 'json', 'csv', or 'both' (default: 'json')
- `verbose` (bool): Print progress information (default: False)

**Returns:**
- List[ExtractionResult]: List of extraction results

**Raises:**
- RuntimeError: If API connection fails or extraction errors occur

### extract_single_page()

Extract a single page by ID.

**Parameters:**
- `page_id` (str): Notion page ID
- `notion_token` (str): API token
- `output_dir` (str, optional): Save directory
- `output_format` (str): Output format
- `verbose` (bool): Verbose output

**Returns:**
- ExtractionResult: Extraction result

### get_database_pages_list()

Get page list without full content extraction (lightweight).

**Parameters:**
- `database_id` (str): Database ID
- `notion_token` (str): API token
- `limit` (int): Max pages to retrieve

**Returns:**
- List[Dict]: List of page objects with metadata

