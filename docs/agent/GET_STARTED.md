# Get Started with the Notion Agent 🚀

Your LangChain-based Notion Agent is ready! Here's everything you need to start using it.

## Quick Setup (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Your API Keys
```bash
# Required for LLM (agent reasoning)
export OPENAI_API_KEY="sk-..."

# Required for Computer Use (vision + screen control)
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Verify Setup
```bash
python -m src.agent check
```

### 4. Start Using!
```bash
# Interactive mode (recommended for first time)
python -m src.agent --interactive

# Or one-shot query
python -m src.agent "list all my pages"
```

## Your First Commands

Try these to get started:

```bash
# See what pages you have (via screenshot)
python -m src.agent "take a screenshot and tell me what pages are visible"

# Navigate and extract
python -m src.agent "click on recipes in the sidebar, then extract the content"

# Extract from database
python -m src.agent "extract 10 recipes"

# Get current context
python -m src.agent "what's my current context?"
```

## What the Agent Can Do

### 🖥️ Computer Use (Default)
- Take screenshots and analyze with Claude vision
- Click on UI elements by name or coordinates
- Type text and press keys
- Navigate any application

### 📄 Page Operations
- Extract page content
- Navigate between pages
- Search for pages

### 🗄️ Database Operations
- Extract multiple pages from databases
- Count items in databases
- Query specific database records

### 💬 Conversation
- Remembers context
- Asks for clarification when needed
- Provides progress updates

## Two Ways to Use

### 1. Interactive Mode (Best for Exploration)
```bash
python -m src.agent --interactive
```

Then chat with the agent:
```
You: take a screenshot
Agent: I can see Notion with pages: Recipes, Roadmap...

You: click on recipes
Agent: Clicked on Recipes. Taking screenshot to verify...

You: extract the database
Agent: Extracting... Done! 15 recipes with 340 blocks.

You: exit
```

### 2. One-Shot Mode (Best for Automation)
```bash
python -m src.agent "your query here"
```

## Documentation

- **[AGENT_QUICKSTART.md](AGENT_QUICKSTART.md)** - 5-minute quick start
- **[AGENT_README.md](AGENT_README.md)** - Complete documentation
- **[AGENT_QUERIES.md](AGENT_QUERIES.md)** - 100+ example queries
- **[COMPUTER_USE.md](COMPUTER_USE.md)** - Computer Use guide

## Testing

Verify everything works:
```bash
python tests/test_agent.py
```

## Need Help?

### Check Environment
```bash
python -m src.agent check
```

### See Examples
```bash
python -m src.agent examples
```

### Troubleshooting
- Make sure Notion desktop app is running
- Verify both API keys are set correctly
- Try verbose mode: `python -m src.agent --verbose "query"`

## What's New

This implementation includes:

✅ **Natural Language Interface** - Ask in plain English  
✅ **Computer Use via Anthropic** - Vision + screen control  
✅ **Intelligent Method Selection** - Auto-chooses best approach  
✅ **Conversation Memory** - Remembers context  
✅ **Interactive Mode** - Chat-style interface  
✅ **Automatic Fallbacks** - Tries multiple methods if needed  

## Example Session

```bash
$ python -m src.agent --interactive

You: take a screenshot
Agent: I can see the Notion app with a sidebar showing:
       - Project Roadmap
       - Meeting Notes  
       - Recipe Database
       ...

You: click on Recipe Database
Agent: Clicking on Recipe Database... Done!
       Taking screenshot to verify - page is loading.

You: extract 5 recipes
Agent: Extracting 5 pages from database... Done!
       Extracted 5 recipes with 127 total blocks.

You: exit
👋 Goodbye!
```

## Ready to Start!

```bash
python -m src.agent --interactive
```

Then try:
- `"take a screenshot"`
- `"click on [page name]"`
- `"extract the content"`

---

**Happy extracting! 🎉**

For more details, see [AGENT_README.md](AGENT_README.md)
