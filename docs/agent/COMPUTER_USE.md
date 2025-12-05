# Computer Use API Integration

The Notion agent uses **Anthropic's Claude Computer Use** by default, providing direct screen control through mouse clicks, keyboard input, and screenshots. This enables the agent to navigate and interact with Notion (or any application) just like a human would.

**Computer Use is ENABLED by default** - no flags required!

## Overview

Computer Use mode provides general-purpose computer control tools. The agent can:

- **See** the screen via screenshots (analyzed by Claude's vision)
- **Click** on UI elements using precise coordinates
- **Type** text using the keyboard
- **Navigate** using arrow keys, Tab, Enter, etc.
- **Extract** content using the existing AX extraction tools

## Requirements

- **OpenAI API Key**: Required for LLM chat (the agent's reasoning)
- **Anthropic API Key**: Required for Computer Use (vision + screen control)
- **macOS**: Uses macOS Quartz and Cocoa APIs for screen interaction
- **Accessibility Permissions**: Required for keyboard/mouse automation

## Quick Start

### Command Line

```bash
# Set your API keys
export OPENAI_API_KEY="sk-..."       # Required for LLM
export ANTHROPIC_API_KEY="sk-ant-..." # Required for Computer Use

# Computer Use is enabled by default!
python -m src.agent "navigate to recipes page"

# Interactive mode (Computer Use enabled by default)
python -m src.agent --interactive

# Verbose mode to see all actions
python -m src.agent --verbose "extract content"

# Disable Computer Use if needed (use standard AX navigation)
python -m src.agent --no-computer-use "extract content"
```

### Programmatic Usage

```python
from src.agent import create_agent

# Create agent with Computer Use enabled (default)
agent = create_agent(
    computer_use=True,
    verbose=True
)

# Agent can now control the screen via Anthropic Claude
response = agent.run("take a screenshot and describe what you see")
print(response)

# Navigate and extract
response = agent.run("click on the Roadmap page in Notion sidebar, then extract its content")
print(response)
```

## Available Tools

When Computer Use is enabled, the agent has access to these tools:

### Screen Observation

- **`take_screenshot`**: Capture the entire screen and analyze with Claude vision
- **`get_screen_info`**: Get screen dimensions (width, height)
- **`get_cursor_position`**: Get current mouse cursor position

### Desktop Management

- **`switch_desktop`**: Switch to a macOS desktop (Mission Control Space) containing a specific application

### Mouse Control

- **`move_mouse`**: Move cursor to specific (x, y) coordinates
- **`left_click`**: Perform left click at coordinates or current position
- **`right_click`**: Perform right click (context menu)
- **`double_click`**: Perform double click

### Keyboard Control

- **`type_text`**: Type text at current cursor location
- **`press_key`**: Press special keys (Return, Tab, Escape, arrows, etc.)

### Notion Extraction (Preserved)

- **`extract_page_content`**: Extract content from current or named page
- **`extract_database`**: Extract multiple pages from a database
- **`get_current_context`**: Check current extraction state
- **`ask_user`**: Ask user for clarification

## How It Works

### 1. Screenshot-Driven Navigation

The agent starts by taking a screenshot to understand the current screen state:

```python
agent.run("take a screenshot")
# Agent sees: "I can see a Notion sidebar with pages: Recipes, Roadmap, Meeting Notes..."
```

### 2. Claude Vision Analysis

Anthropic Claude analyzes the screenshot and provides element locations:

```python
agent.run("click on the Recipes page in the sidebar")
# Agent: Takes screenshot, Claude identifies "Recipes" at (120, 450), clicks there
```

### 3. Keyboard Input

The agent can type text and use special keys:

```python
agent.run("search for 'meeting notes' in Notion")
# Agent: Clicks search box, types "meeting notes", presses Return
```

### 4. Content Extraction

After navigation, the agent uses AX tools to extract content:

```python
agent.run("navigate to Roadmap page and extract all content")
# Agent: Clicks page, waits for load, extracts via AX, returns content
```

## Desktop Switching

### Overview

The agent can automatically switch between macOS desktops (Mission Control Spaces) to access applications that are not visible on the current desktop.

### Usage

```python
# Switch to the desktop containing Notion
agent.run("switch to the desktop with Notion")

# Or be more explicit
agent.run("use switch_desktop to find Notion")
```

### Supported Applications

The tool works with any macOS application:
- `"Notion"` - Notion desktop app
- `"Safari"` - Safari browser
- `"Google Chrome"` - Chrome browser
- `"Finder"` - macOS Finder
- Any other running application

## Example Workflows

### Extract After Navigation

```bash
python -m src.agent "click on the recipes database, then extract all recipes"
```

The agent will:
1. Take a screenshot to see the screen
2. Identify the recipes database in the sidebar
3. Click on it
4. Wait for the page to load
5. Use `extract_database` to capture content
6. Return a summary

### Search and Extract

```bash
python -m src.agent "search for 'project roadmap' and extract the first result"
```

The agent will:
1. Screenshot to find search box
2. Click on search box
3. Type "project roadmap"
4. Press Return
5. Click on first result
6. Extract page content

## Configuration Options

### Display Selection

For multi-monitor setups:

```bash
python -m src.agent --display 2 "take a screenshot"
```

Or in code:

```python
agent = create_agent(
    computer_use=True,
    display_num=2  # Use second display
)
```

### Model Selection

The LLM is powered by OpenAI models (Computer Use vision is Anthropic):

```python
agent = create_agent(
    model="gpt-4o",  # Default model for LLM
    computer_use=True
)
```

## Best Practices

### 1. Always Screenshot First

Before taking actions, let the agent see the screen:

```python
# Good
agent.run("take a screenshot, then click on recipes")

# Less reliable
agent.run("click on recipes")  # Agent can't see where it is
```

### 2. Verify Every Action

The agent should take a screenshot after EVERY action to verify it worked:

```python
# Good - agent verifies each step
agent.run("click on the menu button, take a screenshot to verify it opened, then click on settings")
```

### 3. Be Specific with Coordinates

If you know exact coordinates, provide them:

```python
agent.run("click at coordinates (150, 300)")
```

### 4. Use Verbose Mode for Debugging

See exactly what the agent is doing with timing information:

```bash
python -m src.agent --verbose "your query"
```

## Comparison: Computer Use vs AX Navigation

| Feature | AX Navigation (Traditional) | Computer Use (Anthropic) |
|---------|---------------------------|-------------------|
| **Navigation** | AX tree traversal | Mouse clicks |
| **Visibility** | No screenshots | Full screen visibility via Claude |
| **Flexibility** | Notion-specific | Any application |
| **Reliability** | High (uses accessibility) | High (Claude vision) |
| **Speed** | Fast | Moderate (screenshot analysis) |
| **Setup** | Accessibility permissions | Anthropic + OpenAI API keys |
| **Use Case** | Known page structures | Exploratory navigation |

## Troubleshooting

### "Computer Use initialization failed"

**Cause**: Missing ANTHROPIC_API_KEY

**Solution**:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "OPENAI_API_KEY required"

**Cause**: Missing OpenAI key for LLM

**Solution**:
```bash
export OPENAI_API_KEY="sk-..."
```

### "Failed to capture screenshot"

**Cause**: Missing screen recording permissions

**Solution**: Grant permissions in System Preferences > Privacy > Screen Recording

### "Failed to type text"

**Cause**: Missing accessibility permissions

**Solution**: Enable in System Preferences > Privacy > Accessibility

### Agent clicks wrong coordinates

**Cause**: Resolution mismatch or Retina display scaling

**Solution**: 
- Use verbose mode to see coordinates
- Take screenshots to verify
- Adjust display_num parameter

## Performance Considerations

- **Screenshots**: Each screenshot takes ~130ms (with caching: <1ms)
- **Claude Analysis**: 3-5 seconds per analysis
- **Mouse Actions**: <1ms (highly optimized)
- **Typing**: ~30ms (optimized)

### Performance Tracking

When running with `--verbose`, you'll see timing information for all operations:

```
⏱️  screenshot completed in 129ms
⏱️  execute_action completed in 0.4ms
⏱️  switch_desktop completed in 850ms
```

Performance logs are automatically saved to `output/logs/performance_YYYYMMDD_HHMMSS.jsonl` for analysis.

## Security & Safety

- Computer Use has **full control** of your computer when enabled
- Use `--no-computer-use` flag to disable if not needed
- The agent can only see what's on screen (no file system access via this tool)
- Consider using in a sandboxed environment for untrusted tasks

## See Also

- [Agent Quick Start](AGENT_QUICKSTART.md)
- [Agent README](AGENT_README.md)
- [Example Queries](AGENT_QUERIES.md)
- [Anthropic Computer Use Documentation](https://docs.anthropic.com/claude/docs/computer-use)

## Support

For issues or questions about Computer Use:
1. Check error messages with `--verbose`
2. Verify API keys are set: `echo $ANTHROPIC_API_KEY` and `echo $OPENAI_API_KEY`
3. Test with simple queries: `"take a screenshot"`
4. Review logs in `output/logs/`
5. Open an issue on GitHub with error details
