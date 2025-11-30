# Simplified PRD --- With Notion Page Navigation (Intent Only)

## 1. Goal

Build a macOS tool that:

-   Extracts all visible text from a Notion desktop page using **direct
    macOS accessibility (AX) actions**
-   Navigates between Notion pages programmatically (next/previous/page
    list)
-   Uses **OCR only as fallback**
-   Includes a **Notion API--based test environment** to compare
    extracted content with canonical content

------------------------------------------------------------------------

## 2. Core Intent --- Extraction

-   Read Notion page content through accessibility, not simulated mouse
    input.
-   Detect and traverse the main scrollable content region.
-   Extract all visible text blocks and maintain their order.
-   Use OCR only when an element cannot expose text through AX.
-   Produce deterministic output: repeated runs yield identical results.

------------------------------------------------------------------------

## 3. Core Intent --- Navigation Between Pages

The tool must be able to:

### Page Selection

-   Programmatically choose a target page from:
    -   Sidebar page list
    -   "Back/Forward" navigation within Notion
    -   In-page links (if accessible)

### Page Switching

-   Navigate from one Notion page to another using direct accessibility
    actions.
-   Confirm the new page is fully loaded before extraction begins.

### Navigation Stability

-   Navigation must be:
    -   Deterministic\
    -   Not dependent on window position\
    -   Repeatable across runs

### Page Lists

-   The tool should be able to:
    -   Retrieve the list of pages visible in the Notion sidebar
    -   Select a specific page by name or index
    -   Move sequentially through pages (next/previous)

------------------------------------------------------------------------

## 4. Test Environment Intent

### Gold-Standard Baseline

-   Retrieve page content using the Notion API.
-   Generate a normalized "gold" structure for comparison.

### Extraction Comparison

-   After AX/OCR extraction, compare with API-based gold standard.
-   Identify:
    -   Missing blocks
    -   Ordering differences
    -   Text inaccuracies
    -   OCR artifacts

### Test Modes

-   **Normal mode:** Real AX navigation and extraction.
-   **Dry-run mode:** No actions executed, only actions planned.
-   **Debug mode:** Visual test cursor that shows what the system is
    targeting (non-interactive).

------------------------------------------------------------------------

## 5. Output Requirements

-   Export extracted data to:
    -   JSON
    -   CSV
-   Log all navigation, extraction, scroll cycles, fallback decisions.
-   Save artifacts for test runs:
    -   Gold-standard JSON
    -   Extracted JSON
    -   Diff report
    -   Screenshots or bounding-box visuals (if in debug mode)

------------------------------------------------------------------------

## 6. Quality & Robustness Intent

### Extraction

-   High text fidelity compared to API baseline.
-   OCR should only activate for inaccessible blocks.

### Navigation

-   Page switches should be fully reliable, even with:
    -   Different window sizes
    -   Collapsed sidebar
    -   Deeply nested pages
    -   Rapid consecutive navigations

### Determinism

-   Navigating + extracting the same sequence of pages should produce
    the same output in every run.

### Error Handling

-   Pages that fail extraction must produce:
    -   A clear error reason
    -   A minimal diff
    -   A recoverable state

------------------------------------------------------------------------

# End of simplified PRD
