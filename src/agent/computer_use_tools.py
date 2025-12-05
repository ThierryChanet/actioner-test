"""LangChain tools for OpenAI Computer Control Tools."""

import json
import time
from typing import Optional, Type, Tuple, Union
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from .state import AgentState
from .callbacks import show_progress

# Support both old and new clients for backward compatibility
try:
    from .responses_client import ResponsesAPIClient
    ComputerClient = Union[ResponsesAPIClient, 'ComputerUseClient']
except ImportError:
    from .computer_use_client import ComputerUseClient
    ComputerClient = ComputerUseClient


class ScreenshotInput(BaseModel):
    """Input for screenshot tool."""
    pass


class ScreenshotTool(BaseTool):
    """Tool for capturing screenshots of the screen and describing what's visible."""
    
    name: str = "take_screenshot"
    description: str = (
        "Capture a screenshot of the entire screen and analyze what's visible. "
        "This tool uses vision AI to describe everything on screen including: "
        "UI elements, text content, application windows, buttons, menus, and layout. "
        "Essential for understanding screen state before taking actions. "
        "Returns a detailed description of what's currently visible on the screen."
    )
    args_schema: Type[BaseModel] = ScreenshotInput
    
    client: object = Field(exclude=True)  # ResponsesAPIClient or ComputerUseClient
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Take a screenshot and describe it using vision AI."""
        show_progress("Capturing screenshot...")
        
        try:
            # Use caching for performance with ResponsesAPIClient
            use_cache = True
            if hasattr(self.client, 'take_screenshot'):
                screenshot_b64 = self.client.take_screenshot(use_cache=use_cache)
            else:
                # Fallback for old client (no caching)
                screenshot_b64 = self.client.take_screenshot()
            
            # Store the screenshot in state
            self.state.last_screenshot = screenshot_b64
            self.state.last_screenshot_timestamp = time.time()
            
            # Analyze the screenshot using OpenAI vision (via Responses API if available)
            show_progress("Analyzing screen with vision AI...")
            description = self._analyze_screenshot_optimized(screenshot_b64)
            
            # Get screen dimensions
            width = height = 0
            if hasattr(self.client, 'display_width'):
                width = self.client.display_width
                height = self.client.display_height
            elif hasattr(self.client, 'width'):
                width = self.client.width
                height = self.client.height
            
            return json.dumps({
                "status": "success",
                "width": width,
                "height": height,
                "screen_description": description,
                "note": "Screenshot captured and analyzed"
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to capture/analyze screenshot: {e}"
            }, indent=2)
    
    def _analyze_screenshot_optimized(self, screenshot_b64: str) -> str:
        """Analyze screenshot using OpenAI vision model (optimized).
        
        Uses Responses API if available, falls back to Chat Completions.
        
        Args:
            screenshot_b64: Base64-encoded PNG screenshot
            
        Returns:
            Description of what's visible in the screenshot
        """
        try:
            # Use ResponsesAPIClient if available for better performance
            if hasattr(self.client, 'create_completion'):
                response = self.client.create_completion(
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Describe what you see on this screen concisely. "
                                        "Include: application name, visible UI elements, text content, "
                                        "buttons, menus, sidebars. "
                                        "Be specific about locations and provide approximate coordinates. "
                                        "Focus on actionable information."
                                    )
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{screenshot_b64}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=800,  # Reduced for faster response
                    temperature=0
                )
                return response.choices[0].message.content
            else:
                # Fallback to direct OpenAI call
                return self._analyze_screenshot(screenshot_b64)
            
        except Exception as e:
            return f"Vision analysis failed: {e}"
    
    def _analyze_screenshot(self, screenshot_b64: str) -> str:
        """Fallback: Analyze screenshot using direct OpenAI call.
        
        Args:
            screenshot_b64: Base64-encoded PNG screenshot
            
        Returns:
            Description of what's visible in the screenshot
        """
        try:
            from openai import OpenAI
            import os
            
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            response = client.chat.completions.create(
                model="gpt-4o",  # Vision-capable model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Describe what you see on this screen concisely. "
                                    "Include: application name, visible UI elements, text content, "
                                    "buttons, menus, sidebars. "
                                    "Be specific about locations and provide approximate coordinates. "
                                    "Focus on actionable information."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,  # Reduced for faster response
                temperature=0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Vision analysis failed: {e}"


class MouseMoveInput(BaseModel):
    """Input for mouse move tool."""
    x: int = Field(description="X coordinate (in pixels)")
    y: int = Field(description="Y coordinate (in pixels)")


class MouseMoveTool(BaseTool):
    """Tool for moving the mouse cursor."""
    
    name: str = "move_mouse"
    description: str = (
        "Move the mouse cursor to specific coordinates on screen. "
        "Coordinates are in pixels, with (0,0) at top-left. "
        "Use after taking a screenshot to position cursor."
    )
    args_schema: Type[BaseModel] = MouseMoveInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, x: int, y: int) -> str:
        """Move mouse to coordinates."""
        show_progress(f"Moving mouse to ({x}, {y})...")
        
        try:
            result = self.client.execute_action("mouse_move", coordinate=(x, y))
            
            response = {
                "status": "success",
                "action": "mouse_move",
                "x": x,
                "y": y
            }
            
            # Add latency info if available (from ResponsesAPIClient)
            if hasattr(result, 'latency_ms') and result.latency_ms:
                response["latency_ms"] = round(result.latency_ms, 1)
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to move mouse: {e}"
            }, indent=2)


class LeftClickInput(BaseModel):
    """Input for left click tool."""
    x: Optional[int] = Field(
        default=None,
        description="X coordinate to click (moves mouse first if provided)"
    )
    y: Optional[int] = Field(
        default=None,
        description="Y coordinate to click (moves mouse first if provided)"
    )


class LeftClickTool(BaseTool):
    """Tool for performing left mouse clicks."""
    
    name: str = "left_click"
    description: str = (
        "Perform a left mouse click. "
        "If coordinates are provided, moves mouse there first. "
        "Use to click buttons, links, and UI elements. "
        "IMPORTANT: This tool only executes the click - it does NOT verify success. "
        "You MUST take a screenshot immediately after to verify the click worked."
    )
    args_schema: Type[BaseModel] = LeftClickInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Perform left click."""
        if x is not None and y is not None:
            show_progress(f"Clicking at ({x}, {y})...")
            coord = (x, y)
        else:
            show_progress("Clicking at current position...")
            coord = None
        
        try:
            result = self.client.execute_action("left_click", coordinate=coord)
            
            response = {
                "status": "success",
                "action": "left_click",
                "coordinate": coord
            }
            
            if hasattr(result, 'latency_ms') and result.latency_ms:
                response["latency_ms"] = round(result.latency_ms, 1)
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to click: {e}"
            }, indent=2)


