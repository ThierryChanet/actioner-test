# Examples

This directory contains example scripts demonstrating database extraction.

## Available Examples

### 1. Simple Usage (`simple_usage.py`)

Minimal example showing the easiest way to extract database pages:

```python
from src.database_extractor import extract_database_pages

results = extract_database_pages(
    database_id="your-db-id",
    notion_token="your-token",
    limit=10,
    verbose=True
)

for result in results:
    print(f"{result.title}: {len(result.blocks)} blocks")
```

**Run it:**
```bash
export NOTION_TOKEN="secret_..."
python examples/simple_usage.py
```

### 2. Recipe Database Extractor (`extract_recipe_database.py`)

Interactive script that prompts for database ID and extracts recipes with full output:

```bash
export NOTION_TOKEN="secret_..."
python examples/extract_recipe_database.py
```

Features:
- Interactive prompts
- Progress display
- Summary report
- Saves as JSON and CSV

## Quick Setup

1. Get your Notion API token from https://www.notion.so/my-integrations
2. Share your database with the integration
3. Set the token:
   ```bash
   export NOTION_TOKEN="secret_ABC123..."
   ```
4. Run any example script

## Modify for Your Use Case

All examples can be easily modified for your specific needs:

```python
# Change the database ID
database_id = "your-database-id-here"

# Change the limit
limit=20  # Extract 20 pages instead of 10

# Change output format
output_format='json'  # or 'csv' or 'both'

# Save to custom directory
output_dir='my_exports'
```

## More Examples

See [USAGE_EXAMPLES.md](../USAGE_EXAMPLES.md) for more detailed examples including:
- Export to Markdown
- Build search indexes
- Content analysis
- Batch processing

