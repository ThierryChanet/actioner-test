"""Screen management utilities for agent tools.

Provides consistent screen switching and user notification patterns
for tools that need to interact with specific applications.
"""

import time
import subprocess
from typing import Optional, Callable, Any
from contextlib import contextmanager


class ScreenManager:
    """Manages screen/desktop switching and user notifications.

    This class provides a consistent pattern for tools that need to:
    1. Switch to a specific application (e.g., Notion)
    2. Perform actions
    3. Switch back to terminal
    4. Notify user with sound

    Usage:
        manager = ScreenManager(client)  # Auto-detects terminal
        # Or explicitly specify:
        manager = ScreenManager(client, terminal_name="Cursor")

        # Automatic context manager
        with manager.on_screen("Notion"):
            # Do work on Notion screen
            client.execute_action(...)
        # Automatically switches back and plays sound

        # Or manual control
        manager.switch_to("Notion")
        # Do work
        manager.switch_back()
    """

    def __init__(
        self,
        client: Any,
        terminal_name: Optional[str] = None,
        switch_delay: float = 2.0,
        notification_sound: str = "/System/Library/Sounds/Glass.aiff"
    ):
        """Initialize screen manager.

        Args:
            client: Computer use client with execute_action method
            terminal_name: Name of terminal application to switch back to (auto-detects if None)
            switch_delay: Seconds to wait after switching screens
            notification_sound: Path to notification sound file
        """
        self.client = client
        self.terminal_name = terminal_name or self._detect_terminal()
        self.switch_delay = switch_delay
        self.notification_sound = notification_sound
        self._current_screen: Optional[str] = None

    def _detect_terminal(self) -> str:
        """Auto-detect the current terminal application.
        
        Returns:
            Name of the detected terminal application
        """
        try:
            import subprocess
            # Use AppleScript to get the frontmost application
            script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
            end tell
            return frontApp
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                app_name = result.stdout.strip()
                lowered = app_name.lower() if app_name else ""

                # Avoid switching back to legacy terminal variants; prefer a generic terminal target
                if "iterm" in lowered:
                    return "Terminal"

                # Common terminal apps
                terminal_apps = ["Cursor", "Terminal", "Warp", "Alacritty", "Kitty", "Hyper"]
                for term in terminal_apps:
                    if term.lower() in lowered:
                        return term
                # Return whatever is frontmost as fallback
                return app_name if app_name else "Terminal"
        except Exception:
            pass
        
        # Final fallback
        return "Terminal"

    def switch_to(self, application: str, wait: Optional[float] = None) -> bool:
        """Switch to application screen.

        Args:
            application: Name of application to switch to
            wait: Override default switch delay

        Returns:
            True if switch succeeded, False otherwise
        """
        try:
            result = self.client.execute_action("switch_desktop", text=application)
            if result.success:
                self._current_screen = application
                time.sleep(wait if wait is not None else self.switch_delay)
                return True
            return False
        except Exception as e:
            print(f"Failed to switch to {application}: {e}")
            return False

    def switch_back(self, wait: Optional[float] = None) -> bool:
        """Switch back to terminal screen.

        Args:
            wait: Override default switch delay

        Returns:
            True if switch succeeded, False otherwise
        """
        try:
            result = self.client.execute_action("switch_desktop", text=self.terminal_name)
            if result.success:
                self._current_screen = self.terminal_name
                time.sleep(wait if wait is not None else self.switch_delay)
                return True
            return False
        except Exception as e:
            print(f"Failed to switch to {self.terminal_name}: {e}")
            return False

    def play_notification(self) -> None:
        """Play notification sound to alert user."""
        try:
            subprocess.run(
                ["afplay", self.notification_sound],
                check=False,
                capture_output=True,
                timeout=5
            )
        except Exception:
            # Fallback to terminal bell
            print('\a')

    def notify_user(self, message: Optional[str] = None) -> None:
        """Switch back to terminal and play notification.

        Args:
            message: Optional message to print before notification
        """
        if message:
            print(message)
        self.switch_back()
        self.play_notification()

    @contextmanager
    def on_screen(
        self,
        application: str,
        notify_on_return: bool = True,
        return_message: Optional[str] = None
    ):
        """Context manager for working on a specific application screen.

        Automatically switches to application, executes code, then switches
        back to terminal and optionally plays notification.

        Args:
            application: Application to switch to
            notify_on_return: Play notification when returning to terminal
            return_message: Optional message to show before notification

        Usage:
            with manager.on_screen("Notion"):
                # Work on Notion screen
                client.execute_action(...)
            # Automatically back to terminal with notification

        Example:
            with manager.on_screen("Notion", return_message="Task complete"):
                result = open_page("Recipe")
                extract_content(result)
            # User hears notification and sees "Task complete"
        """
        # Switch to application screen
        success = self.switch_to(application)
        if not success:
            raise RuntimeError(f"Failed to switch to {application}")

        try:
            yield self
        finally:
            # Always switch back and notify, even on error
            if return_message:
                print(return_message)
            self.switch_back()
            if notify_on_return:
                self.play_notification()

    def execute_on_screen(
        self,
        application: str,
        action: Callable[[], Any],
        notify_on_return: bool = True,
        return_message: Optional[str] = None
    ) -> Any:
        """Execute a function on a specific application screen.

        Args:
            application: Application to switch to
            action: Callable to execute on that screen
            notify_on_return: Play notification when returning
            return_message: Optional message before notification

        Returns:
            Result of action callable

        Example:
            def extract_recipe():
                return client.extract_content("Recipe")

            result = manager.execute_on_screen(
                "Notion",
                extract_recipe,
                return_message="Recipe extracted"
            )
        """
        with self.on_screen(application, notify_on_return, return_message):
            return action()


class NotionScreenManager(ScreenManager):
    """Specialized screen manager for Notion operations."""

    def __init__(self, client: Any, **kwargs):
        """Initialize Notion-specific screen manager.

        Args:
            client: Computer use client
            **kwargs: Additional arguments for ScreenManager
        """
        super().__init__(client, **kwargs)
        self.application = "Notion"

    @contextmanager
    def for_action(self, action_name: str = "action"):
        """Context manager for Notion actions.

        Args:
            action_name: Name of action for notification message

        Usage:
            with notion_manager.for_action("opening recipe"):
                # Do Notion work
                pass
            # Auto switches back with notification
        """
        with self.on_screen(
            self.application,
            notify_on_return=True,
            return_message=f"Notion {action_name} complete"
        ):
            yield self
