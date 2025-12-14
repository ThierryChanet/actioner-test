"""Notion-specific LangChain tools for database navigation.

These tools implement Notion's specific UI patterns:
- Database rows require hovering to reveal OPEN button
- Clicking OPEN opens a sidebar panel
- Sidebar needs expansion to full page

These tools are separate from general computer use tools and only loaded
when working with Notion.
"""

import json
import time
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from .state import AgentState
from .callbacks import show_progress
from .screen_manager import NotionScreenManager


class NotionOpenPageInput(BaseModel):
    """Input for Notion page opening tool."""
    page_name: str = Field(
        description="Name of the page/row to open in Notion database (e.g., 'Velouté Potimarron', 'Project Alpha')"
    )


class NotionOpenPageTool(BaseTool):
    """Tool for opening a page in a Notion database.

    This tool handles Notion's specific UI pattern:
    1. Uses Claude vision to find the page name in the database
    2. Hovers over it to reveal the OPEN button
    3. Finds and clicks the OPEN button using vision
    4. Waits for sidebar to appear
    5. Expands sidebar to full page

    This is more reliable than generic clicking for Notion databases.
    Only use this tool when working with Notion.
    """

    name: str = "notion_open_page"
    description: str = (
        "Open a page in a Notion database by name. "
        "This tool handles Notion's specific UI: it finds the page, "
        "reveals the OPEN button by hovering, clicks it, and expands the sidebar. "
        "Use this instead of click_element when working with Notion databases. "
        "Examples: 'Velouté Potimarron', 'Project Alpha', 'Meeting Notes'. "
        "The page will open in a sidebar that this tool automatically expands."
    )
    args_schema: Type[BaseModel] = NotionOpenPageInput

    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _run(self, page_name: str) -> str:
        """Open a Notion page using vision-guided navigation."""
        show_progress(f"Opening Notion page '{page_name}'...")

        try:
            # Check if client has vision capabilities
            if not hasattr(self.client, '_click_element'):
                return json.dumps({
                    "status": "error",
                    "message": "Vision-based navigation not available. This tool requires Anthropic provider."
                }, indent=2)

            # Step 0: Ensure we're focused on Notion window
            show_progress("Switching to Notion window...")
            self.client.execute_action("switch_desktop", text="Notion")
            time.sleep(2.0)  # Wait for desktop switch to complete

            # Step 1: Find the page name and hover over it (don't click yet)
            show_progress(f"Finding '{page_name}' in database...")
            # Use mouse_move to find and hover over the recipe without clicking
            hover_result = self.client.execute_action("mouse_move", text=page_name)

            if not hover_result.success:
                return json.dumps({
                    "status": "error",
                    "page_name": page_name,
                    "message": f"Could not find '{page_name}' in Notion database"
                }, indent=2)

            # Got coordinates - this is where the page name is
            coords = hover_result.data.get('coordinate', [0, 0])
            show_progress(f"Found '{page_name}' at ({coords[0]}, {coords[1]}), hovering...")

            # Step 2: Wait for "OPEN" button to appear after hover
            show_progress("Waiting for OPEN button to appear...")
            time.sleep(1.0)  # Wait for hover state to trigger and button to appear

            # Step 3: Take fresh screenshot and look for OPEN button
            screenshot_b64 = self.client.take_screenshot(use_cache=False)  # Fresh screenshot

            # Ask Claude to find OPEN button near the page we just hovered over
            prompt = f"""Analyze this Notion database screenshot.

I just hovered over "{page_name}" at coordinates ({coords[0]}, {coords[1]}).
The mouse cursor is currently positioned over this item.

TASK: Find the "OPEN" button that should have appeared after hovering.
The OPEN button should be:
- On the SAME horizontal line as "{page_name}" (y-coordinate within 50 pixels of {coords[1]})
- Usually to the LEFT of the item name (x-coordinate less than {coords[0]})
- A small button with text "OPEN" or an open icon
- Visible only when hovering over the row

Provide the EXACT pixel coordinates of the center of the OPEN button in this format:
COORDINATES: (x, y)

If you cannot find an OPEN button on the same horizontal line, respond with: NOT_FOUND"""

            response = self.client.client.messages.create(
                model=self.client.model,
                max_tokens=150,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            response_text = response.content[0].text.strip()

            # Parse coordinates
            import re
            coord_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response_text)

            if coord_match:
                open_x = int(coord_match.group(1))
                open_y = int(coord_match.group(2))

                show_progress(f"Found OPEN button at ({open_x}, {open_y}), clicking...")

                # Step 4: Click the OPEN button
                click_result = self.client.execute_action("left_click", coordinate=(open_x, open_y))

                if not click_result.success:
                    return json.dumps({
                        "status": "error",
                        "message": "Failed to click OPEN button"
                    }, indent=2)

                # Step 5: Wait for sidebar to appear
                time.sleep(1.0)

                # Step 6: Expand sidebar to full page (click expand icon)
                # The expand icon is typically in the top-right of the sidebar
                show_progress("Expanding sidebar to full page...")

                # Ask Claude to find the expand button
                expand_screenshot = self.client.take_screenshot(use_cache=False)
                expand_prompt = """Find the sidebar expand button in this Notion interface.
It's usually an icon in the top-right of the sidebar panel that opens pages.
Look for an expand/maximize icon or arrow.

Provide coordinates: COORDINATES: (x, y)
If not found: NOT_FOUND"""

                expand_response = self.client.client.messages.create(
                    model=self.client.model,
                    max_tokens=100,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": expand_screenshot
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": expand_prompt
                                }
                            ]
                        }
                    ]
                )

                expand_text = expand_response.content[0].text.strip()
                expand_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', expand_text)

                if expand_match:
                    expand_x = int(expand_match.group(1))
                    expand_y = int(expand_match.group(2))
                    self.client.execute_action("left_click", coordinate=(expand_x, expand_y))
                    time.sleep(0.5)

                return json.dumps({
                    "status": "success",
                    "page_name": page_name,
                    "coordinates": coords,
                    "open_button_coordinates": [open_x, open_y],
                    "message": f"Successfully opened '{page_name}' in Notion"
                }, indent=2)

            else:
                # OPEN button not found - maybe page is already open or different UI
                # Try clicking the page name directly as fallback
                show_progress("OPEN button not found, clicking page name directly...")

                return json.dumps({
                    "status": "partial_success",
                    "page_name": page_name,
                    "coordinates": coords,
                    "message": f"Clicked '{page_name}' but could not find OPEN button. Page may be open or UI differs.",
                    "note": "Try using extract_page_content to verify page state"
                }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to open Notion page: {e}"
            }, indent=2)


