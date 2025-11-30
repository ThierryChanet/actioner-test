# Examples

This directory contains example scripts demonstrating various extraction methods.

## Quick Setup

1. **Copy and edit the environment file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your keys (without quotes!)
   ```

2. **Add your API keys to `.env`:**
   - For AI Agent: Add your `OPENAI_API_KEY`
   - For API extraction: Add your `NOTION_TOKEN` (get from https://www.notion.so/my-integrations)
   - **Important:** Don't use quotes around the values!

3. **Run any example script!**
   
   The `.env` file is **automatically loaded** - no need to `export` or `source` it!
   
   ```bash
   python examples/agent_usage.py
   ```

## Available Examples

### 0. Agent Usage (`agent_usage.py`) ⭐ NEWEST!

Programmatic usage of the LangChain AI agent:

```bash
# Set your API key first
export OPENAI_API_KEY="sk-..."

# Run the example
python examples/agent_usage.py
```

Features:
- Natural language queries
- Multi-turn conversations
- State management
- Various configuration examples
- **NEW:** Computer Use mode for screen control

#### Computer Use Mode 🖥️

The agent uses **OpenAI's Computer Control Tools** by default for direct screen control via mouse and keyboard:

```bash
# Requires OpenAI API key
export OPENAI_API_KEY="sk-..."

# Computer Use is enabled by default!
python -m src.agent "navigate to recipes and extract content"

# Or in code (Computer Use enabled by default):
agent = create_agent()
agent.run("take a screenshot and tell me what you see")

# Disable Computer Use if needed:
agent = create_agent(computer_use=False)
```

**Computer Use Features:**
- Take screenshots to see the screen
- Click at specific coordinates
- Type text via keyboard
- Press special keys (Return, Tab, arrows, etc.)
- Full mouse control (move, left/right/double click)

**See [../docs/agent/](../docs/agent/) for more agent documentation.**

### 1. AX-Based Database Extraction (`extract_database_with_ax.py`) ⭐ NEW!

Extract database pages using AX navigation - **no API token needed!**

```bash
# Open a database in Notion first, then run:
python examples/extract_database_with_ax.py
```

Features:
- No API token required
- Interactive prompts
- Navigates through database rows
- Progress display
- Saves as JSON

**This is the recommended method if you don't have an API token!**

### 2. Simple Usage (`simple_usage.py`)

Minimal example showing API-based extraction:

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

### 3. Recipe Database Extractor (`extract_recipe_database.py`)

Interactive script using API that prompts for database ID:

```bash
export NOTION_TOKEN="secret_..."
python examples/extract_recipe_database.py
```

Features:
- Interactive prompts
- Progress display
- Summary report
- Saves as JSON and CSV

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

See [../docs/extraction/USAGE_EXAMPLES.md](../docs/extraction/USAGE_EXAMPLES.md) for more detailed examples including:
- Export to Markdown
- Build search indexes
- Content analysis
- Batch processing

## Documentation

- **[Agent Documentation](../docs/agent/)** - AI agent usage
- **[Extraction Methods](../docs/extraction/)** - Database extraction guides
- **[Setup Guides](../docs/guides/)** - Configuration and troubleshooting

