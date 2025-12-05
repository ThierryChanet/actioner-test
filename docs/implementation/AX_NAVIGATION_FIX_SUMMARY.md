# AX Navigation Troubleshooting - Fix Summary

## Problem Identified

From your terminal output (lines 713-740), the AX navigation extracted **0 pages** from the database:

```
INFO     | Using AX navigation to extract database
INFO     | ✓ Extracted 0 pages via AX
```

The agent reported: *"the current view might not be recognized as a database view"*

## Root Cause

The `get_database_rows()` function in `src/notion/navigator.py` was returning an empty list, which happens when:

1. No `AXRow` elements are found in the content area
2. The fallback link detection also fails
3. The database view structure isn't recognized

## Fixes Implemented

### 1. Enhanced Row Detection (`src/notion/navigator.py`)

**Added multiple fallback strategies:**

- ✅ **Primary**: Look for `AXRow` elements (table views)
- ✅ **Fallback 1**: Look for `AXLink` elements with filtering
- ✅ **Fallback 2**: Look for `AXGroup` elements with clickable children (board/gallery views)
- ✅ **Debug mode**: Added `debug=True` parameter for detailed output

**Key improvements:**
```python
def get_database_rows(self, debug: bool = False) -> List[Dict[str, any]]:
    # Now tries 3 different strategies
    # Filters out navigation links ("Home", "Sidebar", etc.)
    # Provides debug output at each step
```

### 2. Better Error Handling (`src/orchestrator.py`)

**Added pre-flight checks:**
```python
# Check for rows BEFORE attempting extraction
rows = self.navigator.get_database_rows(debug=self.verbose)
if not rows:
    self.logger.warning("No database rows found in current view")
    self.logger.warning("Make sure you're viewing a database (table/board/gallery)")
    self.logger.warning("Try running: python debug_ax_database.py")
    return []
```

### 3. Diagnostic Tool (`debug_ax_database.py`)

Created a comprehensive debug script that:
- ✅ Checks if Notion is accessible
- ✅ Inspects the content area structure
- ✅ Counts AXRow, AXLink, AXButton, AXGroup elements
- ✅ Tests the actual `get_database_rows()` method
- ✅ Provides actionable troubleshooting steps

### 4. Documentation (`TROUBLESHOOT_AX_DATABASE.md`)

Complete troubleshooting guide with:
- Quick fix steps
- Common issues and solutions
- How the detection works
- Manual testing examples
- Next steps if still not working

## How to Use

### Step 1: Run the Diagnostic

```bash
cd /Users/thierry/Documents/code/actioner-test
python debug_ax_database.py
```

This will show you exactly what's happening with your current Notion view.

### Step 2: Try with Verbose Mode

```bash
# With the agent
python -m src.agent --verbosity=verbose "extract database entries"

# Or with CLI
python -m src.cli --verbose extract-database-ax --limit 5
```

Now you'll see detailed debug output showing:
- How many rows were found
- What element types were detected
- Why certain elements were skipped

### Step 3: Ensure Correct View

Make sure you're viewing a **database** in Notion:
- ✅ Table view (best support)
- ✅ Board view (now supported with fallbacks)
- ✅ Gallery view (now supported with fallbacks)
- ❌ Regular page (won't work)

## What Changed in the Code

### Before:
```python
# Only looked for AXRow elements
# Simple fallback to links
# No debug output
# Silent failures
```

### After:
```python
# Multiple detection strategies
# Filters out navigation links
# Debug mode with detailed output
# Clear error messages with suggestions
# Pre-flight row count check
```

## Testing Your Fix

1. **Open your Menu database in Notion** (the one shown in your screenshot)
2. **Make sure you're in table/board view**
3. **Run the debug script**:
   ```bash
   python debug_ax_database.py
   ```
4. **Look for the output**:
   - Should show number of rows found
   - Should list the actual menu items
5. **Try extraction again**:
   ```bash
   python -m src.agent --verbosity=verbose "extract 5 entries from the current database"
   ```

## Expected Output (Good)

```
[DEBUG] Content area found: AXScrollArea
[DEBUG] Found 7 AXRow elements
[DEBUG] Found clickable row: Poulet rôti
[DEBUG] Found clickable row: Ratatouille
[DEBUG] Found clickable row: Épinards sésame
...
[DEBUG] Total rows found: 7

INFO     | Found 7 rows in database view
INFO     | Using AX navigation to extract database
INFO     | ✓ Extracted 5 pages via AX
```

## If Still Not Working

1. **Share the debug output** - Run `python debug_ax_database.py` and share results
2. **Check the view type** - Make sure it's a database view
3. **Try table view** - Switch to table view temporarily
4. **Use Computer Use** - Alternative approach using vision + mouse clicks:
   ```bash
   python -m src.agent "use computer control to extract database entries by clicking each row"
   ```

## Files Modified

- ✅ `src/notion/navigator.py` - Enhanced `get_database_rows()` with fallbacks and debug mode
- ✅ `src/orchestrator.py` - Added pre-flight checks and better error messages
- ✅ `debug_ax_database.py` - New diagnostic tool
- ✅ `TROUBLESHOOT_AX_DATABASE.md` - Complete troubleshooting guide
- ✅ `AX_NAVIGATION_FIX_SUMMARY.md` - This file

## Next Steps

1. Run `python debug_ax_database.py` while viewing your Menu database
2. Share the output if you still see 0 rows detected
3. The debug output will tell us exactly what's happening with your Notion view structure

