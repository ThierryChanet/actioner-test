"""Error handling and custom exceptions."""

from typing import Optional, Any
from functools import wraps
import time


class NotionExtractorError(Exception):
    """Base exception for Notion Extractor."""
    pass


class NotionNotFoundError(NotionExtractorError):
    """Notion application not found or not accessible."""
    pass


class NavigationError(NotionExtractorError):
    """Failed to navigate to a page."""
    
    def __init__(self, page_name: str, reason: Optional[str] = None):
        self.page_name = page_name
        self.reason = reason
        message = f"Failed to navigate to page: {page_name}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class ExtractionError(NotionExtractorError):
    """Failed to extract content from a page."""
    
    def __init__(self, page_name: str, reason: Optional[str] = None):
        self.page_name = page_name
        self.reason = reason
        message = f"Failed to extract content from: {page_name}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)


class PageLoadTimeoutError(NotionExtractorError):
    """Page failed to load within timeout."""
    
    def __init__(self, page_name: str, timeout: float):
        self.page_name = page_name
        self.timeout = timeout
        super().__init__(
            f"Page '{page_name}' did not load within {timeout}s"
        )


class PermissionError(NotionExtractorError):
    """Accessibility permissions not granted."""
    pass


class APIError(NotionExtractorError):
    """Notion API error."""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(message)


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts (seconds)
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    continue
            
            # All attempts failed
            raise last_exception
        
        return wrapper
    return decorator


def safe_execute(func, default=None, logger=None, error_message: str = None):
    """Safely execute a function, returning default on error.
    
    Args:
        func: Function to execute
        default: Default value to return on error
        logger: Optional logger to log errors
        error_message: Optional custom error message
        
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if logger:
            message = error_message or f"Error in {func.__name__}"
            logger.error(f"{message}: {e}")
        return default


class ErrorRecovery:
    """Handles error recovery strategies."""
    
    def __init__(self, logger=None):
        """Initialize error recovery handler.
        
        Args:
            logger: Optional logger for recording recovery attempts
        """
        self.logger = logger
        self.recovery_attempts = []
    
    def recover_from_navigation_failure(
        self, detector, navigator, page_name: str
    ) -> bool:
        """Attempt to recover from navigation failure.
        
        Args:
            detector: NotionDetector instance
            navigator: NotionNavigator instance
            page_name: Page to navigate to
            
        Returns:
            True if recovery successful
        """
        self._log("Attempting navigation recovery")
        
        # Strategy 1: Refresh detector state
        self._log("Strategy 1: Refreshing detector state")
        if detector.refresh():
            if navigator.navigate_to_page(page_name):
                self._log("Recovery successful via detector refresh")
                return True
        
        # Strategy 2: Ensure sidebar is visible
        self._log("Strategy 2: Ensuring sidebar is visible")
        if navigator.ensure_sidebar_visible():
            time.sleep(0.5)
            if navigator.navigate_to_page(page_name):
                self._log("Recovery successful via sidebar toggle")
                return True
        
        # Strategy 3: Try navigation by index if possible
        self._log("Strategy 3: Trying navigation by index")
        pages = navigator.get_sidebar_pages()
        for i, page in enumerate(pages):
            if page['name'].lower() == page_name.lower():
                if navigator.navigate_to_page_by_index(i):
                    self._log("Recovery successful via index navigation")
                    return True
        
        self._log("All recovery strategies failed")
        return False
    
    def recover_from_extraction_failure(
        self, detector, extractor
    ) -> Optional[Any]:
        """Attempt to recover from extraction failure.
        
        Args:
            detector: NotionDetector instance
            extractor: NotionExtractor instance
            
        Returns:
            Extraction result or None if recovery failed
        """
        self._log("Attempting extraction recovery")
        
        # Strategy 1: Wait and retry
        self._log("Strategy 1: Waiting for page to stabilize")
        time.sleep(2.0)
        detector.wait_for_page_load(timeout=5.0)
        
        try:
            result = extractor.extract_page()
            self._log("Recovery successful after waiting")
            return result
        except Exception:
            pass
        
        # Strategy 2: Refresh and retry
        self._log("Strategy 2: Refreshing detector and retrying")
        if detector.refresh():
            try:
                result = extractor.extract_page()
                self._log("Recovery successful after refresh")
                return result
            except Exception:
                pass
        
        self._log("Extraction recovery failed")
        return None
    
    def recover_from_page_load_timeout(
        self, detector, page_name: str, max_wait: float = 30.0
    ) -> bool:
        """Attempt to recover from page load timeout.
        
        Args:
            detector: NotionDetector instance
            page_name: Page that failed to load
            max_wait: Maximum additional time to wait
            
        Returns:
            True if page eventually loaded
        """
        self._log(f"Attempting recovery from load timeout: {page_name}")
        
        # Strategy: Extended wait with periodic checks
        start_time = time.time()
        check_interval = 2.0
        
        while time.time() - start_time < max_wait:
            if not detector.is_loading():
                current_title = detector.get_page_title()
                if current_title and page_name.lower() in current_title.lower():
                    self._log("Page loaded after extended wait")
                    return True
            
            time.sleep(check_interval)
        
        self._log("Page load recovery failed")
        return False
    
    def _log(self, message: str):
        """Log a recovery message.
        
        Args:
            message: Message to log
        """
        self.recovery_attempts.append(message)
        if self.logger:
            self.logger.log_error_recovery("Unknown", message)
    
    def get_recovery_log(self) -> list:
        """Get log of all recovery attempts.
        
        Returns:
            List of recovery attempt messages
        """
        return self.recovery_attempts.copy()


def validate_extraction_result(result) -> tuple[bool, Optional[str]]:
    """Validate an extraction result.
    
    Args:
        result: ExtractionResult to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not result:
        return False, "Result is None"
    
    if not result.title:
        return False, "No page title extracted"
    
    if not result.blocks:
        return False, "No blocks extracted"
    
    # Check for suspicious patterns
    if len(result.blocks) < 2:
        return False, "Too few blocks extracted (possible extraction failure)"
    
    # Check if all blocks are empty
    non_empty = sum(1 for block in result.blocks if block.content.strip())
    if non_empty == 0:
        return False, "All blocks are empty"
    
    return True, None


def handle_exception(e: Exception, logger=None, context: str = "") -> str:
    """Handle an exception and return user-friendly message.
    
    Args:
        e: Exception to handle
        logger: Optional logger
        context: Context description
        
    Returns:
        User-friendly error message
    """
    if isinstance(e, NotionNotFoundError):
        message = "Notion app is not running or not accessible"
    elif isinstance(e, NavigationError):
        message = f"Could not navigate to page: {e.page_name}"
    elif isinstance(e, ExtractionError):
        message = f"Failed to extract content from: {e.page_name}"
    elif isinstance(e, PageLoadTimeoutError):
        message = f"Page did not load: {e.page_name}"
    elif isinstance(e, PermissionError):
        message = "Accessibility permissions not granted. Please enable in System Preferences."
    elif isinstance(e, APIError):
        message = f"Notion API error: {str(e)}"
    else:
        message = f"Unexpected error: {str(e)}"
    
    if context:
        message = f"{context}: {message}"
    
    if logger:
        logger.error(message)
    
    return message

