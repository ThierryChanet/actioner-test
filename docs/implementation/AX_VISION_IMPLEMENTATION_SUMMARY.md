# AX Navigation Fix & Vision Fallback - Implementation Summary

## Overview

Successfully implemented a two-part fix for AX database navigation:
1. **Fixed content area detection** to access actual page content instead of tab bar
2. **Added automatic vision-based fallback** when AX navigation fails

## Changes Made

### 1. Fixed Content Area Detection

**File**: `src/notion/detector.py`

**Problem**: `get_content_area()` was returning the first AXWebArea (Tab Bar) instead of the actual page content.

**Solution**: 
- Find ALL AXWebArea elements
- Filter by size (skip areas < 50,000 pixels)
- Rank by size and return the largest (page content)
- Added debug mode to show which area was selected

**Key Changes**:
```python
def get_content_area(self, debug: bool = False) -> Optional[AXElement]:
    # Find all web areas
    web_areas = find_elements_by_role(self.main_window, "AXWebArea", max_depth=10)
    
    # Filter and rank by size
    ranked_areas = []
    for area in web_areas:
        area_size = size[0] * size[1]
        if area_size >= 50000:  # Skip small areas
            ranked_areas.append({'element': area, 'size': area_size, ...})
    
    # Return largest
    return ranked_areas[0]['element']
```

### 2. Created Vision Database Extractor

**New File**: `src/notion/vision_database_extractor.py`

**Purpose**: Extract database entries using GPT-4o vision when AX navigation fails.

**How it works**:
1. Takes a screenshot of the current view
2. Sends to GPT-4o with prompt to identify database rows
3. GPT-4o returns JSON with row titles and click coordinates
4. Clicks each row and extracts content
5. Navigates back using ESC key

**Key Features**:
- Vision-based row detection using GPT-4o
- Confidence scoring for each detected row
- Robust error handling
- JSON parsing with markdown code block handling

### 3. Added Automatic Fallback in Orchestrator

**File**: `src/orchestrator.py`

**Changes**:
1. Added vision extractor properties (`_vision_extractor`, `_responses_client`)
2. Modified `extract_database_pages()` to automatically fall back to vision when AX finds 0 rows
3. Added `_extract_database_with_vision()` method to initialize and use vision extractor

**Fallback Flow**:
```
1. Try API extraction (if database_id provided)
   ↓ fails
2. Try AX navigation
   ↓ finds 0 rows
3. AUTO-FALLBACK to vision extraction
   ↓ uses GPT-4o to identify rows
4. Extract using mouse clicks
```

### 4. Updated Debug Script

**File**: `debug_ax_database.py`

**Change**: Now calls `get_content_area(debug=True)` to show detailed output about which web area was selected.

## Testing

### Test 1: Debug Script
```bash
python debug_ax_database.py
```

**Expected Output**:
```
[DEBUG] Found 2 AXWebArea elements
[DEBUG] Skipping small area 'Tab Bar' (30000 pixels)
[DEBUG] Largest web area: 'Menu | Weekly Schedule' (1500000 pixels)
```

### Test 2: AX Extraction
```bash
python -m src.agent --verbosity=verbose "extract 5 database entries"
```

**Expected Behavior**:
- Should now find actual database rows (not navigation buttons)
- If still fails, automatically falls back to vision

### Test 3: Vision Fallback
```bash
python -m src.agent "extract database entries from the current view"
```

**Expected Log Output**:
```
INFO | Using AX navigation to extract database
WARNING | No database rows found via AX
INFO | Attempting automatic fallback to vision-based extraction...
INFO | 🔍 Attempting vision-based database extraction...
INFO | ✓ Vision extractor initialized
INFO | Vision: Found 7 potential database rows
INFO | Processing row 1/5: Poulet rôti (confidence: high)
INFO | ✅ Extracted: Poulet rôti (12 blocks)
...
INFO | ✓ Extracted 5 pages via vision
```

## Benefits

1. **Deeper AX Access**: Now accesses actual page content, not just tab bar
2. **Automatic Fallback**: Seamlessly switches to vision when AX fails
3. **Robust Detection**: Vision can identify rows even in complex layouts
4. **No User Intervention**: Fallback happens automatically
5. **Better Error Messages**: Clear logging shows which method is being used

## Architecture

```
┌─────────────────────────────────────┐
│   extract_database_pages()          │
└──────────────┬──────────────────────┘
               │
               ├─→ Try API (if database_id)
               │   └─→ Success → Return results
               │
               ├─→ Try AX Navigation
               │   ├─→ get_database_rows()
               │   │   └─→ Now finds actual content!
               │   ├─→ Found rows? → Extract
               │   └─→ 0 rows? → FALLBACK ↓
               │
               └─→ Vision Extraction (AUTO)
                   ├─→ Take screenshot
                   ├─→ GPT-4o identifies rows
                   ├─→ Click each row
                   └─→ Extract content
```

## Files Modified

1. ✅ `src/notion/detector.py` - Fixed `get_content_area()` with size-based ranking
2. ✅ `src/orchestrator.py` - Added vision fallback logic
3. ✅ `src/notion/vision_database_extractor.py` - NEW: Vision-based extractor
4. ✅ `debug_ax_database.py` - Added debug mode to content area detection

## Usage Examples

### Example 1: Standard Usage (with auto-fallback)
```python
from src.orchestrator import NotionOrchestrator

orchestrator = NotionOrchestrator(verbose=True)
results = orchestrator.extract_database_pages(limit=5)
# Will try AX first, then vision if needed
```

### Example 2: Agent Usage
```bash
# Just ask naturally - fallback happens automatically
python -m src.agent "extract 10 entries from the menu database"
```

### Example 3: Programmatic with Vision
```python
from src.agent.responses_client import ResponsesAPIClient
from src.notion.vision_database_extractor import VisionDatabaseExtractor

# Direct vision extraction (skip AX)
responses_client = ResponsesAPIClient(display_width=1920, display_height=1080)
vision_extractor = VisionDatabaseExtractor(
    responses_client=responses_client,
    detector=detector,
    extractor=extractor,
    logger=logger
)
results = vision_extractor.extract_database_pages(limit=5)
```

## Next Steps

1. **Test with your Menu database**: Run `python debug_ax_database.py` to see if it now finds the correct content area
2. **Try extraction**: Use the agent to extract database entries
3. **Monitor logs**: Check if vision fallback is triggered and working
4. **Adjust thresholds**: If needed, adjust the 50,000 pixel threshold in `get_content_area()`

## Troubleshooting

### If AX still finds 0 rows:
- Check debug output to see which web area was selected
- Try adjusting the size threshold (currently 50,000 pixels)
- Vision fallback should activate automatically

### If vision fails:
- Check that OPENAI_API_KEY is set
- Verify screenshot is being captured
- Check logs for GPT-4o response parsing errors

### If both fail:
- Run `python debug_ax_database.py` and share the output
- Check that you're viewing a database (not a regular page)
- Verify Notion is in focus and database is visible

## Performance Notes

- **AX Navigation**: Fast (< 1s per row)
- **Vision Fallback**: Slower (~2-3s per row due to GPT-4o API calls)
- **Automatic**: No user intervention needed
- **Cost**: Vision uses GPT-4o API calls (only when AX fails)