class NotionClosePageInput(BaseModel):
    """Input for Notion close page tool."""
    pass


class NotionClosePageTool(BaseTool):
    """Tool for closing an open Notion page sidebar.

    This tool closes the right-hand Notion page panel and returns to the
    database view by **pressing the Escape key** once Notion is in focus.

    We found through interactive testing that Escape is more reliable than
    fixed coordinate clicks or heuristics for the close button, and it also
    better matches the native Notion UX.

    Only use this tool when working with Notion.
    """

    name: str = "notion_close_page"
    description: str = (
        "Close the currently open Notion page sidebar to return to database view. "
        "Finds and clicks the close button (chevron icon) to collapse the sidebar. "
        "Use this after extracting content to return to the main database view. "
        "Example: After viewing 'Recipe A', close it before opening 'Recipe B'."
    )
    args_schema: Type[BaseModel] = NotionClosePageInput

    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _run(self) -> str:
        """Close the Notion page panel by pressing Escape."""
        show_progress("Attempting to close Notion page with Escape key...")

        # Initialize screen manager
        screen_mgr = NotionScreenManager(self.client)

        try:
            # Use context manager for automatic screen switching and notification
            with screen_mgr.for_action("panel close"):
                # Step 1: Take before screenshot
                before_screenshot = self.client.take_screenshot(use_cache=False)

                # Step 2: Press Escape to close the panel
                show_progress("Pressing Escape to close panel...")
                self.client.execute_action("key", text="Escape")
                time.sleep(1.5)

                # Step 3: Take after screenshot to verify
                after_screenshot = self.client.take_screenshot(use_cache=False)

                # Step 4: Verify the panel closed
                show_progress("Verifying panel closed...")

                prompt = """Compare these two Notion screenshots (BEFORE and AFTER pressing Escape).

TASK: Did the right panel close and the left panel expand to full width?

Check:
1. BEFORE: Left database list should be ~30% width, right panel open at ~70%
2. AFTER: Left database list should expand to ~100% width, right panel gone

Respond with EXACTLY one of:
SUCCESS - Right panel closed, left expanded to full width
FAILED - Right panel still visible, left still narrow
UNCLEAR - Cannot determine"""

                response = self.client.client.messages.create(
                    model=self.client.model,
                    max_tokens=50,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "BEFORE:"
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": before_screenshot
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": "AFTER:"
                                },
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": after_screenshot
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )

                result_text = response.content[0].text.strip()

                # Context manager will automatically switch back and notify

                if "SUCCESS" in result_text:
                    return json.dumps({
                        "status": "success",
                        "method": "escape_key",
                        "message": "Successfully closed right panel with Escape key",
                        "verification": "Left panel expanded to full width"
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "failed",
                        "method": "escape_key",
                        "message": "Escape key did not close the panel",
                        "verification_result": result_text,
                        "note": "Panel may need manual closing or different approach"
                    }, indent=2)

        except Exception as e:
            # Context manager handles switch back and notification even on error
            return json.dumps({
                "status": "error",
                "message": f"Failed to close recipe page: {e}"
            }, indent=2)

    def _find_with_vision(self) -> Optional[tuple]:
        """Try to find close button using Claude vision."""
        try:
            screenshot_b64 = self.client.take_screenshot(use_cache=False)

            prompt = """Find the close/collapse button in this Notion interface.

Look for a chevron button (>, >>, or similar arrow icon) that closes the sidebar.
It's typically in the top-right area of an open sidebar panel.

Provide EXACT coordinates:
COORDINATES: (x, y)

If not found: NOT_FOUND"""

            response = self.client.client.messages.create(
                model=self.client.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_b64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )

            import re
            text = response.content[0].text
            match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', text)

            if match:
                return (int(match.group(1)), int(match.group(2)))

        except Exception as e:
            print(f"Vision detection failed: {e}")

        return None

    def _find_with_ocr(self) -> Optional[tuple]:
        """Try to find close button using OCR."""
        try:
            from src.ocr.vision import VisionOCR

            ocr = VisionOCR()
            if not ocr.is_available():
                return None

            # Use full screen bounds from client
            x, y = 0, 0
            width = self.client.display_width
            height = self.client.display_height

            # Perform OCR
            observations = ocr.perform_ocr(x, y, width, height)

            # Search for chevron symbols
            chevron_symbols = [">>", ">", "»", "›", "❯"]
            candidates = []

            for obs in observations:
                text = obs.get('text', '').strip()
                for symbol in chevron_symbols:
                    if symbol in text or text == symbol:
                        candidates.append(obs)
                        break

            if not candidates:
                return None

            # Return the rightmost candidate (likely in sidebar)
            rightmost = max(candidates, key=lambda o: o.get('x', 0))
            return (rightmost.get('x'), rightmost.get('y'))

        except Exception as e:
            print(f"OCR detection failed: {e}")

        return None

    def _find_with_ax(self) -> Optional[tuple]:
        """Try to find close button using macOS Accessibility."""
        try:
            from src.notion.detector import NotionDetector
            from src.ax.element import AXElement

            detector = NotionDetector()
            app_element = detector.get_application_element()

            if not app_element:
                return None

            # Search for buttons with close-related attributes
            def find_close_button(element, depth=0, max_depth=10):
                if depth > max_depth:
                    return None

                try:
                    # Check if this is a close button
                    role = element.get_attribute('AXRole')
                    subrole = element.get_attribute('AXSubrole')
                    desc = element.get_attribute('AXDescription')
                    title = element.get_attribute('AXTitle')

                    # Look for close button indicators
                    close_indicators = ['close', 'dismiss', 'collapse', 'back']

                    if role == 'AXButton':
                        for indicator in close_indicators:
                            if (desc and indicator in desc.lower()) or \
                               (title and indicator in title.lower()) or \
                               (subrole and 'close' in subrole.lower()):
                                # Found a potential close button!
                                pos = element.get_attribute('AXPosition')
                                size = element.get_attribute('AXSize')
                                if pos and size:
                                    # Return center of button
                                    x = int(pos['x'] + size['width'] / 2)
                                    y = int(pos['y'] + size['height'] / 2)
                                    print(f"Found close button: {desc or title} at ({x}, {y})")
                                    return (x, y)

                    # Search children
                    children = element.get_attribute('AXChildren')
                    if children:
                        for child in children:
                            result = find_close_button(AXElement(child), depth + 1, max_depth)
                            if result:
                                return result

                except Exception as e:
                    pass

                return None

            return find_close_button(AXElement(app_element))

        except Exception as e:
            print(f"AX detection failed: {e}")

        return None


