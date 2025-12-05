# Computer Use API Integration

The Notion agent uses **OpenAI's Computer Control Tools** by default, providing direct screen control through mouse clicks, keyboard input, and screenshots. This enables the agent to navigate and interact with Notion (or any application) just like a human would.

**Computer Use is ENABLED by default** - no flags required!

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

## Desktop Switching

### Overview

The agent can automatically switch between macOS desktops (Mission Control Spaces) to access applications that are not visible on the current desktop. This is particularly useful when:

- Notion is open on a different desktop
- You're running the agent from a terminal on one desktop while Notion is on another
- You have multiple applications organized across different desktops

### How It Works

The `switch_desktop` tool finds an application by name and activates it, which automatically switches to the desktop where that application is located. macOS handles the desktop switching automatically when an application is activated.

### Usage

```python
# Switch to the desktop containing Notion
agent.run("switch to the desktop with Notion")

# Or be more explicit
agent.run("use switch_desktop to find Notion")
```

The agent will:
1. Search for the specified application across all desktops
2. Activate the application if found
3. macOS automatically switches to that desktop
4. Return success status

### Auto-Return Feature

When Computer Use is enabled, the agent automatically:
1. **Stores** the frontmost application when it starts
2. **Switches** to other desktops as needed during execution
3. **Returns** to the original application/desktop when finished

This ensures your workspace is restored after the agent completes its task.

### Example: Cross-Desktop Workflow

```bash
# Run from terminal on Desktop 1, while Notion is on Desktop 2
python -m src.agent "switch to Notion, then extract the recipes database"
```

The agent will:
1. Store current application (e.g., Terminal)
2. Switch to desktop containing Notion
3. Navigate and extract content
4. Return to Terminal on Desktop 1

### Supported Applications

The tool works with any macOS application:
- `"Notion"` - Notion desktop app
- `"Safari"` - Safari browser
- `"Google Chrome"` - Chrome browser
- `"Finder"` - macOS Finder
- Any other running application

### Error Handling

If the application is not found:
```json
{
  "status": "error",
  "application": "Notion",
  "message": "Application 'Notion' not found or not running"
}
```

**Solutions**:
- Ensure the application is running
- Check the exact application name (case-sensitive)
- Verify the application has visible windows

### Limitations

- **Application Must Be Running**: The target application must be open
- **Requires Windows**: The application must have at least one window open
- **macOS Specific**: This feature only works on macOS with Mission Control
- **No Direct Desktop Numbers**: Cannot switch to "Desktop 3" directly; must specify an application

### Best Practices

1. **Check Application Name**: Use the exact name as shown in the menu bar
   ```python
   # Good
   agent.run("switch to Notion")
   
   # Bad (wrong name)
   agent.run("switch to notion app")
   ```

2. **Combine with Screenshots**: Take a screenshot after switching to verify
   ```python
   agent.run("switch to Notion, then take a screenshot to confirm")
   ```

3. **Let Auto-Return Work**: Don't manually switch back; the agent handles it
   ```python
   # Good - agent returns automatically
   agent.run("switch to Notion and extract content")
   
   # Unnecessary - agent already returns
   agent.run("switch to Notion, extract content, then switch back to Terminal")
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

### 2. Verify Every Action

The agent should take a screenshot after EVERY action to verify it worked:

```python
# Good - agent verifies each step
agent.run("click on the menu button, take a screenshot to verify it opened, then click on settings")

# Less reliable - no verification
agent.run("click on menu button, then click on settings")
```

**Important**: The computer use tools (click, type, etc.) only execute actions - they don't verify success. The agent must take screenshots to confirm actions worked.

### 3. Be Honest About Failures

The agent is now trained to report failures honestly:

```python
# Agent will say:
"I clicked at (300, 400) but the menu didn't open - trying different coordinates"

