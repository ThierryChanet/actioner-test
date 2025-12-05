# Computer Use Implementation Summary

## Overview

The Notion agent uses **Anthropic's Claude Computer Use** for vision-based screen control, combined with **OpenAI GPT-4o** for LLM reasoning. **Computer Use is enabled by default** - no flags required!

## Architecture

```
┌─────────────────────────────────┐
│      NotionAgent                │
│                                 │
│  LLM: OpenAI (gpt-4o)          │
│  Computer Use: Anthropic Claude │
└────────────┬────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────────┐  ┌─────────────────┐
│ Anthropic   │  │ OpenAI LLM      │
│ Computer    │  │ (Agent Brain)   │
│ Use Client  │  │                 │
│             │  │ - Reasoning     │
│ - Vision    │  │ - Tool Selection│
│ - Clicks    │  │ - Response Gen  │
│ - Keyboard  │  └─────────────────┘
└─────────────┘
```

## Key Components

### 1. `src/agent/anthropic_computer_client.py`
- **Anthropic Claude integration** for Computer Use
- Vision analysis of screenshots
- Element detection with coordinate return
- Action execution via macOS APIs

### 2. `src/agent/computer_use_tools.py`
- LangChain tool wrappers for Computer Use actions
- 10 tools implementing computer control:
  - `ScreenshotTool`: Capture screen with Claude vision analysis
  - `GetScreenInfoTool`: Get display dimensions
  - `SwitchDesktopTool`: Switch to macOS desktop containing a specific application
  - `MouseMoveTool`: Move cursor
  - `LeftClickTool`: Left click
  - `RightClickTool`: Right click
  - `DoubleClickTool`: Double click
  - `TypeTextTool`: Type text
  - `PressKeyTool`: Press special keys
  - `GetCursorPositionTool`: Get cursor location

### 3. `src/agent/core.py`
- Initializes both OpenAI LLM and Anthropic Computer Use client
- Conditional tool loading based on computer_use flag
- System prompts optimized for Computer Use workflow

## Requirements

```bash
# Required for LLM (agent reasoning)
export OPENAI_API_KEY="sk-..."

# Required for Computer Use (vision + control)
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional for API extraction
export NOTION_TOKEN="secret_..."
```

### System Permissions
- **Accessibility**: Required (System Preferences > Privacy > Accessibility)
- **Screen Recording**: Required (System Preferences > Privacy > Screen Recording)

## Usage

### CLI (Computer Use enabled by default)
```bash
# Take screenshot and navigate
python -m src.agent "take a screenshot and click on recipes"

# Extract after navigation
python -m src.agent "navigate to roadmap and extract content"

# Disable Computer Use if needed
python -m src.agent --no-computer-use "extract content"
```

### Programmatic
```python
from src.agent import create_agent

# Computer Use enabled by default
agent = create_agent(verbose=True)
response = agent.run("navigate to roadmap and extract content")

# Or disable explicitly
agent = create_agent(computer_use=False)
```

## Tool Replacement Matrix

| Traditional Tool | Computer Use Replacement | Status |
|-----------------|--------------------------|--------|
| `navigate_to_page` | `take_screenshot` + `left_click` | Replaced |
| `list_available_pages` | `take_screenshot` (agent reads sidebar) | Replaced |
| `search_pages` | `left_click` + `type_text` + `press_key` | Replaced |
| `extract_page_content` | Kept (AX extraction superior) | **Kept** |
| `extract_database` | Kept (AX extraction superior) | **Kept** |
| `get_current_context` | Kept (state tracking) | **Kept** |
| `ask_user` | Kept (user interaction) | **Kept** |

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Screenshot capture | ~130ms | macOS Quartz APIs |
| Claude vision analysis | 3-5s | Depends on image complexity |
| Mouse click | <1ms | Optimized delays |
| Type text | ~30ms | AppleScript |
| Press key | ~20ms | AppleScript |

## Technical Details

### Screenshot Capture
- Uses `CGDisplayCreateImage` for full display capture
- Converts to NSImage for processing
- Encodes to base64 PNG for Claude analysis
- Handles Retina displays correctly

### Mouse Control
- `CGEventCreateMouseEvent` for move/click events
- `CGEventPost` to send events to system
- Supports left, right, double clicks
- Coordinate system: (0,0) at top-left

### Keyboard Control
- AppleScript via subprocess for reliability
- Supports text typing with proper escaping
- Special key mapping (Return, Tab, arrows, etc.)

### Vision Analysis
- Screenshots sent to Claude for analysis
- Claude returns element locations with coordinates
- Enables clicking by element text/description

## Security Considerations

1. **Full Control**: Computer Use provides complete control of the computer
2. **Opt-out Support**: Disable with `--no-computer-use`
3. **API Keys Required**: Requires both OpenAI and Anthropic keys
4. **Local Execution**: All actions execute locally
5. **Screen Visibility**: Agent can only see what's on screen

## Files

- `src/agent/anthropic_computer_client.py` - Anthropic Computer Use client
- `src/agent/computer_use_tools.py` - LangChain tool wrappers
- `src/agent/core.py` - Agent integration
- `docs/agent/COMPUTER_USE.md` - User documentation
- `docs/agent/ANTHROPIC_INTEGRATION.md` - Anthropic details

## Backward Compatibility

✅ **Fully Backward Compatible**
- Default behavior includes Computer Use
- Standard AX tools still work with `--no-computer-use`
- No breaking changes to existing scripts

## Summary

The Computer Use integration provides:

1. ✅ **Visual Navigation**: Claude can see and interact with screen
2. ✅ **General-Purpose Control**: Works with any application
3. ✅ **Hybrid Architecture**: OpenAI for reasoning, Anthropic for vision
4. ✅ **Optimized Performance**: Fast mouse/keyboard via macOS APIs
5. ✅ **Flexible Activation**: Enabled by default, opt-out available
6. ✅ **Well Documented**: Comprehensive docs and examples
