# Notion macOS Direct-Action Extractor

A macOS tool that extracts text content from the Notion desktop app using **direct Accessibility (AX) actions** instead of simulated mouse or keyboard input. The extractor navigates between pages, captures all visible content, and uses OCR only as a fallback.

## Features

- **🤖 AI Agent (NEW!)** - Natural language interface powered by LangChain - ask questions in plain English!
- **OCR + Click Navigation (Default)** - Reliable visual navigation using macOS Vision API and mouse automation
- **Direct AX-based text extraction** - Uses macOS Accessibility APIs for content capture
- **Database extraction (AX Navigation)** - Click through database rows to extract pages - **no API token needed!**
- **Database extraction (API)** - Fast bulk extraction using Notion API
- **Hybrid extraction** - Combines OCR navigation with AX content extraction
- **Deterministic scrolling** - Full-page traversal with consistent results across runs
- **Notion API validation** - Compare extracted content with API "gold standard"
- **Multiple modes** - Normal, dry-run, and debug modes
- **Flexible output** - JSON and CSV exports with comprehensive logging

## Requirements

- macOS 10.15 or later
- Python 3.10 or later
- Notion desktop app
- Accessibility permissions enabled

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd actioner-test
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install in development mode:
```bash
pip install -e .
```

3. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your API keys (without quotes!):
# - OPENAI_API_KEY (for AI agent)
# - NOTION_TOKEN (optional, for API-based extraction)
```

The `.env` file is automatically loaded by the application - no need to manually export variables!

4. **Enable Accessibility Permissions:**
   - Go to **System Preferences** > **Security & Privacy** > **Privacy** > **Accessibility**
   - Add your terminal application or Python to the list
   - Grant permission

## Quick Start

### 🤖 NEW: Use the AI Agent (Recommended)

Ask questions in natural language:

```bash
# Set your API key first
export OPENAI_API_KEY="sk-..."

# Ask questions in plain English
python -m src.agent "extract all recipes from my database"
python -m src.agent "what's on the roadmap page?"
python -m src.agent "how many recipes do I have?"

# Interactive mode
python -m src.agent --interactive
```

**📖 See [docs/agent/](docs/agent/) for complete agent documentation:**
- [Get Started (2 min)](docs/agent/GET_STARTED.md)
- [Quick Start (5 min)](docs/agent/AGENT_QUICKSTART.md)
- [Full Documentation](docs/agent/AGENT_README.md)
- [Example Queries](docs/agent/AGENT_QUERIES.md)

---

### Classic CLI: Extract a Single Page

```bash
python -m src.cli extract "Project Roadmap"
```

### Extract All Pages

```bash
python -m src.cli extract-all --output both
```

### List Available Pages

```bash
python -m src.cli list-pages
```

### Validate Against API

```bash
export NOTION_TOKEN="your_notion_api_token"
python -m src.cli validate "Project Roadmap" --page-id "your-page-id"
```

### Extract from Database (Two Methods)

#### Method 1: AX Navigation (No API token needed!)

```bash
# Open database in Notion, then:
python -m src.cli extract-database-ax --limit 10
```

**📖 See [docs/extraction/DATABASE_AX_EXTRACTION.md](docs/extraction/DATABASE_AX_EXTRACTION.md)** - Extracts by clicking through rows

#### Method 2: API-based (Faster for bulk extraction)

```bash
export NOTION_TOKEN="your_notion_api_token"
python -m src.cli extract-database "your-database-id" --limit 10
```

**📖 See [docs/extraction/DATABASE_EXTRACTION.md](docs/extraction/DATABASE_EXTRACTION.md)** - Direct API access

## Usage

### Commands

#### `extract <page_name>`

Extract content from a single page.

**Options:**
- `--mode [normal|dry-run|debug]` - Execution mode (default: normal)
- `--output [json|csv|both]` - Output format (default: json)
- `--no-ocr` - Disable OCR fallback

**Examples:**
```bash
# Extract with JSON output
python -m src.cli extract "Meeting Notes"

# Extract with CSV output
python -m src.cli extract "Sprint Planning" --output csv

# Dry-run mode (no actual extraction)
python -m src.cli extract "Roadmap" --mode dry-run