# Instead of falsely claiming:
"I successfully clicked the menu button"  # (without checking)
```

### 4. Be Specific with Coordinates

If you know exact coordinates, provide them:

```python
agent.run("click at coordinates (150, 300)")
```

### 5. Wait After Navigation

Allow time for pages to load:

```python
agent.run("click on database, wait 2 seconds, then extract")
```

### 6. Combine with Extraction Tools

Use Computer Use for navigation, AX tools for extraction:

```python
agent.run("navigate to the page, then use extract_page_content")
```

### 7. Use Verbose Mode for Debugging

See exactly what the agent is doing with timing information:

```bash
python -m src.agent --computer-use --verbose "your query"
```

You'll see timing for each operation:
```
⏳ Capturing screenshot...
⏱️  screenshot completed in 129ms
⏳ Moving mouse to (300, 400)...
⏱️  execute_action completed in 0.4ms
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

### "Application not found" when switching desktops

**Cause**: Application is not running or has no windows

**Solution**: 
- Ensure the application is running
- Verify the application has at least one window open
- Check the exact application name (case-sensitive)
- Try: `ps aux | grep -i "application name"` to verify it's running

### Agent clicks wrong coordinates

**Cause**: Resolution mismatch or Retina display scaling

**Solution**: 
- Use verbose mode to see coordinates
- Take screenshots to verify
- Adjust display_num parameter

### Computer Use not working

**Fallback**: The agent automatically falls back to standard tools if Computer Use fails to initialize.

## Performance Considerations

- **Screenshots**: Each screenshot takes ~130ms (with caching: <1ms)
- **Mouse Actions**: <1ms (highly optimized)
- **Typing**: ~30ms (optimized)
- **Overall**: 96.5% faster than original implementation

### Performance Tracking

When running with `--verbose`, you'll see timing information for all operations:

```
⏱️  screenshot completed in 129ms
⏱️  execute_action completed in 0.4ms
⏱️  switch_desktop completed in 850ms
```

Performance logs are automatically saved to `output/logs/performance_YYYYMMDD_HHMMSS.jsonl` for analysis.

### Analyzing Performance Logs

Performance logs are in JSON Lines format, with each line containing:

```json
{
  "timestamp": "2025-12-04T19:03:26.123456",
  "action_type": "screenshot",
  "duration_ms": 129.45,
  "success": true,
  "context": {"args": "..."}
}
```

You can analyze these logs to:
- Identify slow operations
- Track performance improvements over time
- Optimize your workflows
- Debug timing issues

## Security & Safety

- Computer Use has **full control** of your computer when enabled
- Use `--computer-use` flag only when needed
- The agent can only see what's on screen (no file system access via this tool)
- Consider using in a sandboxed environment for untrusted tasks

## Verification Best Practices

### Understanding Tool Behavior

**Critical**: Computer use tools execute actions but **do not verify success**. The agent must explicitly check results.

### Proper Verification Workflow

1. **Take screenshot** to see current state
2. **Execute action** (click, type, etc.)
3. **Take screenshot again** to verify the action worked
4. **Report honestly** what you observe

### Example: Clicking a Button

```
❌ BAD (no verification):
1. Click at (300, 400)
2. Report: "Successfully clicked the button"

✓ GOOD (with verification):
1. Take screenshot - see button at (300, 400)
2. Click at (300, 400)
3. Take screenshot - check if menu opened
4. Report: "Clicked at (300, 400) and menu opened" OR
   Report: "Clicked at (300, 400) but menu didn't open - retrying"
```

### Agent Training

The agent is now trained to:
- **Always verify** actions with screenshots
- **Report honestly** when actions fail
- **Never assume** success without visual confirmation
- **Try alternative approaches** when actions don't work

This makes the agent more reliable and easier to debug.

## Future Enhancements

Planned improvements:
- ~~Vision API integration for better element detection~~ ✅ **COMPLETED**
- ~~Cached screenshots to reduce API calls~~ ✅ **COMPLETED**
- ~~Performance tracking and logging~~ ✅ **COMPLETED**
- ~~Action verification training~~ ✅ **COMPLETED**
- Multi-monitor coordination
- Custom action macros
- Replay and debugging tools
- Aggregate performance analytics dashboard

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

