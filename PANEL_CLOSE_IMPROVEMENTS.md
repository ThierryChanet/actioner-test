# Panel Closing Improvements Investigation

## Current Issues

### Test Results Analysis
- **Recipe 1 & 2:** Panel failed to close after 3 Escape attempts
- **Recipe 3, 4, 5:** Panel closed successfully
- **Evidence of mixing:** Recipes 1 & 2 share 5+ ingredients, suggesting panel wasn't properly closed

### Failure Pattern
```
[1] Topinambours au vinaigre: ❌ Failed to close (3 attempts)
[2] Velouté Potimarron:        ❌ Failed to close (3 attempts) - Shows mixed ingredients from #1
[3] Aheobakjin:                ✅ Closed successfully
[4] Thai omelet:               ✅ Closed successfully
[5] Aubergines au sésame:      ✅ Closed successfully
```

## Root Causes

### 1. Focus Not Set on Panel
- **Problem:** Escape key doesn't work if focus is on wrong UI element
- **Evidence:** User previously mentioned clicking neutral panel elements before Escape
- **Solution:** Click on panel background/neutral area before pressing Escape

### 2. Insufficient Wait Time
- **Problem:** Notion panel might still be animating when we try to close it
- **Evidence:** First two recipes fail, later ones succeed (system "warms up")
- **Solution:** Increase wait time after extraction, especially for first recipes

### 3. Single Close Method
- **Problem:** Relying only on Escape key
- **Evidence:** 40% failure rate (2/5 recipes)
- **Solution:** Implement multiple fallback methods

### 4. Verification Prompt Too Broad
- **Problem:** Asking "Is panel showing X?" when panel is already closed shows NO
- **Evidence:** Panel verification works, but doesn't distinguish between "closed" and "showing different recipe"
- **Solution:** More specific verification prompt

## Proposed Solutions

### Solution 1: Click Panel Background Before Escape ⭐ RECOMMENDED
Based on user's earlier suggestion: "click on neutral side panel elements before pressing escape"

```python
def close_panel_with_focus(client, recipe_name: str) -> bool:
    """Close panel by first setting focus, then pressing Escape."""

    # STEP 1: Click neutral area in panel to set focus
    # Right panel is typically around x=900-1000, y=400 (middle)
    neutral_coords = (950, 400)

    print(f'  Setting focus on panel...')
    client.execute_action('left_click', coordinate=neutral_coords)
    time.sleep(0.5)

    # STEP 2: Now press Escape with focus set
    print(f'  Pressing Escape...')
    client.execute_action('key', text='Escape')
    time.sleep(1.5)

    # STEP 3: Verify closed
    return verify_panel_closed(client, recipe_name)
```

**Pros:**
- User confirmed this approach works
- Sets proper focus before Escape
- Matches Notion's expected UX

**Cons:**
- Requires knowing panel coordinates
- Coordinates might vary with screen size

### Solution 2: Multiple Close Methods with Fallback

```python
def close_panel_robust(client, recipe_name: str, max_attempts: int = 3) -> bool:
    """Try multiple methods to close panel."""

    methods = [
        ('focus_then_escape', lambda: close_panel_with_focus(client, recipe_name)),
        ('escape_only', lambda: close_panel_escape_only(client, recipe_name)),
        ('click_x_button', lambda: close_panel_click_x(client)),
    ]

    for attempt, (method_name, method_func) in enumerate(methods, 1):
        print(f'  Close attempt {attempt}/{len(methods)}: {method_name}')

        if method_func():
            print(f'  ✓ Panel closed with {method_name}')
            return True

        if attempt < len(methods):
            print(f'  ⚠️  {method_name} failed, trying next method...')
            time.sleep(1)

    return False
```

### Solution 3: Vision-Based Close Button Detection

```python
def close_panel_vision(client) -> bool:
    """Use Computer Vision to find and click close button."""

    screenshot = client.take_screenshot(use_cache=False)

    prompt = """Look at this Notion screenshot.

Find the CLOSE BUTTON (X) for the right sidebar panel.
Return coordinates in this exact format:
COORDINATES: (x, y)

If no close button visible, return:
NOT_FOUND"""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=100,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': prompt}
            ]
        }]
    )

    response_text = response.content[0].text.strip()

    # Extract coordinates
    import re
    match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response_text)
    if match:
        x, y = int(match.group(1)), int(match.group(2))
        client.execute_action('left_click', coordinate=(x, y))
        time.sleep(1.5)
        return True

    return False
```

### Solution 4: Improved Verification Prompt

```python
def verify_panel_closed(client, recipe_name: str) -> bool:
    """Verify panel is actually closed."""

    screenshot = client.take_screenshot(use_cache=False)

    # More specific prompt
    prompt = f"""Look at this Notion screenshot.

What is the current state of the RIGHT SIDEBAR panel?

Answer with ONE of these options:
A) OPEN - showing "{recipe_name}"
B) OPEN - showing a DIFFERENT recipe
C) CLOSED - no right sidebar visible

Answer with just the letter (A, B, or C):"""

    response = client.client.messages.create(
        model=client.model,
        max_tokens=50,
        messages=[{
            'role': 'user',
            'content': [
                {'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': screenshot}},
                {'type': 'text', 'text': prompt}
            ]
        }]
    )

    answer = response.content[0].text.strip().upper()

    if 'C' in answer or 'CLOSED' in answer:
        return True  # Panel is closed

    return False  # Panel still open
```

## Recommended Implementation Plan

### Phase 1: Quick Win (RECOMMENDED)
Implement Solution 1 (Click Panel Background Before Escape)
- **Effort:** Low
- **Impact:** High (user confirmed this works)
- **Risk:** Low

```python
# In extract_ingredients_with_retry(), replace:
client.execute_action('key', text='Escape')

# With:
# Click neutral panel area to set focus
client.execute_action('left_click', coordinate=(950, 400))
time.sleep(0.5)
# Now press Escape
client.execute_action('key', text='Escape')
```

### Phase 2: Add Fallbacks
Implement Solution 2 (Multiple Methods)
- **Effort:** Medium
- **Impact:** High
- **Risk:** Low

### Phase 3: Vision Enhancement
Implement Solution 3 (Vision-Based Close Button)
- **Effort:** High
- **Impact:** Medium (more robust but slower)
- **Risk:** Medium (vision might not always find button)

### Phase 4: Better Verification
Implement Solution 4 (Improved Verification)
- **Effort:** Low
- **Impact:** Medium
- **Risk:** Low

## Testing Strategy

1. **Test with problematic recipes first:**
   - Run extraction on just "Topinambours au vinaigre" and "Velouté Potimarron"
   - Verify panel closes after each
   - Verify ingredients don't mix

2. **Full regression test:**
   - Run scripts/recipe_extraction_comprehensive.py
   - All 5 recipes should close successfully
   - No ingredient mixing

3. **Edge case testing:**
   - Test with panel already closed
   - Test with multiple panels open
   - Test with tab open instead of panel

## Expected Outcomes

### Before Improvements
- 60% panel close success rate (3/5)
- Ingredient mixing in first 2 recipes
- Unpredictable behavior

### After Phase 1 (Click + Escape)
- **Expected:** 100% panel close success rate
- **Expected:** No ingredient mixing
- **Expected:** Consistent behavior

### After All Phases
- **Expected:** 100% success with multiple fallbacks
- **Expected:** Robust error recovery
- **Expected:** Clear debugging information
