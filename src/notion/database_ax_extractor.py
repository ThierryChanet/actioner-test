"""Database extraction using AX navigation (not API)."""

import time
from typing import List, Optional
from .detector import NotionDetector
from .navigator import NotionNavigator
from .extractor import NotionExtractor, ExtractionResult


class DatabaseAXExtractor:
    """Extracts database pages by navigating through rows using AX actions."""
    
    def __init__(
        self,
        detector: NotionDetector,
        navigator: NotionNavigator,
        extractor: NotionExtractor
    ):
        """Initialize the database AX extractor.
        
        Args:
            detector: NotionDetector instance
            navigator: NotionNavigator instance
            extractor: NotionExtractor instance for page content
        """
        self.detector = detector
        self.navigator = navigator
        self.extractor = extractor
    
    def extract_database_pages(
        self,
        limit: int = 10,
        use_ocr: bool = True,
        scroll_delay: float = 0.3,
        navigation_delay: float = 1.0
    ) -> List[ExtractionResult]:
        """Extract content from database pages by clicking through rows.
        
        This method:
        1. Lists all visible rows in the current database view
        2. Clicks on each row to open the page
        3. Extracts the page content using AX
        4. Navigates back to the database
        5. Repeats for next row
        
        Args:
            limit: Maximum number of pages to extract
            use_ocr: Whether to use OCR for content extraction
            scroll_delay: Delay between scroll actions
            navigation_delay: Delay after navigation (seconds)
            
        Returns:
            List of ExtractionResult objects
        """
        # Store the database page title to navigate back
        database_title = self.detector.get_page_title()
        
        # Get list of rows in the database
        rows = self.navigator.get_database_rows()
        
        if not rows:
            return []
        
        # Limit to requested number
        rows_to_extract = rows[:limit]
        
        results = []
        for i, row in enumerate(rows_to_extract):
            row_title = row["title"]
            print(f"\nProcessing row {i+1}/{len(rows_to_extract)}: {row_title}")
            
            # Navigate to the row
            success = self.navigator.navigate_to_database_row(
                i,
                wait_for_load=True,
                timeout=15.0
            )
            
            if not success:
                print(f"  ⚠️  Failed to navigate to row: {row_title}")
                continue
            
            # Wait for navigation to complete
            time.sleep(navigation_delay)
            
            # Extract the page content
            try:
                result = self.extractor.extract_page(
                    use_ocr=use_ocr,
                    scroll_delay=scroll_delay
                )
                
                # Set the title if not detected
                if not result.title:
                    result.title = row_title
                
                result.metadata["database_row_index"] = i
                result.metadata["source"] = "ax_navigation"
                
                results.append(result)
                print(f"  ✅ Extracted: {result.title} ({len(result.blocks)} blocks)")
                
            except Exception as e:
                print(f"  ❌ Extraction failed for {row_title}: {e}")
                continue
            
            # Navigate back to database
            # We'll use browser back navigation
            back_success = self.navigator.navigate_back(wait_for_load=True, timeout=10.0)
            
            if not back_success:
                print(f"  ⚠️  Failed to navigate back to database")
                # Try to navigate directly to database by title
                if database_title:
                    self.navigator.navigate_to_page(database_title, wait_for_load=True)
            
            # Wait a bit before next navigation
            time.sleep(navigation_delay)
        
        return results
    
    def extract_database_pages_by_titles(
        self,
        page_titles: List[str],
        use_ocr: bool = True,
        scroll_delay: float = 0.3,
        navigation_delay: float = 1.0
    ) -> List[ExtractionResult]:
        """Extract specific database pages by their titles.
        
        Args:
            page_titles: List of page titles to extract
            use_ocr: Whether to use OCR for content extraction
            scroll_delay: Delay between scroll actions
            navigation_delay: Delay after navigation
            
        Returns:
            List of ExtractionResult objects
        """
        database_title = self.detector.get_page_title()
        results = []
        
        for page_title in page_titles:
            print(f"\nProcessing: {page_title}")
            
            # Navigate to the page by title
            success = self.navigator.navigate_to_database_row_by_title(
                page_title,
                wait_for_load=True,
                timeout=15.0
            )
            
            if not success:
                print(f"  ⚠️  Failed to navigate to: {page_title}")
                continue
            
            time.sleep(navigation_delay)
            
            # Extract content
            try:
                result = self.extractor.extract_page(
                    use_ocr=use_ocr,
                    scroll_delay=scroll_delay
                )
                
                if not result.title:
                    result.title = page_title
                
                result.metadata["source"] = "ax_navigation"
                results.append(result)
                
                print(f"  ✅ Extracted: {result.title} ({len(result.blocks)} blocks)")
                
            except Exception as e:
                print(f"  ❌ Extraction failed: {e}")
                continue
            
            # Navigate back
            self.navigator.navigate_back(wait_for_load=True)
            time.sleep(navigation_delay)
        
        return results
    
    def list_database_rows(self) -> List[str]:
        """List all visible rows in the current database view.
        
        Returns:
            List of row titles
        """
        rows = self.navigator.get_database_rows()
        return [row["title"] for row in rows]
    
    def preview_database(self, limit: int = 10) -> List[dict]:
        """Preview database rows without extracting full content.
        
        Args:
            limit: Maximum number of rows to preview
            
        Returns:
            List of dictionaries with preview info
        """
        rows = self.navigator.get_database_rows()
        limited_rows = rows[:limit]
        
        preview = []
        for i, row in enumerate(limited_rows):
            preview.append({
                "index": i,
                "title": row["title"],
                "element_role": row["element"].role if hasattr(row["element"], 'role') else "Unknown"
            })
        
        return preview

