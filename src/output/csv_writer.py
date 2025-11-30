"""CSV output writer for extraction results."""

import csv
from pathlib import Path
from typing import List
from ..notion.extractor import ExtractionResult


class CSVWriter:
    """Writes extraction results to CSV files."""

    def __init__(self, output_dir: str = "output"):
        """Initialize the CSV writer.
        
        Args:
            output_dir: Directory to write files to
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_extraction(
        self, result: ExtractionResult, filename: str = None
    ) -> Path:
        """Write extraction result to CSV file.
        
        Args:
            result: ExtractionResult to write
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to the written file
        """
        if not filename:
            # Generate filename from page title
            safe_title = self._sanitize_filename(result.title or "untitled")
            filename = f"{safe_title}_extraction.csv"
        
        filepath = self.output_dir / filename
        
        # Write blocks as rows
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Order",
                "Type",
                "Content",
                "Source",
                "Role",
            ])
            
            # Data rows
            for block in result.blocks:
                writer.writerow([
                    block.order,
                    block.block_type,
                    block.content,
                    block.source,
                    block.metadata.get("role", ""),
                ])
        
        return filepath

    def write_comparison(
        self, comparison_dict: dict, filename: str = None
    ) -> Path:
        """Write comparison summary to CSV file.
        
        Args:
            comparison_dict: Comparison result dictionary
            filename: Optional filename
            
        Returns:
            Path to the written file
        """
        if not filename:
            page_title = comparison_dict.get("summary", {}).get("gold_title", "untitled")
            safe_title = self._sanitize_filename(page_title)
            filename = f"{safe_title}_comparison.csv"
        
        filepath = self.output_dir / filename
        
        summary = comparison_dict.get("summary", {})
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Summary section
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Gold Title", summary.get("gold_title", "")])
            writer.writerow(["Extracted Title", summary.get("extracted_title", "")])
            writer.writerow(["Accuracy (%)", summary.get("accuracy", 0)])
            writer.writerow(["Block Match Rate (%)", summary.get("block_match_rate", 0)])
            writer.writerow(["Text Similarity (%)", summary.get("text_similarity", 0)])
            writer.writerow(["Gold Blocks", summary.get("gold_blocks", 0)])
            writer.writerow(["Extracted Blocks", summary.get("extracted_blocks", 0)])
            writer.writerow(["Missing Blocks", summary.get("missing_blocks", 0)])
            writer.writerow(["Extra Blocks", summary.get("extra_blocks", 0)])
            writer.writerow(["Text Mismatches", summary.get("text_mismatches", 0)])
            
            # Empty row
            writer.writerow([])
            
            # Missing blocks
            if comparison_dict.get("missing_blocks"):
                writer.writerow(["Missing Blocks"])
                writer.writerow(["Type", "Content"])
                for block in comparison_dict["missing_blocks"]:
                    writer.writerow([
                        block.get("type", ""),
                        block.get("content", ""),
                    ])
                writer.writerow([])
            
            # Extra blocks
            if comparison_dict.get("extra_blocks"):
                writer.writerow(["Extra Blocks"])
                writer.writerow(["Type", "Source", "Content"])
                for block in comparison_dict["extra_blocks"]:
                    writer.writerow([
                        block.get("type", ""),
                        block.get("source", ""),
                        block.get("content", ""),
                    ])
                writer.writerow([])
            
            # Text mismatches
            if comparison_dict.get("text_mismatches"):
                writer.writerow(["Text Mismatches"])
                writer.writerow(["Gold", "Extracted", "Similarity", "Source"])
                for mismatch in comparison_dict["text_mismatches"]:
                    writer.writerow([
                        mismatch.get("gold", ""),
                        mismatch.get("extracted", ""),
                        f"{mismatch.get('similarity', 0) * 100:.1f}%",
                        mismatch.get("source", ""),
                    ])
        
        return filepath

    def write_blocks_list(
        self, blocks: List, filename: str = "blocks.csv"
    ) -> Path:
        """Write a list of blocks to CSV.
        
        Args:
            blocks: List of Block objects
            filename: Filename for CSV
            
        Returns:
            Path to the written file
        """
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Order",
                "Type",
                "Content",
                "Source",
            ])
            
            # Data rows
            for block in blocks:
                writer.writerow([
                    block.order,
                    block.block_type,
                    block.content,
                    block.source,
                ])
        
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

