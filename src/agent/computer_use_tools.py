"""LangChain tools for OpenAI Computer Control Tools."""

import json
from typing import Optional, Type, Tuple
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from .computer_use_client import ComputerUseClient
from .state import AgentState
from .callbacks import show_progress


class ScreenshotInput(BaseModel):
    """Input for screenshot tool."""
    pass


class ScreenshotTool(BaseTool):
    """Tool for capturing screenshots of the screen."""
    
    name: str = "take_screenshot"
    description: str = (
        "Capture a screenshot of the entire screen. "
        "Use this to see what's currently visible on the screen. "
        "Returns base64-encoded image data. "
        "Essential for understanding screen state before taking actions."
    )
    args_schema: Type[BaseModel] = ScreenshotInput
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Take a screenshot."""
        show_progress("Capturing screenshot...")
        
        try:
            screenshot_b64 = self.client.take_screenshot()
            
            return json.dumps({
                "status": "success",
                "message": "Screenshot captured",
                "width": self.client.width,
                "height": self.client.height,
                "note": "Screenshot data available for analysis"
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to capture screenshot: {e}"
            }, indent=2)


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
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, x: int, y: int) -> str:
        """Move mouse to coordinates."""
        show_progress(f"Moving mouse to ({x}, {y})...")
        
        try:
            result = self.client.execute_action("mouse_move", coordinate=(x, y))
            
            return json.dumps({
                "status": "success",
                "action": "mouse_move",
                "x": x,
                "y": y
            }, indent=2)
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
        "Use to click buttons, links, and UI elements."
    )
    args_schema: Type[BaseModel] = LeftClickInput
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Perform left click."""
        if x is not None and y is not None:
            show_progress(f"Left clicking at ({x}, {y})...")
            coord = (x, y)
        else:
            show_progress("Left clicking at current position...")
            coord = None
        
        try:
            result = self.client.execute_action("left_click", coordinate=coord)
            
            return json.dumps({
                "status": "success",
                "action": "left_click",
                "coordinate": coord
            }, indent=2)
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
        "Use to open context menus."
    )
    args_schema: Type[BaseModel] = RightClickInput
    
    client: ComputerUseClient = Field(exclude=True)
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
            
            return json.dumps({
                "status": "success",
                "action": "right_click",
                "coordinate": coord
            }, indent=2)
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
        "Use to open files or activate elements that require double-click."
    )
    args_schema: Type[BaseModel] = DoubleClickInput
    
    client: ComputerUseClient = Field(exclude=True)
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
            
            return json.dumps({
                "status": "success",
                "action": "double_click",
                "coordinate": coord
            }, indent=2)
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
        "Use after clicking into a text field or input area."
    )
    args_schema: Type[BaseModel] = TypeTextInput
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, text: str) -> str:
        """Type text."""
        show_progress(f"Typing: {text[:50]}...")
        
        try:
            result = self.client.execute_action("type", text=text)
            
            return json.dumps({
                "status": "success",
                "action": "type",
                "text": text
            }, indent=2)
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
        "Use for navigation and special actions."
    )
    args_schema: Type[BaseModel] = PressKeyInput
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, key: str) -> str:
        """Press a key."""
        show_progress(f"Pressing key: {key}...")
        
        try:
            result = self.client.execute_action("key", text=key)
            
            return json.dumps({
                "status": "success",
                "action": "key",
                "key": key
            }, indent=2)
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
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Get cursor position."""
        try:
            result = self.client.execute_action("cursor_position")
            
            return json.dumps({
                "status": "success",
                "x": result["x"],
                "y": result["y"]
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get cursor position: {e}"
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
    
    client: ComputerUseClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Get screen info."""
        try:
            info = self.client.get_screen_info()
            
            return json.dumps({
                "status": "success",
                "width": info["width"],
                "height": info["height"],
                "display_num": info["display_num"]
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to get screen info: {e}"
            }, indent=2)


def get_computer_use_tools(client: ComputerUseClient, state: AgentState) -> list:
    """Get all computer use tools for the agent.
    
    Args:
        client: ComputerUseClient instance
        state: AgentState instance
        
    Returns:
        List of LangChain tools for computer control
    """
    return [
        ScreenshotTool(client=client, state=state),
        GetScreenInfoTool(client=client, state=state),
        MouseMoveTool(client=client, state=state),
        LeftClickTool(client=client, state=state),
        RightClickTool(client=client, state=state),
        DoubleClickTool(client=client, state=state),
        TypeTextTool(client=client, state=state),
        PressKeyTool(client=client, state=state),
        GetCursorPositionTool(client=client, state=state),
    ]

