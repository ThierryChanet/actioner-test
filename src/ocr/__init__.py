"""OCR fallback module for inaccessible elements."""

from .vision import VisionOCR
from .fallback import TesseractOCR

__all__ = ["VisionOCR", "TesseractOCR"]

