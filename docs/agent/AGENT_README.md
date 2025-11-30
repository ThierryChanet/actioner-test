# Notion Agent - Intelligent Extraction Assistant

A LangChain-powered AI agent that intelligently extracts and analyzes content from your Notion workspace using natural language queries.

## Overview

The Notion Agent is an intelligent assistant that understands your requests in plain English and autonomously chooses the best method to accomplish tasks. It wraps all the extraction capabilities (AX, OCR, API, Keyboard, Mouse navigation) into a conversational interface.

## Features

- **Natural Language Interface**: Ask questions in plain English
- **Intelligent Method Selection**: Automatically chooses the best extraction method
- **Multi-turn Conversations**: Remembers context across queries
- **Interactive Mode**: Chat-style interface for exploration
- **Automatic Fallbacks**: Tries multiple methods if one fails
- **User Clarification**: Asks for input when stuck
- **State Tracking**: Knows what it has extracted and where it is

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your API key (choose one):
```bash
# For OpenAI (GPT-4)
export OPENAI_API_KEY="sk-..."

# For Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."
```

3. Optional: Set Notion API token for faster database extraction:
```bash
export NOTION_TOKEN="secret_..."
```

## Quick Start

### One-Shot Queries

Ask a single question:

```bash
python -m src.agent "extract all recipes from my database"
```

```bash
python -m src.agent "what's on the roadmap page?"
```

```bash
python -m src.agent "how many recipes do I have?"
```

### Interactive Mode

Start a conversation:

```bash
python -m src.agent --interactive
```

Then chat with the agent:

```
You: list all my pages
Agent: I found 15 pages in your sidebar...

You: extract the first 3 recipes
Agent: Extracting recipes... Done! Extracted 3 pages with 127 blocks total.

You: what did I just extract?
Agent: You extracted 3 recipes: "Thai Omelet", "Pasta Carbonara", "Chicken Tikka"...
```

## Usage Examples

### Basic Extraction

```bash
# Extract a specific page
python -m src.agent "extract content from the Meeting Notes page"

# Extract from database
python -m src.agent "extract 10 recipes"

# Get current page info
python -m src.agent "what's on the current page?"
```

### Navigation

```bash
# Navigate to a page
python -m src.agent "go to the Project Roadmap page"

# List available pages
python -m src.agent "show me all available pages"
```

### Search and Analysis

```bash
# Search for pages
python -m src.agent "find pages about python"

# Count items
python -m src.agent "how many recipes do I have?"

# Analyze content
python -m src.agent "summarize the roadmap page"
```

### With Options

```bash
# Use Anthropic Claude
python -m src.agent --provider anthropic "extract recipes"

# Use specific model
python -m src.agent --model gpt-4 "analyze my pages"

# Verbose mode (see tool calls)
python -m src.agent --verbose "extract database"

# Custom output directory
python -m src.agent --output-dir results "extract pages"
```

## Command Reference

### Main Command

```bash
python -m src.agent [OPTIONS] [QUERY]
```

**Options:**
- `-i, --interactive`: Start interactive mode
- `-p, --provider`: LLM provider (`openai` or `anthropic`)
- `-m, --model`: Specific model to use
- `--notion-token`: Notion API token
- `-o, --output-dir`: Output directory
- `-v, --verbose`: Enable verbose logging

### Subcommands

#### Interactive Mode

```bash
python -m src.agent interactive
```

Start a multi-turn conversation with the agent.

#### Ask

```bash
python -m src.agent ask "your question here"
```

Ask a single question (same as passing query directly).

#### Examples

```bash
python -m src.agent examples
```

Show usage examples.

#### Check

```bash
python -m src.agent check
```

Check if environment is properly configured.

## Programmatic Usage

Use the agent in your Python scripts:

```python
from src.agent import create_agent

# Create agent
agent = create_agent(
    llm_provider="openai",
    verbose=False
)

# Ask a question
response = agent.run("Extract all recipes")
print(response)

# Multi-turn conversation
agent.chat("List my pages")
agent.chat("Extract the first one")

# Check state
print(agent.get_state_summary())

# Reset for fresh start
agent.reset()
```

See [examples/agent_usage.py](examples/agent_usage.py) for more examples.

## How It Works

### Architecture

1. **Orchestrator**: Unified interface to all extraction methods
2. **LangChain Agent**: Decides which tools to use and when
3. **Tools**: High-level wrappers for Notion operations
4. **State Management**: Tracks context across queries
5. **Callbacks**: Handles user interaction and progress

### Tool Selection

The agent has access to these tools:

