"""Anthropic Computer Use client with integrated vision and control.

This module provides a wrapper around Anthropic's Computer Use tool,
which provides unified vision analysis and coordinate-based actions.
"""

import os
import base64
import time
from typing import Optional, Dict, Any, List, Literal, Tuple
from dataclasses import dataclass

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


ActionType = Literal[
    "key", "type", "mouse_move", "left_click", "left_click_drag",
    "right_click", "middle_click", "screenshot", "cursor_position",
    "switch_desktop"
]

VerbosityLevel = Literal["silent", "minimal", "default", "verbose"]


@dataclass
class ActionResult:
    """Result from an action execution."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    latency_ms: float = 0


class AnthropicComputerClient:
    """Client for Anthropic's Computer Use tool."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
        display_width: int = 1920,
        display_height: int = 1080,
        display_num: int = 1,
        verbose: bool = False,
        verbosity: VerbosityLevel = "default",
    ):
        """Initialize Anthropic Computer Use client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-3-5-sonnet-20241022)
            display_width: Display width in pixels
            display_height: Display height in pixels
            display_num: Display number (1-based)
            verbose: Enable verbose logging (deprecated, use verbosity)
            verbosity: Verbosity level (silent, minimal, default, verbose)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        # Handle deprecated verbose parameter
        if verbose and verbosity == "default":
            verbosity = "verbose"

        self.model = model
        self.display_width = display_width
        self.display_height = display_height
        self.display_num = display_num
        self.verbosity = verbosity
        self.verbose = verbosity == "verbose"

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)

        # Screenshot caching for performance
        self._screenshot_cache: Optional[str] = None
        self._screenshot_cache_time: float = 0
        self._screenshot_cache_ttl: float = 2.0  # Cache for 2 seconds

        # Conversation history for context
        self._conversation: List[Dict[str, Any]] = []

        if self.verbose:
            print(f"✓ Anthropic Computer Use client initialized")
            print(f"  Model: {self.model}")
            print(f"  Display: {display_width}x{display_height}")

    def take_screenshot(self, use_cache: bool = True) -> str:
        """Capture screenshot using system tools.

        Args:
            use_cache: Use cached screenshot if available

        Returns:
            Base64-encoded PNG screenshot
        """
        # Check cache
        if use_cache and self._screenshot_cache:
            cache_age = time.time() - self._screenshot_cache_time
            if cache_age < self._screenshot_cache_ttl:
                if self.verbose:
                    print(f"💾 Using cached screenshot ({cache_age:.1f}s old)")
                return self._screenshot_cache

        # Capture new screenshot
        import Quartz
        import Cocoa

        # Get display by number
        online_displays = Quartz.CGGetOnlineDisplayList(32, None, None)[1]
        if self.display_num > len(online_displays):
            display_id = online_displays[0]
        else:
            display_id = online_displays[self.display_num - 1]

        # Capture screenshot
        image = Quartz.CGDisplayCreateImage(display_id)
        if not image:
            raise Exception("Failed to capture screenshot")

        # Convert to NSImage
        width = Quartz.CGImageGetWidth(image)
        height = Quartz.CGImageGetHeight(image)
        ns_image = Cocoa.NSImage.alloc().initWithCGImage_size_(
            image,
            Cocoa.NSMakeSize(width, height)
        )

        # Convert to PNG data
        tiff_data = ns_image.TIFFRepresentation()
        bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(tiff_data)
        png_data = bitmap.representationUsingType_properties_(
            Cocoa.NSBitmapImageFileTypePNG,
            None
        )

        # Encode as base64
        screenshot_b64 = base64.b64encode(bytes(png_data)).decode('utf-8')

        # Update cache
        self._screenshot_cache = screenshot_b64
        self._screenshot_cache_time = time.time()

        return screenshot_b64

    def invalidate_screenshot_cache(self):
        """Invalidate cached screenshot to force fresh capture."""
        self._screenshot_cache = None
        self._screenshot_cache_time = 0

    def execute_action(
        self,
        action: str,
        text: Optional[str] = None,
        coordinate: Optional[Tuple[int, int]] = None
    ) -> ActionResult:
        """Execute a computer use action.

        Args:
            action: Action type (click, type, screenshot, etc.)
            text: Text for type actions or element to click
            coordinate: (x, y) coordinates for click actions

        Returns:
            ActionResult with success status and data
        """
        start_time = time.time()

        try:
            # Build the action description
            if action == "screenshot":
                screenshot_b64 = self.take_screenshot()
                description = self._analyze_screenshot(screenshot_b64)

                latency = (time.time() - start_time) * 1000
                return ActionResult(
                    success=True,
                    data={
                        "screenshot": screenshot_b64,
                        "description": description,
                        "width": self.display_width,
                        "height": self.display_height
                    },
                    latency_ms=latency
                )

            elif action in ("left_click", "click"):
                if coordinate:
                    result = self._click_coordinate(coordinate[0], coordinate[1])
                elif text:
                    result = self._click_element(text)
                else:
                    return ActionResult(
                        success=False,
                        data={},
                        error="Click action requires either coordinate or text",
                        latency_ms=(time.time() - start_time) * 1000
                    )

                latency = (time.time() - start_time) * 1000
                return ActionResult(
                    success=result.get("success", False),
                    data=result,
                    latency_ms=latency
                )

            elif action == "type":
                if not text:
                    return ActionResult(
                        success=False,
                        data={},
                        error="Type action requires text",
                        latency_ms=(time.time() - start_time) * 1000
                    )

                result = self._type_text(text)
                latency = (time.time() - start_time) * 1000
                return ActionResult(
                    success=result.get("success", False),
                    data=result,
                    latency_ms=latency
                )

            elif action == "key":
                if not text:
                    return ActionResult(
                        success=False,
                        data={},
                        error="Key action requires key name",
                        latency_ms=(time.time() - start_time) * 1000
                    )

                result = self._press_key(text)
                latency = (time.time() - start_time) * 1000
                return ActionResult(
                    success=result.get("success", False),
                    data=result,
                    latency_ms=latency
                )

            elif action == "switch_desktop":
                if not text:
                    return ActionResult(
                        success=False,
                        data={},
                        error="Switch desktop requires application name",
                        latency_ms=(time.time() - start_time) * 1000
                    )

                result = self._switch_desktop(text)
                latency = (time.time() - start_time) * 1000
                return ActionResult(
                    success=result.get("success", False),
                    data=result,
                    error=result.get("error"),
                    latency_ms=latency
                )

            else:
                return ActionResult(
                    success=False,
                    data={},
                    error=f"Unsupported action: {action}",
                    latency_ms=(time.time() - start_time) * 1000
                )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ActionResult(
                success=False,
                data={},
                error=str(e),
                latency_ms=latency
            )

    def _analyze_screenshot(self, screenshot_b64: str) -> str:
        """Analyze screenshot using Claude's vision capabilities.

        Enhanced prompt to get precise coordinates like Computer Use would provide.

        Args:
            screenshot_b64: Base64-encoded PNG screenshot

        Returns:
            Detailed description of screen contents with coordinates
        """
        try:
            # Enhanced prompt for better coordinate detection
            prompt = f"""Analyze this screenshot in detail. You are helping me understand what's on screen so I can interact with it.

