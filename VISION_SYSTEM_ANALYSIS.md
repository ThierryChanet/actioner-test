# Vision System Analysis & Improvement Proposal

## Executive Summary

The agent's vision and navigation system has **fundamental architectural issues** that prevent it from reliably interacting with UI elements. This document analyzes the problems and proposes solutions.

## Current Architecture Problems

### 1. **Disconnected Vision Systems**

**Problem**: The agent uses TWO separate, incompatible vision systems:

1. **GPT-4o Vision** (OpenAI) - For understanding what's on screen
   - Takes screenshots
   - Sends to GPT-4o
   - Gets text descriptions
   - **Does NOT provide clickable coordinates**

2. **macOS Vision API OCR** - For finding text to click
   - Takes screenshots
   - Uses macOS Vision framework for OCR
   - Extracts text with bounding boxes
   - Provides clickable coordinates
   - **Does NOT understand context**

**Result**:
- GPT-4o says "I can see Aheobakjin in the sidebar"
- macOS OCR can't find "Aheobakjin" (OCR misread, wrong region, etc.)
- Agent fails despite "seeing" the element

### 2. **Poor Performance**

**Measured Performance**:
- Screenshot analysis: **14.16 seconds** per call
- Tokens used: **1,706 tokens** (1,176 prompt + 530 completion)
- Far too slow for iterative UI interactions

**Impact**:
- Agent hits max iterations before completing tasks
- Long wait times for simple operations
- High API costs

### 3. **OCR Navigation Failures**

**Why OCR Fails to Find Visible Items**:

1. **Text Misreading**:
   - macOS Vision OCR may misread text (e.g., "Aheobakjin" → "Aheobakijn")
   - Fuzzy matching threshold (0.75) too strict to catch errors
   - Special characters (é, ô) cause issues

2. **Region Scanning**:
   - OCR scans entire Notion window
   - May focus on wrong regions
   - Doesn't prioritize sidebar vs content area

3. **Coordinate Conversion**:
   - Complex coordinate system conversions (Retina displays)
   - Window offsets, scale factors
   - Potential for off-by-one errors

4. **No Visual Context**:
   - OCR just finds text
   - Doesn't understand "sidebar" vs "content"
   - Can't distinguish "recipe name" from "random text"

### 4. **Agent Behavior Issues**

**Observed Problems**:

1. **Random Clicking**:
   - Agent clicks at coordinates without verification
   - No feedback loop to confirm success
   - Keeps trying same failed approach

2. **No State Tracking**:
   - Doesn't remember what it tried
   - Repeats failed actions
   - Hits max iterations

3. **Tab Management**:
   - Opens tabs without closing previous ones
   - Loses track of which tab is active
   - Extracts wrong content

## Comparison: OpenAI vs Anthropic Computer Use

### OpenAI GPT-4o Vision

**Pros**:
- ✓ Excellent image understanding
- ✓ Detailed descriptions
- ✓ Already integrated

**Cons**:
- ✗ **14+ seconds** per screenshot
- ✗ No built-in computer control
- ✗ Requires separate OCR for clicking
- ✗ Expensive (1,700+ tokens per screenshot)

### Anthropic Claude Computer Use

**Pros**:
- ✓ Purpose-built for computer control
- ✓ **Integrated vision + actions**
- ✓ Returns coordinates directly
- ✓ Better at UI understanding
- ✓ Potentially faster (needs testing)

**Cons**:
- ✗ Requires ANTHROPIC_API_KEY
- ✗ Different API structure
- ✗ Not yet tested in this codebase

### Key Difference

**OpenAI**: Vision model that describes screens
**Anthropic**: Computer use tool that *controls* screens

## Proposed Solutions

### Option 1: Switch to Anthropic Computer Use (Recommended)

**Implementation**:
1. Add Anthropic Computer Use as primary vision/control system
2. Use Claude's built-in coordinate detection
3. Eliminate separate OCR system
4. Keep OpenAI as fallback

**Benefits**:
- ✓ Unified vision + control
- ✓ Purpose-built for this use case
- ✓ Likely faster performance
- ✓ Better coordinate accuracy

**Effort**: Medium (2-3 days)

