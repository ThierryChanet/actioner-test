"""Mouse-based navigation for database rows (fallback when AX navigation fails)."""

import time
import Quartz
from typing import List, Optional, Tuple
from ..ax.element import AXElement
from ..ax.utils import find_elements_by_role
from .detector import NotionDetector


class MouseNavigator:
    """Navigate database using mouse clicks (fallback method)."""
    
    def __init__(self, detector: NotionDetector):
        """Initialize mouse navigator.
        
        Args:
            detector: NotionDetector instance
        """
        self.detector = detector
    
    def find_text_positions(self, search_texts: List[str]) -> List[Tuple[str, Tuple[int, int]]]:
        """Find screen positions of text elements.
        
        Args:
            search_texts: List of text strings to find
            
        Returns:
            List of (text, (x, y)) tuples with screen coordinates
        """
        content_area = self.detector.get_content_area()
        if not content_area:
            return []
        
        results = []
        
        # Recursively search for text elements
        def search_element(elem, depth=30):
            if depth <= 0:
                return
            
            text = elem.get_text_content()
            if text:
                for search_text in search_texts:
                    if search_text.lower() in text.lower():
                        # Get position
                        pos = elem.position
                        size = elem.size
                        if pos and size:
                            # Click in center of element
                            click_x = int(pos[0] + size[0] / 2)
                            click_y = int(pos[1] + size[1] / 2)
                            results.append((text.strip(), (click_x, click_y)))
                            print(f"  Found: {text.strip()[:40]} at ({click_x}, {click_y})")
            
            # Check children
            try:
                children_ref = elem.get_attribute("AXChildren")
                if children_ref:
                    for child_ref in children_ref:
                        try:
                            child = AXElement(child_ref)
                            search_element(child, depth - 1)
                        except:
                            pass
            except:
                pass
        
        search_element(content_area)
        return results
    
    def click_at_position(self, x: int, y: int, delay: float = 0.5) -> bool:
        """Click at screen coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate  
            delay: Delay after click (seconds)
            
        Returns:
            True if click succeeded
        """
        try:
            # Create click event at position
            click_point = Quartz.CGPoint(x, y)
            
            # Mouse down
            mouse_down = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseDown,
                click_point,
                Quartz.kCGMouseButtonLeft
            )
            
            # Mouse up
            mouse_up = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventLeftMouseUp,
                click_point,
                Quartz.kCGMouseButtonLeft
            )
            
            # Post events
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_down)
            time.sleep(0.05)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_up)
            
            # Wait for response
            time.sleep(delay)
            
            return True
            
        except Exception as e:
            print(f"Click failed: {e}")
            return False
    
    def click_on_text(self, text: str, delay: float = 0.5) -> bool:
        """Find and click on text element.
        
        Args:
            text: Text to search for and click
            delay: Delay after click
            
        Returns:
            True if found and clicked
        """
        print(f"Searching for: {text}")
        positions = self.find_text_positions([text])
        
        if not positions:
            print(f"  ❌ Not found")
            return False
        
        # Click first match
        found_text, (x, y) = positions[0]
        print(f"  ✅ Found at ({x}, {y})")
        print(f"  🖱️  Clicking...")
        
        return self.click_at_position(x, y, delay)
    
    def get_all_visible_text_positions(self, min_length: int = 5) -> List[Tuple[str, Tuple[int, int]]]:
        """Get positions of all visible text elements.
        
        Args:
            min_length: Minimum text length to include
            
        Returns:
            List of (text, (x, y)) tuples
        """
        content_area = self.detector.get_content_area()
        if not content_area:
            return []
        
        results = []
        seen_texts = set()
        
        def scan_element(elem, depth=30):
            if depth <= 0:
                return
            
            text = elem.get_text_content()
            if text and len(text.strip()) >= min_length:
                text = text.strip()
                if text not in seen_texts:
                    seen_texts.add(text)
                    pos = elem.position
                    size = elem.size
                    if pos and size:
                        click_x = int(pos[0] + size[0] / 2)
                        click_y = int(pos[1] + size[1] / 2)
                        results.append((text, (click_x, click_y)))
            
            # Check children
            try:
                children_ref = elem.get_attribute("AXChildren")
                if children_ref:
                    for child_ref in children_ref:
                        try:
                            child = AXElement(child_ref)
                            scan_element(child, depth - 1)
                        except:
                            pass
            except:
                pass
        
        scan_element(content_area)
        return results