# Disable OCR
python -m src.cli extract "Simple Page" --no-ocr
```

#### `extract-all`

Extract content from all pages in the sidebar.

**Options:**
- `--mode [normal|dry-run|debug]` - Execution mode
- `--output [json|csv|both]` - Output format
- `--no-ocr` - Disable OCR fallback

**Example:**
```bash
python -m src.cli extract-all --output both
```

#### `navigate <page_name>`

Navigate to a page without extracting content.

**Example:**
```bash
python -m src.cli navigate "Weekly Report"
```

#### `validate <page_name>`

Compare extracted content with Notion API baseline.

**Options:**
- `--notion-token TOKEN` - Notion API token (or set NOTION_TOKEN env var)
- `--page-id ID` - Notion page ID (optional, will search by name if not provided)
- `--output [json|csv|both]` - Output format

**Example:**
```bash
export NOTION_TOKEN="secret_ABC123..."
python -m src.cli validate "Project Roadmap" --page-id "abc-123-def"
```

#### `extract-database <database_id>`

Extract content from the first N pages of a Notion database.

**Options:**
- `--notion-token TOKEN` - Notion API token (or set NOTION_TOKEN env var)
- `--limit N` - Number of pages to extract (default: 10)
- `--output [json|csv|both]` - Output format (default: json)

**Examples:**
```bash
# Extract first 10 pages from a Recipe database
export NOTION_TOKEN="secret_ABC123..."
python -m src.cli extract-database "abc123def456" --limit 10

# Extract 20 pages with both JSON and CSV output
python -m src.cli extract-database "abc123def456" --limit 20 --output both

# With verbose logging
python -m src.cli --verbose extract-database "abc123def456"
```

**See [docs/extraction/DATABASE_EXTRACTION.md](docs/extraction/DATABASE_EXTRACTION.md) for complete guide.**

#### `extract-database-ax`

Extract database pages using AX navigation (no API token required).

**Options:**
- `--limit N` - Number of pages to extract (default: 10)
- `--output [json|csv|both]` - Output format (default: json)
- `--no-ocr` - Disable OCR fallback
- `--navigation-delay SECONDS` - Delay after navigation (default: 1.0)

**Examples:**
```bash
# Open a database in Notion first, then run:
python -m src.cli extract-database-ax --limit 10

# With verbose output
python -m src.cli --verbose extract-database-ax --limit 5 --output both

# Faster navigation (less reliable)
python -m src.cli extract-database-ax --limit 10 --navigation-delay 0.5
```

**See [docs/extraction/DATABASE_AX_EXTRACTION.md](docs/extraction/DATABASE_AX_EXTRACTION.md) for complete guide.**

#### `list-database-rows`

List all rows in the current database view.

**Example:**
```bash
python -m src.cli list-database-rows
```

#### `list-pages`

List all pages visible in the Notion sidebar.

**Example:**
```bash
python -m src.cli list-pages
```

### Global Options

- `--verbose` - Enable verbose debug logging (deprecated, use `--verbosity=verbose`)
- `--verbosity LEVEL` - Set verbosity level: `silent`, `minimal`, `default`, `verbose`
  - `silent`: Only errors and warnings
  - `minimal`: Only timestamps
  - `default`: Normal output
  - `verbose`: Detailed debug output
- `--output-dir PATH` - Set output directory (default: `output`)

**Example:**
```bash
python -m src.cli --verbosity=verbose --output-dir results extract "My Page"
python -m src.cli --verbosity=minimal extract "My Page"  # Timestamps only
```

## Output

### JSON Output

Extraction results are saved as JSON files with the following structure:

```json
{
  "page_id": null,
  "title": "Project Roadmap",
  "blocks": [
    {
      "type": "heading",
      "content": "Q1 Goals",
      "source": "ax",
      "order": 0,
      "metadata": {
        "role": "AXHeading"
      }
    },
    {
      "type": "text",
      "content": "Complete feature X",
      "source": "ax",
      "order": 1,
      "metadata": {
        "role": "AXStaticText"
      }
    }
  ],
  "metadata": {
    "block_count": 2,
    "scroll_count": 5
  }
}
```

### CSV Output

Extraction results are also available as CSV:

| Order | Type    | Content              | Source | Role          |
|-------|---------|----------------------|--------|---------------|
| 0     | heading | Q1 Goals             | ax     | AXHeading     |
| 1     | text    | Complete feature X   | ax     | AXStaticText  |

### Logs

Comprehensive logs are saved to `output/logs/` with:
- Navigation actions
- Scroll cycles
- OCR fallback decisions
- Error recovery attempts
- Performance metrics

## Validation & Testing

### Compare with Notion API

The tool can fetch the "gold standard" content from the Notion API and compare it with the extracted content:

```bash
export NOTION_TOKEN="your_token"
python -m src.cli validate "My Page"
```

This generates a detailed comparison report:

```
================================================================================
EXTRACTION COMPARISON REPORT
================================================================================

Page: "Project Roadmap"
Gold Standard Source: api
Extracted Source: AX + OCR

SUMMARY
--------------------------------------------------------------------------------
Overall Accuracy: 94.2%
Block Match Rate: 92.0%
Text Similarity: 97.5%

