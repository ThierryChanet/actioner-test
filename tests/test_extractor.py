"""Tests for NotionExtractor."""

import pytest
from unittest.mock import Mock, MagicMock
from src.notion.extractor import NotionExtractor, Block, ExtractionResult
from src.notion.detector import NotionDetector


class TestBlock:
    """Tests for Block class."""
    
    def test_block_creation(self):
        """Test block creation with default values."""
        block = Block(content="Test content")
        assert block.content == "Test content"
        assert block.block_type == "text"
        assert block.source == "ax"
        assert block.order == 0
        assert block.metadata == {}
    
    def test_block_to_dict(self):
        """Test block conversion to dictionary."""
        block = Block(
            content="Test",
            block_type="heading",
            source="ocr",
            order=5,
            metadata={"role": "AXHeading"}
        )
        result = block.to_dict()
        assert result["type"] == "heading"
        assert result["content"] == "Test"
        assert result["source"] == "ocr"
        assert result["order"] == 5
        assert result["metadata"]["role"] == "AXHeading"


class TestExtractionResult:
    """Tests for ExtractionResult class."""
    
    def test_result_creation(self):
        """Test extraction result creation."""
        result = ExtractionResult(page_id="123", title="Test Page")
        assert result.page_id == "123"
        assert result.title == "Test Page"
        assert len(result.blocks) == 0
        assert result.metadata == {}
    
    def test_add_block(self):
        """Test adding blocks to result."""
        result = ExtractionResult(title="Test")
        block1 = Block(content="Block 1")
        block2 = Block(content="Block 2")
        
        result.add_block(block1)
        result.add_block(block2)
        
        assert len(result.blocks) == 2
        assert result.blocks[0].content == "Block 1"
        assert result.blocks[1].content == "Block 2"
    
    def test_to_dict(self):
        """Test result conversion to dictionary."""
        result = ExtractionResult(page_id="123", title="Test")
        result.add_block(Block(content="Test"))
        
        dict_result = result.to_dict()
        assert dict_result["page_id"] == "123"
        assert dict_result["title"] == "Test"
        assert len(dict_result["blocks"]) == 1


class TestNotionExtractor:
    """Tests for NotionExtractor class."""
    
    def test_extractor_creation(self):
        """Test extractor initialization."""
        mock_detector = Mock(spec=NotionDetector)
        extractor = NotionExtractor(mock_detector)
        assert extractor.detector == mock_detector
        assert extractor.ocr_handler is None
    
    def test_set_ocr_handler(self):
        """Test setting OCR handler."""
        mock_detector = Mock(spec=NotionDetector)
        extractor = NotionExtractor(mock_detector)
        mock_ocr = Mock()
        
        extractor.set_ocr_handler(mock_ocr)
        assert extractor.ocr_handler == mock_ocr
    
    def test_role_to_block_type(self):
        """Test role to block type mapping."""
        mock_detector = Mock(spec=NotionDetector)
        extractor = NotionExtractor(mock_detector)
        
        assert extractor._role_to_block_type("AXHeading") == "heading"
        assert extractor._role_to_block_type("AXStaticText") == "text"
        assert extractor._role_to_block_type("AXLink") == "link"
        assert extractor._role_to_block_type("AXUnknown") == "text"

