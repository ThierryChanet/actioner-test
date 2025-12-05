# Agent Improvements Proposal

Based on testing with Claude Code on December 5, 2025, this document proposes improvements to reinforce trial-and-error capabilities, state management, and hover interaction handling.

## Testing Summary

### What Worked ✅
- OCR-based navigation with fuzzy matching successfully located UI elements
- Hover → detect → click workflow for the OPEN button worked perfectly
- Computer vision analysis correctly identified screen content
- Side panel expansion attempted automatically after opening pages

### Issues Encountered ❌
1. **Max iterations without progress**: Agent hit iteration limit while repeatedly trying similar actions
2. **State blindness**: Agent didn't track what it already tried or why actions failed
3. **UI vs Content confusion**: Extraction captured UI elements instead of actual page content
4. **No learning from failures**: Same failed approach repeated without variation
5. **Context switching issues**: Agent sometimes analyzed terminal instead of Notion window

---

## 1. Agent Behavior Improvements

### Issue: Iteration Limits Without Progress
The agent gets stuck in loops, repeating similar actions until max iterations.

### Proposed Solution: Action History with Deduplication

**Implementation in `src/agent/state.py`:**

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

@dataclass
class ActionRecord:
    """Record of a single action attempt."""
    timestamp: datetime
    action_type: str  # "click", "hover", "extract", "screenshot", etc.
    parameters: Dict[str, Any]  # e.g., {"x": 100, "y": 250, "target": "recipe"}
    result: str  # "success", "failed", "partial"
    error_message: Optional[str] = None
    state_snapshot: Optional[Dict[str, Any]] = None

