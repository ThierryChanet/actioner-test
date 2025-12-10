# Gold Standard Testing

This directory contains tools for validating Computer Use extraction against the Notion API gold standard.

## Overview

- **gold_standard_extraction.py** - Extract recipes using Notion API (ground truth)
- **compare_extractions.py** - Compare Computer Use vs API results
- **scripts/recipe_extraction_comprehensive.py** - Extract recipes using Computer Use agent

## Database Configuration

**Recipe Database ID:** `5bb4c854c109480ebd7c6112e357b4e5`

This ID is hardcoded in `gold_standard_extraction.py` for reproducible testing.

## Setup

### 1. Add Notion Token to .env

You need a Notion integration token to use the API. Add it to `.env`:

```bash
NOTION_TOKEN=secret_your_integration_token_here
```

To get a Notion integration token:
1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Share your Recipe database with the integration

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

The key dependency is `notion-client>=2.0.0`.

## Usage

### Step 1: Extract Gold Standard (API)

```bash
python3 gold_standard_extraction.py
```

This will:
- Connect to Notion API
- Extract top 10 recipes from the database
- Save results to `gold_standard_recipes.json`

**Output:**
```
GOLD STANDARD EXTRACTION: Notion API
======================================================================
Database ID: 5bb4c854c109480ebd7c6112e357b4e5
Started at: 2025-12-08 08:00:00

Connecting to Notion API...
✓ Connected to database: Recipes
Querying for up to 10 recipes...
✓ Found 10 recipes

[1/10] Extracting: Topinambours au vinaigre
    ✅ Found 4 ingredients

...

✓ Saved gold standard to: gold_standard_recipes.json
```

### Step 2: Extract with Computer Use

```bash
python3 scripts/recipe_extraction_comprehensive.py
```

This uses the Computer Use agent to:
- Switch to Notion application
- Hover over recipe names to reveal OPEN button
- Click OPEN to show side panel
- Extract ingredients from panel
- Close panel and move to next recipe

### Step 3: Compare Results

```python
from compare_extractions import compare_extractions

# Your Computer Use results
computer_use_results = {
    'Topinambours au vinaigre': [
        'Rice vinegar / Vinaigre de riz',
        'Sugar / Sucre',
        'Beurre / Butter',
        'Topinambours / Jerusalem artichokes'
    ],
    # ... more recipes
}

# Compare against gold standard
compare_extractions(computer_use_results)
```

**Output:**
```
EXTRACTION COMPARISON: Computer Use vs API Gold Standard
======================================================================

Gold Standard: 10 recipes
Computer Use:  10 recipes

======================================================================
DETAILED COMPARISON
======================================================================

✅ Topinambours au vinaigre
  Computer Use: 4 ingredients
  Gold Standard: 4 ingredients
  Matched: 4
  Precision: 100.00%
  Recall: 100.00%
  F1 Score: 100.00%

======================================================================
OVERALL METRICS
======================================================================
Recipes compared:   10
Average Precision:  95.20%
Average Recall:     92.80%
Average F1 Score:   93.98%
======================================================================
```

## Metrics

The comparison tool calculates:

- **Precision:** % of Computer Use ingredients that match gold standard
- **Recall:** % of gold standard ingredients found by Computer Use
- **F1 Score:** Harmonic mean of precision and recall

Thresholds:
- ✅ **Excellent:** F1 ≥ 90%
- ⚠️ **Good:** F1 ≥ 70%
- ❌ **Needs Improvement:** F1 < 70%

## Files Generated

- `gold_standard_recipes.json` - API extraction results (ground truth)
- `computer_use_results.json` - Computer Use extraction results (to be implemented)
- `comparison_report.json` - Detailed comparison metrics (to be implemented)

## Troubleshooting

### "NOTION_TOKEN environment variable not set"

Add your token to `.env` file:
```bash
echo "NOTION_TOKEN=secret_YOUR_TOKEN" >> .env
```

### "Failed to connect to Notion API"

1. Check your token is valid
2. Ensure the integration has access to the Recipe database
3. Verify the database ID is correct: `5bb4c854c109480ebd7c6112e357b4e5`

### Different ingredient counts

The Computer Use extraction may find different numbers because:
- Ingredients might be in nested blocks (API finds all)
- Hover interaction might not reveal all content
- Panel scrolling might be needed for long recipes

This is exactly what the gold standard testing reveals!

## Next Steps

1. ✅ Created gold standard extraction
2. ✅ Created comparison tool
3. ⏳ Modify scripts/recipe_extraction_comprehensive.py to save JSON output
4. ⏳ Run full comparison and generate report
5. ⏳ Iterate on Computer Use extraction to improve accuracy
