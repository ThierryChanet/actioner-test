"""macOS Vision framework OCR implementation."""

from typing import Optional, Tuple
import Quartz
import Vision
import Cocoa
from ..ax.element import AXElement


class VisionOCR:
    """OCR using macOS Vision framework."""

    def __init__(self):
        """Initialize the Vision OCR handler."""
        self.recognition_level = Vision.VNRequestTextRecognitionLevelAccurate

    def extract_from_element(self, element: AXElement) -> Optional[str]:
        """Extract text from an AX element using OCR.
        
        Args:
            element: The AX element to extract from
            
        Returns:
            Extracted text or None if extraction failed
        """
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
        image = self._capture_element_screenshot((x, y), (width, height))
        if not image:
            return None
        
        return self._recognize_text(image)

    def _capture_element_screenshot(
        self, position: Tuple[float, float], size: Tuple[float, float]
    ) -> Optional[Cocoa.NSImage]:
        """Capture a screenshot of a screen region.
        
        Args:
            position: (x, y) position
            size: (width, height) size
            
        Returns:
            NSImage or None if capture failed
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
            
            return ns_image
        except Exception:
            return None

    def _recognize_text(self, image: Cocoa.NSImage) -> Optional[str]:
        """Recognize text in an image using Vision framework.
        
        Args:
            image: NSImage to process
            
        Returns:
            Recognized text or None
        """
        try:
            # Get CGImage from NSImage
            image_data = image.TIFFRepresentation()
            bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(image_data)
            cg_image = bitmap.CGImage()
            
            if not cg_image:
                return None
            
            # Create Vision request
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.setRecognitionLevel_(self.recognition_level)
            request.setUsesLanguageCorrection_(True)
            
            # Create request handler
            handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
                cg_image, {}
            )
            
            # Perform the request
            success, error = handler.performRequests_error_([request], None)
            
            if not success or error:
                return None
            
            # Get results
            results = request.results()
            if not results:
                return None
            
            # Extract text from observations
            text_parts = []
            for observation in results:
                if hasattr(observation, 'text'):
                    text_parts.append(observation.text())
            
            if text_parts:
                return " ".join(text_parts)
            
            return None
        except Exception:
            return None

    def set_recognition_level(self, accurate: bool = True):
        """Set the recognition level.
        
        Args:
            accurate: If True, use accurate (slower) recognition.
                     If False, use fast recognition.
        """
        if accurate:
            self.recognition_level = Vision.VNRequestTextRecognitionLevelAccurate
        else:
            self.recognition_level = Vision.VNRequestTextRecognitionLevelFast

    def is_available(self) -> bool:
        """Check if Vision OCR is available.
        
        Returns:
            True if Vision framework is available
        """
        try:
            # Try to create a request to verify Vision is available
            request = Vision.VNRecognizeTextRequest.alloc().init()
            return request is not None
        except Exception:
            return False

