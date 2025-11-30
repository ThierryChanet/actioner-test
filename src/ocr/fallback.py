"""Tesseract OCR fallback implementation."""

from typing import Optional, Tuple
import tempfile
import os
from PIL import Image
import Quartz
import Cocoa
from ..ax.element import AXElement


class TesseractOCR:
    """OCR using Tesseract as fallback."""

    def __init__(self):
        """Initialize the Tesseract OCR handler."""
        self._check_tesseract()

    def _check_tesseract(self):
        """Check if Tesseract is available."""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.available = True
        except ImportError:
            self.pytesseract = None
            self.available = False

    def extract_from_element(self, element: AXElement) -> Optional[str]:
        """Extract text from an AX element using OCR.
        
        Args:
            element: The AX element to extract from
            
        Returns:
            Extracted text or None if extraction failed
        """
        if not self.available:
            return None
        
        # Get element position and size
        position = element.position
        size = element.size
        
        if not position or not size:
            return None
        
        # Capture screenshot of the element
        image = self._capture_element_screenshot(position, size)
        if not image:
            return None
        
        # Perform OCR
        text = self._recognize_text(image)
        return text

    def extract_from_rect(self, x: float, y: float, width: float, height: float) -> Optional[str]:
        """Extract text from a screen rectangle.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Width of region
            height: Height of region
            
        Returns:
            Extracted text or None if extraction failed
        """
        if not self.available:
            return None
        
        image = self._capture_element_screenshot((x, y), (width, height))
        if not image:
            return None
        
        return self._recognize_text(image)

    def _capture_element_screenshot(
        self, position: Tuple[float, float], size: Tuple[float, float]
    ) -> Optional[Image.Image]:
        """Capture a screenshot of a screen region.
        
        Args:
            position: (x, y) position
            size: (width, height) size
            
        Returns:
            PIL Image or None if capture failed
        """
        try:
            x, y = position
            width, height = size
            
            # Create CGRect for the region
            rect = Quartz.CGRectMake(x, y, width, height)
            
            # Capture the screen region
            image_ref = Quartz.CGWindowListCreateImage(
                rect,
                Quartz.kCGWindowListOptionOnScreenOnly,
                Quartz.kCGNullWindowID,
                Quartz.kCGWindowImageDefault
            )
            
            if not image_ref:
                return None
            
            # Convert to NSImage
            ns_image = Cocoa.NSImage.alloc().initWithCGImage_size_(
                image_ref, Cocoa.NSZeroSize
            )
            
            # Save to temporary file and load with PIL
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                # Get TIFF representation and save
                tiff_data = ns_image.TIFFRepresentation()
                bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(tiff_data)
                png_data = bitmap.representationUsingType_properties_(
                    Cocoa.NSPNGFileType, None
                )
                png_data.writeToFile_atomically_(tmp_path, False)
                
                # Load with PIL
                pil_image = Image.open(tmp_path)
                # Make a copy so we can close and delete the file
                pil_image_copy = pil_image.copy()
                pil_image.close()
                
                return pil_image_copy
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            
        except Exception:
            return None

    def _recognize_text(self, image: Image.Image) -> Optional[str]:
        """Recognize text in an image using Tesseract.
        
        Args:
            image: PIL Image to process
            
        Returns:
            Recognized text or None
        """
        if not self.available:
            return None
        
        try:
            text = self.pytesseract.image_to_string(image)
            if text and text.strip():
                return text.strip()
            return None
        except Exception:
            return None

    def is_available(self) -> bool:
        """Check if Tesseract OCR is available.
        
        Returns:
            True if Tesseract is available
        """
        return self.available


class OCRHandler:
    """Unified OCR handler that tries Vision first, then Tesseract."""

    def __init__(self):
        """Initialize the OCR handler."""
        from .vision import VisionOCR
        
        self.vision = VisionOCR()
        self.tesseract = TesseractOCR()
        
        # Prefer Vision if available
        self.primary = self.vision if self.vision.is_available() else self.tesseract
        self.fallback = self.tesseract if self.primary == self.vision else None

    def extract_from_element(self, element: AXElement) -> Optional[str]:
        """Extract text from an AX element using OCR.
        
        Tries Vision first, falls back to Tesseract if needed.
        
        Args:
            element: The AX element to extract from
            
        Returns:
            Extracted text or None if extraction failed
        """
        # Try primary OCR
        text = self.primary.extract_from_element(element)
        if text:
            return text
        
        # Try fallback if available
        if self.fallback:
            text = self.fallback.extract_from_element(element)
            if text:
                return text
        
        return None

    def extract_from_rect(self, x: float, y: float, width: float, height: float) -> Optional[str]:
        """Extract text from a screen rectangle.
        
        Args:
            x: X coordinate
            y: Y coordinate
            width: Width of region
            height: Height of region
            
        Returns:
            Extracted text or None if extraction failed
        """
        # Try primary OCR
        text = self.primary.extract_from_rect(x, y, width, height)
        if text:
            return text
        
        # Try fallback if available
        if self.fallback:
            text = self.fallback.extract_from_rect(x, y, width, height)
            if text:
                return text
        
        return None

    def is_available(self) -> bool:
        """Check if any OCR method is available.
        
        Returns:
            True if at least one OCR method is available
        """
        return self.vision.is_available() or self.tesseract.is_available()

    def get_active_handler(self) -> str:
        """Get the name of the active OCR handler.
        
        Returns:
            Name of the active handler ("vision", "tesseract", or "none")
        """
        if self.primary == self.vision and self.vision.is_available():
            return "vision"
        elif self.tesseract.is_available():
            return "tesseract"
        else:
            return "none"