Gold Blocks: 25
Extracted Blocks: 24
Matched Blocks: 23
Missing Blocks: 2
Extra Blocks: 1
Text Mismatches: 3
```

### Running Tests

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src --cov-report=html
```

## Architecture

```
src/
├── ax/                    # Accessibility layer
│   ├── client.py          # AX API wrapper
│   ├── element.py         # AX element abstraction
│   └── utils.py           # Helper functions
├── notion/                # Notion-specific logic
│   ├── detector.py        # App detection & state
│   ├── navigator.py       # Page navigation
│   └── extractor.py       # Content extraction
├── ocr/                   # OCR fallback
│   ├── vision.py          # macOS Vision API
│   └── fallback.py        # Tesseract fallback
├── validation/            # Testing framework
│   ├── notion_api.py      # API client
│   ├── comparator.py      # Content comparison
│   └── differ.py          # Diff generation
├── output/                # Export handlers
│   ├── json_writer.py
│   ├── csv_writer.py
│   └── logger.py
├── cli.py                 # CLI interface
├── errors.py              # Error handling
└── main.py                # Entry point
```

## How It Works

### 1. Detection
- Finds Notion.app process using macOS workspace APIs
- Activates application and gets AX element tree
- Waits for page to load (checks for spinners, title changes)

### 2. Navigation
- Locates sidebar pages via AX tree traversal
- Invokes AX "Press" action on page links (no mouse simulation)
- Confirms navigation by detecting title changes
- Supports back/forward navigation and in-page links

### 3. Extraction
- Finds main scrollable content area via AX roles
- Extracts text from AX elements (AXValue, AXTitle attributes)
- Scrolls programmatically using AX scroll actions
- Tracks seen content to avoid duplicates
- Maintains document order consistently

### 4. OCR Fallback
- Identifies elements without accessible text
- Captures screenshots of element bounding boxes
- Uses macOS Vision API for text recognition
- Falls back to Tesseract if Vision unavailable
- Marks blocks with source ("ax" or "ocr")

### 5. Validation
- Fetches content via Notion API
- Normalizes both sources to common format
- Fuzzy-matches blocks by content similarity
- Identifies missing, extra, and mismatched blocks
- Generates accuracy metrics and diff reports

## Troubleshooting

### "Accessibility permissions not granted"

Enable accessibility permissions:
1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Select **Accessibility** from the list
3. Click the lock to make changes
4. Add your terminal or Python to the list
5. Restart your terminal

### "Notion app not found"

Make sure Notion desktop app is running before executing commands.

### Extraction returns empty or incomplete results

- Ensure the Notion page has fully loaded
- Try increasing timeouts (modify source if needed)
- Check logs for specific errors
- Verify Notion app version compatibility

### Navigation fails

- Ensure sidebar is visible (toggle with Cmd+\)
- Check that page name matches exactly (case-insensitive)
- Try using `list-pages` to see available pages
- Some nested pages may not be accessible via sidebar

### OCR not working

- macOS Vision API requires macOS 10.15+
- Install Tesseract as fallback: `brew install tesseract`
- Check logs to see which OCR engine is active

## Performance

- **Single page extraction:** 2-10 seconds (depending on length)
- **Navigation:** 1-2 seconds per page
- **OCR:** Adds 0.5-2 seconds per inaccessible element
- **API validation:** 2-5 seconds per page

## Limitations

- Requires Notion desktop app (does not work with web version)
- Limited to visible text content (no images, embeds, or attachments)
- Electron app structure can change between Notion versions
- Some complex page layouts may not extract perfectly
- Rapid navigation can cause stability issues

## Future Enhancements

- Support for extracting databases and tables
- Image and embed metadata capture
- Parallel page extraction
- Incremental updates (only extract changed pages)
- Integration with other note-taking apps

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Documentation

- **[Agent Documentation](docs/agent/)** - Natural language AI agent
- **[Extraction Methods](docs/extraction/)** - AX, API, OCR extraction guides  
- **[Setup Guides](docs/guides/)** - Permissions, debugging, quick starts
- **[Examples](examples/)** - Code examples
- **[Repository Structure](REPOSITORY_STRUCTURE.md)** - Complete directory guide
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines

📖 **[Browse all documentation](docs/)** | 🗂️ **[Repository structure](REPOSITORY_STRUCTURE.md)**

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

- Built with PyObjC for macOS Accessibility API access
- Uses notion-client for API validation
- LangChain for AI agent functionality
- Inspired by the need for reliable, deterministic content extraction

---

**Note:** This tool is for personal use and automation. Respect Notion's Terms of Service and rate limits when using the API validation features.
