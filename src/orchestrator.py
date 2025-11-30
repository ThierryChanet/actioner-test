"""High-level orchestrator for Notion extraction with automatic method selection."""

import time
import os
from typing import Optional, List, Dict, Any
from enum import Enum

from .ax.client import AXClient
from .notion.detector import NotionDetector
from .notion.navigator import NotionNavigator
from .notion.extractor import NotionExtractor, ExtractionResult
from .notion.database_ax_extractor import DatabaseAXExtractor
from .notion.ocr_navigator import OCRNavigator
from .notion.keyboard_navigator import KeyboardNavigator
from .notion.mouse_navigator import MouseNavigator
from .ocr.fallback import OCRHandler
from .validation.notion_api import NotionAPIClient
from .output.logger import create_logger


class ExtractionMethod(Enum):
    """Available extraction methods."""
    AX = "ax"  # Accessibility API (preferred)
    OCR = "ocr"  # OCR-based navigation
    KEYBOARD = "keyboard"  # Keyboard-based navigation
    MOUSE = "mouse"  # Mouse-based navigation
    API = "api"  # Notion API (fastest but requires token)


class NotionOrchestrator:
    """High-level orchestrator for all Notion operations.
    
    Automatically selects the best extraction method and handles fallbacks.
    """
    
    def __init__(
        self,
        notion_token: Optional[str] = None,
        output_dir: str = "output",
        verbose: bool = False
    ):
        """Initialize the orchestrator.
        
        Args:
            notion_token: Optional Notion API token for API-based extraction
            output_dir: Directory for output files
            verbose: Enable verbose logging
        """
        self.notion_token = notion_token or os.environ.get('NOTION_TOKEN')
        self.output_dir = output_dir
        self.verbose = verbose
        
        # Initialize logger
        self.logger = create_logger(f"{output_dir}/logs", verbose=verbose)
        
        # Initialize components (lazy)
        self._ax_client = None
        self._detector = None
        self._navigator = None
        self._extractor = None
        self._ocr_handler = None
        self._ocr_navigator = None
        self._keyboard_navigator = None
        self._mouse_navigator = None
        self._api_client = None
        self._db_extractor = None
        
    @property
    def ax_client(self) -> AXClient:
        """Get or create AX client."""
        if self._ax_client is None:
            self._ax_client = AXClient()
        return self._ax_client
    
    @property
    def detector(self) -> NotionDetector:
        """Get or create Notion detector."""
        if self._detector is None:
            self._detector = NotionDetector(self.ax_client)
        return self._detector
    
    @property
    def navigator(self) -> NotionNavigator:
        """Get or create Notion navigator."""
        if self._navigator is None:
            self._navigator = NotionNavigator(self.detector)
        return self._navigator
    
    @property
    def extractor(self) -> NotionExtractor:
        """Get or create Notion extractor."""
        if self._extractor is None:
            self._extractor = NotionExtractor(self.detector)
            # Setup OCR if available
            if self.ocr_handler.is_available():
                self._extractor.set_ocr_handler(self.ocr_handler)
        return self._extractor
    
    @property
    def ocr_handler(self) -> OCRHandler:
        """Get or create OCR handler."""
        if self._ocr_handler is None:
            self._ocr_handler = OCRHandler()
        return self._ocr_handler
    
    @property
    def ocr_navigator(self) -> OCRNavigator:
        """Get or create OCR navigator."""
        if self._ocr_navigator is None:
            self._ocr_navigator = OCRNavigator(self.detector)
        return self._ocr_navigator
    
    @property
    def keyboard_navigator(self) -> KeyboardNavigator:
        """Get or create keyboard navigator."""
        if self._keyboard_navigator is None:
            self._keyboard_navigator = KeyboardNavigator(self.detector)
        return self._keyboard_navigator
    
    @property
    def mouse_navigator(self) -> MouseNavigator:
        """Get or create mouse navigator."""
        if self._mouse_navigator is None:
            self._mouse_navigator = MouseNavigator(self.detector)
        return self._mouse_navigator
    
    @property
    def api_client(self) -> Optional[NotionAPIClient]:
        """Get or create API client (if token available)."""
        if self._api_client is None and self.notion_token:
            self._api_client = NotionAPIClient(self.notion_token)
        return self._api_client
    
    @property
    def db_extractor(self) -> DatabaseAXExtractor:
        """Get or create database extractor."""
        if self._db_extractor is None:
            self._db_extractor = DatabaseAXExtractor(
                self.detector,
                self.navigator,
                self.extractor
            )
        return self._db_extractor
    
    def ensure_notion_active(self) -> bool:
        """Ensure Notion app is active and accessible.
        
        Returns:
            True if Notion is active and accessible
        """
        try:
            return self.detector.ensure_notion_active(debug=self.verbose)
        except Exception as e:
            self.logger.error(f"Failed to activate Notion: {e}")
            return False
    
    def get_current_page_title(self) -> Optional[str]:
        """Get the title of the current page.
        
        Returns:
            Page title or None if unavailable
        """
        try:
            return self.detector.get_page_title()
        except Exception as e:
            self.logger.error(f"Failed to get page title: {e}")
            return None
    
    def list_available_pages(self) -> List[Dict[str, str]]:
        """List all pages available in the sidebar.
        
        Returns:
            List of page dictionaries with 'name' key
        """
        try:
            if not self.ensure_notion_active():
                return []
            
            # Try to get sidebar pages
            pages = self.navigator.get_sidebar_pages()
            if pages:
                return [{"name": p["name"]} for p in pages]
            
            # Fallback: if sidebar not accessible, return current page
            current_title = self.get_current_page_title()
            if current_title:
                self.logger.info(f"Sidebar not accessible, using current page: {current_title}")
                return [{"name": current_title, "current": True}]
            
            return []
        except Exception as e:
            self.logger.error(f"Failed to list pages: {e}")
            # Try to at least report current page
            try:
                current_title = self.get_current_page_title()
                if current_title:
                    return [{"name": current_title, "current": True}]
            except:
                pass
            return []
    
    def navigate_to_page(
        self,
        page_name: str,
        method: Optional[ExtractionMethod] = None
    ) -> bool:
        """Navigate to a page by name.
        
        Args:
            page_name: Name of the page
            method: Optional specific method to use (auto-selects if None)
            
        Returns:
            True if navigation successful
        """
        if not self.ensure_notion_active():
            return False
        
        # Check if already on the page
        current_title = self.get_current_page_title()
        if current_title and page_name.lower() in current_title.lower():
            self.logger.info(f"Already on page: {current_title}")
            return True
        
        # Try methods in order of reliability (OCR first as it's more reliable)
        methods = [method] if method else [
            ExtractionMethod.OCR,
            ExtractionMethod.AX,
        ]
        
        for m in methods:
            try:
                if m == ExtractionMethod.AX:
                    self.logger.info(f"Attempting AX navigation to: {page_name}")
                    if self.navigator.navigate_to_page(page_name):
                        self.logger.info(f"✓ Navigated via AX")
                        return True
                
                elif m == ExtractionMethod.OCR:
                    self.logger.info(f"Attempting OCR navigation to: {page_name}")
                    if self.ocr_navigator.find_and_click_text(
                        page_name,
                        fuzzy=True,
                        delay=1.5
                    ):
                        time.sleep(2.0)  # Wait for page to load
                        self.logger.info(f"✓ Navigated via OCR")
                        return True
                        
            except Exception as e:
                self.logger.warning(f"Navigation failed with {m.value}: {e}")
                continue
        
        self.logger.error(f"All navigation methods failed for: {page_name}")
        return False
    
    def extract_current_page(self, use_ocr: bool = True) -> Optional[ExtractionResult]:
        """Extract content from the current page.
        
        Args:
            use_ocr: Whether to use OCR as fallback
            
        Returns:
            ExtractionResult or None if extraction failed
        """
        try:
            if not self.ensure_notion_active():
                return None
            
            current_title = self.get_current_page_title()
            self.logger.info(f"Extracting current page: {current_title}")
            
            result = self.extractor.extract_page(use_ocr=use_ocr)
            
            self.logger.info(f"✓ Extracted {len(result.blocks)} blocks")
            return result
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            return None
    
    def extract_page(
        self,
        page_name: str,
        use_ocr: bool = True,
        method: Optional[ExtractionMethod] = None
    ) -> Optional[ExtractionResult]:
        """Navigate to and extract a page.
        
        Args:
            page_name: Name of the page
            use_ocr: Whether to use OCR as fallback
            method: Optional specific navigation method
            
        Returns:
            ExtractionResult or None if failed
        """
        if not self.navigate_to_page(page_name, method):
            return None
        
        # Wait for page to stabilize
        time.sleep(1.0)
        self.detector.wait_for_page_load()
        
        return self.extract_current_page(use_ocr=use_ocr)
    
    def extract_database_pages(
        self,
        database_id: Optional[str] = None,
        limit: int = 10,
        use_ocr: bool = True,
        method: Optional[ExtractionMethod] = None
    ) -> List[ExtractionResult]:
        """Extract pages from a database.
        
        Args:
            database_id: Database ID (if using API) or None (for current view)
            limit: Maximum number of pages to extract
            use_ocr: Whether to use OCR for extraction
            method: Preferred extraction method (auto-selects if None)
            
        Returns:
            List of ExtractionResult objects
        """
        results = []
        
        # If database_id provided and API available, use API (fastest)
        if database_id and self.api_client:
            try:
                self.logger.info(f"Using API to extract database: {database_id}")
                if self.api_client.test_connection():
                    results = self.api_client.extract_database_pages(
                        database_id,
                        limit=limit
                    )
                    self.logger.info(f"✓ Extracted {len(results)} pages via API")
                    return results
            except Exception as e:
                self.logger.warning(f"API extraction failed: {e}")
        
        # Otherwise, use AX-based navigation through current view
        if not self.ensure_notion_active():
            return []
        
        try:
            self.logger.info("Using AX navigation to extract database")
            results = self.db_extractor.extract_database_pages(
                limit=limit,
                use_ocr=use_ocr,
                navigation_delay=1.0
            )
            self.logger.info(f"✓ Extracted {len(results)} pages via AX")
            return results
            
        except Exception as e:
            self.logger.error(f"Database extraction failed: {e}")
            return []
    
    def search_pages(self, query: str) -> List[Dict[str, str]]:
        """Search for pages matching a query.
        
        Args:
            query: Search query (matches against page names)
            
        Returns:
            List of matching page dictionaries
        """
        all_pages = self.list_available_pages()
        query_lower = query.lower()
        
        matching = [
            p for p in all_pages
            if query_lower in p["name"].lower()
        ]
        
        return matching
    
    def analyze_content(self, result: ExtractionResult) -> Dict[str, Any]:
        """Analyze extracted content.
        
        Args:
            result: ExtractionResult to analyze
            
        Returns:
            Dictionary with analysis metrics
        """
        analysis = {
            "title": result.title,
            "total_blocks": len(result.blocks),
            "block_types": {},
            "sources": {},
            "total_characters": 0,
            "total_words": 0,
        }
        
        for block in result.blocks:
            # Count by type
            block_type = block.block_type
            analysis["block_types"][block_type] = \
                analysis["block_types"].get(block_type, 0) + 1
            
            # Count by source
            source = block.source
            analysis["sources"][source] = \
                analysis["sources"].get(source, 0) + 1
            
            # Text stats
            content = block.content or ""
            analysis["total_characters"] += len(content)
            analysis["total_words"] += len(content.split())
        
        return analysis
    
    def go_back(self) -> bool:
        """Navigate back to previous page.
        
        Returns:
            True if navigation successful
        """
        try:
            return self.navigator.navigate_back(wait_for_load=True)
        except Exception as e:
            self.logger.error(f"Go back failed: {e}")
            return False