**Code Changes**:
```python
# New: src/agent/anthropic_computer_client.py
from anthropic import Anthropic

class AnthropicComputerClient:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)

    def take_action(self, action, **params):
        """Use Claude's computer use tool directly."""
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=[{
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": 1920,
                "display_height_px": 1080
            }],
            messages=[{
                "role": "user",
                "content": f"Click on '{params['text']}'"
            }]
        )
        # Claude returns tool use with coordinates
        return response
```

### Option 2: Improve Current OpenAI System

**Implementation**:
1. Add coordinate hints to GPT-4o prompts
2. Improve OCR fuzzy matching
3. Add verification screenshots
4. Optimize prompt to reduce tokens

**Benefits**:
- ✓ No API changes needed
- ✓ Works with current setup
- ✓ Incremental improvements

**Drawbacks**:
- ✗ Still fundamentally disconnected
- ✗ Still slow (14+ seconds)
- ✗ Won't fully solve the problem

**Effort**: Low (1 day)

**Code Changes**:
```python
# Improved prompt
prompt = (
    "Analyze this screenshot. For EACH clickable element, provide: "
    "1. Element name/text "
    "2. Element type (button/link/tab/etc) "
    "3. APPROXIMATE pixel coordinates (x, y) "
    "4. Location description (top-left/center/etc) "
    "Format as JSON for easy parsing."
)

# Lower fuzzy match threshold
fuzzy_threshold = 0.6  # Was 0.75

# Add retry with lower threshold
if not found:
    fuzzy_threshold = 0.5
    retry_search()
```

### Option 3: Hybrid Approach

**Implementation**:
1. Use GPT-4o for high-level understanding
2. Use Anthropic Computer Use for actual clicking
3. Fall back to current system if both unavailable

**Benefits**:
- ✓ Best of both worlds
- ✓ Flexibility
- ✓ Robust fallback

**Drawbacks**:
- ✗ Complex architecture
- ✗ Two API keys required
- ✗ Higher cost

**Effort**: High (3-5 days)

## Recommendations

### Immediate Actions (This Week)

1. **Test Anthropic Computer Use** ✅ (Script ready)
   - Get ANTHROPIC_API_KEY
   - Run comparison test
   - Measure performance vs OpenAI

2. **Improve OCR Fuzzy Matching** (Quick win)
   - Lower threshold: 0.75 → 0.6
   - Add retry with 0.5 threshold
   - Better Unicode handling for é, ô, etc.

3. **Add Action Verification** (Quick win)
   - Take screenshot after each action
   - Verify expected state change
   - Retry if verification fails

### Medium-term (Next 2 Weeks)

4. **Implement Anthropic Computer Use**
   - Create `AnthropicComputerClient`
   - Integrate with existing tools
   - Test on real Notion workflows

5. **Optimize OpenAI Prompts**
   - Request JSON output with coordinates
   - Reduce max_tokens: 2000 → 500
   - Add caching for repeated screenshots

### Long-term (Next Month)

6. **Add State Management**
   - Track action history
   - Detect infinite loops
   - Smart retry strategies

7. **Performance Monitoring**
   - Log latency for each operation
   - Track success/failure rates
   - Identify bottlenecks

## Success Metrics

**Current**:
- Success rate: ~30% (agent completes task)
- Average time: 50+ seconds (hits max iterations)
- Screenshot latency: 14+ seconds

**Target**:
- Success rate: >80%
- Average time: <20 seconds
- Screenshot latency: <3 seconds

## Next Steps

1. ☐ Get user to set ANTHROPIC_API_KEY
2. ☐ Run full comparison test
3. ☐ Decide on approach based on results
4. ☐ Implement chosen solution
5. ☐ Test with real recipes workflow
6. ☐ Measure improvements

## Test Plan

### Test Case: Open Two Recipes

**Current Behavior**:
1. Agent tries to open "First Recipe" (doesn't exist)
2. OCR can't find it
3. Clicks random coordinates
4. Hits max iterations
5. **FAILS**

**Expected with Fix**:
1. Agent takes screenshot
2. Vision identifies actual recipe names
3. Clicks on first recipe (coordinates provided)
4. Verifies page opened
5. Extracts ingredients
6. Closes tab
7. Clicks second recipe
8. Extracts ingredients
9. Returns both ingredient lists
10. **SUCCESS**

---

**Date**: 2025-12-05
**Author**: Claude Code Analysis
**Status**: Awaiting decision on implementation approach
