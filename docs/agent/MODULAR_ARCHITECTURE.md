# Modular Tool Architecture

This document describes the modular architecture for app-specific tools in the agent system.

## Design Principles

1. **Separation of Concerns**: General-purpose tools are separate from app-specific tools
2. **Conditional Loading**: App-specific tools only load when needed and supported
3. **Provider Independence**: App-specific tools can work with any vision-capable provider
4. **Extensibility**: Easy to add support for new applications

## Architecture Overview

```
src/agent/
├── computer_use_tools.py      # General-purpose tools (ANY app)
│   ├── ScreenshotTool
│   ├── ClickElementTool       # Vision-based element clicking
│   ├── MouseMoveTool
│   ├── LeftClickTool
│   └── ... (10 general tools)
│
├── notion_tools.py             # Notion-specific tools (Notion ONLY)
│   └── NotionOpenPageTool     # Handles Notion's OPEN button workflow
│
├── [future]_tools.py           # Add more app-specific modules as needed
│   └── AppSpecificTool
│
└── core.py                     # Conditionally loads tools based on config
```

## Tool Types

### General-Purpose Tools (computer_use_tools.py)

These tools work with ANY application and have no app-specific knowledge:

- **ScreenshotTool**: Capture and analyze any screen
- **ClickElementTool**: Click UI elements by text (works in most UIs)
- **MouseMoveTool**: Move mouse to coordinates
- **LeftClickTool**: Click at coordinates
- **TypeTextTool**: Type text into focused field
- **PressKeyTool**: Press keyboard keys
- etc.

**When to use**: For general UI automation that doesn't require app-specific knowledge.

### App-Specific Tools (e.g., notion_tools.py)

These tools implement app-specific workflows that general tools can't handle:

- **NotionOpenPageTool**: Opens pages in Notion databases
  - Understands Notion's hover → OPEN button → sidebar workflow
  - Handles database row selection patterns
  - Expands sidebar to full page

**When to use**: When an app has unique UI patterns that need special handling.

## How It Works

### 1. Conditional Loading

Tools are loaded based on configuration and provider capabilities:

```python
# In core.py
def __init__(self, ..., enable_notion_tools: bool = True):
    # Load general tools (always)
    computer_tools = get_computer_use_tools(self.anthropic_client, self.state)

    # Load Notion tools (only if enabled + vision available)
    notion_tools = []
    if enable_notion_tools and hasattr(client, '_click_element'):
        notion_tools = get_notion_specific_tools(client, self.state)

    # Combine all tools
    self.tools = computer_tools + notion_tools + extraction_tools
```

### 2. Agent Discovery

The agent automatically discovers and uses available tools:

```python
# Agent prompt includes tool descriptions
# User: "use notion_open_page to open 'Recipe X'"
# Agent sees NotionOpenPageTool in available tools
# Agent invokes: notion_open_page(page_name="Recipe X")
```

### 3. Graceful Fallback

If an app-specific tool isn't available, general tools still work:

```python
# With Notion tools:
agent: "use notion_open_page to open 'X'"  # Notion-specific workflow

# Without Notion tools (disabled or no vision):
agent: "use click_element to click 'X'"     # General clicking
```

## Adding Support for New Apps

To add support for a new application:

### 1. Create App-Specific Tools Module

```python
# src/agent/slack_tools.py
"""Slack-specific LangChain tools."""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class SlackSendMessageInput(BaseModel):
    channel: str = Field(description="Channel name")
    message: str = Field(description="Message text")

class SlackSendMessageTool(BaseTool):
    """Send a message in a Slack channel.

    This handles Slack's specific UI patterns for composing messages.
    """
    name: str = "slack_send_message"
    description: str = "Send a message to a Slack channel..."

    def _run(self, channel: str, message: str) -> str:
        # Implement Slack-specific workflow:
        # 1. Click channel
        # 2. Click message field
        # 3. Type message
        # 4. Press Enter
        pass

def get_slack_tools(client, state) -> list:
    """Get Slack-specific tools."""
    if not hasattr(client, '_click_element'):
        return []

    return [
        SlackSendMessageTool(client=client, state=state),
    ]
```

### 2. Import in Core

```python
# src/agent/core.py
from .slack_tools import get_slack_tools
```

### 3. Add Conditional Loading

```python
# In __init__ method
slack_tools = []
if enable_slack_tools and hasattr(client, '_click_element'):
    slack_tools = get_slack_tools(self.anthropic_client, self.state)

self.tools = computer_tools + notion_tools + slack_tools + extraction_tools
```

### 4. Add Configuration Parameter

```python
def __init__(
    self,
    ...,
    enable_notion_tools: bool = True,
    enable_slack_tools: bool = False,  # New parameter
):
```

## Usage Examples

### Using General Tools Only

```bash
# Disable app-specific tools
python -m src.agent --no-notion-tools "click on the button labeled 'Submit'"
```

Agent uses general `click_element` tool.

### Using Notion-Specific Tools

```bash
# Default: Notion tools enabled
python -m src.agent "open the Notion page 'Project Alpha' and extract content"
```

Agent uses `notion_open_page` for better Notion navigation.

### Mixed Usage

```python
# Agent automatically chooses the right tool:
user: "open 'Recipe X' in Notion"
agent: uses notion_open_page  # Notion-specific

user: "click the refresh button"
agent: uses click_element       # General

user: "type 'hello world'"
agent: uses type_text           # General
```

## Benefits

### 1. Maintainability
- App-specific logic is isolated in separate modules
- Easy to update one app without affecting others
- Clear responsibility boundaries

### 2. Performance
- Only load tools needed for the task
- No overhead from unused app-specific logic

### 3. Flexibility
- Users can disable app-specific tools
- General tools always available as fallback
- Easy to add new app support

### 4. Testing
- Test general tools independently
- Test app-specific tools in isolation
- Mock dependencies easily

## Provider Requirements

### For General Tools
- Basic vision: Screenshot analysis
- Element detection: Find UI elements by text
- Action execution: Click, type, keyboard

### For App-Specific Tools
All general requirements PLUS:
- Multi-step workflows: Handle complex UI patterns
- Context awareness: Understand app state
- Vision-based navigation: Find app-specific UI elements

## Future Enhancements

### 1. Auto-Detection
Automatically detect which app is active and load relevant tools:

```python
# Detect Notion is active
if current_app == "Notion":
    enable_notion_tools = True
```

### 2. Tool Composition
Combine general and app-specific tools:

```python
class NotionAdvancedTool(BaseTool):
    def _run(self):
        # Use general screenshot tool
        self.screenshot_tool.run()

        # Use Notion-specific logic
        self.find_notion_database()
```

### 3. Plugin System
Load app tools dynamically from plugins:

```python
# Load plugins from directory
for plugin in load_plugins("src/agent/plugins/"):
    app_tools += plugin.get_tools(client, state)
```

## Summary

The modular architecture allows:
- ✅ General tools work everywhere
- ✅ App-specific tools handle edge cases
- ✅ Easy to add new app support
- ✅ Conditional loading based on config
- ✅ No interference between modules
- ✅ Clear separation of concerns

This design makes the agent system extensible and maintainable while keeping general functionality always available.
