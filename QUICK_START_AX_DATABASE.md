# Quick Start: AX-Based Database Extraction

Extract database pages with **no API token needed!** Just open your database in Notion and run the command.

## Super Quick Start

```bash
# 1. Open your database in Notion desktop app
# 2. Run this command:
python -m src.cli extract-database-ax --limit 10
```

That's it! 🎉

## What This Does

This command:
1. **Finds** your open Notion app
2. **Scans** the database for clickable rows
3. **Clicks** on each row (just like you would manually)
4. **Extracts** the page content using Accessibility APIs
5. **Navigates back** to the database
6. **Repeats** for the next page
7. **Saves** everything to `output/` folder

## Requirements

✅ Notion desktop app (not web)  
✅ Accessibility permissions enabled  
✅ A database open in Notion  
❌ **No API token needed!**

## Step-by-Step Setup

### Step 1: Check Permissions

```bash
python -m src.cli check-permissions
```

If not enabled:
1. System Settings → Privacy & Security → Accessibility
2. Add your Terminal app
3. Restart terminal

### Step 2: Open Your Database

1. Open Notion desktop app
2. Navigate to your Recipe database (or any database)
3. Make sure you're in list/table/board view

### Step 3: Preview Rows

```bash
python -m src.cli list-database-rows
```

You'll see:
```
=======================================================================
DATABASE ROWS: Recipe Database
=======================================================================

  1. Chocolate Chip Cookies
  2. Banana Bread
  3. Pasta Carbonara
  ...
```

### Step 4: Extract

```bash
python -m src.cli extract-database-ax --limit 10
```

Watch as it:
- ✅ Clicks on "Chocolate Chip Cookies"
- ✅ Extracts content
- ✅ Goes back
- ✅ Clicks on "Banana Bread"
- ✅ And so on...

## Common Commands

```bash
# Extract 5 pages
python -m src.cli extract-database-ax --limit 5

# Save as both JSON and CSV
python -m src.cli extract-database-ax --limit 10 --output both

# Verbose mode (see what's happening)
python -m src.cli --verbose extract-database-ax --limit 10

# Slower navigation (more reliable)
python -m src.cli extract-database-ax --limit 10 --navigation-delay 2.0

# Without OCR
python -m src.cli extract-database-ax --limit 10 --no-ocr
```

## Or Use the Interactive Script

```bash
python examples/extract_database_with_ax.py
```

This will:
1. Ask how many pages to extract
2. Show you the list of pages
3. Extract them one by one
4. Save everything
5. Show a summary

## Output

Files saved to `output/` directory:

```
output/
  ├── Chocolate_Chip_Cookies_extraction.json
  ├── Banana_Bread_extraction.json
  ├── Pasta_Carbonara_extraction.json
  └── ...
```

Each JSON file contains:
- Page title
- All content blocks
- Block types (heading, text, list, etc.)
- Metadata

## Troubleshooting

### "No database rows found"
→ Make sure you're viewing a database (not a single page)  
→ Try switching to table view

### "Failed to navigate"
→ Increase delay: `--navigation-delay 2.0`  
→ Make sure Notion is responding

### Extraction is slow
→ That's normal! It actually navigates through pages  
→ For bulk extraction (50+ pages), use API method instead

## Next Steps

✅ **You're done!** Check the `output/` folder for your extracted content.

Want more control?
- See [DATABASE_AX_EXTRACTION.md](DATABASE_AX_EXTRACTION.md) for advanced usage
- See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for Python examples

Want faster extraction?
- See [DATABASE_EXTRACTION.md](DATABASE_EXTRACTION.md) for API method

## Why Use This Instead of API?

| AX Navigation | API Method |
|---------------|------------|
| ❌ No token needed | ✅ Needs token |
| ✅ Works offline | ❌ Needs internet |
| ✅ Simple setup | ❌ More setup |
| ❌ Slower | ✅ Much faster |
| ✅ Good for small batches | ✅ Good for bulk |

**Use AX Navigation when:**
- You don't have an API token
- You're extracting < 20 pages
- You want to verify the visual layout
- You're just trying it out

**Use API when:**
- You have an API token
- You're extracting 50+ pages
- Speed matters
- You're automating workflows

## Examples

### Extract all visible recipes

```bash
# List to see how many
python -m src.cli list-database-rows

# Extract them all (if less than 100)
python -m src.cli extract-database-ax --limit 100
```

### Extract specific number

```bash
# Just 3 for testing
python -m src.cli extract-database-ax --limit 3

# 20 recipes
python -m src.cli extract-database-ax --limit 20 --output both
```

### With custom timing

```bash
# Slower, more reliable
python -m src.cli extract-database-ax --limit 10 --navigation-delay 2.0

# Faster (might miss some)
python -m src.cli extract-database-ax --limit 10 --navigation-delay 0.5
```

## That's It!

You're ready to extract database pages without any API setup! 🚀

