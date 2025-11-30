# Computer Use API Integration

The Notion agent now supports **OpenAI's Computer Control Tools**, providing direct screen control through mouse clicks, keyboard input, and screenshots. This enables the agent to navigate and interact with Notion (or any application) just like a human would.

## Overview

Computer Use mode replaces the traditional AX-based navigation tools with general-purpose computer control tools. The agent can:

- **See** the screen via screenshots
- **Click** on UI elements using precise coordinates
- **Type** text using the keyboard
- **Navigate** using arrow keys, Tab, Enter, etc.
- **Extract** content using the existing AX extraction tools

## Requirements

- **OpenAI API Key**: Computer Use requires an OpenAI API key
- **macOS**: Uses macOS Quartz and Cocoa APIs for screen interaction
- **Accessibility Permissions**: Required for keyboard/mouse automation

## Quick Start

### Command Line

```bash
# Set your OpenAI API key
export OPENAI_API_KEY="sk-..."

# Use Computer Use mode
python -m src.agent --computer-use "navigate to recipes page"

# Interactive mode with Computer Use
python -m src.agent --computer-use --interactive

# Verbose mode to see all actions
python -m src.agent --computer-use --verbose "extract content"
```

### Programmatic Usage

```python
from src.agent import create_agent

# Create agent with Computer Use enabled
agent = create_agent(
    computer_use=True,
    verbose=True
)

# Agent can now control the screen
response = agent.run("take a screenshot and describe what you see")
print(response)

# Navigate and extract
response = agent.run("click on the Roadmap page in Notion sidebar, then extract its content")
print(response)
```

## Available Tools

When Computer Use is enabled, the agent has access to these tools:

### Screen Observation

- **`take_screenshot`**: Capture the entire screen to see what's visible
- **`get_screen_info`**: Get screen dimensions (width, height)
- **`get_cursor_position`**: Get current mouse cursor position

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

### 2. Coordinate-Based Clicking

The agent identifies UI elements and their coordinates, then clicks on them:

```python
agent.run("click on the Recipes page in the sidebar")
# Agent: Takes screenshot, identifies "Recipes" at (120, 450), clicks there
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

## Example Workflows

### Extract After Navigation

```bash
python -m src.agent --computer-use "click on the recipes database, then extract all recipes"
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
python -m src.agent --computer-use "search for 'project roadmap' and extract the first result"
```

The agent will:
1. Screenshot to find search box
2. Click on search box
3. Type "project roadmap"
4. Press Return
5. Click on first result
6. Extract page content

### Multi-Step Navigation

```bash
python -m src.agent --computer-use "go to settings, then export all pages"
```

The agent will:
1. Screenshot to locate settings
2. Navigate through UI
3. Find and click export option
4. Complete the workflow

## Configuration Options

### Display Selection

For multi-monitor setups:

```bash
python -m src.agent --computer-use --display 2 "take a screenshot"
```

Or in code:

```python
agent = create_agent(
    computer_use=True,
    display_num=2  # Use second display
)
```

### Model Selection

Computer Use is powered by OpenAI models:

```python
agent = create_agent(
    model="gpt-4-turbo-preview",  # Default model
    computer_use=True
)

# Or use a different OpenAI model
agent = create_agent(
    model="gpt-4",
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

### 2. Be Specific with Coordinates

If you know exact coordinates, provide them:

```python
agent.run("click at coordinates (150, 300)")
```

### 3. Wait After Navigation

Allow time for pages to load:

```python
agent.run("click on database, wait 2 seconds, then extract")
```

### 4. Combine with Extraction Tools

Use Computer Use for navigation, AX tools for extraction:

```python
agent.run("navigate to the page, then use extract_page_content")
```

### 5. Use Verbose Mode for Debugging

See exactly what the agent is doing:

```bash
python -m src.agent --computer-use --verbose "your query"
```

## Comparison: Computer Use vs AX Navigation

| Feature | AX Navigation (Traditional) | Computer Use (New) |
|---------|---------------------------|-------------------|
| **Navigation** | AX tree traversal | Mouse clicks |
| **Visibility** | No screenshots | Full screen visibility |
| **Flexibility** | Notion-specific | Any application |
| **Reliability** | High (uses accessibility) | Medium (visual-based) |
| **Speed** | Fast | Slower (screenshots) |
| **Setup** | Accessibility permissions | OpenAI API key |
| **Use Case** | Known page structures | Exploratory navigation |

## Troubleshooting

### "Computer Use initialization failed"

**Cause**: Missing OPENAI_API_KEY

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

### Computer Use not working

**Fallback**: The agent automatically falls back to standard tools if Computer Use fails to initialize.

## Performance Considerations

- **Screenshots**: Each screenshot takes ~0.2-0.5 seconds
- **Mouse Actions**: Nearly instantaneous
- **Typing**: ~50ms per character
- **Overall**: Slower than direct AX navigation but more flexible

## Security & Safety

- Computer Use has **full control** of your computer when enabled
- Use `--computer-use` flag only when needed
- The agent can only see what's on screen (no file system access via this tool)
- Consider using in a sandboxed environment for untrusted tasks

## Future Enhancements

Planned improvements:
- Vision API integration for better element detection
- Cached screenshots to reduce API calls
- Multi-monitor coordination
- Custom action macros
- Replay and debugging tools

## See Also

- [Agent Quick Start](AGENT_QUICKSTART.md)
- [Agent README](AGENT_README.md)
- [Example Queries](AGENT_QUERIES.md)
- [OpenAI Computer Control Tools Documentation](https://platform.openai.com/docs/guides/tools-computer-use)

## Support

For issues or questions about Computer Use:
1. Check error messages with `--verbose`
2. Verify API key is set: `echo $OPENAI_API_KEY`
3. Test with simple queries: `"take a screenshot"`
4. Review logs in `output/logs/`
5. Open an issue on GitHub with error details

