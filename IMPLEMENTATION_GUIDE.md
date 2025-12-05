# Implementation Guide for Agent Improvements

Quick reference for implementing the proposed enhancements from `AGENT_IMPROVEMENTS_PROPOSAL.md`.

## Quick Start

Run the examples to understand the improvements:

```bash
# See how action history prevents loops
python examples/enhanced_state_example.py

# See how hover caching speeds up navigation
python examples/hover_caching_example.py
```

## Files to Modify

### 1. Enhanced State Management (Priority: HIGH)

**File:** `src/agent/state.py`

**What to add:**
- `ActionRecord` dataclass
- `action_history` field to `AgentState`
- Methods: `record_action()`, `should_retry_action()`, `has_tried_recently()`

**Impact:** Prevents infinite loops (the main issue from testing)

**Effort:** ~2 hours

**Example:**
```python
# Before taking any action in agent tools:
if not state.should_retry_action(action_type, parameters):
    return "Max retries reached, trying different strategy"

if state.has_tried_recently(action_type, parameters):
    return "Just tried this, skipping to avoid loop"

# After action completes:
state.record_action(action_type, parameters, result, error)
```

---

### 2. Hover Caching (Priority: HIGH)

**File:** `src/notion/ocr_navigator.py`

**What to add:**
- `hover_cache` dictionary
- `find_and_click_text_cached()` method
- Cache hit/miss logic

**Impact:** 15x faster for cached items (0.15s vs 2.2s)

**Effort:** ~3 hours

**Usage:**
```python
# First time: Full OCR (2.2s)
navigator.find_and_click_text_cached("Velouté Potimarron")

# Second time: Cache hit (0.15s)
navigator.find_and_click_text_cached("Velouté Potimarron")
```

---

### 3. Content Filtering (Priority: MEDIUM)

**File:** `src/notion/content_filter.py` (new file)

**What to create:**
- `ContentFilter` class
- `is_likely_ui_element()` method
- `filter_content_blocks()` method

**Impact:** Removes 90% of UI noise from extractions

**Effort:** ~2 hours

**Integration:**
```python
# In extract_page_content tool:
blocks = orchestrator.extract_page(page_name)
filtered = ContentFilter.filter_content_blocks(blocks)
# Now filtered contains only actual content, not UI elements
```

---

### 4. Screen Context Tracking (Priority: MEDIUM)

**File:** `src/agent/state.py`

**What to add:**
- `ScreenContext` dataclass
- `UIElementState` dataclass
- `screen_context` field to `AgentState`
- `update_screen_context()` method

**Impact:** Agent knows what's on screen and detects changes

**Effort:** ~4 hours

---

### 5. Strategy Manager (Priority: LOW)

**File:** `src/agent/strategy.py` (new file)

**What to create:**
- `Strategy` class
- `StrategyManager` class
- Pre-defined strategies for common goals

**Impact:** Agent tries multiple approaches instead of giving up

**Effort:** ~5 hours

---

## Implementation Order

### Phase 1: Critical Fixes (Week 1)
1. ✅ **Enhanced State** - Prevents loops
2. ✅ **Hover Caching** - Major performance boost
3. ✅ **Content Filtering** - Better extraction quality

### Phase 2: Intelligence (Week 2)
4. **Screen Context** - Better awareness
5. **Strategy Manager** - Smarter retry logic

---

## Testing Each Enhancement

### Test Enhanced State
```bash
# Run the demo
python examples/enhanced_state_example.py

# Then test with real agent
python -m src.agent "click on Velouté Potimarron 5 times"
# Should stop after 3 attempts instead of max iterations
```

### Test Hover Caching
```bash
# Run the demo
python examples/hover_caching_example.py

# Then test with real agent
python -m src.agent "open Velouté Potimarron, then Poulet rôti, then Velouté Potimarron again"
# Second access to Velouté should be much faster
```

### Test Content Filtering
```bash
# Before: Check extraction quality
python -m src.agent "extract current page"
# Count UI elements in output

# After implementing filter:
python -m src.agent "extract current page"
# Should see fewer UI elements, more content
```

---

## Code Snippets for Quick Implementation

### 1. Add Action History Check to Tools

In any agent tool (e.g., `src/agent/computer_use_tools.py`):

