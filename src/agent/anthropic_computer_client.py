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
        model: str = "claude-sonnet-4-20250514",
        display_width: Optional[int] = None,
        display_height: Optional[int] = None,
        display_num: int = 1,
        verbose: bool = False,
        verbosity: VerbosityLevel = "default",
    ):
        """Initialize Anthropic Computer Use client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (default: claude-sonnet-4-20250514 for better vision)
            display_width: Display width in pixels (auto-detected if None)
            display_height: Display height in pixels (auto-detected if None)
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
        self.display_num = display_num
        self.verbosity = verbosity
        self.verbose = verbosity == "verbose"

        # Auto-detect display dimensions and Retina scaling
        self._detect_display_dimensions(display_width, display_height)

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
            print(f"  Display: {self.display_width}x{self.display_height}")

    def _detect_display_dimensions(self, width: Optional[int], height: Optional[int]):
        """Detect display dimensions and Retina scaling factor.

        On Retina displays, screenshots are captured at 2x resolution,
        but mouse coordinates use the logical (1x) resolution.
        """
        import Quartz
        import Cocoa

        # Get display info
        online_displays = Quartz.CGGetOnlineDisplayList(32, None, None)[1]
        if self.display_num > len(online_displays):
            display_id = online_displays[0]
        else:
            display_id = online_displays[self.display_num - 1]

        # Get logical size (for mouse coordinates)
        bounds = Quartz.CGDisplayBounds(display_id)
        self.logical_width = int(bounds.size.width)
        self.logical_height = int(bounds.size.height)

        # Get actual screenshot pixel size by taking a test screenshot
        # CGDisplayPixelsWide returns logical pixels, not actual screenshot resolution
        image = Quartz.CGDisplayCreateImage(display_id)
        if image:
            self.pixel_width = Quartz.CGImageGetWidth(image)
            self.pixel_height = Quartz.CGImageGetHeight(image)
        else:
            # Fallback to display reported pixels
            self.pixel_width = Quartz.CGDisplayPixelsWide(display_id)
            self.pixel_height = Quartz.CGDisplayPixelsHigh(display_id)

        # Calculate Retina scale factor (screenshot pixels / logical pixels)
        self.retina_scale = self.pixel_width / self.logical_width if self.logical_width else 1.0

        # For Claude vision analysis, use the screenshot dimensions (what Claude sees)
        # Override with user-provided values if specified
        self.display_width = width if width else self.pixel_width
        self.display_height = height if height else self.pixel_height

        # Claude Vision coordinate scaling
        # Anthropic API resizes images to ~1400px width before sending to Claude.
        # Claude returns coordinates in this scaled-down space.
        # We store the last known Claude vision dimensions to scale coordinates back.
        self._claude_vision_width: Optional[int] = None
        self._claude_vision_height: Optional[int] = None

        if self.verbose:
            print(f"  Display: logical={self.logical_width}x{self.logical_height}, "
                  f"screenshot={self.pixel_width}x{self.pixel_height}, scale={self.retina_scale}")

    def _scale_coordinates_for_click(self, x: int, y: int) -> Tuple[int, int]:
        """Scale coordinates from screenshot space to logical screen space.

        Claude analyzes screenshots at pixel resolution (e.g., 2880x1800),
        but mouse clicks happen at logical resolution (e.g., 1440x900).
        """
        scaled_x = int(x / self.retina_scale)
        scaled_y = int(y / self.retina_scale)
        return scaled_x, scaled_y

    def _scale_claude_vision_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Scale coordinates from Claude Vision space to screenshot space.

        Anthropic API resizes images before sending to Claude. Through calibration testing,
        we found that Claude sees images at approximately 1389x862 for a 2880x1800 screenshot
        (roughly 48% of original size, or ~1400px width).

        IMPORTANT: Claude's self-reported image dimensions are unreliable and vary between
        calls. We use a fixed scaling factor based on calibration testing instead.

        Args:
            x, y: Coordinates from Claude Vision (in Claude's scaled image space)

        Returns:
            Coordinates in actual screenshot pixel space
        """
        # Fixed Claude Vision dimensions based on calibration testing
        # Anthropic resizes to approximately 1389x862 for a 2880x1800 image
        # This is roughly 48.2% of original size (max dimension ~1400px)
        CLAUDE_VISION_MAX_WIDTH = 1389
        CLAUDE_VISION_MAX_HEIGHT = 862

        # Calculate what Claude actually sees based on our screenshot aspect ratio
        screenshot_aspect = self.pixel_width / self.pixel_height

        if screenshot_aspect > (CLAUDE_VISION_MAX_WIDTH / CLAUDE_VISION_MAX_HEIGHT):
            # Width-limited
            claude_width = CLAUDE_VISION_MAX_WIDTH
            claude_height = int(CLAUDE_VISION_MAX_WIDTH / screenshot_aspect)
        else:
            # Height-limited
            claude_height = CLAUDE_VISION_MAX_HEIGHT
            claude_width = int(CLAUDE_VISION_MAX_HEIGHT * screenshot_aspect)

        scale_x = self.pixel_width / claude_width
        scale_y = self.pixel_height / claude_height

        scaled_x = int(x * scale_x)
        scaled_y = int(y * scale_y)

        if self.verbose:
            print(f"  Vision coord scaling: ({x}, {y}) -> ({scaled_x}, {scaled_y}) [Claude sees ~{claude_width}x{claude_height}, scale: {scale_x:.2f}x{scale_y:.2f}]")

        return scaled_x, scaled_y

    def _detect_claude_vision_dimensions(self, screenshot_b64: str) -> None:
        """Ask Claude what image dimensions it sees to calibrate coordinate scaling.

        This should be called periodically to ensure accurate coordinate mapping.
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{
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
                            "text": "What are the pixel dimensions of this image? Reply ONLY with: SIZE: (width, height)"
                        }
                    ]
                }],
                temperature=0
            )

            import re
            response_text = response.content[0].text
            match = re.search(r'SIZE:\s*\((\d+),\s*(\d+)\)', response_text)
            if match:
                self._claude_vision_width = int(match.group(1))
                self._claude_vision_height = int(match.group(2))
                if self.verbose:
                    print(f"  Claude Vision dimensions: {self._claude_vision_width}x{self._claude_vision_height}")
        except Exception as e:
            if self.verbose:
                print(f"  Failed to detect Claude Vision dimensions: {e}")

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

            elif action == "mouse_move":
                if coordinate:
                    result = self._mouse_move(coordinate[0], coordinate[1])
                elif text:
                    result = self._mouse_move_to_element(text)
                else:
                    return ActionResult(
                        success=False,
                        data={},
                        error="mouse_move action requires either coordinate or text",
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

        This method:
        1. Takes a screenshot
        2. Asks Claude to find the element (Claude sees a scaled-down image)
        3. Scales Claude's coordinates back to screenshot space
        4. Scales from screenshot space to logical space for clicking
        5. Executes the click

        Args:
            element_text: Text description of element to click

        Returns:
            Result dictionary with success status and coordinates
        """
        try:
            # Take screenshot
            screenshot_b64 = self.take_screenshot()

            # Calibrate Claude Vision dimensions if not yet known
            if not self._claude_vision_width:
                self._detect_claude_vision_dimensions(screenshot_b64)

            # Ask Claude to find the element - strict format required
            prompt = f"""Find "{element_text}" in this screenshot.

Respond with ONLY: COORDINATES: (x, y)
Or if not found: NOT_FOUND

Example: COORDINATES: (500, 300)

No other text."""

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
                # These are Claude Vision coordinates (in scaled-down image space)
                claude_x = int(coord_match.group(1))
                claude_y = int(coord_match.group(2))

                if self.verbose:
                    print(f"  Claude Vision coordinates: ({claude_x}, {claude_y})")

                # Scale from Claude Vision space to screenshot space
                screenshot_x, screenshot_y = self._scale_claude_vision_coordinates(claude_x, claude_y)

                if self.verbose:
                    print(f"  Screenshot coordinates: ({screenshot_x}, {screenshot_y})")

                # Validate coordinates are within screen bounds (screenshot space)
                if 0 <= screenshot_x <= self.pixel_width and 0 <= screenshot_y <= self.pixel_height:
                    # Scale from screenshot space to logical screen space for clicking
                    click_x, click_y = self._scale_coordinates_for_click(screenshot_x, screenshot_y)

                    if self.verbose:
                        print(f"  Click coordinates: ({click_x}, {click_y})")

                    # Actually perform the click at scaled coordinates
                    self._execute_click(click_x, click_y)

                    return {
                        "success": True,
                        "action": "left_click",
                        "claude_coordinate": [claude_x, claude_y],
                        "screenshot_coordinate": [screenshot_x, screenshot_y],
                        "click_coordinate": [click_x, click_y],
                        "element": element_text
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Coordinates ({screenshot_x}, {screenshot_y}) out of bounds"
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

    def _mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        """Move mouse to coordinates (for hovering).

        Args:
            x, y: Screen coordinates in screenshot space

        Returns:
            Result dictionary
        """
        try:
            # Scale coordinates from screenshot space to logical screen space
            move_x, move_y = self._scale_coordinates_for_click(x, y)

            if self.verbose:
                print(f"  Moving mouse: ({x}, {y}) -> ({move_x}, {move_y})")

            self._execute_mouse_move(move_x, move_y)
            return {
                "success": True,
                "action": "mouse_move",
                "coordinate": [x, y],
                "scaled_coordinate": [move_x, move_y]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _mouse_move_to_element(self, element_text: str) -> Dict[str, Any]:
        """Move mouse to an element by text description (for hovering).

        This method:
        1. Takes a screenshot
        2. Asks Claude to find the element (Claude sees a scaled-down image)
        3. Scales Claude's coordinates back to screenshot space
        4. Scales from screenshot space to logical space for mouse movement

        Args:
            element_text: Text description of element to hover over

        Returns:
            Result dictionary with success status and coordinates
        """
        try:
            # Take screenshot
            screenshot_b64 = self.take_screenshot()

            # Calibrate Claude Vision dimensions if not yet known
            if not self._claude_vision_width:
                self._detect_claude_vision_dimensions(screenshot_b64)

            # Ask Claude to find the element - strict format required
            prompt = f"""Find "{element_text}" in this screenshot.

Respond with ONLY: COORDINATES: (x, y)
Or if not found: NOT_FOUND

Example: COORDINATES: (500, 300)

No other text."""

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
                temperature=0
            )

            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            if self.verbose:
                print(f"  Claude response: {response_text}")

            if "NOT_FOUND" in response_text:
                return {
                    "success": False,
                    "error": f"Element '{element_text}' not found in screenshot"
                }

            # Parse coordinates
            import re
            coord_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response_text)
            if not coord_match:
                coord_match = re.search(r'\((\d+),\s*(\d+)\)', response_text)

            if coord_match:
                # These are Claude Vision coordinates (in scaled-down image space)
                claude_x = int(coord_match.group(1))
                claude_y = int(coord_match.group(2))

                if self.verbose:
                    print(f"  Claude Vision coordinates: ({claude_x}, {claude_y})")

                # Scale from Claude Vision space to screenshot space
                screenshot_x, screenshot_y = self._scale_claude_vision_coordinates(claude_x, claude_y)

                if self.verbose:
                    print(f"  Screenshot coordinates: ({screenshot_x}, {screenshot_y})")

                if 0 <= screenshot_x <= self.pixel_width and 0 <= screenshot_y <= self.pixel_height:
                    # Scale from screenshot space to logical space and move
                    move_x, move_y = self._scale_coordinates_for_click(screenshot_x, screenshot_y)

                    if self.verbose:
                        print(f"  Move coordinates: ({move_x}, {move_y})")

                    self._execute_mouse_move(move_x, move_y)

                    return {
                        "success": True,
                        "action": "mouse_move",
                        "claude_coordinate": [claude_x, claude_y],
                        "screenshot_coordinate": [screenshot_x, screenshot_y],
                        "move_coordinate": [move_x, move_y],
                        "element": element_text
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Coordinates ({screenshot_x}, {screenshot_y}) out of bounds"
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

    def _execute_mouse_move(self, x: int, y: int):
        """Execute a mouse move using system APIs.

        Args:
            x, y: Screen coordinates (in logical space)
        """
        import Quartz

        move_point = Quartz.CGPoint(x, y)
        move_event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventMouseMoved,
            move_point,
            Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_event)
        time.sleep(0.01)

    def hover_and_find_open_button(
        self,
        recipe_coords: Tuple[int, int],
        recipe_name: str,
        wait_time: float = 1.5
    ) -> Dict[str, Any]:
        """Hover over a recipe and find the Open button using vision.

        This is a helper method for the common pattern of:
        1. Hovering over a recipe/item
        2. Waiting for the Open button to appear
        3. Using vision to find and return the Open button coordinates

        Args:
            recipe_coords: (x, y) coordinates of the recipe in screenshot space
            recipe_name: Name of the recipe/item for context in vision prompt
            wait_time: Time to wait after hovering for button to appear (default: 1.5s)

        Returns:
            Dictionary with:
            - success: bool
            - open_button_coords: (x, y) if found, None otherwise
            - error: error message if failed
        """
        try:
            # Move mouse to recipe coordinates (hover)
            move_result = self._mouse_move(recipe_coords[0], recipe_coords[1])
            if not move_result.get("success", False):
                return {
                    "success": False,
                    "error": "Failed to move mouse to recipe coordinates"
                }

            # Wait for Open button to appear
            time.sleep(wait_time)

            # Take fresh screenshot
            screenshot_b64 = self.take_screenshot(use_cache=False)

            # Use vision to find Open button
            prompt = f"""Analyze this Notion database screenshot.

I just hovered over "{recipe_name}" at coordinates ({recipe_coords[0]}, {recipe_coords[1]}).
The mouse cursor is currently positioned over this item.

TASK: Find the "OPEN" button that should have appeared after hovering.
The OPEN button should be:
- On the SAME horizontal line as "{recipe_name}" (y-coordinate within 50 pixels of {recipe_coords[1]})
- Usually to the LEFT of the item name (x-coordinate less than {recipe_coords[0]})
- A small button with text "OPEN" or an open icon
- Visible only when hovering over the row

Provide the EXACT pixel coordinates of the center of the OPEN button in this format:
COORDINATES: (x, y)

If you cannot find an OPEN button on the same horizontal line, respond with: NOT_FOUND"""

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
                temperature=0
            )

            response_text = ""
            for block in response.content:
                if block.type == "text":
                    response_text += block.text

            # Parse coordinates
            import re
            coord_match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response_text)

            if coord_match:
                # These are Claude Vision coordinates (in scaled-down image space)
                claude_x = int(coord_match.group(1))
                claude_y = int(coord_match.group(2))

                # Scale from Claude Vision space to screenshot space
                screenshot_x, screenshot_y = self._scale_claude_vision_coordinates(claude_x, claude_y)

                # Validate coordinates
                if 0 <= screenshot_x <= self.pixel_width and 0 <= screenshot_y <= self.pixel_height:
                    return {
                        "success": True,
                        "open_button_coords": (screenshot_x, screenshot_y),
                        "claude_coords": (claude_x, claude_y),
                        "recipe_coords": recipe_coords,
                        "recipe_name": recipe_name
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Open button coordinates ({screenshot_x}, {screenshot_y}) out of bounds"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Could not find Open button for '{recipe_name}' after hovering",
                    "vision_response": response_text
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to hover and find Open button: {e}"
            }

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
            # Small delay before key presses to ensure the target app has focus
            # and UI has settled (helps with actions like closing panels in Notion).
            time.sleep(0.5)

            import subprocess

            # Map key names to AppleScript key codes for non-printable keys
            key_code_map = {
                "Return": 36,
                "Enter": 36,
                "Tab": 48,
                "Escape": 53,
                "Esc": 53,
                "Space": 49,
                "Delete": 51,
                "Backspace": 51,
                "Left": 123,
                "Right": 124,
                "Down": 125,
                "Up": 126,
            }

            script: str

            if key in key_code_map:
                # Use key code for special keys
                code = key_code_map[key]
                script = f'''
                tell application "System Events"
                    key code {code}
                end tell
                '''
            else:
                # For single printable characters, use keystroke
                # Normalize common casing (e.g., "a", "A")
                if len(key) == 1:
                    to_type = key
                else:
                    # Fallback: use first character
                    to_type = key[0]

                # Escape characters for AppleScript string
                escaped = to_type.replace("\\", "\\\\").replace('"', '\\"')

                script = f'''
                tell application "System Events"
                    keystroke "{escaped}"
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
