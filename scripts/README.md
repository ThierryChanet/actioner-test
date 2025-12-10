# Scripts Directory

This directory contains one-off diagnostic, testing, and utility scripts. These are **not** part of the automated test suite (which lives in `tests/`).

## Organization

### Recipe Extraction Scripts
- `recipe_extraction_comprehensive.py` - Comprehensive extraction test for top 5 recipes
- `single_recipe_extraction.py` - Quick test for a single recipe
- `two_recipes_extraction.py` - Test extraction on two recipes successively
- `extract_top5_recipes.py` - Extract ingredients from top 5 recipes
- `extract_top5_recipes_improved.py` - Improved version with retry logic and tab detection

### Gold Standard & Comparison
- `gold_standard_extraction.py` - Extract recipes using Notion API (ground truth)
- `compare_extractions.py` - Compare Computer Use vs API results
- `verify_specific_recipes.py` - Verify specific recipes by comparing methods

### Diagnostic & Debug Scripts
- `analyze_recipe_row.py` - Analyze a recipe row to find clickable elements
- `debug_ax_database.py` - Debug AX database navigation issues
- `debug_failing_recipes.py` - Debug script for specific recipe failures
- `diagnose_mixed_ingredients.py` - Diagnose ingredient mixing issues
- `investigate_blocks.py` - Investigate block types in recipes

### Panel Opening Methods
- `panel_opening_methods.py` - Test different methods to open side panel
- `cmd_click.py` - Test Cmd+Click to open panel in peek mode
- `hover_open_button.py` - Test hover → "Open" button pattern
- `single_recipe_open.py` - Simple test to open first recipe
- `simple_open.py` - Use simple click action to find and click OPEN button

### Panel Closing Methods
- `close_methods.py` - Test different methods to close Notion panel
- `close_debug_flow.py` - Debug test with explicit screen switching
- `close_interactive.py` - Interactive test to find best way to close panel
- `escape_with_focus.py` - Test closing panel by clicking neutral elements then Escape

### Configuration Scripts
- `configure_notion_peek_mode.py` - Configure Notion database to open in peek/side panel mode
- `fix_notion_peek_mode.py` - Fix Notion to open recipes in peek mode instead of tabs

### Other Utilities
- `benchmark_performance.py` - Performance benchmarking utilities
- `vision_comparison.py` - Vision comparison utilities
- `anthropic_click.py` - Anthropic click testing utilities

## Usage

All scripts should be run from the repository root:

```bash
python scripts/script_name.py
```

Scripts automatically add the repository root to `sys.path`, so imports from `src/` will work correctly.

## Note

These scripts are **not** part of the automated test suite. For actual tests, see the `tests/` directory and run:

```bash
pytest
```

