"""Utility functions for AX element traversal and searching."""

from typing import List, Optional, Callable, Set
from .element import AXElement


def find_elements_by_role(
    element: AXElement, role: str, max_depth: int = 10
) -> List[AXElement]:
    """Find all elements with a specific role.
    
    Args:
        element: Root element to search from
        role: The AX role to search for (e.g., "AXButton")
        max_depth: Maximum depth to traverse
        
    Returns:
        List of matching elements
    """
    results = []
    _traverse_tree(
        element,
        lambda e: e.role == role,
        results,
        max_depth=max_depth,
    )
    return results


def find_element_by_role_and_title(
    element: AXElement, role: str, title: str, max_depth: int = 10
) -> Optional[AXElement]:
    """Find an element by role and title.
    
    Args:
        element: Root element to search from
        role: The AX role
        title: The title to match
        max_depth: Maximum depth to traverse
        
    Returns:
        First matching element or None
    """
    results = []
    _traverse_tree(
        element,
        lambda e: e.role == role and e.title == title,
        results,
        max_depth=max_depth,
        find_first=True,
    )
    return results[0] if results else None


def find_elements_by_predicate(
    element: AXElement,
    predicate: Callable[[AXElement], bool],
    max_depth: int = 10,
) -> List[AXElement]:
    """Find elements matching a predicate function.
    
    Args:
        element: Root element to search from
        predicate: Function that returns True for matching elements
        max_depth: Maximum depth to traverse
        
    Returns:
        List of matching elements
    """
    results = []
    _traverse_tree(element, predicate, results, max_depth=max_depth)
    return results


def find_text_elements(
    element: AXElement, max_depth: int = 10
) -> List[AXElement]:
    """Find all elements that contain text.
    
    Args:
        element: Root element to search from
        max_depth: Maximum depth to traverse
        
    Returns:
        List of elements with text content
    """
    text_roles = {
        "AXStaticText",
        "AXTextField",
        "AXTextArea",
        "AXHeading",
        "AXLabel",
    }
    
    def has_text(e: AXElement) -> bool:
        if e.role in text_roles:
            return True
        text = e.get_text_content()
        return text is not None and len(text.strip()) > 0
    
    return find_elements_by_predicate(element, has_text, max_depth)


def get_all_text(element: AXElement, max_depth: int = 10) -> List[str]:
    """Extract all text from an element and its children.
    
    Args:
        element: Root element to extract from
        max_depth: Maximum depth to traverse
        
    Returns:
        List of text strings in document order
    """
    text_elements = find_text_elements(element, max_depth)
    texts = []
    
    for elem in text_elements:
        text = elem.get_text_content()
        if text and text.strip():
            texts.append(text.strip())
    
    return texts


def find_scroll_area(element: AXElement, max_depth: int = 10) -> Optional[AXElement]:
    """Find the first scroll area in the element hierarchy.
    
    Args:
        element: Root element to search from
        max_depth: Maximum depth to traverse
        
    Returns:
        First scroll area element or None
    """
    results = []
    _traverse_tree(
        element,
        lambda e: e.role == "AXScrollArea",
        results,
        max_depth=max_depth,
        find_first=True,
    )
    return results[0] if results else None


def get_element_path(element: AXElement) -> List[str]:
    """Get the path from root to element as list of roles.
    
    Args:
        element: The element to get path for
        
    Returns:
        List of role names from root to element
    """
    path = []
    current = element
    
    while current:
        role = current.role or "Unknown"
        path.insert(0, role)
        current = current.parent
        
        # Prevent infinite loops
        if len(path) > 100:
            break
    
    return path


def print_tree(
    element: AXElement, max_depth: int = 5, _indent: int = 0, _current_depth: int = 0
):
    """Print the AX element tree for debugging.
    
    Args:
        element: Root element to print
        max_depth: Maximum depth to print
        _indent: Internal use for indentation
        _current_depth: Internal use for depth tracking
    """
    if _current_depth > max_depth:
        return
    
    indent_str = "  " * _indent
    role = element.role or "Unknown"
    title = element.title or ""
    value = element.value
    
    info = f"{indent_str}{role}"
    if title:
        info += f" title='{title}'"
    if value and isinstance(value, str) and len(value) < 50:
        info += f" value='{value}'"
    
    print(info)
    
    for child in element.children:
        print_tree(child, max_depth, _indent + 1, _current_depth + 1)


def _traverse_tree(
    element: AXElement,
    predicate: Callable[[AXElement], bool],
    results: List[AXElement],
    max_depth: int = 10,
    _current_depth: int = 0,
    find_first: bool = False,
    _visited: Optional[Set] = None,
):
    """Internal function to traverse the AX tree.
    
    Args:
        element: Current element
        predicate: Function to test each element
        results: List to append matching elements to
        max_depth: Maximum depth to traverse
        _current_depth: Current depth in traversal
        find_first: Stop after finding first match
        _visited: Set of visited elements to prevent cycles
    """
    if _current_depth > max_depth:
        return
    
    # Initialize visited set on first call
    if _visited is None:
        _visited = set()
    
    # Prevent cycles - use id of the underlying ax_element
    element_id = id(element.ax_element)
    if element_id in _visited:
        return
    _visited.add(element_id)
    
    # Check if current element matches
    try:
        if predicate(element):
            results.append(element)
            if find_first:
                return
    except Exception:
        # Ignore errors in predicate evaluation
        pass
    
    # Traverse children
    try:
        for child in element.children:
            _traverse_tree(
                child,
                predicate,
                results,
                max_depth,
                _current_depth + 1,
                find_first,
                _visited,
            )
            if find_first and results:
                return
    except Exception:
        # Ignore errors in child traversal
        pass


def wait_for_element(
    root: AXElement,
    predicate: Callable[[AXElement], bool],
    timeout: float = 5.0,
    poll_interval: float = 0.2,
) -> Optional[AXElement]:
    """Wait for an element matching a predicate to appear.
    
    Args:
        root: Root element to search from
        predicate: Function to test each element
        timeout: Maximum time to wait (seconds)
        poll_interval: Time between checks (seconds)
        
    Returns:
        First matching element or None if timeout
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        results = find_elements_by_predicate(root, predicate)
        if results:
            return results[0]
        time.sleep(poll_interval)
    
    return None


def get_visible_elements(element: AXElement) -> List[AXElement]:
    """Get all visible elements (with position and size).
    
    Args:
        element: Root element to search from
        
    Returns:
        List of visible elements
    """
    def is_visible(e: AXElement) -> bool:
        pos = e.position
        size = e.size
        return pos is not None and size is not None and size[0] > 0 and size[1] > 0
    
    return find_elements_by_predicate(element, is_visible)


def element_contains_text(element: AXElement, text: str, case_sensitive: bool = False) -> bool:
    """Check if an element contains specific text.
    
    Args:
        element: Element to check
        text: Text to search for
        case_sensitive: Whether to do case-sensitive search
        
    Returns:
        True if text is found in element
    """
    element_text = element.get_text_content()
    if not element_text:
        return False
    
    if not case_sensitive:
        element_text = element_text.lower()
        text = text.lower()
    
    return text in element_text