SCREEN SIZE: {self.display_width}x{self.display_height} pixels

TASK: List ALL visible UI elements with their PRECISE pixel coordinates.

For each element, provide:
1. Element type (button, link, text, menu, etc.)
2. Visible text content
3. EXACT pixel coordinates (x, y) of the element's center
4. Location description (top-left, center, etc.)

Format your response like this:
- [TYPE] "Text" at (x, y) - location description

Examples:
- [LINK] "Velouté Potimarron" at (250, 180) - left sidebar
- [BUTTON] "Share" at (1150, 50) - top right
- [TEXT] "Recipes | All Meals" at (400, 30) - title bar

Include EVERYTHING you can see: buttons, links, text, menus, tabs, sidebars, etc.
Be PRECISE with coordinates - they will be used for clicking."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,  # More tokens for detailed analysis
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
                temperature=0  # Deterministic for better consistency
            )

            # Extract text from response
            text_content = ""
            for block in response.content:
                if block.type == "text":
                    text_content += block.text

            return text_content

        except Exception as e:
            return f"Screenshot analysis failed: {e}"

    def _click_element(self, element_text: str) -> Dict[str, Any]:
        """Click on an element by text description using Claude vision.

        Since we're using Haiku (no Computer Use tool), we:
        1. Ask Claude to analyze the screenshot and find the element
        2. Parse coordinates from Claude's response
        3. Click using system APIs

        This mimics Anthropic Computer Use behavior.

        Args:
            element_text: Text description of element to click

        Returns:
            Result dictionary with success status and coordinates
        """
        try:
            # Take screenshot
            screenshot_b64 = self.take_screenshot()

            # Ask Claude to find the element and provide coordinates
            # This mimics what Computer Use would do internally
            prompt = f"""You are analyzing a screenshot to help me click on a specific element.

TASK: Find '{element_text}' in this screenshot and tell me its EXACT pixel coordinates.

INSTRUCTIONS:
1. Look for text that matches or contains '{element_text}'
2. Identify the center point of that element
3. Provide coordinates in this EXACT format: COORDINATES: (x, y)
4. X and Y must be absolute pixel positions on a {self.display_width}x{self.display_height} screen
5. Be precise - the coordinates will be used for clicking

IMPORTANT:
- Respond ONLY with the coordinates line, nothing else
- Format: COORDINATES: (x, y)
- Example: COORDINATES: (450, 320)

If you cannot find '{element_text}', respond with: NOT_FOUND"""

            response = self.client.messages.create(
                model=self.model,
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
                ],
                temperature=0  # Deterministic for coordinates
            )

            # Extract text response
            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            if self.verbose:
                print(f"  Claude response: {response_text}")

            # Parse coordinates from response
            if "NOT_FOUND" in response_text:
                return {
                    "success": False,
                    "error": f"Element '{element_text}' not found in screenshot"
                }

            # Extract coordinates using regex
            import re
            coord_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response_text)

            if not coord_match:
                # Try alternative formats
                coord_match = re.search(r'\((\d+),\s*(\d+)\)', response_text)

            if coord_match:
                x = int(coord_match.group(1))
                y = int(coord_match.group(2))

                if self.verbose:
                    print(f"  Parsed coordinates: ({x}, {y})")

                # Validate coordinates are within screen bounds
                if 0 <= x <= self.display_width and 0 <= y <= self.display_height:
                    # Actually perform the click
                    self._execute_click(x, y)

                    return {
                        "success": True,
                        "action": "left_click",
                        "coordinate": [x, y],
                        "element": element_text
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Coordinates ({x}, {y}) out of bounds"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Could not parse coordinates from response: {response_text}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _click_coordinate(self, x: int, y: int) -> Dict[str, Any]:
        """Click at specific coordinates.

        Args:
            x, y: Screen coordinates

        Returns:
            Result dictionary
        """
        try:
            self._execute_click(x, y)
            return {
                "success": True,
                "action": "left_click",
                "coordinate": [x, y]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_click(self, x: int, y: int):
        """Execute a mouse click at coordinates using system APIs.

        Args:
            x, y: Screen coordinates
        """
        import Quartz

        click_point = Quartz.CGPoint(x, y)

        # Mouse down
        down_event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseDown,
            click_point,
            Quartz.kCGMouseButtonLeft
        )

        # Mouse up
        up_event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventLeftMouseUp,
            click_point,
            Quartz.kCGMouseButtonLeft
        )

        # Post events
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
        time.sleep(0.02)  # Small delay between down and up
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)
        time.sleep(0.01)  # Small delay after click

    def _type_text(self, text: str) -> Dict[str, Any]:
        """Type text using system APIs.

        Args:
            text: Text to type

        Returns:
            Result dictionary
        """
        try:
            import subprocess

            # Use AppleScript for reliable text input
            # Escape single quotes in text
            escaped_text = text.replace("'", "'\\''")

            script = f'''
            tell application "System Events"
                keystroke "{escaped_text}"
            end tell
            '''

            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True
            )

            return {
                "success": True,
                "action": "type",
                "text": text
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _press_key(self, key: str) -> Dict[str, Any]:
        """Press a special key.

        Args:
            key: Key name (Return, Tab, Escape, etc.)

        Returns:
            Result dictionary
        """
        try:
            import subprocess

            # Map key names to AppleScript key codes
            key_map = {
                "Return": "return",
                "Enter": "return",
                "Tab": "tab",
                "Escape": "escape",
                "Space": "space",
                "Delete": "delete",
                "Backspace": "delete",
            }

            apple_key = key_map.get(key, key.lower())

            script = f'''
            tell application "System Events"
                key code using {{shift down, command down}}
            end tell
            '''

            if apple_key in key_map.values():
                script = f'''
                tell application "System Events"
                    keystroke {apple_key}
                end tell
                '''

            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True
            )

            return {
                "success": True,
                "action": "key",
                "key": key
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _switch_desktop(self, application_name: str) -> Dict[str, Any]:
        """Switch to desktop containing the specified application.

        Args:
            application_name: Name of the application to switch to

        Returns:
            Result dictionary
        """
        try:
            import subprocess

            # Use AppleScript to activate the application
            # macOS automatically switches to the desktop containing it
            script = f'''
            tell application "{application_name}"
                activate
            end tell
            '''

            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Give it a moment to switch
                time.sleep(0.5)

                return {
                    "success": True,
                    "action": "switch_desktop",
                    "application": application_name,
                    "message": f"Switched to desktop containing {application_name}"
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return {
                    "success": False,
                    "error": f"Failed to activate {application_name}: {error_msg}"
                }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Timeout activating {application_name}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
