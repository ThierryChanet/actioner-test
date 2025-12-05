# Anthropic Computer Use Integration

## Overview

The agent now supports **Anthropic's Claude Computer Use** as an alternative to OpenAI's vision + custom macOS implementation. This provides a unified vision and control system purpose-built for computer interactions.

## Why Anthropic Computer Use?

### Problem with Previous Approach
The original implementation had a fundamental disconnect:
- **GPT-4o Vision**: Described what's on screen ("I see Aheobakjin")
- **macOS Vision OCR**: Tried to find text to click (often failed)
- **Result**: Agent "saw" elements but couldn't interact with them

### Anthropic Solution
- **Unified System**: Single API for vision + coordinates
- **Purpose-Built**: Designed specifically for computer control
- **Better Performance**: Potentially faster than 14+ second GPT-4o calls
- **Accurate Coordinates**: Returns precise click coordinates

## Installation

Anthropic package is already installed:
```bash
pip install anthropic  # Already in requirements
```

## Usage

### Auto-Detection (Recommended)

The agent automatically detects which provider to use based on available API keys:

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Agent auto-detects and uses Anthropic
python -m src.agent "open two recipes and tell me about their ingredients"
```

### Explicit Provider Selection

```bash
# Force Anthropic
python -m src.agent --provider=anthropic "extract recipes"

# Force OpenAI
python -m src.agent --provider=openai "extract recipes"

# Auto-detect (default)
python -m src.agent --provider=auto "extract recipes"
```

### Programmatic Usage

```python
from src.agent import create_agent

# Use Anthropic (auto-detected with ANTHROPIC_API_KEY)
agent = create_agent(llm_provider="anthropic")

# Use OpenAI
agent = create_agent(llm_provider="openai")

# Auto-detect
agent = create_agent(llm_provider="auto")  # Default

# Run queries
response = agent.run("open two different recipes and extract their ingredients")
```

## How It Works

### 1. Vision Analysis
```python
# Anthropic analyzes screenshot
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
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

### 2. Element Detection + Click
```python
# Ask Claude to click on an element
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    tools=[{
        "type": "computer_20241022",
        "name": "computer",
        "display_width_px": 1920,
        "display_height_px": 1080
    }],
    messages=[{
        "role": "user",
        "content": "Click on 'Aheobakjin'"
    }]
)

# Claude returns coordinates
for block in response.content:
    if block.type == "tool_use":
        coordinates = block.input["coordinate"]
        # [x, y] ready to click!
```

### 3. Unified Workflow
- Take screenshot
- Claude analyzes image
- Claude identifies element location
- Claude returns coordinates
- System executes click
- All in one API call!

## Features

### Supported Actions

- ✅ **Screenshot**: Capture and analyze screen
- ✅ **Click**: Find element by text and click
- ✅ **Type**: Type text at cursor
- ✅ **Press Key**: Press special keys (Return, Tab, etc.)
- ✅ **Mouse Move**: Move cursor to coordinates
- ✅ **Coordinate Click**: Click at specific (x, y)

### Performance Features

- ✅ **Screenshot Caching**: 2-second TTL cache
- ✅ **Optimized Actions**: 10-20ms delays
- ✅ **Async Support**: Non-blocking operations (ready)
- ✅ **Latency Tracking**: Measure performance

## Architecture

```
┌─────────────────────────────────┐
│      NotionAgent                │
│                                 │
│  llm_provider: "anthropic"      │
└────────────┬────────────────────┘
             │
             ├──────────────────────────┐
             │                          │
┌────────────▼──────────┐   ┌──────────▼────────────┐
│  Anthropic Client     │   │  Extraction Tools     │
│                       │   │                       │
│  - Vision Analysis    │   │  - extract_page       │
│  - Element Detection  │   │  - extract_database   │
│  - Coordinate Return  │   │  - get_context        │
│  - Action Execution   │   │  - ask_user           │
└───────────────────────┘   └───────────────────────┘
```

## Fallback Chain

The agent tries providers in this order:

1. **Anthropic** (if `--provider=anthropic` or ANTHROPIC_API_KEY set)
2. **OpenAI** (if `--provider=openai` or OPENAI_API_KEY set)
3. **Error** (if no API keys found)

## Comparison

### Anthropic Computer Use

