"""Comparison logic for extracted vs. API content."""

from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
from ..notion.extractor import ExtractionResult, Block


class ComparisonResult:
    """Result of comparing two extraction results."""

    def __init__(self, gold: ExtractionResult, extracted: ExtractionResult):
        """Initialize comparison result.
        
        Args:
            gold: Gold standard (API) result
            extracted: Extracted (AX/OCR) result
        """
        self.gold = gold
        self.extracted = extracted
        
        self.missing_blocks: List[Block] = []
        self.extra_blocks: List[Block] = []
        self.matched_blocks: List[Tuple[Block, Block]] = []
        self.text_mismatches: List[Dict[str, Any]] = []
        
        self.accuracy: float = 0.0
        self.block_match_rate: float = 0.0
        self.text_similarity: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            "gold_title": self.gold.title,
            "extracted_title": self.extracted.title,
            "gold_blocks": len(self.gold.blocks),
            "extracted_blocks": len(self.extracted.blocks),
            "missing_blocks": len(self.missing_blocks),
            "extra_blocks": len(self.extra_blocks),
            "matched_blocks": len(self.matched_blocks),
            "text_mismatches": len(self.text_mismatches),
            "accuracy": round(self.accuracy * 100, 2),
            "block_match_rate": round(self.block_match_rate * 100, 2),
            "text_similarity": round(self.text_similarity * 100, 2),
        }