class RightClickInput(BaseModel):
    """Input for right click tool."""
    x: Optional[int] = Field(
        default=None,
        description="X coordinate to click (moves mouse first if provided)"
    )
    y: Optional[int] = Field(
        default=None,
        description="Y coordinate to click (moves mouse first if provided)"
    )


class RightClickTool(BaseTool):
    """Tool for performing right mouse clicks."""
    
    name: str = "right_click"
    description: str = (
        "Perform a right mouse click (context menu). "
        "If coordinates are provided, moves mouse there first. "
        "Use to open context menus. "
        "IMPORTANT: This tool only executes the click - it does NOT verify success. "
        "You MUST take a screenshot immediately after to verify the context menu appeared."
    )
    args_schema: Type[BaseModel] = RightClickInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Perform right click."""
        if x is not None and y is not None:
            show_progress(f"Right clicking at ({x}, {y})...")
            coord = (x, y)
        else:
            show_progress("Right clicking at current position...")
            coord = None
        
        try:
            result = self.client.execute_action("right_click", coordinate=coord)
            
            response = {
                "status": "success",
                "action": "right_click",
                "coordinate": coord
            }
            
            if hasattr(result, 'latency_ms') and result.latency_ms:
                response["latency_ms"] = round(result.latency_ms, 1)
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to right click: {e}"
            }, indent=2)


class DoubleClickInput(BaseModel):
    """Input for double click tool."""
    x: Optional[int] = Field(
        default=None,
        description="X coordinate to click (moves mouse first if provided)"
    )
    y: Optional[int] = Field(
        default=None,
        description="Y coordinate to click (moves mouse first if provided)"
    )


class DoubleClickTool(BaseTool):
    """Tool for performing double clicks."""
    
    name: str = "double_click"
    description: str = (
        "Perform a double click. "
        "If coordinates are provided, moves mouse there first. "
        "Use to open files or activate elements that require double-click. "
        "IMPORTANT: This tool only executes the double-click - it does NOT verify success. "
        "You MUST take a screenshot immediately after to verify the action worked."
    )
    args_schema: Type[BaseModel] = DoubleClickInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Perform double click."""
        if x is not None and y is not None:
            show_progress(f"Double clicking at ({x}, {y})...")
            coord = (x, y)
        else:
            show_progress("Double clicking at current position...")
            coord = None
        
        try:
            result = self.client.execute_action("double_click", coordinate=coord)
            
            response = {
                "status": "success",
                "action": "double_click",
                "coordinate": coord
            }
            
            if hasattr(result, 'latency_ms') and result.latency_ms:
                response["latency_ms"] = round(result.latency_ms, 1)
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to double click: {e}"
            }, indent=2)


