"""State management for the Notion agent."""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class AgentState:
    """Tracks the current state of the Notion agent."""
    
    current_page: Optional[str] = None
    """Title of the current page"""
    
    last_extraction: Optional[Dict[str, Any]] = None
    """Last extraction result summary"""
    
    recent_pages: List[str] = field(default_factory=list)
    """Recently visited pages (stack)"""
    
    extraction_count: int = 0
    """Number of extractions performed in this session"""
    
    available_pages: List[str] = field(default_factory=list)
    """Cached list of available pages"""
    
    last_screenshot: Optional[str] = None
    """Base64-encoded screenshot data from last capture"""
    
    last_screenshot_timestamp: Optional[float] = None
    """Timestamp of last screenshot"""
    
    original_desktop: Optional[int] = None
    """Desktop number where the agent started (for auto-return)"""
    
    current_desktop: Optional[int] = None
    """Current desktop number (if known)"""
    
    original_application: Optional[str] = None
    """Name of the frontmost application when agent started (for auto-return)"""
    
    def update_current_page(self, page_title: str):
        """Update the current page and add to history."""
        if self.current_page:
            self.recent_pages.append(self.current_page)
        self.current_page = page_title
    
    def record_extraction(self, title: str, block_count: int):
        """Record an extraction."""
        self.extraction_count += 1
        self.last_extraction = {
            "title": title,
            "blocks": block_count,
        }
    
    def get_context_summary(self) -> str:
        """Get a summary of the current context."""
        lines = []
        
        if self.current_page:
            lines.append(f"Current page: {self.current_page}")
        
        if self.last_extraction:
            lines.append(
                f"Last extraction: {self.last_extraction['title']} "
                f"({self.last_extraction['blocks']} blocks)"
            )
        
        if self.extraction_count > 0:
            lines.append(f"Extractions this session: {self.extraction_count}")
        
        if not lines:
            lines.append("No context available yet")
        
        return "\n".join(lines)