```python
# At the start of _run() method:
def _run(self, x: int, y: int) -> str:
    action_type = "click"
    parameters = {"x": x, "y": y}

    # CHECK 1: Max retries
    if not self.state.should_retry_action(action_type, parameters):
        return json.dumps({
            "status": "skipped",
            "reason": "Max retries reached for this action",
            "suggestion": "Try a different approach"
        })

    # CHECK 2: Recent duplicate
    if self.state.has_tried_recently(action_type, parameters, within_last_n=3):
        return json.dumps({
            "status": "warning",
            "reason": "Just tried this action recently",
            "proceeding": True
        })

    # Do the actual action...
    try:
        result = self._do_click(x, y)

        # Record success
        self.state.record_action(action_type, parameters, "success")
        return json.dumps({"status": "success"})

    except Exception as e:
        # Record failure
        self.state.record_action(action_type, parameters, "failed", str(e))
        return json.dumps({"status": "failed", "error": str(e)})
```

### 2. Add Hover Caching to Navigator

In `src/notion/ocr_navigator.py`:

```python
class OCRNavigator:
    def __init__(self, detector):
        self.detector = detector
        self.ocr = VisionOCR()
        self.hover_cache = {}  # NEW

    def find_and_click_text_cached(self, text: str, use_cache: bool = True) -> bool:
        """Find and click with caching."""

        # Try cache first
        if use_cache and text in self.hover_cache:
            cached = self.hover_cache[text]
            if time.time() - cached["last_successful"] < 300:  # 5 min
                print(f"💾 Using cached location for '{text}'")
                x, y = cached["open_button_coords"]
                if self.click_at_position(x, y):
                    cached["last_successful"] = time.time()
                    return True

        # Cache miss - do full OCR
        success = self.find_and_click_text(text)  # Original method

        # If successful, extract coordinates and cache them
        # (This requires capturing the coords during find_and_click_text)

        return success
```

### 3. Add Content Filter

Create `src/notion/content_filter.py`:

```python
class ContentFilter:
    UI_KEYWORDS = {"tab bar", "open sidebar", "back", "forward", "search"}

    @classmethod
    def is_likely_ui_element(cls, block: dict) -> bool:
        content = block.get("content", "").lower()
        return any(keyword in content for keyword in cls.UI_KEYWORDS)

    @classmethod
    def filter_content_blocks(cls, blocks: list) -> list:
        return [b for b in blocks if not cls.is_likely_ui_element(b)]
```

Then in extraction tools:

```python
from ..notion.content_filter import ContentFilter

# After extraction:
blocks = orchestrator.extract_page(page_name)
content_only = ContentFilter.filter_content_blocks(blocks)
return {"blocks": content_only, "filtered_out": len(blocks) - len(content_only)}
```

---

## Validation Checklist

After implementing each enhancement:

- [ ] Agent stops after 3 identical failed actions (not max iterations)
- [ ] Hover cache hit rate > 80% for repeated items
- [ ] Content extraction has < 10% UI elements
- [ ] Action history visible in debug logs
- [ ] Different strategies attempted when one fails
- [ ] No infinite loops in any scenario

---

## Performance Benchmarks

### Before Improvements
- Database navigation: 2.2s per item
- Repeated navigation: 2.2s per item (no learning)
- Max iterations hit: Common
- UI elements in extraction: 60%

### After Improvements (Expected)
- Database navigation: 2.2s first time, 0.15s cached
- Repeated navigation: 15x faster for cached items
- Max iterations hit: Rare (agent stops after 3 retries)
- UI elements in extraction: < 10%

---

## Debugging Tips

### Enable Action History Logging

```python
# In src/agent/state.py
def record_action(self, ...):
    record = ActionRecord(...)
    self.action_history.append(record)

    # ADD LOGGING
    print(f"📝 Action recorded: {action_type} → {result}")
    if result == "failed":
        retry_count = self.retry_counts[self._action_key(action_type, parameters)]
        print(f"   Retry count: {retry_count}/{self.max_retries_per_action}")
```

### Check Cache Statistics

```python
# Add to OCRNavigator
def get_cache_stats(self):
    return {
        "cached_items": len(self.hover_cache),
        "items": list(self.hover_cache.keys()),
        "total_hits": sum(c.get("success_count", 0) for c in self.hover_cache.values())
    }

# Use in agent
stats = navigator.get_cache_stats()
print(f"Cache stats: {stats}")
```

---

## Questions?

See `AGENT_IMPROVEMENTS_PROPOSAL.md` for detailed explanations and full code.

Run `examples/enhanced_state_example.py` and `examples/hover_caching_example.py` to see the improvements in action.
