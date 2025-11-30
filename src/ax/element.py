"""AXUIElement wrapper for pythonic access to macOS Accessibility APIs."""

from typing import Optional, List, Any, Dict
import Cocoa
from . import bridge


class AXElement:
    """Wrapper around AXUIElementRef for easier Python interaction."""

    def __init__(self, ax_element):
        """Initialize with an AXUIElementRef.
        
        Args:
            ax_element: PyObjC AXUIElementRef object
        """
        self.ax_element = ax_element
        self._cache = {}

    def get_attribute(self, attribute: str) -> Optional[Any]:
        """Get an accessibility attribute value.
        
        Args:
            attribute: The AX attribute name (e.g., "AXRole", "AXValue")
            
        Returns:
            The attribute value, or None if not available
        """
        try:
            error_code, value = bridge.copy_attribute_value(self.ax_element, attribute)
            if error_code == bridge.kAXErrorSuccess:
                return value
            return None
        except Exception:
            return None

    def set_attribute(self, attribute: str, value: Any) -> bool:
        """Set an accessibility attribute value.
        
        Args:
            attribute: The AX attribute name
            value: The value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            error_code = bridge.set_attribute_value(self.ax_element, attribute, value)
            return error_code == bridge.kAXErrorSuccess
        except Exception:
            return False

    def get_attributes(self) -> List[str]:
        """Get list of available attribute names.
        
        Returns:
            List of attribute names
        """
        try:
            error_code, attributes = bridge.copy_attribute_names(self.ax_element)
            if error_code == bridge.kAXErrorSuccess:
                return list(attributes)
            return []
        except Exception:
            return []

    def get_actions(self) -> List[str]:
        """Get list of available action names.
        
        Returns:
            List of action names (e.g., "AXPress", "AXShowMenu")
        """
        try:
            error_code, actions = bridge.copy_action_names(self.ax_element)
            if error_code == bridge.kAXErrorSuccess:
                return list(actions)
            return []
        except Exception:
            return []

    def perform_action(self, action: str) -> bool:
        """Perform an accessibility action.
        
        Args:
            action: The action name (e.g., "AXPress")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            error_code = bridge.perform_action(self.ax_element, action)
            return error_code == bridge.kAXErrorSuccess
        except Exception:
            return False

    @property
    def role(self) -> Optional[str]:
        """Get the element's role."""
        return self.get_attribute("AXRole")

    @property
    def subrole(self) -> Optional[str]:
        """Get the element's subrole."""
        return self.get_attribute("AXSubrole")

    @property
    def title(self) -> Optional[str]:
        """Get the element's title."""
        return self.get_attribute("AXTitle")

    @property
    def value(self) -> Optional[Any]:
        """Get the element's value."""
        return self.get_attribute("AXValue")

    @property
    def description(self) -> Optional[str]:
        """Get the element's description."""
        return self.get_attribute("AXDescription")

    @property
    def children(self) -> List["AXElement"]:
        """Get the element's children as AXElement objects."""
        children_ref = self.get_attribute("AXChildren")
        if not children_ref:
            return []
        return [AXElement(child) for child in children_ref]

    @property
    def parent(self) -> Optional["AXElement"]:
        """Get the element's parent."""
        parent_ref = self.get_attribute("AXParent")
        if parent_ref:
            return AXElement(parent_ref)
        return None

    @property
    def position(self) -> Optional[tuple]:
        """Get the element's position as (x, y)."""
        pos = self.get_attribute("AXPosition")
        if pos:
            # Handle different return types (NSValue, CGPoint, dict, etc.)
            if hasattr(pos, 'x') and hasattr(pos, 'y'):
                return (pos.x, pos.y)
            elif hasattr(pos, 'pointValue'):
                point = pos.pointValue()
                return (point.x, point.y)
            elif isinstance(pos, (list, tuple)) and len(pos) >= 2:
                return (pos[0], pos[1])
            # If it's a dict-like object
            elif hasattr(pos, '__getitem__'):
                try:
                    return (pos['X'], pos['Y'])
                except:
                    pass
        return None

    @property
    def size(self) -> Optional[tuple]:
        """Get the element's size as (width, height)."""
        size = self.get_attribute("AXSize")
        if size:
            # Handle different return types (NSValue, CGSize, dict, etc.)
            if hasattr(size, 'width') and hasattr(size, 'height'):
                return (size.width, size.height)
            elif hasattr(size, 'sizeValue'):
                sz = size.sizeValue()
                return (sz.width, sz.height)
            elif isinstance(size, (list, tuple)) and len(size) >= 2:
                return (size[0], size[1])
            # If it's a dict-like object
            elif hasattr(size, '__getitem__'):
                try:
                    return (size['Width'], size['Height'])
                except:
                    pass
        return None

    @property
    def enabled(self) -> bool:
        """Check if the element is enabled."""
        return self.get_attribute("AXEnabled") or False

    @property
    def focused(self) -> bool:
        """Check if the element is focused."""
        return self.get_attribute("AXFocused") or False

    def set_focused(self, focused: bool) -> bool:
        """Set the element's focus state."""
        return self.set_attribute("AXFocused", focused)

    def get_text_content(self) -> Optional[str]:
        """Get text content from the element.
        
        Tries multiple attributes: AXValue, AXTitle, AXDescription.
        
        Returns:
            Text content or None if not available
        """
        # Try value first (for text fields, labels)
        text = self.value
        if text and isinstance(text, str):
            return text

        # Try title (for buttons, windows)
        text = self.title
        if text:
            return text

        # Try description as last resort
        text = self.description
        if text:
            return text

        return None

    def scroll_to_visible(self) -> bool:
        """Scroll the element into view if it's in a scrollable area."""
        # Try to get the scroll area parent
        parent = self.parent
        while parent:
            if parent.role == "AXScrollArea":
                # Set this element as the selected item to scroll it into view
                parent.set_attribute("AXVisibleChildren", [self.ax_element])
                return True
            parent = parent.parent
        return False

    def press(self) -> bool:
        """Perform a press action on the element."""
        return self.perform_action("AXPress")

    def __repr__(self) -> str:
        """String representation of the element."""
        role = self.role or "Unknown"
        title = self.title or ""
        if title:
            return f"<AXElement role={role} title='{title}'>"
        return f"<AXElement role={role}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert element to dictionary representation.
        
        Returns:
            Dictionary with element attributes
        """
        return {
            "role": self.role,
            "subrole": self.subrole,
            "title": self.title,
            "value": self.value,
            "description": self.description,
            "position": self.position,
            "size": self.size,
            "enabled": self.enabled,
            "focused": self.focused,
        }

