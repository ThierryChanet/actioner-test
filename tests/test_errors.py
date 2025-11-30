"""Tests for error handling."""

import pytest
from src.errors import (
    NotionExtractorError,
    NotionNotFoundError,
    NavigationError,
    ExtractionError,
    PageLoadTimeoutError,
    validate_extraction_result,
    handle_exception,
)
from src.notion.extractor import Block, ExtractionResult


class TestCustomExceptions:
    """Tests for custom exception classes."""
    
    def test_notion_not_found_error(self):
        """Test NotionNotFoundError."""
        error = NotionNotFoundError("Test error")
        assert isinstance(error, NotionExtractorError)
        assert str(error) == "Test error"
    
    def test_navigation_error(self):
        """Test NavigationError."""
        error = NavigationError("Test Page", "Page not found")
        assert error.page_name == "Test Page"
        assert error.reason == "Page not found"
        assert "Test Page" in str(error)
        assert "Page not found" in str(error)
    
    def test_extraction_error(self):
        """Test ExtractionError."""
        error = ExtractionError("Test Page", "No content")
        assert error.page_name == "Test Page"
        assert error.reason == "No content"
    
    def test_page_load_timeout_error(self):
        """Test PageLoadTimeoutError."""
        error = PageLoadTimeoutError("Test Page", 10.0)
        assert error.page_name == "Test Page"
        assert error.timeout == 10.0
        assert "10" in str(error)


class TestValidation:
    """Tests for validation functions."""
    
    def test_validate_extraction_result_valid(self):
        """Test validation of valid extraction result."""
        result = ExtractionResult(title="Test")
        result.add_block(Block(content="Block 1"))
        result.add_block(Block(content="Block 2"))
        
        is_valid, error = validate_extraction_result(result)
        assert is_valid
        assert error is None
    
    def test_validate_extraction_result_none(self):
        """Test validation of None result."""
        is_valid, error = validate_extraction_result(None)
        assert not is_valid
        assert "None" in error
    
    def test_validate_extraction_result_no_title(self):
        """Test validation of result without title."""
        result = ExtractionResult(title=None)
        result.add_block(Block(content="Block"))
        
        is_valid, error = validate_extraction_result(result)
        assert not is_valid
        assert "title" in error
    
    def test_validate_extraction_result_no_blocks(self):
        """Test validation of result without blocks."""
        result = ExtractionResult(title="Test")
        
        is_valid, error = validate_extraction_result(result)
        assert not is_valid
        assert "blocks" in error
    
    def test_validate_extraction_result_empty_blocks(self):
        """Test validation of result with empty blocks."""
        result = ExtractionResult(title="Test")
        result.add_block(Block(content=""))
        result.add_block(Block(content="  "))
        
        is_valid, error = validate_extraction_result(result)
        assert not is_valid


class TestErrorHandling:
    """Tests for error handling functions."""
    
    def test_handle_navigation_error(self):
        """Test handling of NavigationError."""
        error = NavigationError("Test Page")
        message = handle_exception(error)
        assert "navigate" in message.lower()
        assert "Test Page" in message
    
    def test_handle_generic_exception(self):
        """Test handling of generic exception."""
        error = ValueError("Something went wrong")
        message = handle_exception(error)
        assert "Unexpected error" in message
        assert "Something went wrong" in message

