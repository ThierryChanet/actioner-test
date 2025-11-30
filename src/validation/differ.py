"""Diff report generation for comparison results."""

from typing import Optional
import difflib
from .comparator import ComparisonResult


class Differ:
    """Generates diff reports from comparison results."""

    def __init__(self):
        """Initialize the differ."""
        pass

    def generate_report(
        self, comparison: ComparisonResult, detailed: bool = True
    ) -> str:
        """Generate a human-readable diff report.
        
        Args:
            comparison: ComparisonResult to generate report from
            detailed: Whether to include detailed block-by-block comparison
            
        Returns:
            Formatted report string
        """
        lines = []
        
        # Header
        lines.append("=" * 80)
        lines.append("EXTRACTION COMPARISON REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Page info
        lines.append(f"Page: \"{comparison.gold.title}\"")
        lines.append(f"Gold Standard Source: {comparison.gold.metadata.get('source', 'api')}")
        lines.append(f"Extracted Source: AX + OCR")
        lines.append("")
        
        # Summary metrics
        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Overall Accuracy: {comparison.accuracy * 100:.1f}%")
        lines.append(f"Block Match Rate: {comparison.block_match_rate * 100:.1f}%")
        lines.append(f"Text Similarity: {comparison.text_similarity * 100:.1f}%")
        lines.append("")
        
        # Block counts
        lines.append(f"Gold Blocks: {len(comparison.gold.blocks)}")
        lines.append(f"Extracted Blocks: {len(comparison.extracted.blocks)}")
        lines.append(f"Matched Blocks: {len(comparison.matched_blocks)}")
        lines.append(f"Missing Blocks: {len(comparison.missing_blocks)}")
        lines.append(f"Extra Blocks: {len(comparison.extra_blocks)}")
        lines.append(f"Text Mismatches: {len(comparison.text_mismatches)}")
        lines.append("")
        
        if not detailed:
            lines.append("=" * 80)
            return "\n".join(lines)
        
        # Missing blocks
        if comparison.missing_blocks:
            lines.append("MISSING BLOCKS (In gold, not in extracted)")
            lines.append("-" * 80)
            for i, block in enumerate(comparison.missing_blocks, 1):
                lines.append(f"{i}. [{block.block_type}]")
                lines.append(f"   {self._truncate(block.content, 200)}")
                lines.append("")
        
        # Extra blocks
        if comparison.extra_blocks:
            lines.append("EXTRA BLOCKS (In extracted, not in gold)")
            lines.append("-" * 80)
            for i, block in enumerate(comparison.extra_blocks, 1):
                lines.append(f"{i}. [{block.block_type}] (source: {block.source})")
                lines.append(f"   {self._truncate(block.content, 200)}")
                lines.append("")
        
        # Text mismatches
        if comparison.text_mismatches:
            lines.append("TEXT MISMATCHES (Matched but different text)")
            lines.append("-" * 80)
            for i, mismatch in enumerate(comparison.text_mismatches, 1):
                lines.append(f"{i}. Similarity: {mismatch['similarity'] * 100:.1f}% "
                           f"(source: {mismatch['source']})")
                lines.append(f"   Gold:      {self._truncate(mismatch['gold'], 150)}")
                lines.append(f"   Extracted: {self._truncate(mismatch['extracted'], 150)}")
                lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)

    def generate_unified_diff(
        self, comparison: ComparisonResult
    ) -> str:
        """Generate a unified diff between gold and extracted.
        
        Args:
            comparison: ComparisonResult to generate diff from
            
        Returns:
            Unified diff string
        """
        # Create text representations
        gold_text = self._blocks_to_text(comparison.gold.blocks)
        extracted_text = self._blocks_to_text(comparison.extracted.blocks)
        
        # Generate unified diff
        diff = difflib.unified_diff(
            gold_text.splitlines(keepends=True),
            extracted_text.splitlines(keepends=True),
            fromfile="Gold (API)",
            tofile="Extracted (AX/OCR)",
            lineterm="",
        )
        
        return "".join(diff)

    def generate_html_diff(
        self, comparison: ComparisonResult
    ) -> str:
        """Generate an HTML diff report.
        
        Args:
            comparison: ComparisonResult to generate diff from
            
        Returns:
            HTML string
        """
        gold_text = self._blocks_to_text(comparison.gold.blocks)
        extracted_text = self._blocks_to_text(comparison.extracted.blocks)
        
        differ = difflib.HtmlDiff()
        html = differ.make_file(
            gold_text.splitlines(),
            extracted_text.splitlines(),
            fromdesc="Gold Standard (API)",
            todesc="Extracted (AX/OCR)",
        )
        
        return html

    def _blocks_to_text(self, blocks) -> str:
        """Convert blocks to text representation.
        
        Args:
            blocks: List of Block objects
            
        Returns:
            Text string
        """
        lines = []
        for block in blocks:
            lines.append(f"[{block.block_type}] {block.content}")
        return "\n".join(lines)

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    def generate_json_diff(self, comparison: ComparisonResult) -> dict:
        """Generate a JSON-serializable diff.
        
        Args:
            comparison: ComparisonResult to generate diff from
            
        Returns:
            Dictionary with diff information
        """
        return {
            "summary": comparison.to_dict(),
            "missing_blocks": [
                {
                    "type": block.block_type,
                    "content": block.content,
                    "order": block.order,
                }
                for block in comparison.missing_blocks
            ],
            "extra_blocks": [
                {
                    "type": block.block_type,
                    "content": block.content,
                    "source": block.source,
                    "order": block.order,
                }
                for block in comparison.extra_blocks
            ],
            "text_mismatches": [
                {
                    "gold": mismatch["gold"],
                    "extracted": mismatch["extracted"],
                    "similarity": mismatch["similarity"],
                    "source": mismatch["source"],
                }
                for mismatch in comparison.text_mismatches
            ],
        }

    def generate_summary(self, comparison: ComparisonResult) -> str:
        """Generate a one-line summary of the comparison.
        
        Args:
            comparison: ComparisonResult to summarize
            
        Returns:
            Summary string
        """
        accuracy = comparison.accuracy * 100
        missing = len(comparison.missing_blocks)
        extra = len(comparison.extra_blocks)
        mismatches = len(comparison.text_mismatches)
        
        return (
            f"Accuracy: {accuracy:.1f}% | "
            f"Missing: {missing} | "
            f"Extra: {extra} | "
            f"Mismatches: {mismatches}"
        )

