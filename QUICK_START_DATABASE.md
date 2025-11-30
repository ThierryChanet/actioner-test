# Quick Start: Database Extraction

Extract the first 10 pages from a Notion Recipe database (or any database).

## TL;DR

```bash
# 1. Set your Notion token
export NOTION_TOKEN="secret_ABC123..."

# 2. Extract 10 pages from your database
python -m src.cli extract-database "your-database-id" --limit 10 --output both
```

## Three Ways to Use

### 1️⃣ Command Line (Simplest)

```bash
export NOTION_TOKEN="secret_..."
python -m src.cli extract-database "abc123def456" --limit 10
```

### 2️⃣ Python One-Liner

```python
from src.database_extractor import extract_database_pages
results = extract_database_pages("db-id", "token", limit=10)
```

### 3️⃣ Example Script

```bash
export NOTION_TOKEN="secret_..."
python examples/extract_recipe_database.py
```

## Get Your Credentials

### Database ID
1. Open database in Notion
2. Look at URL: `https://notion.so/workspace/DATABASE_ID?v=...`
3. Copy `DATABASE_ID`

### API Token
1. Visit: https://www.notion.so/my-integrations
2. Create integration
3. Copy token (starts with `secret_`)
4. **Important**: Share database with your integration!

## Common Options

```bash
# Extract 20 pages instead of 10
--limit 20

# Save as JSON only (default)
--output json

# Save as CSV only
--output csv

# Save as both JSON and CSV
--output both

# Show detailed progress
--verbose
```

## Complete Example

```bash
# Recipe database extraction
export NOTION_TOKEN="secret_ABC123..."

python -m src.cli extract-database \
  "abc123def456" \
  --limit 10 \
  --output both \
  --verbose
```

## Output

Files saved to `output/` directory:
- `Recipe_Name_extraction.json` - Full structured data
- `Recipe_Name_extraction.csv` - Tabular format

## Python Usage

```python
from src.database_extractor import extract_database_pages

# Extract and save
results = extract_database_pages(
    database_id="abc123def456",
    notion_token="secret_...",
    limit=10,
    output_dir='output',
    output_format='both',
    verbose=True
)

# Process results
for recipe in results:
    print(f"{recipe.title}:")
    for block in recipe.blocks:
        print(f"  - {block.content}")
```

## Troubleshooting

### "Failed to connect to Notion API"
- Check your token is correct
- Verify it starts with `secret_`

### "Failed to retrieve database"
- Verify database ID is correct
- **Share the database with your integration!**
  1. Open database in Notion
  2. Click "Share"
  3. Add your integration

### "No pages found"
- Database might be empty
- Try increasing `--limit`
- Check database filters

## Need More Help?

- **Complete guide**: [DATABASE_EXTRACTION.md](DATABASE_EXTRACTION.md)
- **Examples**: [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **Main docs**: [README.md](README.md)

## Next Steps

1. ✅ Get credentials (token + database ID)
2. ✅ Share database with integration
3. ✅ Run extraction command
4. ✅ Check `output/` folder for results

**That's it! You're done! 🎉**