class Comparator:
    """Compares extracted content with API baseline."""

    def __init__(self, similarity_threshold: float = 0.8):
        """Initialize the comparator.
        
        Args:
            similarity_threshold: Minimum similarity ratio for matching blocks
        """
        self.similarity_threshold = similarity_threshold

    def compare(
        self, gold: ExtractionResult, extracted: ExtractionResult
    ) -> ComparisonResult:
        """Compare extracted content with gold standard.
        
        Args:
            gold: Gold standard from API
            extracted: Extracted content from AX/OCR
            
        Returns:
            ComparisonResult with detailed comparison
        """
        result = ComparisonResult(gold, extracted)
        
        # Match blocks
        self._match_blocks(result)
        
        # Calculate metrics
        self._calculate_metrics(result)
        
        return result

    def _match_blocks(self, result: ComparisonResult):
        """Match blocks between gold and extracted.
        
        Args:
            result: ComparisonResult to populate
        """
        gold_blocks = result.gold.blocks.copy()
        extracted_blocks = result.extracted.blocks.copy()
        
        # Track which blocks have been matched
        matched_gold = set()
        matched_extracted = set()
        
        # First pass: exact matches
        for i, gold_block in enumerate(gold_blocks):
            for j, ext_block in enumerate(extracted_blocks):
                if j in matched_extracted:
                    continue
                
                if self._blocks_match_exactly(gold_block, ext_block):
                    result.matched_blocks.append((gold_block, ext_block))
                    matched_gold.add(i)
                    matched_extracted.add(j)
                    break
        
        # Second pass: fuzzy matches
        for i, gold_block in enumerate(gold_blocks):
            if i in matched_gold:
                continue
            
            best_match = None
            best_similarity = 0.0
            
            for j, ext_block in enumerate(extracted_blocks):
                if j in matched_extracted:
                    continue
                
                similarity = self._calculate_text_similarity(
                    gold_block.content, ext_block.content
                )
                
                if similarity >= self.similarity_threshold and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (j, ext_block)
            
            if best_match:
                j, ext_block = best_match
                result.matched_blocks.append((gold_block, ext_block))
                matched_gold.add(i)
                matched_extracted.add(j)
                
                # Check if text is not identical
                if gold_block.content != ext_block.content:
                    result.text_mismatches.append({
                        "gold": gold_block.content,
                        "extracted": ext_block.content,
                        "similarity": best_similarity,
                        "source": ext_block.source,
                    })
        
        # Identify missing and extra blocks
        for i, gold_block in enumerate(gold_blocks):
            if i not in matched_gold:
                result.missing_blocks.append(gold_block)
        
        for j, ext_block in enumerate(extracted_blocks):
            if j not in matched_extracted:
                result.extra_blocks.append(ext_block)

    def _blocks_match_exactly(self, block1: Block, block2: Block) -> bool:
        """Check if two blocks match exactly.
        
        Args:
            block1: First block
            block2: Second block
            
        Returns:
            True if blocks match exactly
        """
        # Normalize whitespace
        text1 = " ".join(block1.content.split())
        text2 = " ".join(block2.content.split())
        
        return text1 == text2

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        # Normalize whitespace
        text1 = " ".join(text1.split())
        text2 = " ".join(text2.split())
        
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _calculate_metrics(self, result: ComparisonResult):
        """Calculate comparison metrics.
        
        Args:
            result: ComparisonResult to populate metrics for
        """
        gold_count = len(result.gold.blocks)
        extracted_count = len(result.extracted.blocks)
        matched_count = len(result.matched_blocks)
        
        # Block match rate: how many gold blocks were found
        if gold_count > 0:
            result.block_match_rate = matched_count / gold_count
        else:
            result.block_match_rate = 1.0 if extracted_count == 0 else 0.0
        
        # Text similarity: average similarity of matched blocks
        if matched_count > 0:
            similarities = []
            for gold_block, ext_block in result.matched_blocks:
                sim = self._calculate_text_similarity(
                    gold_block.content, ext_block.content
                )
                similarities.append(sim)
            result.text_similarity = sum(similarities) / len(similarities)
        else:
            result.text_similarity = 0.0
        
        # Overall accuracy: weighted average
        # 70% weight on block matching, 30% on text similarity
        result.accuracy = (
            0.7 * result.block_match_rate +
            0.3 * result.text_similarity
        )

    def compare_titles(self, gold: ExtractionResult, extracted: ExtractionResult) -> float:
        """Compare page titles.
        
        Args:
            gold: Gold standard result
            extracted: Extracted result
            
        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        if not gold.title or not extracted.title:
            return 0.0
        
        return self._calculate_text_similarity(gold.title, extracted.title)

    def identify_ocr_errors(self, result: ComparisonResult) -> List[Dict[str, Any]]:
        """Identify likely OCR-specific errors.
        
        Args:
            result: Comparison result
            
        Returns:
            List of OCR errors with details
        """
        ocr_errors = []
        
        for mismatch in result.text_mismatches:
            if mismatch.get("source") == "ocr":
                # Analyze common OCR errors
                error_info = {
                    "gold": mismatch["gold"],
                    "extracted": mismatch["extracted"],
                    "similarity": mismatch["similarity"],
                    "likely_issues": self._analyze_ocr_error(
                        mismatch["gold"], mismatch["extracted"]
                    ),
                }
                ocr_errors.append(error_info)
        
        return ocr_errors

    def _analyze_ocr_error(self, gold: str, extracted: str) -> List[str]:
        """Analyze OCR-specific errors.
        
        Args:
            gold: Gold standard text
            extracted: OCR extracted text
            
        Returns:
            List of likely issue descriptions
        """
        issues = []
        
        # Check for common OCR character confusions
        confusions = [
            ("0", "O"), ("1", "l"), ("5", "S"), ("8", "B"),
            ("rn", "m"), ("vv", "w"), ("cl", "d")
        ]
        
        for char1, char2 in confusions:
            if char1 in gold and char2 in extracted:
                issues.append(f"Possible '{char1}' -> '{char2}' confusion")
            elif char2 in gold and char1 in extracted:
                issues.append(f"Possible '{char2}' -> '{char1}' confusion")
        
        # Check length differences
        len_diff = abs(len(gold) - len(extracted))
        if len_diff > len(gold) * 0.2:
            issues.append(f"Significant length difference ({len_diff} chars)")
        
        # Check for missing/extra spaces
        if gold.replace(" ", "") == extracted.replace(" ", ""):
            issues.append("Spacing issues only")
        
        return issues

