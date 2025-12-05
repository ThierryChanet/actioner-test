# Troubleshooting AX Database Navigation

## Problem: Extracted 0 pages via AX

When you see:
```
INFO     | Using AX navigation to extract database
INFO     | ✓ Extracted 0 pages via AX
```

This means the AX navigation couldn't find any database rows in the current Notion view.

## Quick Fix Steps

### 1. Run the Debug Script

First, run the diagnostic tool to see what's happening:

```bash
cd /Users/thierry/Documents/code/actioner-test
python debug_ax_database.py
```

This will show you:
- Whether Notion is accessible
- What elements are found in the current view
- Why rows aren't being detected

### 2. Common Issues and Solutions

#### Issue: "No content area found"
**Solution**: 
- Click into the Notion window to make sure it's in focus
- Make sure you're on an actual page, not the sidebar

#### Issue: "No AXRow elements found"
**Solution**:
- You might be viewing a board or gallery view instead of a table
- The script now has fallback detection for these views
- Try switching to table view temporarily

#### Issue: "No rows detected"
**Possible causes**:
1. **You're on a page, not a database**
   - Navigate to a database view (table, board, gallery, list)
   - Make sure you see multiple items/rows

2. **The database is empty**
   - Add some entries to test with

3. **Accessibility structure has changed**
   - Notion may have updated their UI
   - The debug script will show what elements are available

### 3. Test with Verbose Mode

Run with verbose mode to see detailed debugging:

```bash
# With the agent
python -m src.agent --verbosity=verbose "extract database entries"

# Or directly
python -m src.cli --verbose extract-database-ax --limit 5
```

### 4. What the Debug Script Shows

The debug script will print:
1. ✅ or ❌ for each detection step
2. Number of rows/links/buttons found
3. Actual element types in your current view
4. The results of `get_database_rows()`

Example good output:
```
✅ Notion app found and activated
✅ Content area found
Found 15 AXRow elements
Result: 10 rows found
```

Example bad output (needs fixing):
```
❌ No content area found!
Found 0 AXRow elements
Result: 0 rows found
```

## How It Works

The AX database extractor:

1. Gets the content area of the current Notion page
2. Looks for `AXRow` elements (table rows)
3. For each row, finds clickable elements (links/buttons)
4. If no rows found, falls back to:
   - Looking for all `AXLink` elements
   - Looking for `AXGroup` elements with clickable children (for board/gallery views)

## Improvements Made

I've enhanced the code to:

1. **Better fallback detection** - Now tries multiple strategies:
   - AXRow elements (table view)
   - AXLink elements (fallback)
   - AXGroup with clickable children (board/gallery view)

2. **Debug mode** - Pass `debug=True` to see detailed output:
   ```python
   rows = navigator.get_database_rows(debug=True)
   ```

3. **Better error messages** - The orchestrator now:
   - Checks for rows before attempting extraction
   - Provides helpful suggestions if no rows found
   - Suggests running the debug script

4. **Navigation link filtering** - Filters out common navigation links like "Home", "Sidebar", etc.

## Manual Testing

To manually test if your database is accessible:

```python
from src.ax.client import AXClient
from src.notion.detector import NotionDetector
from src.notion.navigator import NotionNavigator

# Initialize
ax_client = AXClient()
detector = NotionDetector(ax_client)
navigator = NotionNavigator(detector)

# Activate Notion
detector.ensure_notion_active()

# Get rows with debug output
rows = navigator.get_database_rows(debug=True)
print(f"\nFound {len(rows)} rows:")
for i, row in enumerate(rows[:5]):
    print(f"  {i+1}. {row['title']}")
```

## Next Steps if Still Not Working

1. **Share the debug output**: Run `python debug_ax_database.py` and share the full output

2. **Check your Notion view type**: 
   - Table view works best
   - Board/gallery view should work with the new fallbacks
   - Timeline view might not work yet

3. **Try a different database**: Test with a simple database to isolate the issue

4. **Check Accessibility permissions**: 
   - System Preferences > Security & Privacy > Privacy > Accessibility
   - Make sure Python/Terminal is allowed

## Using Computer Use Instead

If AX navigation continues to have issues, you can use Computer Use (screen-based navigation):

```bash
# Uses vision and mouse clicks instead of AX
python -m src.agent "switch to Notion then extract database by clicking on each row"
```

This is slower but more reliable if the AX structure is problematic.

