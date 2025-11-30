"""Anthropic Computer Use API client for screen interaction."""

import os
import base64
import time
from typing import Optional, Tuple, Dict, Any, Literal
from pathlib import Path
import tempfile

import Quartz
import Cocoa
from anthropic import Anthropic


ActionType = Literal["key", "type", "mouse_move", "left_click", "left_click_drag", 
                      "right_click", "middle_click", "double_click", "screenshot", 
                      "cursor_position"]


class ComputerUseClient:
    """Client for Anthropic Computer Use API with macOS integration."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        display_num: int = 1,
        display_width: Optional[int] = None,
        display_height: Optional[int] = None,
    ):
        """Initialize the Computer Use client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            display_num: Display number (1-based, usually 1)
            display_width: Override display width (auto-detected if None)
            display_height: Override display height (auto-detected if None)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=self.api_key)
        self.display_num = display_num
        
        # Get display dimensions
        if display_width and display_height:
            self.width = display_width
            self.height = display_height
        else:
            self.width, self.height = self._get_display_dimensions()
    
    def _get_display_dimensions(self) -> Tuple[int, int]:
        """Get the dimensions of the main display.
        
        Returns:
            Tuple of (width, height) in pixels
        """
        try:
            # Get main display
            display_id = Quartz.CGMainDisplayID()
            
            # Get display mode
            mode = Quartz.CGDisplayCopyDisplayMode(display_id)
            
            # Get pixel dimensions
            width = Quartz.CGDisplayModeGetPixelWidth(mode)
            height = Quartz.CGDisplayModeGetPixelHeight(mode)
            
            return (int(width), int(height))
        except Exception:
            # Fallback to reasonable defaults
            return (1920, 1080)
    
    def take_screenshot(self) -> str:
        """Capture a screenshot of the entire screen.
        
        Returns:
            Base64-encoded PNG image
        """
        try:
            # Capture entire screen
            display_id = Quartz.CGMainDisplayID()
            
            # Create image of entire display
            image_ref = Quartz.CGDisplayCreateImage(display_id)
            
            if not image_ref:
                raise RuntimeError("Failed to capture screenshot")
            
            # Convert to NSImage
            ns_image = Cocoa.NSImage.alloc().initWithCGImage_size_(
                image_ref, Cocoa.NSZeroSize
            )
            
            # Convert to PNG data
            tiff_data = ns_image.TIFFRepresentation()
            bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(tiff_data)
            png_data = bitmap.representationUsingType_properties_(
                Cocoa.NSBitmapImageFileTypePNG, None
            )
            
            # Encode to base64
            b64_data = base64.b64encode(png_data.bytes()).decode('utf-8')
            
            return b64_data
            
        except Exception as e:
            raise RuntimeError(f"Screenshot capture failed: {e}")
    
    def execute_action(
        self,
        action: ActionType,
        text: Optional[str] = None,
        coordinate: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Execute a computer action using macOS APIs.
        
        Args:
            action: Type of action to perform
            text: Text to type (for "type" action)
            coordinate: (x, y) coordinate (for mouse actions)
            
        Returns:
            Dict with action result
        """
        if action == "screenshot":
            screenshot_b64 = self.take_screenshot()
            return {
                "action": "screenshot",
                "base64_image": screenshot_b64
            }
        
        elif action == "cursor_position":
            # Get current mouse position
            event = Quartz.CGEventCreate(None)
            location = Quartz.CGEventGetLocation(event)
            return {
                "action": "cursor_position",
                "x": int(location.x),
                "y": int(location.y)
            }
        
        elif action == "mouse_move":
            if not coordinate:
                raise ValueError("coordinate required for mouse_move")
            self._mouse_move(coordinate[0], coordinate[1])
            return {
                "action": "mouse_move",
                "x": coordinate[0],
                "y": coordinate[1]
            }
        
        elif action == "left_click":
            if coordinate:
                self._mouse_move(coordinate[0], coordinate[1])
                time.sleep(0.1)
            self._mouse_click(left=True)
            return {
                "action": "left_click",
                "coordinate": coordinate
            }
        
        elif action == "right_click":
            if coordinate:
                self._mouse_move(coordinate[0], coordinate[1])
                time.sleep(0.1)
            self._mouse_click(left=False)
            return {
                "action": "right_click",
                "coordinate": coordinate
            }
        
        elif action == "double_click":
            if coordinate:
                self._mouse_move(coordinate[0], coordinate[1])
                time.sleep(0.1)
            self._mouse_click(left=True, double=True)
            return {
                "action": "double_click",
                "coordinate": coordinate
            }
        
        elif action == "type":
            if not text:
                raise ValueError("text required for type action")
            self._type_text(text)
            return {
                "action": "type",
                "text": text
            }
        
        elif action == "key":
            if not text:
                raise ValueError("text required for key action")
            self._press_key(text)
            return {
                "action": "key",
                "key": text
            }
        
        else:
            raise ValueError(f"Unsupported action: {action}")
    
    def _mouse_move(self, x: int, y: int):
        """Move mouse to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        # Create mouse move event
        move_event = Quartz.CGEventCreateMouseEvent(
            None,
            Quartz.kCGEventMouseMoved,
            (x, y),
            0
        )
        
        # Post the event
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_event)
    
    def _mouse_click(self, left: bool = True, double: bool = False):
        """Perform a mouse click at current position.
        
        Args:
            left: If True, left click; if False, right click
            double: If True, perform double click
        """
        # Get current mouse position
        event = Quartz.CGEventCreate(None)
        location = Quartz.CGEventGetLocation(event)
        
        if left:
            down_type = Quartz.kCGEventLeftMouseDown
            up_type = Quartz.kCGEventLeftMouseUp
            button = Quartz.kCGMouseButtonLeft
        else:
            down_type = Quartz.kCGEventRightMouseDown
            up_type = Quartz.kCGEventRightMouseUp
            button = Quartz.kCGMouseButtonRight
        
        # Create and post mouse down event
        down_event = Quartz.CGEventCreateMouseEvent(
            None, down_type, location, button
        )
        
        if double:
            Quartz.CGEventSetIntegerValueField(
                down_event,
                Quartz.kCGMouseEventClickState,
                2
            )
        
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, down_event)
        time.sleep(0.05)
        
        # Create and post mouse up event
        up_event = Quartz.CGEventCreateMouseEvent(
            None, up_type, location, button
        )
        
        if double:
            Quartz.CGEventSetIntegerValueField(
                up_event,
                Quartz.kCGMouseEventClickState,
                2
            )
        
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, up_event)
    
    def _type_text(self, text: str):
        """Type text using keyboard events.
        
        Args:
            text: Text to type
        """
        # Use AppleScript for reliable text input
        from Cocoa import NSAppleScript
        
        # Escape single quotes in text
        escaped_text = text.replace("'", "\\'")
        
        script = f'''
        tell application "System Events"
            keystroke "{escaped_text}"
        end tell
        '''
        
        ns_script = NSAppleScript.alloc().initWithSource_(script)
        result, error = ns_script.executeAndReturnError_(None)
        
        if error:
            raise RuntimeError(f"Failed to type text: {error}")
    
    def _press_key(self, key: str):
        """Press a special key.
        
        Args:
            key: Key name (e.g., "Return", "Tab", "Escape")
        """
        from Cocoa import NSAppleScript
        
        # Map common key names to AppleScript key codes
        key_map = {
            "Return": "return",
            "Enter": "return",
            "Tab": "tab",
            "Escape": "escape",
            "Delete": "delete",
            "Backspace": "delete",
            "Up": "up arrow",
            "Down": "down arrow",
            "Left": "left arrow",
            "Right": "right arrow",
            "Space": "space",
        }
        
        apple_key = key_map.get(key, key.lower())
        
        script = f'''
        tell application "System Events"
            key code (ASCII character "{apple_key}")
        end tell
        '''
        
        # For arrow keys and special keys, use keystroke
        if apple_key in ["up arrow", "down arrow", "left arrow", "right arrow", 
                         "return", "tab", "escape", "delete", "space"]:
            script = f'''
            tell application "System Events"
                keystroke "{apple_key}"
            end tell
            '''
        
        ns_script = NSAppleScript.alloc().initWithSource_(script)
        result, error = ns_script.executeAndReturnError_(None)
        
        if error:
            raise RuntimeError(f"Failed to press key: {error}")
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Get information about the screen.
        
        Returns:
            Dict with width, height, and display info
        """
        return {
            "width": self.width,
            "height": self.height,
            "display_num": self.display_num
        }

