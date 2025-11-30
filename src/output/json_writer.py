"""JSON output writer for extraction results."""

import json
from pathlib import Path
from typing import Any, Dict
from ..notion.extractor import ExtractionResult


class JSONWriter:
    """Writes extraction results to JSON files."""

    def __init__(self, output_dir: str = "output"):
        """Initialize the JSON writer.
        
        Args:
            output_dir: Directory to write files to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_extraction(
        self, result: ExtractionResult, filename: str = None
    ) -> Path:
        """Write extraction result to JSON file.
        
        Args:
            result: ExtractionResult to write
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to the written file
        """
        if not filename:
            # Generate filename from page title
            safe_title = self._sanitize_filename(result.title or "untitled")
            filename = f"{safe_title}_extraction.json"
        
        filepath = self.output_dir / filename
        
        data = result.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath

    def write_comparison(
        self, comparison_result: Dict[str, Any], filename: str = None
    ) -> Path:
        """Write comparison result to JSON file.
        
        Args:
            comparison_result: Comparison result dictionary
            filename: Optional filename
            
        Returns:
            Path to the written file
        """
        if not filename:
            page_title = comparison_result.get("summary", {}).get("gold_title", "untitled")
            safe_title = self._sanitize_filename(page_title)
            filename = f"{safe_title}_comparison.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(comparison_result, f, indent=2, ensure_ascii=False)
        
        return filepath

    def write_metadata(
        self, metadata: Dict[str, Any], filename: str = "metadata.json"
    ) -> Path:
        """Write metadata to JSON file.
        
        Args:
            metadata: Metadata dictionary
            filename: Filename for metadata
            
        Returns:
            Path to the written file
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        return filepath

    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as filename.
        
        Args:
            name: String to sanitize
            
        Returns:
            Safe filename string
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        
        # Limit length
        if len(name) > 100:
            name = name[:100]
        
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        
        return name or "untitled"

    def read_extraction(self, filepath: str) -> Dict[str, Any]:
        """Read extraction result from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Dictionary with extraction data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

