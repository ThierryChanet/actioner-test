Got it — so instead of **simulating mouse movement**, you want **direct programmatic actions** whenever possible.

On macOS, this means:

### ✔ Prefer **AX API actions** (AXPress, AXShowMenu, AXRaise, AXScroll)

### ❌ Avoid mouse simulation unless no other option exists

### ✔ Use accessibility actions the same way a screen reader or automation engine would

This is **more reliable, faster, and less fragile** than human-like mouse simulation.

Below is the **revised PRD**, simplified and aligned with *direct action execution only*.

---

# **Product Requirements Document (PRD)**

## **Project: Notion macOS Direct-Action Data Extractor**

**Scope:** Your personal use
**Platform:** macOS

---

# **1. Product Overview**

This is a local Python tool that extracts structured content from the Notion macOS desktop application using the **macOS Accessibility API (AX API)**.

It does *not* simulate physical mouse or keyboard input.

Instead, it uses **direct accessibility actions** to:

* Select UI elements
* Trigger scrolling
* Access text values
* Navigate through the Notion content area

When extraction via AX fails, OCR is still used as a fallback.

---

# **2. Objectives & Success Criteria (Tough Version)**

## **Primary Objective**

Extract **complete and accurate** text content from Notion desktop pages using **direct macOS accessibility actions**, without synthetic mouse events.

## **Success Criteria**

| Category                     | Requirement                                                                   |
| ---------------------------- | ----------------------------------------------------------------------------- |
| **Accuracy (AX extraction)** | ≥ **99% fidelity** of text extracted compared to visible content              |
| **OCR fallback accuracy**    | ≥ **92% correct text retrieval**                                              |
| **Page completeness**        | Should extract **100% of visible blocks** including nested or folded elements |
| **Stability**                | Process must handle **100 pages sequentially** without errors                 |
| **Speed**                    | Extract a 50-block page in **< 2 seconds**                                    |
| **Robustness**               | Works regardless of Notion window position or size                            |
| **Determinism**              | Re-running extraction on the same page yields the exact same output           |

This is stricter than before — the tool must achieve near-perfect extraction.

---

# **3. Scope**

### **In Scope**

* Only the Notion desktop macOS app
* Use only:

  * AX API (via PyObjC)
  * Direct AX actions (e.g., AXScrollDown, AXShowMenu, AXPress)
* Extract all text blocks displayed on a Notion page
* Identify scrollable container
* Page traversal using AX scroll actions
* Fallback OCR for inaccessible elements
* Export results to JSON and CSV
* Logging of AX actions, missing elements, OCR usage

### **Not In Scope**

* Editing Notion content
* Navigating between Notion pages automatically
* Windows version
* Multi-app flows

---

# **4. User Stories**

* *As the user, I want* the tool to locate the Notion window automatically.
* *As the user, I want* the tool to inspect the accessibility hierarchy of the focused page.
* *As the user, I want* the tool to scroll using AXScrollDown/AXScrollPageDown.
* *As the user, I want* to extract the full text content without missing blocks.
* *As the user, I want* a single command to export a Notion page to JSON or CSV.

---

# **5. Technical Framework (Direct AX Actions)**

## **5.1 Language**

➡️ **Python** with **PyObjC**

## **5.2 Core macOS Accessibility API Actions**

The tool must use direct AX actions, including:

| Action                        | Description                           |
| ----------------------------- | ------------------------------------- |
| **AXPress**                   | Activate a button, toggle, menuitem   |
| **AXScrollDown / AXScrollUp** | Scroll container content              |
| **AXScrollToVisible**         | Ensure element is on screen           |
| **AXIncrement / AXDecrement** | Step navigation for sliders/spinners  |
| **AXRaise**                   | Bring window to front                 |
| **AXSetValue**                | Set text field values (rarely needed) |

These actions avoid mouse simulation entirely.

---

# **6. Architecture**

## **6.1 Layer 1 — Notion Window Detector**

* Use NSWorkspace + AXUIElementCreateApplication
* Identify Notion.app
* Retrieve main window
* Extract the content root element

## **6.2 Layer 2 — AX Tree Explorer**

Recursively enumerate nodes, capturing:

* AXRole
* AXSubrole
* AXValue
* AXChildren
* AXFrame
* Action support list (AXPress, AXScroll, etc.)

Focus on:

* AXStaticText
* AXGroup
* AXScrollArea
* AXTextArea

## **6.3 Layer 3 — Direct Action Navigator**

Rather than using PyAutoGUI scrolling, do:

```
scroll_area.performAction("AXScrollPageDown")
```

Loop until:

* scroll position stops changing
* bottom of page reached

## **6.4 Layer 4 — Extraction Engine**

Extraction order:

1. Find the main scrollable AX element
2. For each scroll step:

   * Collect all visible AXStaticText nodes
   * Deduplicate by bounding box or content hash
3. For nodes with no AXValue:

   * Crop region (Quartz screenshot)
   * OCR text with pytesseract
4. Append to block list

## **6.5 Layer 5 — Output Engine**

Formats the output as:

### JSON

```json
{
  "title": "Page Title",
  "blocks": [
    {"role": "paragraph", "text": "Hello world"},
    {"role": "heading2", "text": "My Title"}
  ]
}
```

### CSV

* linear text extraction
* block-level identifiers

---

# **7. Risks & Mitigation**

| Risk                                    | Mitigation                               |
| --------------------------------------- | ---------------------------------------- |
| Notion does not expose much via AX      | Combine AX with OCR fallback             |
| Dynamic loading of blocks during scroll | Use AXScrollToVisible + stable waits     |
| AX API returns stale hierarchy          | Refresh hierarchy after each scroll      |
| Nested blocks lost                      | Use bounding boxes to maintain order     |
| OCR errors                              | Crop single lines only, no full-page OCR |

---

# **8. Roadmap**

### **Phase 1 — Basic Direct Control**

* Detect Notion window
* Read AX tree
* Identify scroll area

### **Phase 2 — Extraction**

* Extract visible AXStaticText
* Perform AXScrollPageDown looping
* Implement deduplication logic

### **Phase 3 — Output**

* Format JSON/CSV
* Add logs

### **Phase 4 — Hardening & Stress Testing**

* 100-page run
* Fallback OCR
* Edge case recovery
