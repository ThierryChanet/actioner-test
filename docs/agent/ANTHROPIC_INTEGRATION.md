# Anthropic Computer Use Integration

## Overview

The agent uses **Anthropic's Claude Computer Use** for all screen control and vision capabilities. This provides a unified vision and control system purpose-built for computer interactions.

## Architecture

```
┌─────────────────────────────────┐
│      NotionAgent                │
│                                 │
│  LLM: OpenAI (gpt-4o)          │
│  Computer Use: Anthropic Claude │
└────────────┬────────────────────┘
             │
             ├──────────────────────────┐
             │                          │
┌────────────▼──────────┐   ┌──────────▼────────────┐
│  Anthropic Client     │   │  OpenAI LLM           │
│                       │   │                       │
│  - Vision Analysis    │   │  - Agent Reasoning    │
│  - Element Detection  │   │  - Tool Selection     │
│  - Coordinate Return  │   │  - Response Gen       │
│  - Action Execution   │   │                       │
└───────────────────────┘   └───────────────────────┘
             │
┌────────────▼──────────────────────────────────────┐
│  Extraction Tools (via macOS Accessibility)       │
│                                                   │
│  - extract_page_content                           │
│  - extract_database                               │
│  - get_current_context                            │
│  - ask_user                                       │
└───────────────────────────────────────────────────┘
```

## Why Anthropic for Computer Use?

### Benefits

- **Unified System**: Single API for vision + coordinates
- **Purpose-Built**: Designed specifically for computer control
- **Accurate Coordinates**: Returns precise click coordinates
- **Better Element Detection**: Understands UI context

## Installation

```bash
# Anthropic package is in requirements.txt
pip install anthropic
```

## Usage

### Environment Setup

```bash
# Required for Computer Use (vision + control)
export ANTHROPIC_API_KEY="sk-ant-..."

# Required for LLM (agent reasoning)
export OPENAI_API_KEY="sk-..."

# Optional: Notion API for faster database extraction
export NOTION_TOKEN="secret_..."
```

### Command Line

```bash
# Computer Use is enabled by default
python -m src.agent "open two recipes and tell me about their ingredients"

# Verbose mode to see all actions
python -m src.agent --verbose "extract recipes"

# Disable Computer Use if needed
python -m src.agent --no-computer-use "extract recipes"
```

### Programmatic Usage

```python
from src.agent import create_agent

# Create agent (Computer Use enabled by default)
agent = create_agent(
    computer_use=True,  # Default
    verbose=True
)

# Run queries
response = agent.run("open two different recipes and extract their ingredients")
```

## How It Works

### 1. Vision Analysis

Claude analyzes screenshots to understand screen content:

```python
# Anthropic analyzes screenshot
response = client.messages.create(
    model="claude-3-haiku-20240307",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {"type": "base64", "data": screenshot_b64}
            },
            {
                "type": "text",
                "text": "Analyze this screenshot..."
            }
        ]
    }]
)
```

### 2. Element Detection

Claude finds UI elements and returns coordinates:

```python
# Ask Claude to find an element
result = client.execute_action(
    action="left_click",
    text="Recipes"  # Find and click this element
)
# Claude returns: {"coordinate": [120, 450], "success": true}
```

### 3. Action Execution

macOS APIs execute the actual clicks and keyboard input:

```python
# Click is executed via macOS Quartz
import Quartz
down_event = Quartz.CGEventCreateMouseEvent(
    None, Quartz.kCGEventLeftMouseDown, click_point, Quartz.kCGMouseButtonLeft
)
Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
```

## Features

### Supported Actions

- ✅ **Screenshot**: Capture and analyze screen
- ✅ **Click**: Find element by text and click
- ✅ **Type**: Type text at cursor
- ✅ **Press Key**: Press special keys (Return, Tab, etc.)
- ✅ **Mouse Move**: Move cursor to coordinates
- ✅ **Coordinate Click**: Click at specific (x, y)
- ✅ **Desktop Switch**: Switch to app on different desktop

### Performance Features

- ✅ **Screenshot Caching**: 2-second TTL cache
- ✅ **Optimized Actions**: 10-20ms delays
- ✅ **Latency Tracking**: Measure performance

## Configuration

### Display Settings

```bash
# Default (1920x1080, display 1)
python -m src.agent "query"

# Custom display
python -m src.agent --display=2 "query"
```

### In Code

```python
agent = create_agent(
    computer_use=True,
    display_num=2,  # Use second display
    verbose=True
)
```

## Troubleshooting

### "Computer Use initialization failed"

```bash
# Check Anthropic key
echo $ANTHROPIC_API_KEY

# Set if missing
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "OPENAI_API_KEY required"

```bash
# LLM requires OpenAI
export OPENAI_API_KEY="sk-..."
```

### "Anthropic package not installed"

```bash
pip install anthropic
```

### Element detection fails

1. Use `--verbose` to see Claude's analysis
2. Take a screenshot first to understand screen state
3. Be specific about element text/location

## Performance Expectations

| Metric | Expected |
|--------|----------|
| Screenshot capture | ~130ms |
| Claude vision analysis | 3-5 seconds |
| Click execution | <1ms |
| Element detection accuracy | ~90% |

## Known Limitations

1. **macOS Only**: Uses macOS APIs for actual clicking
2. **Single Display**: Multi-display support limited
3. **Claude Limits**: Subject to Anthropic's rate limits
4. **Retina Displays**: Coordinate scaling may need adjustment

## References

- [Anthropic Computer Use Docs](https://docs.anthropic.com/claude/docs/computer-use)
- [Computer Use Guide](COMPUTER_USE.md)

---

**Status**: ✅ Primary Computer Use implementation
**Date**: 2025-12-05
