# Get Started with the Notion Agent 🚀

Your LangChain-based Notion Agent is ready! Here's everything you need to start using it.

## Quick Setup (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Your API Key
```bash
# For OpenAI (GPT-4)
export OPENAI_API_KEY="sk-..."

# OR for Anthropic (Claude)
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
# See what pages you have
python -m src.agent "what pages do I have?"

# Extract a page
python -m src.agent "extract the Roadmap page"

# Extract from database
python -m src.agent "extract 10 recipes"

# Get current context
python -m src.agent "what's my current context?"
```

## What the Agent Can Do

### 📄 Page Operations
- Extract page content
- Navigate between pages
- Search for pages
- List all available pages

### 🗄️ Database Operations
- Extract multiple pages from databases
- Count items in databases
- Query specific database records

### 🔍 Analysis
- Count blocks/pages
- Summarize content
- Compare pages

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
You: list my pages
Agent: I found 15 pages...

You: extract the first 3
Agent: Extracting... Done!

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
- **[examples/agent_usage.py](examples/agent_usage.py)** - Code examples

## Testing

Verify everything works:
```bash
python test_agent.py
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
- Verify API key is set correctly
- Try verbose mode: `python -m src.agent --verbose "query"`

## What's New

This implementation adds:

✅ **Natural Language Interface** - Ask in plain English  
✅ **Intelligent Method Selection** - Auto-chooses best extraction method  
✅ **Conversation Memory** - Remembers context  
✅ **Interactive Mode** - Chat-style interface  
✅ **Automatic Fallbacks** - Tries multiple methods if needed  
✅ **User Clarification** - Asks when stuck  

## Example Session

```bash
$ python -m src.agent --interactive

You: what can you do?
Agent: I can help you extract and analyze content from Notion...

You: list all my pages
Agent: I found 15 pages in your sidebar:
       1. Project Roadmap
       2. Meeting Notes
       3. Recipe Database
       ...

You: extract 5 recipes
Agent: Extracting 5 pages from database... Done!
       Extracted 5 recipes with 127 total blocks.

You: how many blocks total?
Agent: The 5 recipes contain 127 blocks total.

You: exit
👋 Goodbye!
```

## Ready to Start!

```bash
python -m src.agent --interactive
```

Then try:
- `"what pages do I have?"`
- `"extract the roadmap"`
- `"extract 10 recipes"`

---

**Happy extracting! 🎉**

For more details, see [AGENT_README.md](AGENT_README.md)

