"""OCR-based database navigation - find and click recipe names on screen."""

import time
import Quartz
import Cocoa
from typing import List, Tuple, Optional, Dict
from ..ocr.vision import VisionOCR
from ..ocr.fallback import OCRHandler
from .detector import NotionDetector


class OCRNavigator:
    """Navigate database by OCR'ing the screen to find recipe names."""
    
    def __init__(self, detector: NotionDetector):
        """Initialize OCR navigator.
        
        Args:
            detector: NotionDetector instance
        """
        self.detector = detector
        self.ocr = VisionOCR()
        if not self.ocr.is_available():
            # Fallback to Tesseract
            ocr_handler = OCRHandler()
            self.ocr = ocr_handler.tesseract if ocr_handler.tesseract_available else None
    
    def screenshot_region(self, x: int, y: int, width: int, height: int) -> Optional[str]:
        """Take screenshot of a screen region and save to temp file.
        
        Args:
            x, y: Top-left corner
            width, height: Dimensions
            
        Returns:
            Path to screenshot file
        """
        import tempfile
        
        # Create CGImage from screen region
        region = Quartz.CGRectMake(x, y, width, height)
        image = Quartz.CGWindowListCreateImage(
            region,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault
        )
        
        if not image:
            return None
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        url = Cocoa.NSURL.fileURLWithPath_(temp_path)
        dest = Quartz.CGImageDestinationCreateWithURL(
            url, 
            "public.png",
            1,
            None
        )
        
        if dest:
            Quartz.CGImageDestinationAddImage(dest, image, None)
            Quartz.CGImageDestinationFinalize(dest)
            return temp_path
        
        return None
    
    def screenshot_notion_window(self) -> Optional[Tuple[str, Tuple[int, int, int, int], float]]:
        """Screenshot the Notion window.
        
        Returns:
            Tuple of (screenshot_path, (x, y, width, height), scale_factor)
            where scale_factor accounts for Retina displays
        """
        # Get Notion window using CGWindowList
        notion_pid = self.detector.notion_pid
        if not notion_pid:
            print("❌ No Notion PID")
            return None
        
        # Get all windows
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID
        )
        
        # Find Notion's main window
        notion_window = None
        for window in window_list:
            if window.get('kCGWindowOwnerPID') == notion_pid:
                # Skip small windows (menu bars, etc)
                bounds = window.get('kCGWindowBounds')
                if bounds and bounds.get('Width', 0) > 400 and bounds.get('Height', 0) > 400:
                    notion_window = window
                    break
        
        if not notion_window:
            print("❌ Could not find Notion window in window list")
            return None
        
        # Get bounds (in logical screen coordinates)
        bounds = notion_window.get('kCGWindowBounds')
        if not bounds:
            print("❌ No bounds in window info")
            return None
        
        x = int(bounds['X'])
        y = int(bounds['Y'])
        width = int(bounds['Width'])
        height = int(bounds['Height'])
        
        print(f"📐 Window bounds: ({x}, {y}) {width}x{height}")
        
        screenshot_path = self.screenshot_region(x, y, width, height)
        
        if not screenshot_path:
            print("❌ Screenshot failed")
            return None
        
        # Calculate scale factor by checking actual image size
        # This handles Retina displays where actual pixels != logical points
        try:
            image = Cocoa.NSImage.alloc().initWithContentsOfFile_(screenshot_path)
            if image:
                image_data = image.TIFFRepresentation()
                bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(image_data)
                cg_image = bitmap.CGImage()
                
                if cg_image:
                    actual_width = Quartz.CGImageGetWidth(cg_image)
                    actual_height = Quartz.CGImageGetHeight(cg_image)
                    
                    # Calculate scale (typically 2.0 for Retina, 1.0 for non-Retina)
                    scale_x = actual_width / width if width > 0 else 1.0
                    scale_y = actual_height / height if height > 0 else 1.0
                    
                    # Use average scale (should be same for both dimensions)
                    scale_factor = (scale_x + scale_y) / 2.0
                    
                    print(f"📸 Image size: {actual_width}x{actual_height}, scale: {scale_factor:.1f}x")
                    
                    return screenshot_path, (x, y, width, height), scale_factor
        except Exception as e:
            print(f"⚠️  Could not determine scale factor: {e}")
        
        # Fallback: assume no scaling
        return screenshot_path, (x, y, width, height), 1.0
    
    def find_text_on_screen(
        self,
        search_terms: Optional[List[str]] = None,
        min_confidence: float = 0.5
    ) -> List[Dict]:
        """Find text elements on screen using OCR.
        
        Args:
            search_terms: Optional list of specific terms to find
            min_confidence: Minimum OCR confidence (0-1)
            
        Returns:
            List of dicts with 'text', 'x', 'y', 'width', 'height', 'confidence'
        """
        # Screenshot Notion window
        result = self.screenshot_notion_window()
        if not result:
            print("❌ Could not screenshot Notion window")
            return []
        
        screenshot_path, (win_x, win_y, win_width, win_height), scale_factor = result
        
        print(f"📸 Screenshot: {screenshot_path}")
        print(f"   Window: ({win_x}, {win_y}) {win_width}x{win_height}")
        
        # Run OCR
        if not self.ocr:
            print("❌ No OCR available")
            return []
        
        try:
            ocr_results = self.ocr.extract_text_with_positions(screenshot_path)
        except:
            # Fallback to basic extraction
            text = self.ocr.extract_text(screenshot_path)
            print(f"OCR text (no positions): {text[:200]}")
            return []
        
        # Parse OCR results
        found_items = []
        
        for item in ocr_results:
            text = item.get('text', '').strip()
            confidence = item.get('confidence', 1.0)
            bbox = item.get('bbox')  # (x, y, width, height) in IMAGE PIXELS
            
            if not text or len(text) < 3:
                continue
            
            if confidence < min_confidence:
                continue
            
            # If searching for specific terms
            if search_terms:
                if not any(term.lower() in text.lower() for term in search_terms):
                    continue
            
            # Convert image coordinates to screen coordinates
            # OCR returns pixel coordinates, but screen uses logical points
            # Scale factor accounts for Retina displays (e.g., 2.0x)
            if bbox:
                img_x, img_y, img_w, img_h = bbox
                
                # Scale down from pixels to logical points
                logical_x = img_x / scale_factor
                logical_y = img_y / scale_factor
                logical_w = img_w / scale_factor
                logical_h = img_h / scale_factor
                
                # Add window offset to get screen coordinates
                screen_x = win_x + logical_x
                screen_y = win_y + logical_y
                
                found_items.append({
                    'text': text,
                    'x': int(screen_x),
                    'y': int(screen_y),
                    'width': int(logical_w),
                    'height': int(logical_h),
                    'confidence': confidence
                })
        
        # Clean up screenshot
        import os
        try:
            os.unlink(screenshot_path)
        except:
            pass
        
        return found_items
    
    def click_at_position(self, x: int, y: int, delay: float = 0.5) -> bool:
        """Click at screen coordinates.
        
        Args:
            x, y: Screen coordinates
            delay: Delay after click
            
        Returns:
            True if successful
        """
        try:
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
            
            time.sleep(delay)
            return True
            
        except Exception as e:
            print(f"❌ Click failed: {e}")
            return False
    
    def find_and_click_text(self, text: str, delay: float = 1.0) -> bool:
        """Find text on screen, hover over it to reveal OPEN button, then click OPEN.
        
        Args:
            text: Text to search for (recipe name)
            delay: Delay after click
            
        Returns:
            True if found and clicked
        """
        print(f"🔍 Searching for: {text}")
        
        items = self.find_text_on_screen(search_terms=[text])
        
        if not items:
            print(f"  ❌ Not found")
            return False
        
        # Found the recipe - hover over it to reveal OPEN button
        item = items[0]
        hover_x = int(item['x'] + item['width'] / 2)
        hover_y = int(item['y'] + item['height'] / 2)
        
        print(f"  ✅ Found at ({hover_x}, {hover_y})")
        print(f"  🖱️  Hovering to reveal OPEN button...")
        
        # Move mouse to recipe to trigger hover state
        try:
            mouse_point = Quartz.CGPoint(hover_x, hover_y)
            mouse_move = Quartz.CGEventCreateMouseEvent(
                None,
                Quartz.kCGEventMouseMoved,
                mouse_point,
                Quartz.kCGMouseButtonLeft
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, mouse_move)
            time.sleep(0.5)  # Wait for OPEN button to appear
        except Exception as e:
            print(f"  ⚠️  Hover failed: {e}")
        
        # Now look for OPEN button near the recipe
        print(f"  🔍 Looking for OPEN button...")
        open_items = self.find_text_on_screen(search_terms=["OPEN"])
        
        if not open_items:
            print(f"  ⚠️  OPEN button not found, clicking recipe name instead")
            return self.click_at_position(hover_x, hover_y, delay)
        
        # Find OPEN button closest to the recipe (should be on same row)
        # Filter to buttons that are roughly on the same Y coordinate (within 50 pixels)
        nearby_opens = [
            btn for btn in open_items 
            if abs(btn['y'] - item['y']) < 50
        ]
        
        if not nearby_opens:
            print(f"  ⚠️  OPEN button not on same row, clicking recipe name instead")
            return self.click_at_position(hover_x, hover_y, delay)
        
        # Click the OPEN button
        open_btn = nearby_opens[0]
        click_x = int(open_btn['x'] + open_btn['width'] / 2)
        click_y = int(open_btn['y'] + open_btn['height'] / 2)
        
        print(f"  ✅ Found OPEN button at ({click_x}, {click_y})")
        print(f"  🖱️  Clicking OPEN...")
        
        return self.click_at_position(click_x, click_y, delay)
    
    def scan_database_rows(self) -> List[Dict]:
        """Scan database view and find all visible recipe names.
        
        Returns:
            List of dicts with recipe info
        """
        print("\n📸 Scanning database for recipes...")
        
        # Take screenshot and OCR
        items = self.find_text_on_screen(min_confidence=0.7)
        
        if not items:
            print("❌ No text found via OCR")
            return []
        
        # Filter to likely recipe names
        # Skip UI elements
        skip_terms = ['search', 'filter', 'sort', 'new', 'close', 'back',
                     'forward', 'share', 'more', 'settings', 'name',
                     'ingredients', 'duration', 'link', 'tags', 'all meals']
        
        recipes = []
        for item in items:
            text_lower = item['text'].lower()
            
            # Skip short text
            if len(item['text']) < 5:
                continue
            
            # Skip UI elements
            if any(skip in text_lower for skip in skip_terms):
                continue
            
            # Skip if looks like emoji or symbols
            if not any(c.isalpha() for c in item['text']):
                continue
            
            recipes.append(item)
        
        return recipes

