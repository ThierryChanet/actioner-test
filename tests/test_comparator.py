"""Tests for Comparator."""

import pytest
from src.validation.comparator import Comparator, ComparisonResult
from src.notion.extractor import Block, ExtractionResult


class TestComparator:
    """Tests for Comparator class."""
    
    def test_comparator_creation(self):
        """Test comparator initialization."""
        comparator = Comparator(similarity_threshold=0.8)
        assert comparator.similarity_threshold == 0.8
    
    def test_calculate_text_similarity_identical(self):
        """Test text similarity calculation for identical texts."""
        comparator = Comparator()
        similarity = comparator._calculate_text_similarity("hello world", "hello world")
        assert similarity == 1.0
    
    def test_calculate_text_similarity_different(self):
        """Test text similarity calculation for different texts."""
        comparator = Comparator()
        similarity = comparator._calculate_text_similarity("hello", "world")
        assert 0.0 <= similarity < 1.0
    
    def test_calculate_text_similarity_whitespace_normalized(self):
        """Test that whitespace is normalized in similarity calculation."""
        comparator = Comparator()
        similarity = comparator._calculate_text_similarity(
            "hello  world",
            "hello world"
        )
        assert similarity == 1.0
    
    def test_blocks_match_exactly(self):
        """Test exact block matching."""
        comparator = Comparator()
        block1 = Block(content="Test content")
        block2 = Block(content="Test content")
        block3 = Block(content="Different content")
        
        assert comparator._blocks_match_exactly(block1, block2)
        assert not comparator._blocks_match_exactly(block1, block3)
    
    def test_compare_perfect_match(self):
        """Test comparison with perfect match."""
        gold = ExtractionResult(title="Test")
        gold.add_block(Block(content="Block 1", order=0))
        gold.add_block(Block(content="Block 2", order=1))
        
        extracted = ExtractionResult(title="Test")
        extracted.add_block(Block(content="Block 1", order=0))
        extracted.add_block(Block(content="Block 2", order=1))
        
        comparator = Comparator()
        result = comparator.compare(gold, extracted)
        
        assert result.accuracy == 1.0
        assert result.block_match_rate == 1.0
        assert result.text_similarity == 1.0
        assert len(result.missing_blocks) == 0
        assert len(result.extra_blocks) == 0
    
    def test_compare_missing_blocks(self):
        """Test comparison with missing blocks."""
        gold = ExtractionResult(title="Test")
        gold.add_block(Block(content="Block 1"))
        gold.add_block(Block(content="Block 2"))
        
        extracted = ExtractionResult(title="Test")
        extracted.add_block(Block(content="Block 1"))
        
        comparator = Comparator()
        result = comparator.compare(gold, extracted)
        
        assert len(result.missing_blocks) == 1
        assert result.missing_blocks[0].content == "Block 2"
        assert result.block_match_rate == 0.5
    
    def test_compare_extra_blocks(self):
        """Test comparison with extra blocks."""
        gold = ExtractionResult(title="Test")
        gold.add_block(Block(content="Block 1"))
        
        extracted = ExtractionResult(title="Test")
        extracted.add_block(Block(content="Block 1"))
        extracted.add_block(Block(content="Block 2"))
        
        comparator = Comparator()
        result = comparator.compare(gold, extracted)
        
        assert len(result.extra_blocks) == 1
        assert result.extra_blocks[0].content == "Block 2"
    
    def test_comparison_result_to_dict(self):
        """Test comparison result conversion to dictionary."""
        gold = ExtractionResult(title="Gold")
        extracted = ExtractionResult(title="Extracted")
        
        result = ComparisonResult(gold, extracted)
        result.accuracy = 0.95
        result.block_match_rate = 0.9
        result.text_similarity = 0.98
        
        dict_result = result.to_dict()
        
        assert dict_result["gold_title"] == "Gold"
        assert dict_result["extracted_title"] == "Extracted"
        assert dict_result["accuracy"] == 95.0
        assert dict_result["block_match_rate"] == 90.0
        assert dict_result["text_similarity"] == 98.0

