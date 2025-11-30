"""Bridge module for AX API functions using ctypes.

This module loads ApplicationServices AX functions via ctypes since they're not
properly exposed through pyobjc's Quartz module.
"""

import ctypes
import ctypes.util
import objc
from Cocoa import NSString

# Load ApplicationServices framework
_appservices_path = ctypes.util.find_library('ApplicationServices')
if not _appservices_path:
    _appservices_path = '/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices'
_lib = ctypes.CDLL(_appservices_path)

# AX Error codes
kAXErrorSuccess = 0
kAXErrorFailure = -25200
kAXErrorIllegalArgument = -25201
kAXErrorInvalidUIElement = -25202
kAXErrorInvalidUIElementObserver = -25203
kAXErrorCannotComplete = -25204
kAXErrorAttributeUnsupported = -25205
kAXErrorActionUnsupported = -25206
kAXErrorNotificationUnsupported = -25207
kAXErrorNotImplemented = -25208
kAXErrorNotificationAlreadyRegistered = -25209
kAXErrorNotificationNotRegistered = -25210
kAXErrorAPIDisabled = -25211
kAXErrorNoValue = -25212
kAXErrorParameterizedAttributeUnsupported = -25213
kAXErrorNotEnoughPrecision = -25214

# Configure AXIsProcessTrusted
AXIsProcessTrusted = _lib.AXIsProcessTrusted
AXIsProcessTrusted.restype = ctypes.c_bool
AXIsProcessTrusted.argtypes = []

# Configure AXIsProcessTrustedWithOptions
AXIsProcessTrustedWithOptions = _lib.AXIsProcessTrustedWithOptions
AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]

# Configure AXUIElementCreateApplication
AXUIElementCreateApplication = _lib.AXUIElementCreateApplication
AXUIElementCreateApplication.restype = ctypes.c_void_p
AXUIElementCreateApplication.argtypes = [ctypes.c_int32]

# Configure AXUIElementCreateSystemWide
AXUIElementCreateSystemWide = _lib.AXUIElementCreateSystemWide
AXUIElementCreateSystemWide.restype = ctypes.c_void_p
AXUIElementCreateSystemWide.argtypes = []

# Configure AXUIElementCopyAttributeNames
AXUIElementCopyAttributeNames = _lib.AXUIElementCopyAttributeNames
AXUIElementCopyAttributeNames.restype = ctypes.c_int
AXUIElementCopyAttributeNames.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]

# Configure AXUIElementCopyAttributeValue
AXUIElementCopyAttributeValue = _lib.AXUIElementCopyAttributeValue
AXUIElementCopyAttributeValue.restype = ctypes.c_int
AXUIElementCopyAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]

# Configure AXUIElementSetAttributeValue
AXUIElementSetAttributeValue = _lib.AXUIElementSetAttributeValue
AXUIElementSetAttributeValue.restype = ctypes.c_int
AXUIElementSetAttributeValue.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

# Configure AXUIElementCopyActionNames
AXUIElementCopyActionNames = _lib.AXUIElementCopyActionNames
AXUIElementCopyActionNames.restype = ctypes.c_int
AXUIElementCopyActionNames.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]

# Configure AXUIElementPerformAction
AXUIElementPerformAction = _lib.AXUIElementPerformAction
AXUIElementPerformAction.restype = ctypes.c_int
AXUIElementPerformAction.argtypes = [ctypes.c_void_p, ctypes.c_void_p]


def create_application_element(pid: int):
    """Create an AXUIElement for an application by PID.
    
    Args:
        pid: Process ID of the application
        
    Returns:
        ObjC AXUIElementRef object or None if failed
    """
    ptr = AXUIElementCreateApplication(pid)
    if not ptr:
        return None
    return objc.objc_object(c_void_p=ptr)


def create_systemwide_element():
    """Create a system-wide AXUIElement.
    
    Returns:
        ObjC AXUIElementRef object
    """
    ptr = AXUIElementCreateSystemWide()
    return objc.objc_object(c_void_p=ptr)