class TypeTextInput(BaseModel):
    """Input for type text tool."""
    text: str = Field(description="Text to type on the keyboard")


class TypeTextTool(BaseTool):
    """Tool for typing text via keyboard."""
    
    name: str = "type_text"
    description: str = (
        "Type text using the keyboard. "
        "Types the text at the current cursor/focus location. "
        "Use after clicking into a text field or input area. "
        "IMPORTANT: This tool only types the text - it does NOT verify it was entered. "
        "You MUST take a screenshot immediately after to verify the text appeared."
    )
    args_schema: Type[BaseModel] = TypeTextInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, text: str) -> str:
        """Type text."""
        show_progress(f"Typing: {text[:50]}...")
        
        try:
            result = self.client.execute_action("type", text=text)
            
            response = {
                "status": "success",
                "action": "type",
                "text": text
            }
            
            if hasattr(result, 'latency_ms') and result.latency_ms:
                response["latency_ms"] = round(result.latency_ms, 1)
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to type text: {e}"
            }, indent=2)


class PressKeyInput(BaseModel):
    """Input for press key tool."""
    key: str = Field(
        description=(
            "Key name to press. Common keys: Return, Enter, Tab, Escape, Delete, "
            "Backspace, Up, Down, Left, Right, Space"
        )
    )


class PressKeyTool(BaseTool):
    """Tool for pressing special keys."""
    
    name: str = "press_key"
    description: str = (
        "Press a special key on the keyboard. "
        "Supports: Return/Enter, Tab, Escape, Delete, Backspace, "
        "Up/Down/Left/Right arrows, Space. "
        "Use for navigation and special actions. "
        "IMPORTANT: This tool only presses the key - it does NOT verify the result. "
        "You MUST take a screenshot immediately after to verify the expected action occurred."
    )
    args_schema: Type[BaseModel] = PressKeyInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, key: str) -> str:
        """Press a key."""
        show_progress(f"Pressing key: {key}...")
        
        try:
            result = self.client.execute_action("key", text=key)
            
            response = {
                "status": "success",
                "action": "key",
                "key": key
            }
            
            if hasattr(result, 'latency_ms') and result.latency_ms:
                response["latency_ms"] = round(result.latency_ms, 1)
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to press key: {e}"
            }, indent=2)


class GetCursorPositionInput(BaseModel):
    """Input for get cursor position tool."""
    pass


