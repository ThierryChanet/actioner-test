"""OpenAI Computer Use API client for screen interaction."""

import os
import base64
import time
from typing import Optional, Tuple, Dict, Any, Literal
from pathlib import Path
from functools import wraps

import Quartz
import Cocoa
from openai import OpenAI


ActionType = Literal["key", "type", "mouse_move", "left_click", "left_click_drag", 
                      "right_click", "middle_click", "double_click", "screenshot", 
                      "cursor_position", "switch_desktop"]

VerbosityLevel = Literal["silent", "minimal", "default", "verbose"]


def log_timing(action_name: str):
    """Decorator to log action timing."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(self, *args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Log timing if verbose
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"⏱️  {action_name} completed in {duration_ms:.1f}ms")
                
                # Log to performance logger
                try:
                    from ..output.performance_logger import log_action
                    context = {}
                    if args:
                        context['args'] = str(args)[:100]  # Truncate long args
                    log_action(action_name, duration_ms, success=True, context=context)
                except Exception:
                    pass  # Don't fail if logging fails
                
                # Add timing to result if it's a dict
                if isinstance(result, dict):
                    result['duration_ms'] = round(duration_ms, 1)
                return result
            except Exception as e:
                success = False
                duration_ms = (time.time() - start_time) * 1000
                if hasattr(self, 'verbose') and self.verbose:
                    print(f"⏱️  {action_name} failed after {duration_ms:.1f}ms")
                
                # Log failure
                try:
                    from ..output.performance_logger import log_action
                    log_action(action_name, duration_ms, success=False, context={"error": str(e)[:100]})
                except Exception:
                    pass
                raise
        return wrapper
    return decorator


class ComputerUseClient:
    """Client for OpenAI Computer Use API with macOS integration."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        display_num: int = 1,
        display_width: Optional[int] = None,
        display_height: Optional[int] = None,
        verbose: bool = False,
        verbosity: VerbosityLevel = "default",
    ):
        """Initialize the Computer Use client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            display_num: Display number (1-based, usually 1)
            display_width: Override display width (auto-detected if None)
            display_height: Override display height (auto-detected if None)
            verbose: Enable verbose logging with timing information (deprecated, use verbosity)
            verbosity: Verbosity level (silent, minimal, default, verbose)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        # Handle deprecated verbose parameter
        if verbose and verbosity == "default":
            verbosity = "verbose"
        
        self.client = OpenAI(api_key=self.api_key)
        self.display_num = display_num
        self.verbosity = verbosity
        self.verbose = verbosity == "verbose"
        
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
    
    @log_timing("screenshot")
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
    
    @log_timing("execute_action")
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
            Dict with action result including timing information
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
                time.sleep(0.01)  # Minimal delay for UI responsiveness
            self._mouse_click(left=True)
            return {
                "action": "left_click",
                "coordinate": coordinate
            }
        
        elif action == "right_click":
            if coordinate:
                self._mouse_move(coordinate[0], coordinate[1])
                time.sleep(0.01)  # Minimal delay for UI responsiveness
            self._mouse_click(left=False)
            return {
                "action": "right_click",
                "coordinate": coordinate
            }
        
        elif action == "double_click":
            if coordinate:
                self._mouse_move(coordinate[0], coordinate[1])
                time.sleep(0.01)  # Minimal delay for UI responsiveness
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
        
        elif action == "switch_desktop":
            if not text:
                raise ValueError("text (app_name) required for switch_desktop action")
            result = self.switch_desktop_by_app(text)
            return result
        
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
        time.sleep(0.02)  # Reduced delay for faster clicks
        
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
    
    def _get_current_desktop(self) -> Optional[int]:
        """Get the current desktop (Mission Control Space) number.
        
        Returns:
            Desktop number (1-based) or None if unable to determine
        """
        # Note: macOS doesn't expose Mission Control Space numbers directly via AppleScript
        # We'll use a workaround by tracking which desktop we're on through window positions
        # For now, return None and rely on the switch mechanism
        return None
    
    def _get_frontmost_application(self) -> Optional[str]:
        """Get the name of the currently frontmost application.
        
        Returns:
            Name of the frontmost application or None if unable to determine
        """
        from Cocoa import NSAppleScript
        
        script = '''
        tell application "System Events"
            return name of first process whose frontmost is true
        end tell
        '''
        
        ns_script = NSAppleScript.alloc().initWithSource_(script)
        result, error = ns_script.executeAndReturnError_(None)
        
        if error or not result:
            return None
        
        return str(result.stringValue()) if result else None
    
    def _find_desktop_by_app(self, app_name: str) -> Optional[int]:
        """Find which desktop contains a specific application.
        
        This method tries to activate the application directly, which is more reliable
        than checking for processes and windows. If activation succeeds, the app exists.
        
        Args:
            app_name: Name of the application to find (e.g., "Notion", "Safari")
            
        Returns:
            Desktop number (1-based) where app is found, or None if not found
        """
        from Cocoa import NSAppleScript
        
        # Escape single quotes in app name
        escaped_app = app_name.replace("'", "\\'")
        
        # Try activation directly - this is more reliable and handles case sensitivity better
        script = f'''
        try
            tell application "{escaped_app}" to activate
            return "found"
        on error
            return "not_found"
        end try
        '''
        
        ns_script = NSAppleScript.alloc().initWithSource_(script)
        result, error = ns_script.executeAndReturnError_(None)
        
        # If activation succeeded, the app exists
        if result and str(result.stringValue()) == "found":
            return 1  # Placeholder - app exists and was activated
        
        return None
    
    def _switch_to_desktop(self, desktop_num: int) -> bool:
        """Switch to a specific desktop by number.
        
        Note: macOS doesn't provide direct API access to switch desktops by number.
        This method uses keyboard shortcuts (Control + number) if configured,
        or Control + Arrow keys to navigate sequentially.
        
        Args:
            desktop_num: Desktop number to switch to (1-based)
            
        Returns:
            True if switch was attempted, False on error
        """
        from Cocoa import NSAppleScript
        
        # Try using Control + number shortcut (if user has it configured)
        script = f'''
        tell application "System Events"
            key code {17 + desktop_num} using control down
        end tell
        '''
        
        ns_script = NSAppleScript.alloc().initWithSource_(script)
        result, error = ns_script.executeAndReturnError_(None)
        
        if error:
            return False
        
        # Wait for desktop switch animation
        time.sleep(0.5)
        return True
    
    def _activate_application(self, app_name: str) -> bool:
        """Activate an application, bringing it to the foreground.
        
        This will automatically switch to the desktop where the app is located.
        
        Args:
            app_name: Name of the application to activate
            
        Returns:
            True if activation succeeded, False otherwise
        """
        from Cocoa import NSAppleScript
        
        # Escape single quotes in app name
        escaped_app = app_name.replace("'", "\\'")
        
        script = f'''
        tell application "{escaped_app}"
            activate
        end tell
        '''
        
        ns_script = NSAppleScript.alloc().initWithSource_(script)
        result, error = ns_script.executeAndReturnError_(None)
        
        if error:
            return False
        
        # Wait for app activation and desktop switch
        time.sleep(0.8)
        return True
    
    @log_timing("switch_desktop")
    def switch_desktop_by_app(self, app_name: str) -> Dict[str, Any]:
        """Switch to the desktop containing a specific application.
        
        This is the main public method for desktop switching. It finds the
        application and activates it, which automatically switches to its desktop.
        
        Args:
            app_name: Name of the application (e.g., "Notion", "Safari")
            
        Returns:
            Dict with status and information about the switch including timing
        """
        # Try to find and activate the app (this does both in one step now)
        desktop_num = self._find_desktop_by_app(app_name)
        
        if desktop_num is None:
            return {
                "success": False,
                "error": f"Application '{app_name}' not found or not running",
                "app_name": app_name
            }
        
        # App was found and activated, wait for desktop switch
        time.sleep(0.8)
        
        return {
            "success": True,
            "app_name": app_name,
            "message": f"Switched to desktop containing {app_name}"
        }