@dataclass
class AgentState:
    """Enhanced state management with action history."""

    # Existing fields...
    current_page: Optional[str] = None
    last_extraction: Optional[Dict[str, Any]] = None
    recent_pages: List[str] = field(default_factory=list)
    extraction_count: int = 0

    # NEW: Action history
    action_history: List[ActionRecord] = field(default_factory=list)
    max_history_size: int = 50

    # NEW: Hover state tracking
    hover_sensitive_elements: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Format: {"recipe_name": {"x": 100, "y": 200, "open_button_x": 366, "open_button_y": 400}}

    # NEW: Retry tracking
    retry_counts: Dict[str, int] = field(default_factory=dict)
    max_retries_per_action: int = 3

    def record_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        result: str,
        error_message: Optional[str] = None
    ) -> ActionRecord:
        """Record an action attempt."""
        record = ActionRecord(
            timestamp=datetime.now(),
            action_type=action_type,
            parameters=parameters,
            result=result,
            error_message=error_message,
            state_snapshot={
                "current_page": self.current_page,
                "extraction_count": self.extraction_count
            }
        )

        self.action_history.append(record)

        # Trim history if too long
        if len(self.action_history) > self.max_history_size:
            self.action_history = self.action_history[-self.max_history_size:]

        # Update retry counts
        action_key = self._action_key(action_type, parameters)
        if result == "failed":
            self.retry_counts[action_key] = self.retry_counts.get(action_key, 0) + 1
        elif result == "success":
            self.retry_counts[action_key] = 0

        return record

    def _action_key(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Generate a unique key for an action."""
        # Create a stable hash of action type + sorted parameters
        param_str = str(sorted(parameters.items()))
        key_str = f"{action_type}:{param_str}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def should_retry_action(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        """Check if an action should be retried or if max retries reached."""
        action_key = self._action_key(action_type, parameters)
        retry_count = self.retry_counts.get(action_key, 0)
        return retry_count < self.max_retries_per_action

    def has_tried_recently(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        within_last_n: int = 5
    ) -> bool:
        """Check if an action was tried in the last N actions."""
        action_key = self._action_key(action_type, parameters)

        recent_actions = self.action_history[-within_last_n:]
        for record in recent_actions:
            if self._action_key(record.action_type, record.parameters) == action_key:
                return True
        return False

    def get_failed_actions(self, action_type: Optional[str] = None) -> List[ActionRecord]:
        """Get all failed actions, optionally filtered by type."""
        failed = [r for r in self.action_history if r.result == "failed"]
        if action_type:
            failed = [r for r in failed if r.action_type == action_type]
        return failed

    def get_action_summary(self) -> str:
        """Get a summary of recent actions for the agent to see."""
        if not self.action_history:
            return "No actions taken yet."

        recent = self.action_history[-10:]
        lines = ["Recent actions:"]
        for i, record in enumerate(recent, 1):
            status_icon = "✅" if record.result == "success" else "❌" if record.result == "failed" else "⚠️"
            params_preview = str(record.parameters)[:50]
            lines.append(f"{i}. {status_icon} {record.action_type} {params_preview}")
            if record.error_message:
                lines.append(f"   Error: {record.error_message}")

        return "\n".join(lines)
```

**Update agent prompts to include action history:**

```python
# In src/agent/core.py - update the system prompt
ENHANCED_SYSTEM_PROMPT = """...existing prompt...

## Action History & Learning

Before taking an action:
1. Check if you've tried this exact action recently (use get_current_context to see action history)
2. If an action failed multiple times, try a DIFFERENT approach
3. Look for patterns in failures - maybe the target moved, wrong window, etc.

If you find yourself repeating actions:
- STOP and analyze what's not working
- Try a completely different strategy
- Ask the user for help if stuck after 3 attempts

Example:
- If clicking at (100, 250) failed 3 times → try finding the element via screenshot first
- If extraction returns only UI elements → try scrolling or waiting for content to load
- If hover doesn't reveal button → try direct click on the item name instead
"""
```

---

## 2. State Management Enhancements

### Issue: Limited State Awareness
Current state only tracks `current_page` and `extraction_count`. No awareness of UI state, hover effects, or screen context.

### Proposed Solution: Rich State with UI Context

**Enhanced state tracking in `src/agent/state.py`:**

```python
@dataclass
class UIElementState:
    """State of a UI element discovered on screen."""
    element_type: str  # "button", "link", "recipe_row", "menu", etc.
    text: str
    coordinates: Dict[str, int]  # {"x": 100, "y": 200, "width": 50, "height": 20}
    is_hover_sensitive: bool = False
    hover_reveals: Optional[str] = None  # e.g., "open_button"
    last_seen: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0

@dataclass
class ScreenContext:
    """Current screen context from last screenshot analysis."""
    application_name: str
    visible_elements: List[UIElementState] = field(default_factory=list)
    page_title: Optional[str] = None
    is_database_view: bool = False
    is_page_view: bool = False
    has_sidebar: bool = False
    timestamp: datetime = field(default_factory=datetime.now)

    def find_element(self, text: str, fuzzy: bool = True) -> Optional[UIElementState]:
        """Find an element by text."""
        for elem in self.visible_elements:
            if fuzzy:
                from difflib import SequenceMatcher
                ratio = SequenceMatcher(None, elem.text.lower(), text.lower()).ratio()
                if ratio > 0.8:
                    return elem
            else:
                if text.lower() in elem.text.lower():
                    return elem
        return None

@dataclass
class AgentState:
    """Enhanced state with screen context."""

    # ...existing fields...

    # NEW: Screen context
    screen_context: Optional[ScreenContext] = None
    screen_context_history: List[ScreenContext] = field(default_factory=list)

    # NEW: Hover cache
    hover_sensitive_elements: Dict[str, UIElementState] = field(default_factory=dict)

    def update_screen_context(self, context: ScreenContext):
        """Update screen context and preserve history."""
        if self.screen_context:
            self.screen_context_history.append(self.screen_context)
        self.screen_context = context

        # Keep only last 5 contexts
        if len(self.screen_context_history) > 5:
            self.screen_context_history = self.screen_context_history[-5:]

        # Update hover-sensitive elements cache
        for elem in context.visible_elements:
            if elem.is_hover_sensitive:
                self.hover_sensitive_elements[elem.text] = elem

    def detect_state_change(self) -> Optional[str]:
        """Detect if screen state changed significantly."""
        if not self.screen_context_history:
            return None

        prev = self.screen_context_history[-1]
        curr = self.screen_context

        if not curr:
            return None

        changes = []

        if prev.page_title != curr.page_title:
            changes.append(f"Page changed: {prev.page_title} → {curr.page_title}")

        if prev.is_database_view != curr.is_database_view:
            view = "database" if curr.is_database_view else "page"
            changes.append(f"View changed to {view}")

        # Check if major elements changed
        prev_texts = {e.text for e in prev.visible_elements}
        curr_texts = {e.text for e in curr.visible_elements}

        new_elements = curr_texts - prev_texts
        removed_elements = prev_texts - curr_texts

        if len(new_elements) > 3:
            changes.append(f"{len(new_elements)} new elements appeared")
        if len(removed_elements) > 3:
            changes.append(f"{len(removed_elements)} elements disappeared")

        return "; ".join(changes) if changes else None
```

**Integration with screenshot tool:**

```python
# In src/agent/computer_use_tools.py - update ScreenshotTool

def _run(self) -> str:
    """Enhanced screenshot with state update."""
    show_progress("Capturing screenshot...")

    screenshot_b64 = self.client.take_screenshot()
    self.state.last_screenshot = screenshot_b64

    show_progress("Analyzing screen with vision AI...")
    description = self._analyze_screenshot_optimized(screenshot_b64)

    # NEW: Parse description to update screen context
    context = self._parse_screen_description(description)
    self.state.update_screen_context(context)

    # NEW: Detect state changes
    state_change = self.state.detect_state_change()

    result = {
        "status": "success",
        "screen_description": description,
        "state_change": state_change,
        "context": {
            "page": context.page_title,
            "view_type": "database" if context.is_database_view else "page",
            "elements_visible": len(context.visible_elements)
        }
    }

    return json.dumps(result, indent=2)

def _parse_screen_description(self, description: str) -> ScreenContext:
    """Parse vision AI description into structured screen context."""
    # Use simple heuristics or another AI call to extract structure
    context = ScreenContext(
        application_name="Notion",  # Could parse from description
        page_title=self._extract_page_title(description),
        is_database_view="database" in description.lower() or "table" in description.lower(),
        is_page_view="page" in description.lower(),
        has_sidebar="sidebar" in description.lower()
    )

    # Extract visible elements (simplified - could use regex or AI)
    # For now, just mark basic detection
    if "recipe" in description.lower():
        # Would extract actual recipe names and positions
        pass

    return context

def _extract_page_title(self, description: str) -> Optional[str]:
    """Extract page title from description."""
    # Look for patterns like "titled 'X'" or "page: X"
    import re
    patterns = [
        r"titled\s+['\"]([^'\"]+)['\"]",
        r"page:\s+([^\n,]+)",
        r"current page\s+is\s+['\"]([^'\"]+)['\"]"
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None
```

---

## 3. Hover Interaction Improvements

### Issue: Hover Detection Works But Not Cached
The OCR-based hover detection works well but doesn't cache results or learn from successful hovers.

### Proposed Solution: Hover State Caching + Predictive Hovering

**Enhanced OCR Navigator with caching:**

```python
# In src/notion/ocr_navigator.py

class OCRNavigator:
    """Enhanced navigator with hover caching."""

    def __init__(self, detector: NotionDetector):
        self.detector = detector
        self.ocr = VisionOCR()

        # NEW: Hover cache
        self.hover_cache: Dict[str, Dict[str, Any]] = {}
        # Format: {"recipe_name": {
        #     "element_coords": (x, y, w, h),
        #     "open_button_coords": (x, y),
        #     "last_successful": timestamp,
        #     "success_count": 3
        # }}

    def find_and_click_text_cached(
        self,
        text: str,
        delay: float = 1.0,
        use_cache: bool = True
    ) -> bool:
        """Find and click text with caching support.

        Args:
            text: Text to search for
            delay: Delay after click
            use_cache: Whether to use cached hover button locations
        """
        # Check cache first
        if use_cache and text in self.hover_cache:
            cached = self.hover_cache[text]
            cache_age = time.time() - cached.get("last_successful", 0)

            # Use cache if less than 5 minutes old
            if cache_age < 300:
                print(f"  💾 Using cached hover location for '{text}'")
                open_x, open_y = cached["open_button_coords"]

                # Try cached location
                success = self.click_at_position(open_x, open_y, delay)
                if success:
                    cached["success_count"] = cached.get("success_count", 0) + 1
                    cached["last_successful"] = time.time()
                    return True
                else:
                    print(f"  ⚠️  Cached location failed, falling back to OCR")
                    # Fall through to OCR method

        # Original OCR method
        print(f"🔍 Searching for: {text}")
        items = self.find_text_on_screen(search_terms=[text], fuzzy=True)

        if not items:
            print(f"  ❌ Not found")
            return False

        item = items[0]
        hover_x = int(item['x'] + item['width'] / 2)
        hover_y = int(item['y'] + item['height'] / 2)

        print(f"  ✅ Found at ({hover_x}, {hover_y})")
        print(f"  🖱️  Hovering to reveal OPEN button...")

        # Hover
        self._move_mouse(hover_x, hover_y)
        time.sleep(0.5)

        # Look for OPEN button
        print(f"  🔍 Looking for OPEN button...")
        open_items = self.find_text_on_screen(search_terms=["OPEN"])

        if open_items:
            nearby_opens = [
                btn for btn in open_items
                if abs(btn['y'] - item['y']) < 50
            ]

            if nearby_opens:
                open_btn = nearby_opens[0]
                click_x = int(open_btn['x'] + open_btn['width'] / 2)
                click_y = int(open_btn['y'] + open_btn['height'] / 2)

                print(f"  ✅ Found OPEN button at ({click_x}, {click_y})")

                # CACHE THIS SUCCESS
                self.hover_cache[text] = {
                    "element_coords": (item['x'], item['y'], item['width'], item['height']),
                    "open_button_coords": (click_x, click_y),
                    "last_successful": time.time(),
                    "success_count": 1
                }

                success = self.click_at_position(click_x, click_y, delay)
                if success:
                    time.sleep(1.0)
                    self.expand_side_panel_to_full_page(delay=0.5)
                return success

        # Fallback: click recipe name
        print(f"  ⚠️  OPEN button not found, clicking recipe name")
        success = self.click_at_position(hover_x, hover_y, delay)
        if success:
            time.sleep(1.0)
            self.expand_side_panel_to_full_page(delay=0.5)
        return success

    def _move_mouse(self, x: int, y: int):
        """Move mouse without clicking."""
        try:
            mouse_point = Quartz.CGPoint(x, y)
            mouse_move = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventMouseMoved,
                mouse_point,
                Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_move)
        except Exception as e:
            print(f"  ⚠️  Mouse move failed: {e}")

    def get_hover_statistics(self) -> Dict[str, Any]:
        """Get statistics about hover cache performance."""
        return {
            "cached_elements": len(self.hover_cache),
            "total_successes": sum(c.get("success_count", 0) for c in self.hover_cache.values()),
            "cache_entries": list(self.hover_cache.keys())
        }
```

---

## 4. Trial and Error Reinforcement

### Issue: No Learning Mechanism
Agent doesn't learn from failures or adapt strategies.

### Proposed Solution: Strategy Manager with Learning

**New strategy manager:**

```python
# New file: src/agent/strategy.py

from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum

class StrategyResult(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class Strategy:
    """A strategy for accomplishing a goal."""
    name: str
    description: str
    execute: Callable  # Function to execute the strategy
    preconditions: List[str] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    average_duration: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total

    def record_attempt(self, result: StrategyResult, duration: float):
        """Record a strategy attempt."""
        if result == StrategyResult.SUCCESS:
            self.success_count += 1
        elif result == StrategyResult.FAILED:
            self.failure_count += 1

        # Update average duration
        total_attempts = self.success_count + self.failure_count
        self.average_duration = (
            (self.average_duration * (total_attempts - 1) + duration) / total_attempts
        )

class StrategyManager:
    """Manages multiple strategies for achieving goals."""

    def __init__(self):
        self.strategies: Dict[str, List[Strategy]] = {}

    def register_strategy(self, goal: str, strategy: Strategy):
        """Register a strategy for a goal."""
        if goal not in self.strategies:
            self.strategies[goal] = []
        self.strategies[goal].append(strategy)

    def get_best_strategy(self, goal: str) -> Optional[Strategy]:
        """Get the best strategy for a goal based on success rate."""
        if goal not in self.strategies:
            return None

        strategies = self.strategies[goal]
        if not strategies:
            return None

        # Prioritize strategies with attempts, then by success rate
        attempted = [s for s in strategies if (s.success_count + s.failure_count) > 0]
        unattempted = [s for s in strategies if (s.success_count + s.failure_count) == 0]

        if attempted:
            # Sort by success rate descending
            return max(attempted, key=lambda s: s.success_rate)
        else:
            # Try unattempted strategies
            return unattempted[0]

    def get_next_strategy(self, goal: str, exclude: List[str] = None) -> Optional[Strategy]:
        """Get next strategy to try, excluding failed ones."""
        if goal not in self.strategies:
            return None

        exclude = exclude or []
        available = [s for s in self.strategies[goal] if s.name not in exclude]

        if not available:
            return None

        # Try strategies with fewer failures first
        return min(available, key=lambda s: s.failure_count)

# Example strategies for "open_recipe" goal
def strategy_hover_and_click_open(ocr_nav, recipe_name: str) -> StrategyResult:
    """Strategy: Hover over recipe to reveal OPEN button, then click."""
    success = ocr_nav.find_and_click_text(recipe_name)
    return StrategyResult.SUCCESS if success else StrategyResult.FAILED

def strategy_direct_click_name(ocr_nav, recipe_name: str) -> StrategyResult:
    """Strategy: Click directly on recipe name."""
    items = ocr_nav.find_text_on_screen(search_terms=[recipe_name])
    if items:
        item = items[0]
        x = int(item['x'] + item['width'] / 2)
        y = int(item['y'] + item['height'] / 2)
        success = ocr_nav.click_at_position(x, y)
        return StrategyResult.SUCCESS if success else StrategyResult.FAILED
    return StrategyResult.FAILED

def strategy_use_keyboard_navigation(ocr_nav, recipe_name: str) -> StrategyResult:
    """Strategy: Use keyboard (Tab + Enter) to navigate."""
    # Implementation would use keyboard commands
    # This is a placeholder
    return StrategyResult.FAILED

# Register strategies
strategy_manager = StrategyManager()

strategy_manager.register_strategy("open_recipe", Strategy(
    name="hover_and_click_open",
    description="Hover over recipe to reveal OPEN button, then click it",
    execute=strategy_hover_and_click_open,
    preconditions=["recipe_visible", "ocr_available"]
))

strategy_manager.register_strategy("open_recipe", Strategy(
    name="direct_click_name",
    description="Click directly on the recipe name",
    execute=strategy_direct_click_name,
    preconditions=["recipe_visible"]
))

strategy_manager.register_strategy("open_recipe", Strategy(
    name="keyboard_navigation",
    description="Use Tab and Enter to navigate",
    execute=strategy_use_keyboard_navigation,
    preconditions=[]
))
```

**Integration with agent:**

```python
# In agent tools - add a new tool for strategy execution

class StrategyExecutionTool(BaseTool):
    """Tool that tries multiple strategies with learning."""

    name: str = "try_strategies"
    description: str = (
        "Attempt a goal using multiple strategies, learning from failures. "
        "Will try different approaches automatically if one fails. "
        "Use this when a straightforward action might have multiple ways to accomplish it."
    )

    strategy_manager: StrategyManager = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _run(self, goal: str, context: Dict[str, Any]) -> str:
        """Execute strategies for a goal until one succeeds."""
        import time

        attempted = []
        max_attempts = 3

        for attempt in range(max_attempts):
            # Get next best strategy
            strategy = self.strategy_manager.get_next_strategy(goal, exclude=attempted)

            if not strategy:
                return json.dumps({
                    "status": "failed",
                    "message": f"No more strategies available for goal: {goal}",
                    "attempted": attempted
                })

            print(f"  🎯 Attempting strategy: {strategy.name}")
            print(f"     {strategy.description}")

            # Execute strategy
            start_time = time.time()
            try:
                result = strategy.execute(**context)
                duration = time.time() - start_time

                strategy.record_attempt(result, duration)
                attempted.append(strategy.name)

                # Record in state
                self.state.record_action(
                    action_type=f"strategy_{strategy.name}",
                    parameters={"goal": goal, **context},
                    result=result.value
                )

                if result == StrategyResult.SUCCESS:
                    return json.dumps({
                        "status": "success",
                        "strategy_used": strategy.name,
                        "attempts": len(attempted),
                        "duration": duration
                    })
                else:
                    print(f"  ❌ Strategy '{strategy.name}' failed, trying next...")

            except Exception as e:
                print(f"  ❌ Strategy '{strategy.name}' raised error: {e}")
                strategy.record_attempt(StrategyResult.FAILED, time.time() - start_time)
                attempted.append(strategy.name)

        return json.dumps({
            "status": "failed",
            "message": f"All {max_attempts} strategies failed for goal: {goal}",
            "attempted": attempted
        })
```

---

## 5. Content vs UI Element Discrimination

### Issue: Extraction Captures UI Elements Instead of Content
After navigating to a page, extraction returns tab bars, buttons, etc. instead of actual content.

### Proposed Solution: Content-Aware Extraction with Filtering

**Enhanced extraction with UI filtering:**

```python
# In src/notion/extractor.py (or create new filter module)

class ContentFilter:
    """Filter to distinguish content from UI elements."""

    # UI element indicators
    UI_ROLES = {
        "AXButton", "AXToolbar", "AXTabGroup", "AXStaticText",
        "AXGroup", "AXScrollBar", "AXSplitter"
    }

    UI_KEYWORDS = {
        "tab bar", "open sidebar", "back", "forward", "share",
        "more", "search", "filter", "sort", "settings", "menu",
        "close", "minimize", "maximize"
    }

    @classmethod
    def is_likely_ui_element(cls, block: Dict[str, Any]) -> bool:
        """Determine if a block is likely a UI element vs content."""

        # Check role
        role = block.get("metadata", {}).get("role", "")
        if role in cls.UI_ROLES:
            return True

        # Check content keywords
        content = block.get("content", "").lower()
        if any(keyword in content for keyword in cls.UI_KEYWORDS):
            return True

        # Check position - UI elements often at top/bottom
        order = block.get("order", 999)
        if order < 3:  # First few elements are often UI
            return True

        # Very short content is often UI
        if len(content) < 5:
            return True

        return False

    @classmethod
    def filter_content_blocks(cls, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter out UI elements, keep only content."""
        return [
            block for block in blocks
            if not cls.is_likely_ui_element(block)
        ]

    @classmethod
    def filter_with_explanation(cls, blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Filter blocks and explain what was removed."""
        content_blocks = []
        ui_blocks = []

        for block in blocks:
            if cls.is_likely_ui_element(block):
                ui_blocks.append(block)
            else:
                content_blocks.append(block)

        return {
            "content_blocks": content_blocks,
            "ui_blocks": ui_blocks,
            "summary": {
                "total": len(blocks),
                "content": len(content_blocks),
                "ui_filtered": len(ui_blocks)
            }
        }
```

**Integration with extraction:**

```python
# Update extract_page_content tool to use filtering

def extract_page_content(page_name: Optional[str] = None) -> Dict[str, Any]:
    """Extract content with UI filtering."""

    # ... existing extraction code ...

    blocks = orchestrator.extract_page(page_name)

    # NEW: Filter UI elements
    filtered = ContentFilter.filter_with_explanation(blocks)

    return {
        "page": page_name,
        "blocks": filtered["content_blocks"],
        "block_count": len(filtered["content_blocks"]),
        "ui_elements_filtered": filtered["summary"]["ui_filtered"],
        "extraction_quality": "high" if filtered["summary"]["content"] > 0 else "low"
    }
```

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- [ ] Implement enhanced `AgentState` with action history
- [ ] Add action deduplication checks to prevent loops
- [ ] Update agent prompts to use action history

### Phase 2: State Awareness (Week 2)
- [ ] Implement `ScreenContext` and `UIElementState`
- [ ] Integrate screen context updates with screenshot tool
- [ ] Add state change detection

### Phase 3: Hover Improvements (Week 3)
- [ ] Add hover caching to `OCRNavigator`
- [ ] Implement predictive hover based on cache
- [ ] Add hover statistics tracking

### Phase 4: Strategy System (Week 4)
- [ ] Implement `Strategy` and `StrategyManager`
- [ ] Define strategies for common goals
- [ ] Add strategy execution tool

### Phase 5: Content Filtering (Week 5)
- [ ] Implement `ContentFilter`
- [ ] Integrate with extraction tools
- [ ] Add extraction quality metrics

### Phase 6: Testing & Refinement (Week 6)
- [ ] Test all improvements end-to-end
- [ ] Tune thresholds and parameters
- [ ] Document usage patterns

---

## Expected Outcomes

After implementing these improvements:

1. **No More Infinite Loops**: Action history prevents repeating failed actions
2. **Smarter Retries**: Agent tries different strategies when one fails
3. **Faster Interactions**: Hover caching speeds up repeated database navigation
4. **Better Extraction**: Content filtering removes UI noise
5. **State Awareness**: Agent knows what it tried and what the screen looks like
6. **Learning Over Time**: Strategy success rates improve agent decision-making

---

## Testing Checklist

- [ ] Agent stops after 3 failed identical actions
- [ ] Different strategies attempted for same goal
- [ ] Hover cache hit rate > 80% for repeated items
- [ ] Content extraction has < 10% UI elements
- [ ] State change detection catches page navigation
- [ ] Action history prevents repeating recent failures

---

Generated by Claude Code testing on 2025-12-05
