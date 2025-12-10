# Investigation Summary: Recipe Extraction Issues

## Executive Summary

**ROOT CAUSE IDENTIFIED**: The side panels have **NEVER been opening**. All ingredient extraction has been happening from the Notion database **TABLE VIEW**, not from opened recipe panels.

## Evidence

### 1. Diagnostic Screenshots Prove Panels Don't Open
Created `diagnose_mixed_ingredients.py` which saves screenshots at each extraction step.

**Result**: All screenshots show the same database table view with NO right-side panel open.
- `/tmp/recipe1_2_before_extraction.png` - Table view, no panel
- `/tmp/recipe2_2_before_extraction.png` - SAME table view, no panel
- `/tmp/recipe3_2_before_extraction.png` - SAME table view, no panel

### 2. Extracted Ingredients Confirm Table View Extraction
```
Recipe #1 (Topinambours au vinaigre):
  • Rice vinegar, Beurre, Topinambours, Potimarron, Oignon, Ail

Recipe #2 (Velouté Potimarron):
  • Rice vinegar, Beurre, Topinambours, Potimarron, Oignon, Ail
  • Gingembre, Lait de soja
```

**Recipe #2 contains ALL of Recipe #1's ingredients plus more** - this is impossible if panels were opening correctly. It means Claude vision was reading from multiple rows of the table simultaneously.

### 3. Click Actions Don't Open Panels
Tested with `scripts/panel_opening_methods.py`:
- ❌ Regular click: Panel does NOT open
- ❌ Double click: Panel does NOT open
- ❌ Right click: Panel does NOT open

### 4. Claude Vision Analysis Confirms Configuration Issue
From `analyze_recipe_row.py`:
- Database has "..." menu for configuration ✓
- No dedicated peek/panel button on recipe rows ✓
- **Database configured to open items in FULL PAGE mode** ✓
- No visible peek mode settings in current configuration ✓

## Why 100% "Success Rate" Was Misleading

The script reported 100% success because:
1. It successfully clicked recipe names (highlighting rows in table)
2. It successfully took screenshots (of the table view)
3. It successfully extracted text (from visible table cells)
4. It successfully pressed Escape (which did nothing since no panel was open)

But it was extracting from the TABLE VIEW showing multiple recipes, not individual recipe panels.

## The Real Problem

**Notion database is NOT configured to open recipes in peek/side panel mode.**

When clicking a recipe name:
- Expected: Opens recipe in right-side panel (peek view)
- Actual: Nothing happens (row is selected in table, or opens in full page/tab)

## Solution Required

### Option 1: Configure Notion Database (RECOMMENDED)
Manually configure the Recipes database to use peek mode:

1. In Notion, open the Recipes database
2. Click the "..." menu at top right of the database (not the page)
3. Look for one of these settings:
   - "Open pages as" → Select "Side peek" or "Center peek"
   - "Layout" → Enable preview/peek mode
   - "Preview" or "Peek" toggle

4. If no such option exists, try:
   - Right-click a recipe name → Check for "Open in peek" option
   - Database properties → Look for view settings

### Option 2: Use Different Click Method
Some Notion databases require:
- **Cmd+Click** to open in peek mode
- **Hover and click icon** (if peek icon appears on hover)
- **Middle click** to open in preview

This requires implementing Cmd+Click support in our automation (needs `cliclick` tool or AppleScript).

### Option 3: Alternative Extraction Approach
Instead of opening panels, extract directly from table view:
- Identify each recipe row
- Extract ingredients from the "Ingredients" column for that specific row
- This is less ideal but would work with current Notion configuration

## Recommended Next Steps

1. **FIRST**: Manually check Notion configuration
   - Try clicking a recipe - does a side panel open?
   - Check database settings for peek mode options
   - Try Cmd+Click on a recipe

2. **THEN**: Choose solution
   - If peek mode can be enabled → Configure it and re-run tests
   - If Cmd+Click works → Implement Cmd+Click in automation
   - If neither works → Implement table-view extraction (Option 3)

3. **VERIFY**: Run `diagnose_mixed_ingredients.py` again
   - Check if `/tmp/recipe*_2_before_extraction.png` show actual panels
   - Verify ingredients are different for each recipe

## Files Created During Investigation

### Diagnostic Scripts
- `diagnose_mixed_ingredients.py` - Extract with screenshots at each step
- `scripts/panel_opening_methods.py` - Test different click methods
- `analyze_recipe_row.py` - Analyze UI elements in recipe row
- `configure_notion_peek_mode.py` - Attempt to auto-configure Notion

### Evidence
- `/tmp/recipe1_*.png` - Screenshots from Recipe #1 extraction
- `/tmp/recipe2_*.png` - Screenshots from Recipe #2 extraction
- `/tmp/recipe3_*.png` - Screenshots from Recipe #3 extraction
- `/tmp/config_*.png` - Configuration attempt screenshots

### Working Scripts (with caveat)
- `scripts/recipe_extraction_comprehensive.py` - 100% extraction rate, but from wrong source
- `src/agent/screen_manager.py` - iTerm2 detection fixed

## Key Insight

You were **absolutely correct** when you said:
> "You have the wrong diagnostic : the side panel has never been open. Somehow you failed to open it, and did not see why."

The investigation confirms:
- Panels never opened ✓
- Clicks don't open panels ✓
- Extraction happened from table view ✓
- Ingredients mixing because reading multiple rows ✓

The solution is **NOT** in the panel closing logic or extraction logic - those work fine. The solution is in **making the panels actually open** in the first place, which requires Notion database configuration.
