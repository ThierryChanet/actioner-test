"""Keyboard-based database navigation for when AX detection fails."""

import time
import Quartz
from typing import Optional
from .detector import NotionDetector


class KeyboardNavigator:
    """Navigate database using keyboard (Tab + Enter)."""
    
    def __init__(self, detector: NotionDetector):
        """Initialize keyboard navigator.
        
        Args:
            detector: NotionDetector instance
        """
        self.detector = detector
    
    def send_key(self, keycode: int, modifiers: int = 0, delay: float = 0.1):
        """Send a keyboard event.
        
        Args:
            keycode: Virtual key code
            modifiers: Modifier flags (Command, Shift, etc.)
            delay: Delay after keypress
        """
        # Key down
        event_down = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
        if modifiers:
            Quartz.CGEventSetFlags(event_down, modifiers)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)
        
        time.sleep(0.05)
        
        # Key up
        event_up = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)
        
        time.sleep(delay)
    
    def press_tab(self, shift: bool = False, delay: float = 0.3):
        """Press Tab key (or Shift+Tab).
        
        Args:
            shift: If True, press Shift+Tab (move backwards)
            delay: Delay after press
        """
        modifiers = Quartz.kCGEventFlagMaskShift if shift else 0
        self.send_key(0x30, modifiers, delay)  # 0x30 = Tab
    
    def press_enter(self, delay: float = 1.0):
        """Press Enter key.
        
        Args:
            delay: Delay after press (for page load)
        """
        self.send_key(0x24, 0, delay)  # 0x24 = Return/Enter
    
    def press_escape(self, delay: float = 0.5):
        """Press Escape key.
        
        Args:
            delay: Delay after press
        """
        self.send_key(0x35, 0, delay)  # 0x35 = Escape
    
    def navigate_to_first_row(self, tabs_to_content: int = 5):
        """Navigate to the first database row.
        
        Args:
            tabs_to_content: Number of tabs needed to reach first row
            
        Returns:
            True if successful
        """
        # Tab through UI to reach first database row
        for i in range(tabs_to_content):
            self.press_tab(delay=0.2)
        
        return True
    
    def focus_notion_window(self):
        """Ensure Notion window is focused and active."""
        # Activate Notion
        self.detector.ensure_notion_active()
        time.sleep(0.3)
    
    def navigate_to_database_row(
        self,
        row_index: int,
        tabs_to_first_row: int = 5,
        wait_for_load: bool = True
    ) -> bool:
        """Navigate to a specific database row using keyboard.
        
        Strategy:
        1. Ensure Notion is focused (prevent escaping to other apps)
        2. Tab to first row
        3. Tab N times to reach target row
        4. Press Enter to open
        
        Args:
            row_index: Zero-based row index
            tabs_to_first_row: Tabs needed to reach first row from page top
            wait_for_load: Wait for page to load after opening
            
        Returns:
            True if successful
        """
        # CRITICAL: Refocus Notion to prevent tabbing into other apps
        self.focus_notion_window()
        
        print(f"  🎹 Tabbing to row {row_index}...")
        
        # Get current title
        old_title = self.detector.get_page_title()
        
        # Tab to first row
        for i in range(tabs_to_first_row):
            # Re-check focus every few tabs
            if i % 3 == 0:
                self.focus_notion_window()
            self.press_tab(delay=0.15)
        
        # Tab to target row
        for i in range(row_index):
            # Re-check focus periodically
            if i % 3 == 0 and i > 0:
                self.focus_notion_window()
            self.press_tab(delay=0.15)
        
        # Press Enter to open
        print(f"  🎹 Pressing Enter...")
        self.press_enter(delay=1.5)
        
        if wait_for_load:
            # Check if page changed
            time.sleep(0.5)
            new_title = self.detector.get_page_title()
            
            if new_title and new_title != old_title:
                print(f"  ✅ Page opened: {new_title}")
                # Wait for full load
                self.detector.wait_for_page_load(timeout=10.0)
                return True
            else:
                print(f"  ⚠️  Page didn't change (might need more tabs)")
                return False
        
        return True
    
    def go_back_to_database(self, database_title: Optional[str] = None):
        """Return to database view.
        
        Args:
            database_title: Optional database title to verify
        """
        # Use Cmd+[ to go back
        self.send_key(0x21, Quartz.kCGEventFlagMaskCommand, delay=1.0)  # 0x21 = [
        
        if database_title:
            time.sleep(0.5)
            current = self.detector.get_page_title()
            if database_title in current:
                return True
        
        return True
    
    def extract_database_pages_keyboard(
        self,
        limit: int = 10,
        tabs_to_first_row: int = 5,
        extractor = None
    ):
        """Extract database pages using keyboard navigation.
        
        Args:
            limit: Number of pages to extract
            tabs_to_first_row: Tabs to reach first database row
            extractor: NotionExtractor instance for content extraction
            
        Returns:
            List of ExtractionResult objects
        """
        from .extractor import ExtractionResult
        
        database_title = self.detector.get_page_title()
        print(f"\n🗄️  Database: {database_title}")
        print(f"📋 Will extract {limit} rows using keyboard navigation\n")
        
        results = []
        
        for i in range(limit):
            print(f"\n{'='*70}")
            print(f"Row {i+1}/{limit}")
            print('='*70)
            
            # Navigate to row
            success = self.navigate_to_database_row(
                i,
                tabs_to_first_row=tabs_to_first_row,
                wait_for_load=True
            )
            
            if not success:
                print(f"  ⚠️  Skipping row {i+1}")
                # Go back and continue
                self.go_back_to_database(database_title)
                time.sleep(1.0)
                continue
            
            # Extract content
            if extractor:
                try:
                    result = extractor.extract_page(use_ocr=True)
                    result.metadata["row_index"] = i
                    result.metadata["source"] = "keyboard_navigation"
                    results.append(result)
                    print(f"  ✅ Extracted: {result.title} ({len(result.blocks)} blocks)")
                except Exception as e:
                    print(f"  ❌ Extraction failed: {e}")
            
            # Go back to database
            print(f"  🔙 Returning to database...")
            self.go_back_to_database(database_title)
            time.sleep(1.0)
        
        return results