- `navigate_to_page`: Navigate to a page by name
- `extract_page_content`: Extract content from a page
- `extract_database`: Extract multiple pages from database
- `list_available_pages`: List all pages in sidebar
- `search_pages`: Search for pages by name
- `get_current_context`: Check current state
- `ask_user`: Request clarification from user

The agent autonomously decides which tools to use based on your query.

### Method Selection

The orchestrator automatically chooses the best extraction method:

1. **API** (fastest) - If database_id and token provided
2. **AX Navigation** (most reliable) - Using Accessibility APIs
3. **OCR Navigation** (fallback) - Using screen capture and OCR
4. **Keyboard/Mouse** (last resort) - Direct input simulation

## Example Interactions

### Scenario 1: Exploring Workspace

```
You: what pages do I have?
Agent: [Uses list_available_pages] I found 15 pages: Roadmap, Meeting Notes, ...

You: extract the meeting notes
Agent: [Uses navigate_to_page, then extract_page_content] Extracted 42 blocks from Meeting Notes page.
```

### Scenario 2: Database Extraction

```
You: extract all my recipes
Agent: I need to know where your recipes are. Can you tell me:
       - Are they in a database view that's currently open?
       - Or do you have a database ID I can use with the API?

You: they're in the current view
Agent: [Uses extract_database] Extracted 47 recipes with 1,234 total blocks.
```

### Scenario 3: Smart Fallback

```
You: get the content from the Project Roadmap
Agent: [Tries navigate_to_page via AX - fails]
       [Tries OCR navigation - succeeds]
       Successfully extracted Roadmap page using OCR navigation.
```

## Configuration

### Environment Variables

```bash
# LLM Provider (required - choose one)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Notion API (optional, for faster database extraction)
export NOTION_TOKEN="secret_..."
```

### LLM Models

**OpenAI (default):**
- `gpt-4-turbo-preview` (default)
- `gpt-4`
- `gpt-3.5-turbo`

**Anthropic:**
- `claude-3-5-sonnet-20241022` (default)
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`

Specify with `--model`:
```bash
python -m src.agent --model gpt-3.5-turbo "your query"
```

## Interactive Mode Commands

In interactive mode, you can use special commands:

- `exit` or `quit`: Exit the agent
- `reset`: Clear conversation history and start fresh
- `status`: Show current agent state

## Tips

### Getting Better Results

1. **Be specific**: "Extract the Project Roadmap page" vs "get roadmap"
2. **Use context**: The agent remembers previous queries
3. **Break down complex tasks**: "First list pages, then extract the top 3"
4. **Let it ask**: If the agent needs clarification, it will ask

### Performance

- **API extraction** is fastest (requires token and database_id)
- **AX navigation** is most reliable (no token needed)
- **OCR fallback** is slowest but works when AX fails

### Troubleshooting

**Agent can't find pages:**
- Try: "list all pages" first to see what's available
- Use exact page names in quotes

**Extraction fails:**
- Make sure Notion app is open and focused
- Try verbose mode: `--verbose` to see what's happening
- Check permissions: `python -m src.cli check-permissions`

**API key issues:**
- Run: `python -m src.agent check` to verify configuration
- Make sure environment variable is set correctly

## Output

All extracted content is saved to the output directory:

```
output/
├── Page_Name_extraction.json
├── Page_Name_extraction.csv
└── logs/
    └── extraction_YYYYMMDD_HHMMSS.log
```

## Advanced Usage

### Custom Output Directory

```bash
python -m src.agent --output-dir custom_output "extract pages"
```

### Chaining Operations

```bash
# In interactive mode
You: list all pages
You: search for pages with 'recipe'
You: extract all the matching pages
```

### With Notion API

For faster database extraction, provide token and database ID:

```bash
export NOTION_TOKEN="secret_..."
python -m src.agent "extract from database abc123def456"
```

## Limitations

- Requires macOS (for Accessibility API)
- Notion desktop app must be running
- Some complex page layouts may not extract perfectly
- Large extractions can be slow

## Comparison with Original CLI

**Original CLI:**
```bash
python -m src.cli extract "Page Name"
python -m src.cli extract-database "db-id" --limit 10
python -m src.cli extract-database-ax --limit 10
```

**Agent CLI:**
```bash
python -m src.agent "extract Page Name"
python -m src.agent "extract 10 pages from my database"
python -m src.agent "extract all recipes"  # Auto-selects method
```

The agent is simpler, more flexible, and automatically chooses the best method.

## Support

For issues or questions:
1. Check environment: `python -m src.agent check`
2. Try verbose mode: `--verbose`
3. See [README.md](README.md) for general troubleshooting
4. Check [examples/agent_usage.py](examples/agent_usage.py) for code examples

## License

MIT License - see [LICENSE](LICENSE) file