class GetCursorPositionTool(BaseTool):
    """Tool for getting current cursor position."""
    
    name: str = "get_cursor_position"
    description: str = (
        "Get the current mouse cursor position. "
        "Returns x and y coordinates in pixels. "
        "Useful for verifying cursor location."
    )
    args_schema: Type[BaseModel] = GetCursorPositionInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Get cursor position."""
        try:
            result = self.client.execute_action("cursor_position")
            
            # Handle both ToolResult and dict responses
            if hasattr(result, 'data'):
                data = result.data
            else:
                data = result
            
            return json.dumps({
                "status": "success",
                "x": data.get("x", 0),
                "y": data.get("y", 0)
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get cursor position: {e}"
            }, indent=2)


class SwitchDesktopInput(BaseModel):
    """Input for switch desktop tool."""
    application_name: str = Field(
        description="Name of the application to find and switch to (e.g., 'Notion', 'Safari', 'Chrome')"
    )


class SwitchDesktopTool(BaseTool):
    """Tool for switching to a desktop containing a specific application."""
    
    name: str = "switch_desktop"
    description: str = (
        "Switch to the macOS desktop (Mission Control Space) containing a specific application. "
        "Use this when you need to interact with an application that is not visible on the current desktop. "
        "For example, if Notion is open on a different desktop, use this tool to switch to it. "
        "The tool will activate the application, automatically switching to its desktop. "
        "Returns success status and information about the switch."
    )
    args_schema: Type[BaseModel] = SwitchDesktopInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, application_name: str) -> str:
        """Switch to desktop containing the application."""
        show_progress(f"Switching to desktop with {application_name}...")

        try:
            # Use the client's desktop switching method
            if hasattr(self.client, 'switch_desktop_by_app'):
                result = self.client.switch_desktop_by_app(application_name)
            else:
                # Fallback: try execute_action
                result = self.client.execute_action("switch_desktop", text=application_name)

            # Handle both ActionResult objects and dictionaries
            if hasattr(result, 'success'):
                # ActionResult object (Anthropic client)
                success = result.success
                error_msg = result.error if hasattr(result, 'error') else None
                data = result.data if hasattr(result, 'data') else {}
            else:
                # Dictionary (OpenAI client)
                success = result.get("success", False)
                error_msg = result.get("error")
                data = result

            if success:
                return json.dumps({
                    "status": "success",
                    "application": application_name,
                    "message": data.get("message", f"Switched to desktop containing {application_name}") if isinstance(data, dict) else f"Switched to desktop containing {application_name}"
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "application": application_name,
                    "message": error_msg or data.get("error", "Failed to switch desktop") if isinstance(data, dict) else "Failed to switch desktop"
                }, indent=2)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "application": application_name,
                "message": f"Desktop switch failed: {e}"
            }, indent=2)


class GetScreenInfoInput(BaseModel):
    """Input for get screen info tool."""
    pass


class GetScreenInfoTool(BaseTool):
    """Tool for getting screen information."""
    
    name: str = "get_screen_info"
    description: str = (
        "Get information about the screen dimensions. "
        "Returns width and height in pixels. "
        "Use to understand the coordinate space before taking actions."
    )
    args_schema: Type[BaseModel] = GetScreenInfoInput
    
    client: object = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Get screen info."""
        try:
            info = self.client.get_screen_info()
            
            response = {
                "status": "success",
                "width": info.get("width", 0),
                "height": info.get("height", 0)
            }
            
            # Add optional fields if available
            if "display_num" in info:
                response["display_num"] = info["display_num"]
            if "native_computer_use" in info:
                response["using_native_api"] = info["native_computer_use"]
            
            return json.dumps(response, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get screen info: {e}"
            }, indent=2)


def get_computer_use_tools(client, state: AgentState) -> list:
    """Get all computer use tools for the agent.
    
    Args:
        client: ResponsesAPIClient or ComputerUseClient instance
        state: AgentState instance
        
    Returns:
        List of LangChain tools for computer control
    """
    return [
        ScreenshotTool(client=client, state=state),
        GetScreenInfoTool(client=client, state=state),
        SwitchDesktopTool(client=client, state=state),
        MouseMoveTool(client=client, state=state),
        LeftClickTool(client=client, state=state),
        RightClickTool(client=client, state=state),
        DoubleClickTool(client=client, state=state),
        TypeTextTool(client=client, state=state),
        PressKeyTool(client=client, state=state),
        GetCursorPositionTool(client=client, state=state),
    ]