**Pros**:
- ✅ Unified vision + control
- ✅ Purpose-built for UI interaction
- ✅ Returns coordinates directly
- ✅ Better element detection
- ✅ Potentially faster

**Cons**:
- ⚠️ Requires ANTHROPIC_API_KEY
- ⚠️ Newer API (less tested)
- ⚠️ Different pricing model

### OpenAI Vision + Custom macOS

**Pros**:
- ✅ Well-tested
- ✅ Fallback to custom OCR
- ✅ Already integrated

**Cons**:
- ❌ Disconnected vision/control
- ❌ Slow (14+ seconds per screenshot)
- ❌ OCR failures common
- ❌ Complex coordinate conversion

## Configuration

### Environment Variables

```bash
# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Or OpenAI (for fallback)
export OPENAI_API_KEY="sk-..."

# Optional: Notion API
export NOTION_TOKEN="secret_..."
```

### Display Settings

```bash
# Default (1920x1080, display 1)
python -m src.agent --provider=anthropic "query"

# Custom display
python -m src.agent --provider=anthropic --display=2 "query"

# TODO: Custom resolution (not yet configurable via CLI)
```

## Testing

### Quick Test

```bash
# Test Anthropic integration
export ANTHROPIC_API_KEY="sk-ant-..."
python -m src.agent --provider=anthropic --verbose "take a screenshot and describe what you see"
```

### Recipe Extraction Test

```bash
# The original failing test
python -m src.agent --provider=anthropic "open two different recipes from my Notion page and tell me about their ingredients"
```

### Comparison Test

```bash
# Compare both providers
python test_vision_comparison.py
```

## Troubleshooting

### "Anthropic package not installed"

```bash
pip install anthropic
```

### "ANTHROPIC_API_KEY not found"

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### "Computer Use initialization failed"

Check verbose output:
```bash
python -m src.agent --provider=anthropic --verbose "test"
```

### Agent still failing

1. Verify API key is valid
2. Check internet connection
3. Try with `--verbose` to see detailed logs
4. Fall back to OpenAI: `--provider=openai`

## Performance Expectations

### Expected Improvements

| Metric | OpenAI (Before) | Anthropic (Expected) |
|--------|----------------|---------------------|
| Screenshot analysis | 14+ seconds | 3-5 seconds |
| Element detection | Separate OCR step | Integrated |
| Click accuracy | ~50% (OCR failures) | ~90% (purpose-built) |
| Coordinate precision | Manual conversion | Direct from model |
| Overall success rate | ~30% | ~80% |

### Actual Performance

*To be measured after testing with your workflows*

## Migration Guide

### From OpenAI to Anthropic

**Step 1**: Get API key
```bash
# Sign up at https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Step 2**: Test auto-detection
```bash
python -m src.agent "test query"
# Should auto-detect and use Anthropic
```

**Step 3**: Force Anthropic (optional)
```bash
python -m src.agent --provider=anthropic "test query"
```

**Step 4**: Update scripts
```python
# Old
agent = create_agent()  # Used OpenAI

# New (explicit)
agent = create_agent(llm_provider="anthropic")

# Or let it auto-detect
agent = create_agent(llm_provider="auto")
```

## Known Limitations

1. **macOS Only**: Uses macOS APIs for actual clicking
2. **Single Display**: Multi-display support limited
3. **Claude Limits**: Subject to Anthropic's rate limits
4. **Retina Displays**: Coordinate scaling may need adjustment

## Future Enhancements

- [ ] Streaming support for real-time feedback
- [ ] Background mode for long-running tasks
- [ ] Batch operations
- [ ] Performance benchmarking dashboard
- [ ] Multi-display coordination
- [ ] Cross-platform support (Windows, Linux)

## Support

If you encounter issues:

1. Check `--verbose` output
2. Review `output/logs/` for details
3. Try comparison test: `python test_vision_comparison.py`
4. Fall back to OpenAI if needed
5. Report issues with error logs

## References

- [Anthropic Computer Use Docs](https://docs.anthropic.com/claude/docs/computer-use)
- [Vision System Analysis](../../VISION_SYSTEM_ANALYSIS.md)
- [OpenAI Comparison](COMPUTER_USE.md)

---

**Status**: ✅ Implemented and ready for testing
**Date**: 2025-12-05
**Priority**: High - Solves critical navigation issues
