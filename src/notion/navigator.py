"""Notion page navigation without mouse simulation."""

import time
from typing import Optional, List, Dict
from ..ax.element import AXElement
from ..ax.utils import (
    find_elements_by_role,
    find_element_by_role_and_title,
    element_contains_text,
)
from .detector import NotionDetector


class NotionNavigator:
    """Handles programmatic navigation between Notion pages."""

    def __init__(self, detector: NotionDetector):
        """Initialize the navigator.
        
        Args:
            detector: NotionDetector instance
        """
        self.detector = detector

    def get_sidebar_pages(self) -> List[Dict[str, str]]:
        """Get list of pages from the sidebar.
        
        Returns:
            List of dicts with page info (name, element)
        """
        sidebar = self.detector.get_sidebar()
        if not sidebar:
            return []
        
        pages = []
        
        # Look for links in the sidebar
        links = find_elements_by_role(sidebar, "AXLink", max_depth=15)
        
        for link in links:
            title = link.title or link.get_text_content()
            if title and len(title.strip()) > 0:
                pages.append({
                    "name": title.strip(),
                    "element": link,
                })
        
        # Also look for buttons that might be page links
        buttons = find_elements_by_role(sidebar, "AXButton", max_depth=15)
        
        for button in buttons:
            title = button.title or button.get_text_content()
            if title and len(title.strip()) > 0:
                # Avoid duplicates
                if not any(p["name"] == title.strip() for p in pages):
                    pages.append({
                        "name": title.strip(),
                        "element": button,
                    })
        
        return pages

    def navigate_to_page(
        self,
        page_name: str,
        wait_for_load: bool = True,
        timeout: float = 10.0
    ) -> bool:
        """Navigate to a page by name.
        
        Args:
            page_name: Name of the page to navigate to
            wait_for_load: Whether to wait for page to load
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if navigation successful
        """
        # Get current title to detect change
        old_title = self.detector.get_page_title()
        
        # Find the page in the sidebar
        pages = self.get_sidebar_pages()
        target_page = None
        
        for page in pages:
            if page["name"].lower() == page_name.lower():
                target_page = page
                break
        
        if not target_page:
            return False
        
        # Click the page link
        element = target_page["element"]
        success = element.press()
        
        if not success:
            # Try to focus and press
            element.set_focused(True)
            time.sleep(0.1)
            success = element.press()
        
        if not success:
            return False
        
        if wait_for_load:
            # Wait for title to change
            new_title = self.detector.wait_for_title_change(
                old_title, timeout=timeout
            )
            if not new_title:
                return False
            
            # Wait for page to finish loading
            return self.detector.wait_for_page_load(timeout=timeout)
        
        return True

    def navigate_to_page_by_index(
        self,
        index: int,
        wait_for_load: bool = True,
        timeout: float = 10.0
    ) -> bool:
        """Navigate to a page by index in the sidebar.
        
        Args:
            index: Zero-based index of the page
            wait_for_load: Whether to wait for page to load
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if navigation successful
        """
        pages = self.get_sidebar_pages()
        
        if index < 0 or index >= len(pages):
            return False
        
        page_name = pages[index]["name"]
        return self.navigate_to_page(page_name, wait_for_load, timeout)

    def navigate_back(self, wait_for_load: bool = True, timeout: float = 10.0) -> bool:
        """Navigate back in history using keyboard shortcut.
        
        Args:
            wait_for_load: Whether to wait for page to load
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if navigation successful
        """
        # Get current title to detect change
        old_title = self.detector.get_page_title()
        
        # Send Cmd+[ keyboard shortcut for back navigation
        success = self._send_keyboard_shortcut("AXBack")
        
        if not success:
            # Try alternative: simulate the keyboard shortcut
            # This is more reliable than action
            import Quartz
            
            # Create keyboard event for Cmd+[
            event = Quartz.CGEventCreateKeyboardEvent(None, 0x21, True)  # 0x21 is '['
            Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            
            # Release
            event = Quartz.CGEventCreateKeyboardEvent(None, 0x21, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            
            success = True
        
        if wait_for_load:
            # Wait for title to change
            new_title = self.detector.wait_for_title_change(
                old_title, timeout=timeout
            )
            if not new_title:
                return False
            
            # Wait for page to finish loading
            return self.detector.wait_for_page_load(timeout=timeout)
        
        return success

    def navigate_forward(self, wait_for_load: bool = True, timeout: float = 10.0) -> bool:
        """Navigate forward in history using keyboard shortcut.
        
        Args:
            wait_for_load: Whether to wait for page to load
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if navigation successful
        """
        # Get current title to detect change
        old_title = self.detector.get_page_title()
        
        # Send Cmd+] keyboard shortcut for forward navigation
        success = self._send_keyboard_shortcut("AXForward")
        
        if not success:
            # Try alternative: simulate the keyboard shortcut
            import Quartz
            
            # Create keyboard event for Cmd+]
            event = Quartz.CGEventCreateKeyboardEvent(None, 0x1E, True)  # 0x1E is ']'
            Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            
            # Release
            event = Quartz.CGEventCreateKeyboardEvent(None, 0x1E, False)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
            
            success = True
        
        if wait_for_load:
            # Wait for title to change
            new_title = self.detector.wait_for_title_change(
                old_title, timeout=timeout
            )
            if not new_title:
                return False
            
            # Wait for page to finish loading
            return self.detector.wait_for_page_load(timeout=timeout)
        
        return success

    def find_in_page_links(self) -> List[Dict[str, str]]:
        """Find all links within the current page content.
        
        Returns:
            List of dicts with link info (text, element)
        """
        content_area = self.detector.get_content_area()
        if not content_area:
            return []
        
        links = []
        link_elements = find_elements_by_role(content_area, "AXLink", max_depth=20)
        
        for link in link_elements:
            text = link.get_text_content()
            if text and len(text.strip()) > 0:
                links.append({
                    "text": text.strip(),
                    "element": link,
                })
        
        return links

    def follow_in_page_link(
        self,
        link_text: str,
        wait_for_load: bool = True,
        timeout: float = 10.0
    ) -> bool:
        """Follow an in-page link by text.
        
        Args:
            link_text: Text of the link to follow
            wait_for_load: Whether to wait for page to load
            timeout: Maximum time to wait (seconds)
            
        Returns:
            True if navigation successful
        """
        # Get current title to detect change
        old_title = self.detector.get_page_title()
        
        # Find the link
        links = self.find_in_page_links()
        target_link = None
        
        for link in links:
            if link["text"].lower() == link_text.lower():
                target_link = link
                break
        
        if not target_link:
            return False
        
        # Click the link
        element = target_link["element"]
        success = element.press()
        
        if not success:
            # Try to focus and press
            element.set_focused(True)
            time.sleep(0.1)
            success = element.press()
        
        if not success:
            return False
        
        if wait_for_load:
            # Wait for title to change
            new_title = self.detector.wait_for_title_change(
                old_title, timeout=timeout
            )
            if not new_title:
                return False
            
            # Wait for page to finish loading
            return self.detector.wait_for_page_load(timeout=timeout)
        
        return True

    def _send_keyboard_shortcut(self, action: str) -> bool:
        """Send a keyboard shortcut via AX action.
        
        Args:
            action: The action name (e.g., "AXBack", "AXForward")
            
        Returns:
            True if successful
        """
        if not self.detector.main_window:
            return False
        
        # Try to perform the action on the main window
        return self.detector.main_window.perform_action(action)

    def ensure_sidebar_visible(self) -> bool:
        """Ensure the sidebar is visible.
        
        Returns:
            True if sidebar is now visible
        """
        if self.detector.is_sidebar_visible():
            return True
        
        # Try to toggle sidebar with Cmd+\
        import Quartz
        
        event = Quartz.CGEventCreateKeyboardEvent(None, 0x2A, True)  # 0x2A is '\'
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        # Release
        event = Quartz.CGEventCreateKeyboardEvent(None, 0x2A, False)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        # Wait a bit and check again
        time.sleep(0.5)
        return self.detector.is_sidebar_visible()

    def get_current_page_info(self) -> Dict[str, str]:
        """Get information about the current page.
        
        Returns:
            Dictionary with page info
        """
        return {
            "title": self.detector.get_page_title() or "Unknown",
            "loading": self.detector.is_loading(),
        }

