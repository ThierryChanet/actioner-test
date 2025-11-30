# Notion Agent - Quick Start Guide

Get started with the Notion Agent in 5 minutes!

## 1. Install Dependencies

```bash
cd actioner-test
pip install -r requirements.txt
```

Or if you're using the package:

```bash
pip install -e .
```

## 2. Set Your API Key

Choose one LLM provider:

**Option A: OpenAI (GPT-4)**
```bash
export OPENAI_API_KEY="sk-..."
```

**Option B: Anthropic (Claude)**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 3. Verify Installation

```bash
python -m src.agent check
```

You should see:
```
✅ OpenAI API key found (or Anthropic)
✅ LangChain installed
✅ Agent module imports successfully
✅ All checks passed!
```

## 4. Test the Agent

Run the test script:

```bash
python test_agent.py
```

This verifies everything is working correctly.

## 5. Try Your First Query

### One-Shot Query

```bash
python -m src.agent "list all my pages"
```

### Interactive Mode

```bash
python -m src.agent --interactive
```

Then type your questions:
```
You: list all my pages
You: extract the roadmap page
You: how many recipes do I have?
```

Type `exit` to quit.

## Common First Commands

### Explore Your Workspace
```bash
python -m src.agent "what pages do I have?"
```

### Extract a Page
```bash
python -m src.agent "extract the Meeting Notes page"
```

### Extract from Database
```bash
python -m src.agent "extract 10 recipes from my database"
```

### Get Current Info
```bash
python -m src.agent "what page am I on?"
```

## Quick Tips

1. **Make sure Notion is running** - The agent needs the Notion desktop app open
2. **Be specific** - Use exact page names when possible
3. **Use interactive mode** - Better for exploration and multi-step tasks
4. **Let it ask** - If the agent needs info, it will prompt you
5. **Check context** - Ask "what's my current context?" to see what the agent knows

## Troubleshooting

### "No API key found"
Set your API key:
```bash
export OPENAI_API_KEY="sk-..."
```

### "Notion app not found"
Make sure Notion desktop app is running.

### "Agent import failed"
Install dependencies:
```bash
pip install -r requirements.txt
```

### Extraction fails
Try verbose mode to see details:
```bash
python -m src.agent --verbose "your query"
```

## Next Steps

- Read [AGENT_README.md](AGENT_README.md) for full documentation
- Check [AGENT_QUERIES.md](AGENT_QUERIES.md) for more example queries
- Try [examples/agent_usage.py](examples/agent_usage.py) for programmatic usage

## Example Session

Here's a typical first session:

```bash
$ python -m src.agent --interactive

You: what can you do?
Agent: I can help you extract and analyze content from your Notion workspace...

You: list all my pages
Agent: I found 15 pages in your sidebar:
       1. Project Roadmap
       2. Meeting Notes
       ...

You: extract the roadmap
Agent: Extracting "Project Roadmap"... Done! Extracted 42 blocks.
       The page contains sections for Q1 Goals, Q2 Planning, and Team Updates.

You: how many goals are in Q1?
Agent: Based on the extraction, Q1 Goals section contains 5 items...

You: exit
👋 Goodbye!
```

## Keyboard Shortcuts (Interactive Mode)

- `Ctrl+C` - Exit the agent
- `Ctrl+D` - Exit the agent
- Type `exit` or `quit` - Exit gracefully
- Type `reset` - Clear conversation history
- Type `status` - Show current state

## Advanced Usage

### Use Specific Model
```bash
python -m src.agent --model gpt-4 "extract recipes"
```

### Use Anthropic
```bash
python -m src.agent --provider anthropic "extract pages"
```

### Custom Output Directory
```bash
python -m src.agent --output-dir results "extract database"
```

### Verbose Mode
```bash
python -m src.agent --verbose "extract pages"
```

## Configuration

### Optional: Notion API Token

For faster database extraction, set your Notion API token:

```bash
export NOTION_TOKEN="secret_..."
```

This enables API-based extraction (much faster than AX navigation for large databases).

### Optional: Accessibility Permissions

The agent uses macOS Accessibility APIs. If you get permission errors:

1. Open System Settings
2. Privacy & Security → Accessibility
3. Add your Terminal app
4. Restart terminal

Check permissions:
```bash
python -m src.cli check-permissions
```

## Getting Help

### In the Agent
```bash
python -m src.agent "what can you do?"
```

### Show Examples
```bash
python -m src.agent examples
```

### Check Environment
```bash
python -m src.agent check
```

### Read Documentation
- [AGENT_README.md](AGENT_README.md) - Full documentation
- [AGENT_QUERIES.md](AGENT_QUERIES.md) - Example queries
- [README.md](README.md) - General system documentation

---

**You're ready! Try it now:**

```bash
python -m src.agent "list all my pages"
```

or

```bash
python -m src.agent --interactive
```

Happy extracting! 🚀

