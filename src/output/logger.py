"""Comprehensive logging for extraction operations."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Dict, Literal


VerbosityLevel = Literal["silent", "minimal", "default", "verbose"]


class ExtractionLogger:
    """Logger for extraction operations with structured output."""

    def __init__(
        self,
        log_dir: str = "output/logs",
        log_to_file: bool = True,
        log_to_console: bool = True,
        log_level: str = "INFO",
        verbosity: VerbosityLevel = "default"
    ):
        """Initialize the extraction logger.
        
        Args:
            log_dir: Directory for log files
            log_to_file: Whether to log to file
            log_to_console: Whether to log to console
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
            verbosity: Verbosity level (silent, minimal, default, verbose)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.verbosity = verbosity
        
        # Create logger
        self.logger = logging.getLogger("notion_extractor")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Create formatters based on verbosity
        if verbosity == "minimal":
            # Minimal: timestamp only
            console_formatter = logging.Formatter(
                '%(asctime)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        elif verbosity == "silent":
            # Silent: no console output
            console_formatter = None
        else:
            # Default and verbose: different detail levels
            detailed_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            simple_formatter = logging.Formatter(
                '%(levelname)-8s | %(message)s'
            )
            console_formatter = detailed_formatter if verbosity == "verbose" else simple_formatter
        
        # File handler (always detailed when enabled)
        if log_to_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.log_dir / f"extraction_{timestamp}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
        
        # Console handler
        if log_to_console and verbosity != "silent" and console_formatter:
            console_handler = logging.StreamHandler(sys.stdout)
            if verbosity == "minimal":
                console_handler.setLevel(logging.CRITICAL + 1)  # Effectively disabled for normal logs
            elif verbosity == "verbose":
                console_handler.setLevel(logging.DEBUG)
            else:
                console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        self.session_start = datetime.now()
        self.events = []
    
    def should_log(self, level: str = "info") -> bool:
        """Check if should log based on verbosity level.
        
        Args:
            level: Log level (info, debug, warning, error)
            
        Returns:
            True if should log
        """
        if self.verbosity == "silent":
            return level in ["error", "warning"]
        elif self.verbosity == "minimal":
            return False  # Only timestamps in minimal
        return True

    def info(self, message: str):
        """Log an info message."""
        if self.should_log("info"):
            self.logger.info(message)
        self.events.append({"level": "INFO", "message": message, "time": datetime.now()})
        
        # In minimal mode, just print timestamp
        if self.verbosity == "minimal":
            print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def debug(self, message: str):
        """Log a debug message."""
        if self.should_log("debug"):
            self.logger.debug(message)
        self.events.append({"level": "DEBUG", "message": message, "time": datetime.now()})

    def warning(self, message: str):
        """Log a warning message."""
        if self.should_log("warning"):
            self.logger.warning(message)
        self.events.append({"level": "WARNING", "message": message, "time": datetime.now()})

    def error(self, message: str):
        """Log an error message."""
        if self.should_log("error"):
            self.logger.error(message)
        self.events.append({"level": "ERROR", "message": message, "time": datetime.now()})

    def log_navigation(self, action: str, target: str, success: bool):
        """Log a navigation action.
        
        Args:
            action: Type of navigation (e.g., "navigate_to_page")
            target: Target of navigation
            success: Whether navigation succeeded
        """
        status = "SUCCESS" if success else "FAILED"
        self.info(f"Navigation [{action}] -> '{target}': {status}")

    def log_scroll(self, scroll_count: int, new_blocks: int):
        """Log a scroll action.
        
        Args:
            scroll_count: Current scroll iteration
            new_blocks: Number of new blocks found
        """
        self.debug(f"Scroll #{scroll_count}: {new_blocks} new blocks")

    def log_extraction_start(self, page_title: str):
        """Log the start of page extraction.
        
        Args:
            page_title: Title of the page being extracted
        """
        self.info(f"Starting extraction: '{page_title}'")

    def log_extraction_complete(
        self, page_title: str, block_count: int, duration: float
    ):
        """Log completion of page extraction.
        
        Args:
            page_title: Title of the page
            block_count: Number of blocks extracted
            duration: Time taken in seconds
        """
        self.info(
            f"Extraction complete: '{page_title}' - "
            f"{block_count} blocks in {duration:.2f}s"
        )

    def log_ocr_fallback(self, element_role: str, success: bool):
        """Log OCR fallback usage.
        
        Args:
            element_role: Role of the element that needed OCR
            success: Whether OCR succeeded
        """
        status = "SUCCESS" if success else "FAILED"
        self.debug(f"OCR fallback for {element_role}: {status}")

    def log_comparison(self, accuracy: float, missing: int, extra: int):
        """Log comparison results.
        
        Args:
            accuracy: Accuracy percentage
            missing: Number of missing blocks
            extra: Number of extra blocks
        """
        self.info(
            f"Comparison: {accuracy:.1f}% accuracy, "
            f"{missing} missing, {extra} extra"
        )

    def log_error_recovery(self, error: str, recovery_action: str):
        """Log error recovery attempt.
        
        Args:
            error: Description of the error
            recovery_action: Action taken to recover
        """
        self.warning(f"Error: {error} | Recovery: {recovery_action}")

    def log_session_summary(self, pages_processed: int, total_blocks: int):
        """Log session summary.
        
        Args:
            pages_processed: Number of pages processed
            total_blocks: Total blocks extracted
        """
        duration = (datetime.now() - self.session_start).total_seconds()
        self.info(
            f"Session complete: {pages_processed} pages, "
            f"{total_blocks} blocks in {duration:.1f}s"
        )

    def save_event_log(self, filename: str = None) -> Path:
        """Save structured event log to file.
        
        Args:
            filename: Optional filename
            
        Returns:
            Path to saved log file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"events_{timestamp}.log"
        
        filepath = self.log_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("EXTRACTION EVENT LOG\n")
            f.write("=" * 80 + "\n")
            f.write(f"Session Start: {self.session_start}\n")
            f.write(f"Total Events: {len(self.events)}\n")
            f.write("=" * 80 + "\n\n")
            
            for event in self.events:
                time_str = event["time"].strftime("%H:%M:%S")
                f.write(f"[{time_str}] {event['level']}: {event['message']}\n")
        
        return filepath

    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics.
        
        Returns:
            Dictionary with statistics
        """
        level_counts = {}
        for event in self.events:
            level = event["level"]
            level_counts[level] = level_counts.get(level, 0) + 1
        
        duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "session_duration": duration,
            "total_events": len(self.events),
            "level_counts": level_counts,
            "start_time": self.session_start.isoformat(),
        }


# Convenience function to create a default logger
def create_logger(
    output_dir: str = "output/logs",
    verbose: bool = False,
    verbosity: VerbosityLevel = "default"
) -> ExtractionLogger:
    """Create a default extraction logger.
    
    Args:
        output_dir: Directory for log files
        verbose: If True, set log level to DEBUG (deprecated, use verbosity)
        verbosity: Verbosity level (silent, minimal, default, verbose)
        
    Returns:
        ExtractionLogger instance
    """
    # Handle deprecated verbose parameter
    if verbose and verbosity == "default":
        verbosity = "verbose"
    
    log_level = "DEBUG" if verbosity == "verbose" else "INFO"
    return ExtractionLogger(
        log_dir=output_dir,
        log_to_file=True,
        log_to_console=True,
        log_level=log_level,
        verbosity=verbosity
    )