def copy_attribute_names(element):
    """Get list of attribute names for an element.
    
    Args:
        element: AXUIElementRef object
        
    Returns:
        Tuple of (error_code, list_of_names)
    """
    names_ptr = ctypes.c_void_p()
    elem_ptr = objc.pyobjc_id(element)
    error_code = AXUIElementCopyAttributeNames(elem_ptr, ctypes.byref(names_ptr))
    
    if error_code == kAXErrorSuccess and names_ptr.value:
        names_obj = objc.objc_object(c_void_p=names_ptr.value)
        return (error_code, list(names_obj))
    return (error_code, [])


def copy_attribute_value(element, attribute_name: str):
    """Get the value of an attribute.
    
    Args:
        element: AXUIElementRef object
        attribute_name: Name of the attribute (e.g., "AXRole")
        
    Returns:
        Tuple of (error_code, value)
    """
    value_ptr = ctypes.c_void_p()
    elem_ptr = objc.pyobjc_id(element)
    
    # Use NSString and extract its underlying pointer using objc internals
    attr_str = NSString.stringWithString_(attribute_name)
    # objc strings have an internal pointer we can access via __pyobjc_object__
    # which returns the underlying object - then we get its id
    attr_underlying = attr_str.__pyobjc_object__
    # Use id() to get memory address, but we need to use objc.pyobjc_id on the NSString itself
    # Actually, let's try using ctypes.cast to convert the string object
    # The trick is to pass the actual PyObjC object ID
    try:
        # For NSString/CFString, we need to pass the actual object pointer
        # Let's use the internal objc function to get the pointer
        import objc._objc as _objc
        if hasattr(_objc, 'object_to_id'):
            attr_ptr = _objc.object_to_id(attr_str)
        else:
            # Fallback: encode the string as UTF-8 bytes and pass directly
            # C functions can accept Python strings if they're the right type
            attr_ptr = objc.pyobjc_id(attr_str.__pyobjc_object__)
    except:
        # Last resort: create CFStringRef from bytes
        from CoreFoundation import CFStringCreateWithBytes, kCFStringEncodingUTF8
        attr_bytes = attribute_name.encode('utf-8')
        attr_cfstr = CFStringCreateWithBytes(
            None,  # allocator
            attr_bytes,  # bytes
            len(attr_bytes),  # length
            kCFStringEncodingUTF8,  # encoding
            False  # isExternalRepresentation
        )
        attr_ptr = objc.pyobjc_id(attr_cfstr.__pyobjc_object__)
    
    error_code = AXUIElementCopyAttributeValue(elem_ptr, attr_ptr, ctypes.byref(value_ptr))
    
    if error_code == kAXErrorSuccess and value_ptr.value:
        value_obj = objc.objc_object(c_void_p=value_ptr.value)
        return (error_code, value_obj)
    return (error_code, None)


def set_attribute_value(element, attribute_name: str, value):
    """Set the value of an attribute.
    
    Args:
        element: AXUIElementRef object
        attribute_name: Name of the attribute
        value: Value to set
        
    Returns:
        Error code
    """
    elem_ptr = objc.pyobjc_id(element)
    attr_str = NSString.stringWithString_(attribute_name)
    attr_ptr = objc.pyobjc_id(attr_str.__pyobjc_object__)
    value_ptr = objc.pyobjc_id(value)
    
    return AXUIElementSetAttributeValue(elem_ptr, attr_ptr, value_ptr)


def copy_action_names(element):
    """Get list of action names for an element.
    
    Args:
        element: AXUIElementRef object
        
    Returns:
        Tuple of (error_code, list_of_names)
    """
    names_ptr = ctypes.c_void_p()
    elem_ptr = objc.pyobjc_id(element)
    error_code = AXUIElementCopyActionNames(elem_ptr, ctypes.byref(names_ptr))
    
    if error_code == kAXErrorSuccess and names_ptr.value:
        names_obj = objc.objc_object(c_void_p=names_ptr.value)
        return (error_code, list(names_obj))
    return (error_code, [])


def perform_action(element, action_name: str):
    """Perform an action on an element.
    
    Args:
        element: AXUIElementRef object
        action_name: Name of the action (e.g., "AXPress")
        
    Returns:
        Error code
    """
    elem_ptr = objc.pyobjc_id(element)
    action_str = NSString.stringWithString_(action_name)
    action_ptr = objc.pyobjc_id(action_str.__pyobjc_object__)
    
    return AXUIElementPerformAction(elem_ptr, action_ptr)

