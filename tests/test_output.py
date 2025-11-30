"""Tests for output writers."""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
import csv

from src.output.json_writer import JSONWriter
from src.output.csv_writer import CSVWriter
from src.notion.extractor import Block, ExtractionResult


class TestJSONWriter:
    """Tests for JSONWriter."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    def test_json_writer_creation(self, temp_dir):
        """Test JSON writer initialization."""
        writer = JSONWriter(temp_dir)
        assert writer.output_dir == Path(temp_dir)
        assert writer.output_dir.exists()
    
    def test_write_extraction(self, temp_dir):
        """Test writing extraction result to JSON."""
        writer = JSONWriter(temp_dir)
        
        result = ExtractionResult(page_id="123", title="Test Page")
        result.add_block(Block(content="Block 1"))
        result.add_block(Block(content="Block 2"))
        
        filepath = writer.write_extraction(result)
        
        assert filepath.exists()
        assert filepath.suffix == ".json"
        
        # Read and verify
        with open(filepath) as f:
            data = json.load(f)
        
        assert data["page_id"] == "123"
        assert data["title"] == "Test Page"
        assert len(data["blocks"]) == 2
    
    def test_sanitize_filename(self, temp_dir):
        """Test filename sanitization."""
        writer = JSONWriter(temp_dir)
        
        assert writer._sanitize_filename("Normal Name") == "Normal Name"
        assert writer._sanitize_filename("Name/With\\Invalid:Chars") == "Name_With_Invalid_Chars"
        assert writer._sanitize_filename("") == "untitled"
        assert len(writer._sanitize_filename("a" * 200)) <= 100


class TestCSVWriter:
    """Tests for CSVWriter."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    def test_csv_writer_creation(self, temp_dir):
        """Test CSV writer initialization."""
        writer = CSVWriter(temp_dir)
        assert writer.output_dir == Path(temp_dir)
        assert writer.output_dir.exists()
    
    def test_write_extraction(self, temp_dir):
        """Test writing extraction result to CSV."""
        writer = CSVWriter(temp_dir)
        
        result = ExtractionResult(title="Test Page")
        result.add_block(Block(content="Block 1", order=0))
        result.add_block(Block(content="Block 2", order=1))
        
        filepath = writer.write_extraction(result)
        
        assert filepath.exists()
        assert filepath.suffix == ".csv"
        
        # Read and verify
        with open(filepath, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
        
        # Header + 2 data rows
        assert len(rows) == 3
        assert rows[0][0] == "Order"
        assert rows[1][2] == "Block 1"
        assert rows[2][2] == "Block 2"

