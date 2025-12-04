"""Async versions of computer use tools for improved performance.

These tools use async operations to reduce latency and improve responsiveness.
"""

import json
import asyncio
from typing import Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from .state import AgentState
from .callbacks import show_progress
from .responses_client import ResponsesAPIClient


class AsyncScreenshotInput(BaseModel):
    """Input for async screenshot tool."""
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached screenshot if available (default: True)"
    )


class AsyncScreenshotTool(BaseTool):
    """Async tool for capturing screenshots with caching."""
    
    name: str = "take_screenshot_async"
    description: str = (
        "Asynchronously capture a screenshot of the screen. "
        "Uses caching to reduce latency - cached screenshots are valid for 2 seconds. "
        "Set use_cache=False to force a fresh capture."
    )
    args_schema: Type[BaseModel] = AsyncScreenshotInput
    
    client: ResponsesAPIClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    async def _arun(self, use_cache: bool = True) -> str:
        """Take a screenshot asynchronously."""
        show_progress("Capturing screenshot (async)...")
        
        try:
            # Use async screenshot capture
            screenshot_b64 = await self.client.take_screenshot_async(use_cache=use_cache)
            
            # Store in state
            import time
            self.state.last_screenshot = screenshot_b64
            self.state.last_screenshot_timestamp = time.time()
            
            return json.dumps({
                "status": "success",
                "width": self.client.display_width,
                "height": self.client.display_height,
                "cached": use_cache,
                "note": "Screenshot captured asynchronously"
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to capture screenshot: {e}"
            }, indent=2)
    
    def _run(self, use_cache: bool = True) -> str:
        """Sync fallback - runs async version in event loop."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                return asyncio.create_task(self._arun(use_cache))
            else:
                # Run in new event loop
                return loop.run_until_complete(self._arun(use_cache))
        except Exception:
            # Fallback to sync version
            return self.client.take_screenshot(use_cache=use_cache)


class AsyncMouseMoveInput(BaseModel):
    """Input for async mouse move."""
    x: int = Field(description="X coordinate in pixels")
    y: int = Field(description="Y coordinate in pixels")


class AsyncMouseMoveTool(BaseTool):
    """Async tool for moving the mouse cursor."""
    
    name: str = "move_mouse_async"
    description: str = (
        "Asynchronously move the mouse cursor to coordinates. "
        "Non-blocking operation for better performance."
    )
    args_schema: Type[BaseModel] = AsyncMouseMoveInput
    
    client: ResponsesAPIClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    async def _arun(self, x: int, y: int) -> str:
        """Move mouse asynchronously."""
        show_progress(f"Moving mouse to ({x}, {y}) (async)...")
        
        try:
            result = await self.client.execute_action_async(
                "mouse_move",
                coordinate=(x, y)
            )
            
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
    
    def _run(self, x: int, y: int) -> str:
        """Sync fallback."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(x, y))
        except Exception:
            return self.client.execute_action("mouse_move", coordinate=(x, y))


class AsyncLeftClickInput(BaseModel):
    """Input for async left click."""
    x: Optional[int] = Field(
        default=None,
        description="X coordinate (moves mouse first if provided)"
    )
    y: Optional[int] = Field(
        default=None,
        description="Y coordinate (moves mouse first if provided)"
    )


class AsyncLeftClickTool(BaseTool):
    """Async tool for left mouse clicks."""
    
    name: str = "left_click_async"
    description: str = (
        "Asynchronously perform a left mouse click. "
        "If coordinates provided, moves mouse there first. "
        "Non-blocking for better performance."
    )
    args_schema: Type[BaseModel] = AsyncLeftClickInput
    
    client: ResponsesAPIClient = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    async def _arun(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Perform left click asynchronously."""
        coord = (x, y) if x is not None and y is not None else None
        
        if coord:
            show_progress(f"Left clicking at ({x}, {y}) (async)...")
        else:
            show_progress("Left clicking at current position (async)...")
        
        try:
            result = await self.client.execute_action_async(
                "left_click",
                coordinate=coord
            )
            
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
    
    def _run(self, x: Optional[int] = None, y: Optional[int] = None) -> str:
        """Sync fallback."""
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self._arun(x, y))
        except Exception:
            coord = (x, y) if x is not None and y is not None else None
            return self.client.execute_action("left_click", coordinate=coord)


def get_async_computer_use_tools(
    client: ResponsesAPIClient,
    state: AgentState
) -> list:
    """Get async versions of computer use tools.
    
    These tools use async operations for better performance and reduced latency.
    
    Args:
        client: ResponsesAPIClient instance
        state: AgentState instance
        
    Returns:
        List of async LangChain tools
    """
    return [
        AsyncScreenshotTool(client=client, state=state),
        AsyncMouseMoveTool(client=client, state=state),
        AsyncLeftClickTool(client=client, state=state),
    ]

