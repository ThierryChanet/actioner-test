"""Notion content extraction with deterministic scrolling."""

import time
from typing import List, Dict, Optional, Any, Set
from ..ax.element import AXElement
from ..ax.utils import find_text_elements, find_scroll_area, get_all_text
from .detector import NotionDetector


class Block:
    """Represents an extracted content block."""

    def __init__(
        self,
        content: str,
        block_type: str = "text",
        source: str = "ax",
        order: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a block.
        
        Args:
            content: The text content
            block_type: Type of block (text, heading, etc.)
            source: Source of extraction (ax or ocr)
            order: Order in document
            metadata: Additional metadata
        """
        self.content = content
        self.block_type = block_type
        self.source = source
        self.order = order
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert block to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "type": self.block_type,
            "content": self.content,
            "source": self.source,
            "order": self.order,
            "metadata": self.metadata,
        }


class ExtractionResult:
    """Result of page extraction."""

    def __init__(self, page_id: Optional[str] = None, title: Optional[str] = None):
        """Initialize extraction result.
        
        Args:
            page_id: Optional page ID
            title: Page title
        """
        self.page_id = page_id
        self.title = title
        self.blocks: List[Block] = []
        self.metadata: Dict[str, Any] = {}

    def add_block(self, block: Block):
        """Add a block to the result.
        
        Args:
            block: Block to add
        """
        self.blocks.append(block)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "page_id": self.page_id,
            "title": self.title,
            "blocks": [block.to_dict() for block in self.blocks],
            "metadata": self.metadata,
        }


class NotionExtractor:
    """Extracts content from Notion pages using AX APIs."""

    def __init__(self, detector: NotionDetector):
        """Initialize the extractor.
        
        Args:
            detector: NotionDetector instance
        """
        self.detector = detector
        self.ocr_handler = None  # Will be set later if needed

    def set_ocr_handler(self, ocr_handler):
        """Set the OCR handler for fallback extraction.
        
        Args:
            ocr_handler: OCR handler instance
        """
        self.ocr_handler = ocr_handler

    def extract_page(
        self,
        use_ocr: bool = True,
        scroll_delay: float = 0.3,
        max_scrolls: int = 100
    ) -> ExtractionResult:
        """Extract content from the current page.
        
        Args:
            use_ocr: Whether to use OCR for inaccessible elements
            scroll_delay: Delay between scroll actions (seconds)
            max_scrolls: Maximum number of scroll iterations
            
        Returns:
            ExtractionResult with all extracted blocks
        """
        # Get page title
        title = self.detector.get_page_title()
        
        # Create result
        result = ExtractionResult(title=title)
        result.metadata["scroll_count"] = 0
        result.metadata["ocr_used"] = False
        
        # Get content area
        content_area = self.detector.get_content_area()
        if not content_area:
            return result
        
        # Extract visible content with scrolling
        blocks = self._extract_with_scrolling(
            content_area,
            scroll_delay=scroll_delay,
            max_scrolls=max_scrolls
        )
        
        # Add blocks to result
        for i, block in enumerate(blocks):
            block.order = i
            result.add_block(block)
        
        result.metadata["block_count"] = len(blocks)
        
        # Try OCR for elements without text if enabled
        if use_ocr and self.ocr_handler:
            ocr_blocks = self._extract_with_ocr(content_area)
            if ocr_blocks:
                result.metadata["ocr_used"] = True
                result.metadata["ocr_blocks"] = len(ocr_blocks)
                # Add OCR blocks with appropriate ordering
                for block in ocr_blocks:
                    block.order = len(result.blocks)
                    result.add_block(block)
        
        return result

    def _extract_with_scrolling(
        self,
        content_area: AXElement,
        scroll_delay: float = 0.3,
        max_scrolls: int = 100
    ) -> List[Block]:
        """Extract content by scrolling through the page.
        
        Args:
            content_area: The scrollable content area
            scroll_delay: Delay between scrolls (seconds)
            max_scrolls: Maximum scroll iterations
            
        Returns:
            List of extracted blocks
        """
        blocks = []
        seen_texts: Set[str] = set()
        scroll_count = 0
        no_new_content_count = 0
        
        # Scroll to top first
        self._scroll_to_top(content_area)
        time.sleep(scroll_delay)
        
        while scroll_count < max_scrolls:
            # Extract visible text elements
            new_blocks = self._extract_visible_blocks(content_area, seen_texts)
            
            if new_blocks:
                blocks.extend(new_blocks)
                no_new_content_count = 0
            else:
                no_new_content_count += 1
                
                # If no new content for 3 consecutive scrolls, we're done
                if no_new_content_count >= 3:
                    break
            
            # Try to scroll down
            if not self._scroll_down(content_area):
                # Scroll failed, we've reached the end
                break
            
            scroll_count += 1
            time.sleep(scroll_delay)
        
        return blocks

    def _extract_visible_blocks(
        self,
        content_area: AXElement,
        seen_texts: Set[str]
    ) -> List[Block]:
        """Extract blocks from currently visible content.
        
        Args:
            content_area: The content area to extract from
            seen_texts: Set of already seen text (to avoid duplicates)
            
        Returns:
            List of new blocks
        """
        blocks = []
        
        # Find all text elements
        text_elements = find_text_elements(content_area, max_depth=20)
        
        for elem in text_elements:
            text = elem.get_text_content()
            if not text or not text.strip():
                continue
            
            text = text.strip()
            
            # Skip if we've seen this text before
            if text in seen_texts:
                continue
            
            seen_texts.add(text)
            
            # Determine block type from role
            role = elem.role or "AXStaticText"
            block_type = self._role_to_block_type(role)
            
            # Create block
            block = Block(
                content=text,
                block_type=block_type,
                source="ax",
                metadata={
                    "role": role,
                    "position": elem.position,
                    "size": elem.size,
                }
            )
            
            blocks.append(block)
        
        return blocks

    def _scroll_to_top(self, element: AXElement) -> bool:
        """Scroll element to the top.
        
        Args:
            element: Element to scroll
            
        Returns:
            True if successful
        """
        # Try to set scroll position to 0
        scroll_area = find_scroll_area(element, max_depth=5)
        if scroll_area:
            # Try to get scroll bars and set value
            try:
                vertical_scroll = scroll_area.get_attribute("AXVerticalScrollBar")
                if vertical_scroll:
                    scroll_elem = AXElement(vertical_scroll)
                    scroll_elem.set_attribute("AXValue", 0.0)
                    return True
            except Exception:
                pass
        
        # Fallback: use keyboard shortcut Cmd+Up
        import Quartz
        
        event = Quartz.CGEventCreateKeyboardEvent(None, 0x7E, True)  # Up arrow
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        event = Quartz.CGEventCreateKeyboardEvent(None, 0x7E, False)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        return True

    def _scroll_down(self, element: AXElement, amount: float = 0.1) -> bool:
        """Scroll element down.
        
        Args:
            element: Element to scroll
            amount: Amount to scroll (0.0 to 1.0)
            
        Returns:
            True if scrolled successfully
        """
        scroll_area = find_scroll_area(element, max_depth=5)
        if not scroll_area:
            scroll_area = element
        
        # Try AX scroll action
        actions = scroll_area.get_actions()
        if "AXScrollDownByPage" in actions:
            return scroll_area.perform_action("AXScrollDownByPage")
        
        # Try to modify scroll bar value
        try:
            vertical_scroll = scroll_area.get_attribute("AXVerticalScrollBar")
            if vertical_scroll:
                scroll_elem = AXElement(vertical_scroll)
                current_value = scroll_elem.value or 0.0
                
                # Get max value
                max_value = scroll_elem.get_attribute("AXMaxValue")
                if max_value is None:
                    max_value = 1.0
                
                new_value = min(current_value + amount, max_value)
                
                # If we're at max, we can't scroll further
                if abs(new_value - current_value) < 0.001:
                    return False
                
                scroll_elem.set_attribute("AXValue", new_value)
                return True
        except Exception:
            pass
        
        # Fallback: use keyboard Page Down
        import Quartz
        
        event = Quartz.CGEventCreateKeyboardEvent(None, 0x79, True)  # Page Down
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        event = Quartz.CGEventCreateKeyboardEvent(None, 0x79, False)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        
        return True

    def _extract_with_ocr(self, content_area: AXElement) -> List[Block]:
        """Extract content using OCR for inaccessible elements.
        
        Args:
            content_area: The content area to extract from
            
        Returns:
            List of blocks extracted via OCR
        """
        if not self.ocr_handler:
            return []
        
        # Find visible elements without text
        from ..ax.utils import get_visible_elements
        
        visible_elements = get_visible_elements(content_area)
        ocr_blocks = []
        
        for elem in visible_elements:
            # Skip if element already has text
            if elem.get_text_content():
                continue
            
            # Skip if too small
            size = elem.size
            if not size or size[0] < 20 or size[1] < 10:
                continue
            
            # Try OCR on this element
            try:
                text = self.ocr_handler.extract_from_element(elem)
                if text and text.strip():
                    block = Block(
                        content=text.strip(),
                        block_type="text",
                        source="ocr",
                        metadata={
                            "role": elem.role,
                            "position": elem.position,
                            "size": elem.size,
                        }
                    )
                    ocr_blocks.append(block)
            except Exception:
                # Ignore OCR errors for individual elements
                pass
        
        return ocr_blocks

    def _role_to_block_type(self, role: str) -> str:
        """Convert AX role to block type.
        
        Args:
            role: AX role name
            
        Returns:
            Block type string
        """
        role_mapping = {
            "AXHeading": "heading",
            "AXStaticText": "text",
            "AXTextField": "text",
            "AXTextArea": "text",
            "AXLink": "link",
            "AXList": "list",
            "AXImage": "image",
            "AXButton": "button",
        }
        
        return role_mapping.get(role, "text")

    def extract_metadata(self) -> Dict[str, Any]:
        """Extract metadata about the current page.
        
        Returns:
            Dictionary with page metadata
        """
        return {
            "title": self.detector.get_page_title(),
            "is_loading": self.detector.is_loading(),
            "sidebar_visible": self.detector.is_sidebar_visible(),
        }

