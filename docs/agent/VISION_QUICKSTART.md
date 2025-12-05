# Vision AI Quick Start

## What's New?

The agent can now **see and understand** your screen using GPT-4o vision! 🎉

## How It Works

When you take a screenshot, the agent:
1. Captures your screen
2. Sends it to GPT-4o vision model
3. Gets a detailed description
4. Uses that to help you

## Try It Now

```bash
# Make sure you have your API key set
export OPENAI_API_KEY="sk-..."

# Ask the agent to look at your screen
python -m src.agent "take a screenshot and describe what you see"
```

## Example Interactions

### See What's On Screen
```bash
python -m src.agent "take a screenshot and tell me what's visible"
```

**Agent Response:**
> "I can see the Notion app is open with a database view showing recipes. The sidebar on the left has pages like 'Roadmap', 'Meeting Notes', and 'Recipes'. The main area shows a table with recipe names and categories."

### Navigate Based on Vision
```bash
python -m src.agent "take a screenshot, find the recipes database, and click on it"
```

**Agent Response:**
> "I can see the Recipes database in the left sidebar at approximately (150, 300). Clicking on it now..."

### Extract After Visual Confirmation
```bash
python -m src.agent "take a screenshot to confirm we're on the right page, then extract the content"
```

## What The Agent Can See

The vision AI can identify:

- ✅ **Applications**: Which app is open (Notion, Chrome, etc.)
- ✅ **UI Elements**: Buttons, menus, sidebars, toolbars
- ✅ **Text Content**: Visible text, titles, labels
- ✅ **Layout**: Where things are positioned on screen
- ✅ **Colors & Themes**: Dark mode, light mode, color schemes
- ✅ **State**: Loading indicators, selected items, focus

## Tips for Best Results

1. **Be Specific**: "take a screenshot and find the blue button"
2. **Ask for Confirmation**: "take a screenshot to verify we're on the recipes page"
3. **Combine Actions**: "screenshot, find the search box, and type 'pasta'"
4. **Describe What You Want**: "take a screenshot and tell me if you see any errors"

## Vision vs Standard Mode

| Feature | Standard Mode | Vision Mode (Computer Use) |
|---------|--------------|---------------------------|
| Screenshot | ✅ Captures | ✅ Captures + Analyzes |
| Screen Description | ❌ No | ✅ Yes |
| UI Understanding | ❌ No | ✅ Yes |
| Visual Navigation | ❌ No | ✅ Yes |
| Model Used | gpt-4-turbo | gpt-4o (vision) |

## Cost & Performance

- **Screenshot + Analysis**: ~3-5 seconds
- **Cost per Screenshot**: ~$0.01-0.02
- **Recommendation**: Use strategically for navigation and verification

## Troubleshooting

### "Vision analysis failed"
- Check your OPENAI_API_KEY is valid
- Ensure you have GPT-4o access
- Check your internet connection

### "Screenshot captured but no description"
- Vision analysis may have timed out
- Try again with a simpler request
- Check API rate limits

### Agent says it can't see
- Make sure Computer Use is enabled (it's on by default)
- Don't use `--no-computer-use` flag
- Verify you're using the agent, not the classic CLI

## Advanced Usage

### Python API
```python
from src.agent import create_agent

# Vision enabled by default with Computer Use
agent = create_agent(verbose=True)

# Agent can now see your screen
response = agent.run("take a screenshot and describe the layout")
print(response)
```

### Interactive Mode
```bash
python -m src.agent --interactive
```

Then:
```
You: take a screenshot
Agent: I can see Notion is open with...

You: click on the recipes database
Agent: Clicking on Recipes at (150, 300)...

You: now extract the content
Agent: Extracting content from Recipes database...
```

## Examples

### Find and Click
```bash
python -m src.agent "take a screenshot, find the 'New Page' button, and click it"
```

### Verify Before Action
```bash
python -m src.agent "take a screenshot to check if we're on the roadmap page, then extract it"
```

### Describe and Navigate
```bash
python -m src.agent "take a screenshot, tell me what databases are visible, then open the recipes one"
```

### Visual Search
```bash
python -m src.agent "take a screenshot and tell me if you see any error messages"
```

## What's Next?

The vision integration enables:
- 🎯 **Smart Navigation**: Agent finds elements visually
- 🔍 **Visual Verification**: Confirms actions succeeded
- 📊 **Layout Understanding**: Knows where things are
- 🤖 **Intelligent Interaction**: Acts like a human user

Try it out and see how the agent can now truly "see" your screen!

## Need Help?

- See [COMPUTER_USE_IMPLEMENTATION.md](../implementation/COMPUTER_USE_IMPLEMENTATION.md) for technical details
- See [VISION_INTEGRATION_SUMMARY.md](../implementation/VISION_INTEGRATION_SUMMARY.md) for implementation info
- Run `python -m src.agent --help` for command options

