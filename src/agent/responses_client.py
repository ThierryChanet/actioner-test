"""OpenAI Responses API client with Computer Use support.

This module provides a wrapper around OpenAI's Responses API with native
Computer Use tool integration and fallback to custom macOS implementation.
"""

import os
import asyncio
import time
from typing import Optional, Dict, Any, List, Literal, Union, Callable
from dataclasses import dataclass
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from .state import AgentState


ActionType = Literal[
    "key", "type", "mouse_move", "left_click", "left_click_drag",
    "right_click", "middle_click", "double_click", "screenshot", "cursor_position"
]


@dataclass
class ToolResult:
    """Result from a tool execution."""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


class ResponsesAPIClient:
    """Client for OpenAI Responses API with Computer Use support."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        use_native_computer_use: bool = False,
        display_width: int = 1920,
        display_height: int = 1080,
        display_num: int = 1,
        verbose: bool = False,
    ):
        """Initialize the Responses API client.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4o for vision support)
            use_native_computer_use: Try to use OpenAI's native Computer Use tool
            display_width: Display width in pixels
            display_height: Display height in pixels
            display_num: Display number (1-based)
            verbose: Enable verbose logging
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.model = model
        self.use_native_computer_use = use_native_computer_use
        self.display_width = display_width
        self.display_height = display_height
        self.display_num = display_num
        self.verbose = verbose
        
        # Initialize OpenAI clients
        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)
        
        # Computer Use client fallback
        self.computer_client = None
        self._has_native_computer_use = False
        
        # Screenshot caching for performance
        self._screenshot_cache: Optional[str] = None
        self._screenshot_cache_time: float = 0
        self._screenshot_cache_ttl: float = 2.0  # Cache for 2 seconds
        
        # Test if native Computer Use is available
        if use_native_computer_use:
            self._test_native_computer_use()
        
        # If native not available, use custom implementation
        if not self._has_native_computer_use:
            self._init_custom_computer_client()
    
    def _test_native_computer_use(self):
        """Test if native Computer Use tool is available."""
        try:
            if self.verbose:
                print("Testing native Computer Use tool availability...")
            
            # Try to make a simple call with computer tool
            tools = [{
                "type": "computer_20241022",
                "name": "computer",
                "display_width_px": self.display_width,
                "display_height_px": self.display_height,
                "display_number": self.display_num
            }]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                tools=tools,
                max_tokens=10
            )
            
            self._has_native_computer_use = True
            if self.verbose:
                print("✓ Native Computer Use tool is available")
                
        except Exception as e:
            self._has_native_computer_use = False
            if self.verbose:
                print(f"→ Native Computer Use not available: {e}")
                print("→ Will use custom macOS implementation")
    
    def _init_custom_computer_client(self):
        """Initialize custom macOS Computer Use client as fallback."""
        try:
            from .computer_use_client import ComputerUseClient
            self.computer_client = ComputerUseClient(
                api_key=self.api_key,
                display_num=self.display_num,
                display_width=self.display_width,
                display_height=self.display_height,
            )
            if self.verbose:
                print("✓ Custom macOS Computer Use client initialized")
        except Exception as e:
            if self.verbose:
                print(f"⚠️  Could not initialize custom computer client: {e}")
    
    def has_computer_use(self) -> bool:
        """Check if any Computer Use implementation is available."""
        return self._has_native_computer_use or self.computer_client is not None
    
    @property
    def native_computer_use_available(self) -> bool:
        """Check if native Computer Use is available."""
        return self._has_native_computer_use
    
    @property
    def custom_client(self):
        """Get the custom computer client (for backward compatibility)."""
        return self.computer_client
    
    def invalidate_screenshot_cache(self):
        """Invalidate the screenshot cache."""
        self._screenshot_cache = None
        self._screenshot_cache_time = 0
    
    def create_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0,
        stream: bool = False,
    ) -> ChatCompletion:
        """Create a chat completion using Responses API.
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            ChatCompletion response
        """
        # Add computer use tool if available and not already in tools
        if self._has_native_computer_use and tools is not None:
            has_computer_tool = any(t.get("type") == "computer_20241022" for t in tools)
            if not has_computer_tool:
                tools.append({
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": self.display_width,
                    "display_height_px": self.display_height,
                    "display_number": self.display_num
                })
        
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=stream,
        )
    
    async def create_completion_async(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0,
    ) -> ChatCompletion:
        """Create a chat completion asynchronously.
        
        Args:
            messages: List of message dicts
            tools: Optional list of tool definitions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            ChatCompletion response
        """
        # Add computer use tool if available
        if self._has_native_computer_use and tools is not None:
            has_computer_tool = any(t.get("type") == "computer_20241022" for t in tools)
            if not has_computer_tool:
                tools.append({
                    "type": "computer_20241022",
                    "name": "computer",
                    "display_width_px": self.display_width,
                    "display_height_px": self.display_height,
                    "display_number": self.display_num
                })
        
        return await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    
    def take_screenshot(self, use_cache: bool = True) -> str:
        """Capture a screenshot with optional caching.
        
        Args:
            use_cache: Whether to use cached screenshot if available
        
        Returns:
            Base64-encoded PNG image
        """
        # Check cache if enabled
        if use_cache and self._screenshot_cache:
            age = time.time() - self._screenshot_cache_time
            if age < self._screenshot_cache_ttl:
                if self.verbose:
                    print(f"  → Using cached screenshot ({age:.1f}s old)")
                return self._screenshot_cache
        
        # Capture new screenshot
        if self.computer_client:
            screenshot = self.computer_client.take_screenshot()
            # Update cache
            self._screenshot_cache = screenshot
            self._screenshot_cache_time = time.time()
            return screenshot
        else:
            raise RuntimeError("No Computer Use implementation available")
    
    async def take_screenshot_async(self, use_cache: bool = True) -> str:
        """Capture a screenshot asynchronously with optional caching.
        
        Args:
            use_cache: Whether to use cached screenshot if available
        
        Returns:
            Base64-encoded PNG image
        """
        # Check cache if enabled
        if use_cache and self._screenshot_cache:
            age = time.time() - self._screenshot_cache_time
            if age < self._screenshot_cache_ttl:
                if self.verbose:
                    print(f"  → Using cached screenshot ({age:.1f}s old)")
                return self._screenshot_cache
        
        # Run screenshot capture in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        screenshot = await loop.run_in_executor(None, self.take_screenshot, False)
        return screenshot
    
    def execute_action(
        self,
        action: ActionType,
        text: Optional[str] = None,
        coordinate: Optional[tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Execute a computer action.
        
        Args:
            action: Type of action to perform
            text: Text for type/key actions
            coordinate: Coordinate for mouse actions
            
        Returns:
            Dict with action result
        """
        if self._has_native_computer_use:
            # Use native Computer Use tool
            return self._execute_native_action(action, text, coordinate)
        elif self.computer_client:
            # Use custom implementation with optimizations
            return self._execute_custom_action(action, text, coordinate)
        else:
            raise RuntimeError("No Computer Use implementation available")
    
    def _execute_native_action(
        self,
        action: ActionType,
        text: Optional[str] = None,
        coordinate: Optional[tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Execute action using native Computer Use tool.
        
        This is called when OpenAI's native Computer Use is available.
        """
        # Build action payload for native tool
        action_payload = {"action": action}
        
        if text:
            action_payload["text"] = text
        if coordinate:
            action_payload["coordinate"] = coordinate
        
        # Native Computer Use tool handles the action
        # The actual execution happens through OpenAI's infrastructure
        return action_payload
    
    def _execute_custom_action(
        self,
        action: ActionType,
        text: Optional[str] = None,
        coordinate: Optional[tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Execute action using custom macOS implementation.
        
        This version has optimizations to reduce latency.
        """
        if not self.computer_client:
            raise RuntimeError("Custom computer client not available")
        
        # Use custom client with reduced delays
        return self.computer_client.execute_action(
            action=action,
            text=text,
            coordinate=coordinate
        )
    
    async def execute_action_async(
        self,
        action: ActionType,
        text: Optional[str] = None,
        coordinate: Optional[tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Execute action asynchronously.
        
        Args:
            action: Type of action
            text: Text for type/key actions
            coordinate: Coordinate for mouse actions
            
        Returns:
            Dict with action result
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.execute_action, 
            action, 
            text, 
            coordinate
        )
    
    def get_screen_info(self) -> Dict[str, Any]:
        """Get screen information.
        
        Returns:
            Dict with width, height, and display info
        """
        return {
            "width": self.display_width,
            "height": self.display_height,
            "display_num": self.display_num,
            "native_computer_use": self._has_native_computer_use,
        }
