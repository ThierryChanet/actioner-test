"""Tests for database extraction functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.database_extractor import (
    extract_database_pages,
    get_database_pages_list,
    extract_single_page,
    save_results
)
from src.notion.extractor import ExtractionResult, Block


class TestDatabaseExtractor:
    """Test database extraction functions."""
    
    @patch('src.database_extractor.NotionAPIClient')
    def test_extract_database_pages_basic(self, mock_client_class):
        """Test basic database extraction."""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        
        # Create mock results
        result1 = ExtractionResult(page_id="page1", title="Recipe 1")
        result1.add_block(Block("Ingredients", "heading"))
        result1.add_block(Block("Mix flour", "text"))
        
        result2 = ExtractionResult(page_id="page2", title="Recipe 2")
        result2.add_block(Block("Steps", "heading"))
        
        mock_client.extract_database_pages.return_value = [result1, result2]
        
        # Call function
        results = extract_database_pages(
            database_id="test-db-id",
            notion_token="test-token",
            limit=2
        )
        
        # Verify
        assert len(results) == 2
        assert results[0].title == "Recipe 1"
        assert results[1].title == "Recipe 2"
        assert len(results[0].blocks) == 2
        
        # Verify API calls
        mock_client.test_connection.assert_called_once()
        mock_client.extract_database_pages.assert_called_once_with("test-db-id", limit=2)
    
    @patch('src.database_extractor.NotionAPIClient')
    def test_extract_database_pages_connection_failure(self, mock_client_class):
        """Test handling of connection failures."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = False
        
        with pytest.raises(RuntimeError, match="Failed to connect"):
            extract_database_pages(
                database_id="test-db-id",
                notion_token="bad-token",
                limit=10
            )
    
    @patch('src.database_extractor.NotionAPIClient')
    def test_get_database_pages_list(self, mock_client_class):
        """Test getting database pages list."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        
        mock_pages = [
            {"id": "page1", "properties": {"Name": {"title": [{"plain_text": "Recipe 1"}]}}},
            {"id": "page2", "properties": {"Name": {"title": [{"plain_text": "Recipe 2"}]}}}
        ]
        mock_client.query_database.return_value = mock_pages
        
        # Call function
        pages = get_database_pages_list(
            database_id="test-db-id",
            notion_token="test-token",
            limit=10
        )
        
        # Verify
        assert len(pages) == 2
        assert pages[0]["id"] == "page1"
        assert pages[1]["id"] == "page2"
        
        mock_client.query_database.assert_called_once_with("test-db-id", page_size=10)
    
    @patch('src.database_extractor.NotionAPIClient')
    def test_extract_single_page(self, mock_client_class):
        """Test extracting a single page."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        
        # Create mock result
        result = ExtractionResult(page_id="page1", title="Single Page")
        result.add_block(Block("Content", "text"))
        mock_client.page_to_extraction_result.return_value = result
        
        # Call function
        extracted = extract_single_page(
            page_id="page1",
            notion_token="test-token"
        )
        
        # Verify
        assert extracted.title == "Single Page"
        assert len(extracted.blocks) == 1
        assert extracted.blocks[0].content == "Content"
        
        mock_client.page_to_extraction_result.assert_called_once_with("page1")
    
    @patch('src.database_extractor.CSVWriter')
    @patch('src.database_extractor.JSONWriter')
    def test_save_results_json(self, mock_json_writer_class, mock_csv_writer_class):
        """Test saving results as JSON."""
        mock_json_writer = Mock()
        mock_json_writer_class.return_value = mock_json_writer
        mock_json_writer.write_extraction.return_value = "output/test.json"
        
        # Create test results
        result = ExtractionResult(title="Test")
        result.add_block(Block("Test content", "text"))
        
        # Save as JSON
        save_results([result], "output", "json", verbose=False)
        
        # Verify
        mock_json_writer_class.assert_called_once_with("output")
        mock_json_writer.write_extraction.assert_called_once_with(result)
        mock_csv_writer_class.assert_not_called()
    
    @patch('src.database_extractor.CSVWriter')
    @patch('src.database_extractor.JSONWriter')
    def test_save_results_both(self, mock_json_writer_class, mock_csv_writer_class):
        """Test saving results as both JSON and CSV."""
        mock_json_writer = Mock()
        mock_csv_writer = Mock()
        mock_json_writer_class.return_value = mock_json_writer
        mock_csv_writer_class.return_value = mock_csv_writer
        
        result = ExtractionResult(title="Test")
        result.add_block(Block("Test content", "text"))
        
        # Save as both
        save_results([result], "output", "both", verbose=False)
        
        # Verify both writers called
        mock_json_writer_class.assert_called_once_with("output")
        mock_csv_writer_class.assert_called_once_with("output")
        mock_json_writer.write_extraction.assert_called_once()
        mock_csv_writer.write_extraction.assert_called_once()
    
    @patch('src.database_extractor.NotionAPIClient')
    def test_extract_database_pages_with_verbose(self, mock_client_class, capsys):
        """Test verbose output during extraction."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        
        result = ExtractionResult(page_id="page1", title="Test")
        result.add_block(Block("Content", "text"))
        mock_client.extract_database_pages.return_value = [result]
        mock_client.get_database.return_value = {
            "title": [{"plain_text": "Test Database"}]
        }
        
        # Call with verbose=True
        extract_database_pages(
            database_id="test-db",
            notion_token="token",
            limit=1,
            verbose=True
        )
        
        # Check output
        captured = capsys.readouterr()
        assert "Connecting to Notion API" in captured.out
        assert "Connected to Notion API" in captured.out
        assert "Database: Test Database" in captured.out
    
    @patch('src.database_extractor.NotionAPIClient')
    def test_extract_database_pages_empty(self, mock_client_class):
        """Test extracting from empty database."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        mock_client.extract_database_pages.return_value = []
        
        results = extract_database_pages(
            database_id="empty-db",
            notion_token="token",
            limit=10
        )
        
        assert len(results) == 0

