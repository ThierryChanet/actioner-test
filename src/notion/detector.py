"""Notion application detection and page state verification."""

import time
from typing import Optional, Dict, Any
from ..ax.client import AXClient
from ..ax.element import AXElement
from ..ax.utils import find_element_by_role_and_title, find_elements_by_role, wait_for_element


class NotionDetector:
    """Detects and monitors Notion application state."""

    NOTION_BUNDLE_ID = "notion.id"
    NOTION_APP_NAME = "Notion"
    
    # Common loading indicators
    LOADING_INDICATORS = ["Loading", "Syncing", "Updating"]

    def __init__(self, ax_client: Optional[AXClient] = None):
        """Initialize the detector.
        
        Args:
            ax_client: AXClient instance, or None to create new one
        """
        self.ax_client = ax_client or AXClient()
        self.notion_pid: Optional[int] = None
        self.notion_app: Optional[AXElement] = None
        self.main_window: Optional[AXElement] = None

    def find_notion(self, debug: bool = False) -> bool:
        """Find the Notion application.
        
        Args:
            debug: If True, print debug information
        
        Returns:
            True if Notion is found and accessible
        """
        # Try to find by bundle ID first
        self.notion_pid = self.ax_client.find_application(
            bundle_id=self.NOTION_BUNDLE_ID
        )
        
        if debug:
            print(f"[DEBUG] Search by bundle ID '{self.NOTION_BUNDLE_ID}': PID = {self.notion_pid}")
        
        # Fallback to app name
        if not self.notion_pid:
            self.notion_pid = self.ax_client.find_application(
                name=self.NOTION_APP_NAME
            )
            if debug:
                print(f"[DEBUG] Search by name '{self.NOTION_APP_NAME}': PID = {self.notion_pid}")
        
        if not self.notion_pid:
            if debug:
                print("[DEBUG] Notion PID not found")
            return False
        
        if debug:
            print(f"[DEBUG] Found Notion with PID {self.notion_pid}")
        
        # Get the application element
        self.notion_app = self.ax_client.get_application_element(self.notion_pid)
        if not self.notion_app:
            if debug:
                print("[DEBUG] Failed to get application element")
            return False
        
        if debug:
            print(f"[DEBUG] Got application element: {self.notion_app}")
        
        # Get the main window
        self.main_window = self.ax_client.get_main_window(self.notion_app, debug=debug)
        if debug:
            print(f"[DEBUG] Got main window: {self.main_window}")
        
        return self.main_window is not None

    def ensure_notion_active(self, debug: bool = False) -> bool:
        """Ensure Notion is found and activated.
        
        Args:
            debug: If True, print debug information
        
        Returns:
            True if Notion is active
        """
        # First, just find the app by PID
        self.notion_pid = self.ax_client.find_application(
            bundle_id=self.NOTION_BUNDLE_ID
        )
        if not self.notion_pid:
            self.notion_pid = self.ax_client.find_application(
                name=self.NOTION_APP_NAME
            )
        
        if not self.notion_pid:
            if debug:
                print("[DEBUG] Notion PID not found")
            return False
        
        if debug:
            print(f"[DEBUG] Found Notion with PID {self.notion_pid}")
        
        # Activate the application FIRST
        success = self.ax_client.activate_application(self.notion_pid, wait=1.0)
        if debug:
            print(f"[DEBUG] Activation result: {success}")
        
        # Now try to get the application element and windows
        if not self.find_notion(debug=debug):
            if debug:
                print("[DEBUG] Failed to get Notion UI elements after activation")
            return False
        
        return True

    def wait_for_notion(self, timeout: float = 10.0) -> bool:
        """Wait for Notion to be running.
        
        Args:
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if Notion is found within timeout
        """
        self.notion_pid = self.ax_client.wait_for_application(
            bundle_id=self.NOTION_BUNDLE_ID,
            timeout=timeout
        )
        
        if self.notion_pid:
            return self.find_notion()
        
        return False

    def get_page_title(self) -> Optional[str]:
        """Get the current page title.
        
        Returns:
            Page title or None if not found
        """
        if not self.main_window:
            return None
        
        # Try to find the title in the window
        # Notion typically has the page title as the window title
        window_title = self.main_window.title
        if window_title and window_title != self.NOTION_APP_NAME:
            return window_title
        
        # Try to find title element in the content area
        # Look for heading elements or static text with large size
        from ..ax.utils import find_elements_by_role
        
        headings = find_elements_by_role(self.main_window, "AXHeading", max_depth=15)
        if headings:
            # Get the first heading (likely the page title)
            title_text = headings[0].get_text_content()
            if title_text:
                return title_text
        
        # Look for static text elements that might be the title
        static_texts = find_elements_by_role(self.main_window, "AXStaticText", max_depth=10)
        for text_elem in static_texts:
            text = text_elem.get_text_content()
            if text and len(text) > 0 and len(text) < 200:
                # First substantial text might be the title
                return text
        
        return None

    def is_loading(self) -> bool:
        """Check if a page is currently loading.
        
        Returns:
            True if loading indicators are present
        """
        if not self.main_window:
            return False
        
        # Look for progress indicators
        from ..ax.utils import find_elements_by_role
        
        progress_indicators = find_elements_by_role(
            self.main_window, "AXProgressIndicator", max_depth=10
        )
        if progress_indicators:
            return True
        
        # Look for loading text
        from ..ax.utils import find_text_elements
        
        text_elements = find_text_elements(self.main_window, max_depth=10)
        for elem in text_elements:
            text = elem.get_text_content()
            if text:
                for indicator in self.LOADING_INDICATORS:
                    if indicator.lower() in text.lower():
                        return True
        
        return False

    def wait_for_page_load(
        self,
        timeout: float = 10.0,
        poll_interval: float = 0.3,
        stable_duration: float = 0.5
    ) -> bool:
        """Wait for the current page to finish loading.
        
        Args:
            timeout: Maximum time to wait (seconds)
            poll_interval: Time between checks (seconds)
            stable_duration: Time page must be stable to consider loaded
            
        Returns:
            True if page loaded successfully
        """
        start_time = time.time()
        last_stable_time = None
        
        while time.time() - start_time < timeout:
            if not self.is_loading():
                # Page appears loaded, check if it stays stable
                if last_stable_time is None:
                    last_stable_time = time.time()
                elif time.time() - last_stable_time >= stable_duration:
                    # Page has been stable for required duration
                    return True
            else:
                # Still loading, reset stable timer
                last_stable_time = None
            
            time.sleep(poll_interval)
        
        return False

    def wait_for_title_change(
        self,
        old_title: Optional[str],
        timeout: float = 10.0,
        poll_interval: float = 0.3
    ) -> Optional[str]:
        """Wait for the page title to change.
        
        Args:
            old_title: Previous page title
            timeout: Maximum time to wait (seconds)
            poll_interval: Time between checks (seconds)
            
        Returns:
            New page title, or None if timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_title = self.get_page_title()
            if current_title and current_title != old_title:
                # Wait a bit for page to stabilize
                time.sleep(0.5)
                return current_title
            
            time.sleep(poll_interval)
        
        return None

    def get_content_area(self) -> Optional[AXElement]:
        """Get the main content area of the Notion page.
        
        Returns:
            Content area element or None if not found
        """
        if not self.main_window:
            return None
        
        # Look for the scroll area that contains the content
        from ..ax.utils import find_scroll_area
        
        scroll_area = find_scroll_area(self.main_window, max_depth=15)
        if scroll_area:
            return scroll_area
        
        # Fallback: look for web area (Notion uses Electron)
        from ..ax.utils import find_elements_by_role
        
        web_areas = find_elements_by_role(self.main_window, "AXWebArea", max_depth=10)
        if web_areas:
            return web_areas[0]
        
        # Last resort: return the main window itself
        return self.main_window

    def get_sidebar(self) -> Optional[AXElement]:
        """Get the sidebar element.
        
        Returns:
            Sidebar element or None if not found
        """
        if not self.main_window:
            return None
        
        # Look for the sidebar - typically a group on the left side
        from ..ax.utils import find_elements_by_role
        
        groups = find_elements_by_role(self.main_window, "AXGroup", max_depth=8)
        
        # Try to identify sidebar by position (left side) and size
        for group in groups:
            pos = group.position
            size = group.size
            if pos and size:
                # Sidebar is typically narrow and on the left
                if pos[0] < 100 and size[0] < 400 and size[1] > 400:
                    return group
        
        return None

    def is_sidebar_visible(self) -> bool:
        """Check if the sidebar is visible.
        
        Returns:
            True if sidebar is visible
        """
        sidebar = self.get_sidebar()
        return sidebar is not None

    def get_state(self) -> Dict[str, Any]:
        """Get the current Notion state.
        
        Returns:
            Dictionary with current state information
        """
        return {
            "notion_running": self.notion_pid is not None,
            "notion_active": self.notion_app is not None,
            "window_available": self.main_window is not None,
            "page_title": self.get_page_title(),
            "is_loading": self.is_loading(),
            "sidebar_visible": self.is_sidebar_visible(),
        }

    def refresh(self) -> bool:
        """Refresh the detector state.
        
        Returns:
            True if Notion is still accessible
        """
        return self.find_notion()

