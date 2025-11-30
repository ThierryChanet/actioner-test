"""AX Client for connecting to and managing macOS application accessibility."""

from typing import Optional, List
import time
import Cocoa
from .element import AXElement
from . import bridge


class AXClient:
    """Client for accessing macOS Accessibility APIs."""

    def __init__(self, check_permissions: bool = True):
        """Initialize the AX client.
        
        Args:
            check_permissions: Whether to check permissions on init (default: True)
        """
        if check_permissions:
            self._check_permissions()

    def _check_permissions(self) -> bool:
        """Check if accessibility permissions are granted.
        
        Returns:
            True if permissions are granted
            
        Raises:
            PermissionError: If accessibility permissions are not granted
        """
        trusted = bridge.AXIsProcessTrusted()
        if not trusted:
            import sys
            python_path = sys.executable
            raise PermissionError(
                f"\n{'='*70}\n"
                f"ACCESSIBILITY PERMISSIONS NOT GRANTED\n"
                f"{'='*70}\n\n"
                f"This application needs Accessibility permissions to control Notion.\n\n"
                f"To fix this:\n"
                f"1. Open System Settings > Privacy & Security > Accessibility\n"
                f"2. Click the lock icon to make changes\n"
                f"3. Look for one of these in the list:\n"
                f"   - Your Terminal app (Terminal, iTerm2, etc.)\n"
                f"   - Python ({python_path})\n"
                f"4. Check the box to enable it\n"
                f"5. If not in the list, click '+' and add it\n"
                f"6. RESTART your terminal after granting permissions\n\n"
                f"Note: You may need to grant permissions to both your terminal AND Python.\n"
                f"{'='*70}\n"
            )
        return True
    
    @staticmethod
    def request_permissions() -> bool:
        """Request accessibility permissions with a system prompt.
        
        This will show a system dialog asking the user to grant permissions.
        
        Returns:
            True if already trusted, False otherwise
        """
        # Create a CFDictionary with the prompt option
        from Cocoa import NSDictionary
        import objc
        
        options_dict = NSDictionary.dictionaryWithObject_forKey_(
            True, "AXTrustedCheckOptionPrompt"
        )
        # Convert to void pointer for ctypes
        options_ptr = objc.pyobjc_id(options_dict)
        return bridge.AXIsProcessTrustedWithOptions(options_ptr)
    
    @staticmethod
    def is_trusted() -> bool:
        """Check if process has accessibility permissions without raising an error.
        
        Returns:
            True if permissions are granted, False otherwise
        """
        return bridge.AXIsProcessTrusted()

    def get_running_applications(self) -> List[dict]:
        """Get list of all running applications.
        
        Returns:
            List of dicts with app info (name, pid, bundle_id)
        """
        workspace = Cocoa.NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        
        result = []
        for app in apps:
            result.append({
                "name": app.localizedName(),
                "pid": app.processIdentifier(),
                "bundle_id": app.bundleIdentifier(),
            })
        return result

    def find_application(self, name: str = None, bundle_id: str = None) -> Optional[int]:
        """Find an application by name or bundle ID.
        
        Args:
            name: Application name (e.g., "Notion")
            bundle_id: Bundle identifier (e.g., "notion.id")
            
        Returns:
            Process ID (PID) if found, None otherwise
        """
        apps = self.get_running_applications()
        
        for app in apps:
            if name and app["name"] == name:
                return app["pid"]
            if bundle_id and app["bundle_id"] == bundle_id:
                return app["pid"]
        
        return None

    def get_application_element(self, pid: int) -> Optional[AXElement]:
        """Get the root AX element for an application.
        
        Args:
            pid: Process ID of the application
            
        Returns:
            AXElement for the application, or None if not accessible
        """
        try:
            app_ref = bridge.create_application_element(pid)
            if app_ref:
                return AXElement(app_ref)
        except Exception as e:
            import sys
            if hasattr(sys, '_debugging'):
                print(f"[DEBUG] Error creating application element: {e}")
            pass
        return None

    def get_focused_application(self) -> Optional[AXElement]:
        """Get the currently focused application.
        
        Returns:
            AXElement for the focused application
        """
        workspace = Cocoa.NSWorkspace.sharedWorkspace()
        active_app = workspace.frontmostApplication()
        if active_app:
            pid = active_app.processIdentifier()
            return self.get_application_element(pid)
        return None

    def activate_application(self, pid: int, wait: float = 0.5) -> bool:
        """Bring an application to the foreground.
        
        Args:
            pid: Process ID of the application
            wait: Time to wait after activation (seconds)
            
        Returns:
            True if successful
        """
        workspace = Cocoa.NSWorkspace.sharedWorkspace()
        apps = workspace.runningApplications()
        
        for app in apps:
            if app.processIdentifier() == pid:
                success = app.activateWithOptions_(
                    Cocoa.NSApplicationActivateIgnoringOtherApps
                )
                if success and wait > 0:
                    time.sleep(wait)
                return success
        
        return False

    def get_system_wide_element(self) -> AXElement:
        """Get the system-wide AX element.
        
        This can be used to access elements across all applications.
        
        Returns:
            AXElement for the system-wide element
        """
        system_ref = bridge.create_systemwide_element()
        return AXElement(system_ref)

    def get_element_at_position(self, x: float, y: float) -> Optional[AXElement]:
        """Get the AX element at a specific screen position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            AXElement at the position, or None if not found
        """
        system_element = self.get_system_wide_element()
        try:
            error_code, element_ref = Quartz.AXUIElementCopyElementAtPosition(
                system_element.ax_element, x, y, None
            )
            if error_code == Quartz.kAXErrorSuccess and element_ref:
                return AXElement(element_ref)
        except Exception:
            pass
        return None

    def wait_for_application(
        self, name: str = None, bundle_id: str = None, timeout: float = 10.0
    ) -> Optional[int]:
        """Wait for an application to be running.
        
        Args:
            name: Application name
            bundle_id: Bundle identifier
            timeout: Maximum time to wait (seconds)
            
        Returns:
            Process ID if found within timeout, None otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            pid = self.find_application(name=name, bundle_id=bundle_id)
            if pid:
                return pid
            time.sleep(0.5)
        
        return None

    def get_windows(self, app_element: AXElement, debug: bool = False) -> List[AXElement]:
        """Get all windows for an application.
        
        Args:
            app_element: The application's AXElement
            debug: If True, print debug information
            
        Returns:
            List of window AXElements
        """
        windows_ref = app_element.get_attribute("AXWindows")
        if debug:
            print(f"[DEBUG] AXWindows raw value: {windows_ref}")
            print(f"[DEBUG] AXWindows type: {type(windows_ref)}")
        if not windows_ref:
            return []
        if debug:
            print(f"[DEBUG] Windows list length: {len(windows_ref) if hasattr(windows_ref, '__len__') else 'N/A'}")
        return [AXElement(window) for window in windows_ref]

    def get_main_window(self, app_element: AXElement, debug: bool = False) -> Optional[AXElement]:
        """Get the main window of an application.
        
        Args:
            app_element: The application's AXElement
            debug: If True, print debug information
            
        Returns:
            Main window AXElement, or None if not found
        """
        if debug:
            print(f"[DEBUG] Getting main window for app element: {app_element}")
            print(f"[DEBUG] App role: {app_element.role}")
            print(f"[DEBUG] App attributes: {app_element.get_attributes()}")
        
        main_window_ref = app_element.get_attribute("AXMainWindow")
        if debug:
            print(f"[DEBUG] AXMainWindow: {main_window_ref}")
        if main_window_ref:
            return AXElement(main_window_ref)
        
        # Fallback: try to get the first focused window
        focused_window_ref = app_element.get_attribute("AXFocusedWindow")
        if debug:
            print(f"[DEBUG] AXFocusedWindow: {focused_window_ref}")
        if focused_window_ref:
            return AXElement(focused_window_ref)
        
        # Last resort: get the first window
        windows = self.get_windows(app_element, debug=debug)
        if debug:
            print(f"[DEBUG] Windows count: {len(windows)}")
            for i, win in enumerate(windows[:3]):  # Show first 3
                print(f"[DEBUG]   Window {i}: {win.title}")
        if windows:
            return windows[0]
        
        return None