class NotionVisionExtractInput(BaseModel):
    """Input for Notion vision extraction tool."""
    focus_area: Optional[str] = Field(
        default=None,
        description="Optional hint about what to focus on (e.g., 'main content', 'properties', 'list items')"
    )


class NotionVisionExtractTool(BaseTool):
    """Tool for extracting content from an open Notion page using vision.

    This tool captures the current Notion screen and uses Claude vision to
    extract structured content from the visible page or panel. It works with
    any type of Notion content - pages, database entries, documents, etc.

    The tool analyzes the right-hand panel (if open) or main content area
    and extracts:
    - Page title
    - Main sections and their content
    - Lists, properties, and structured data
    - Full text content

    Use this when standard extraction misses content or when you need to
    read from an open side panel.
    """

    name: str = "notion_vision_extract"
    description: str = (
        "Extract content from the currently visible Notion page using vision analysis. "
        "This tool reads whatever is visible on screen - the open page panel, main content, or database entry. "
        "It captures titles, sections, lists, properties, and all text content. "
        "Use this when you need to extract from an open side panel or when standard extraction misses content. "
        "Optionally provide a focus_area hint like 'main content' or 'properties' to emphasize specific parts. "
        "IMPORTANT: After calling this tool, you MUST display the extracted content to the user - show the lists, sections, and data in your response."
    )
    args_schema: Type[BaseModel] = NotionVisionExtractInput

    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _run(self, focus_area: Optional[str] = None) -> str:
        """Extract content using Claude vision."""
        show_progress("Extracting page content with vision...")

        # Initialize screen manager
        screen_mgr = NotionScreenManager(self.client)

        try:
            # Use context manager for automatic screen switching
            with screen_mgr.for_action("vision extraction"):
                # Take screenshot of current Notion state
                screenshot_b64 = self.client.take_screenshot(use_cache=False)

                # Build prompt based on focus area
                focus_hint = ""
                if focus_area:
                    focus_hint = f"\nFOCUS: Pay special attention to {focus_area}."

                prompt = f"""Analyze this Notion page screenshot and extract all visible content.

Look at the main content area or right-hand panel (if a page is open in a sidebar).
Ignore navigation elements, sidebars on the left, and top chrome.
{focus_hint}

Extract and return a JSON object with:
{{
  "page_title": "Title of the page/entry",
  "sections": {{
    "Section Name": ["content line 1", "content line 2", ...],
    "Another Section": ["content..."]
  }},
  "properties": {{
    "Property Name": "value",
    ...
  }},
  "lists": [
    {{"type": "bullet/numbered", "items": ["item 1", "item 2"]}},
    ...
  ],
  "full_text": "Complete plain text of main content area"
}}

Guidelines:
- Preserve the original structure and formatting
- Group content by visible sections/headings
- Extract lists, properties, and structured data separately
- For properties (like tags, dates, metadata), include them in the properties object
- The full_text should contain everything from the main content, excluding chrome/navigation
- If you see a list of items (like ingredients or steps), put them in lists array

Return ONLY valid JSON, no markdown formatting."""

                # Call Claude vision
                response = self.client.client.messages.create(
                    model=self.client.model,
                    max_tokens=4000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": screenshot_b64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    temperature=0
                )

                # Extract response text
                response_text = response.content[0].text.strip()

                # Parse JSON (handle markdown code blocks)
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()

                try:
                    extracted_data = json.loads(response_text)

                    return json.dumps({
                        "status": "success",
                        "extraction_method": "vision",
                        "focus_area": focus_area,
                        "data": extracted_data
                    }, indent=2)

                except json.JSONDecodeError as e:
                    # Return raw text if JSON parsing fails
                    return json.dumps({
                        "status": "partial_success",
                        "extraction_method": "vision",
                        "message": "Vision extraction succeeded but JSON parsing failed",
                        "raw_response": response_text,
                        "parse_error": str(e)
                    }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Vision extraction failed: {e}"
            }, indent=2)


def get_notion_tools(client: object, state: AgentState) -> list:
    """Get Notion-specific tools.

    Args:
        client: AnthropicComputerClient instance (must support vision)
        state: AgentState instance

    Returns:
        List of Notion-specific LangChain tools
    """
    # Only return tools if client supports vision
    if not hasattr(client, '_click_element'):
        return []

    return [
        NotionOpenPageTool(client=client, state=state),
        NotionClosePageTool(client=client, state=state),
        NotionVisionExtractTool(client=client, state=state),
    ]
