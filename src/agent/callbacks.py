"""Custom callbacks for user interaction and progress tracking."""

import sys
from typing import Any, Dict, List, Optional
from langchain.callbacks.base import BaseCallbackHandler


class UserInputCallback(BaseCallbackHandler):
    """Callback that prompts user for input when agent needs clarification."""
    
    def __init__(self, verbose: bool = False):
        """Initialize callback.
        
        Args:
            verbose: Whether to show detailed progress
        """
        self.verbose = verbose
    
    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        **kwargs: Any
    ) -> None:
        """Called when tool starts."""
        if self.verbose:
            tool_name = serialized.get("name", "unknown")
            print(f"\n🔧 Using tool: {tool_name}")
            print(f"   Input: {input_str[:100]}...")
    
    def on_tool_end(
        self,
        output: str,
        **kwargs: Any
    ) -> None:
        """Called when tool ends."""
        if self.verbose:
            print(f"   ✓ Tool completed")
    
    def on_tool_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """Called when tool errors."""
        print(f"   ❌ Tool error: {error}")
    
    def on_agent_action(
        self,
        action: Any,
        **kwargs: Any
    ) -> None:
        """Called when agent takes an action."""
        if self.verbose:
            print(f"\n💭 Agent thinking: {action.log}")


class ProgressCallback(BaseCallbackHandler):
    """Callback that shows progress indicators."""
    
    def __init__(self):
        """Initialize callback."""
        self.current_step = 0
        self.total_steps = 0
    
    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when chain starts."""
        print("\n" + "="*70)
        print("AGENT PROCESSING")
        print("="*70)
    
    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        **kwargs: Any
    ) -> None:
        """Called when chain ends."""
        print("\n" + "="*70)
        print("AGENT COMPLETE")
        print("="*70 + "\n")


def ask_user_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt user for input.
    
    Args:
        prompt: Prompt to display
        default: Default value if user just presses enter
        
    Returns:
        User's input
    """
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    try:
        response = input(prompt).strip()
        if not response and default:
            return default
        return response
    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled by user.")
        sys.exit(0)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    """Ask user a yes/no question.
    
    Args:
        prompt: Question to ask
        default: Default answer
        
    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    response = ask_user_input(f"{prompt} ({default_str})", 
                             "y" if default else "n")
    
    if response.lower() in ['y', 'yes']:
        return True
    elif response.lower() in ['n', 'no']:
        return False
    else:
        return default


def confirm_action(action: str) -> bool:
    """Confirm potentially destructive action.
    
    Args:
        action: Description of action
        
    Returns:
        True if confirmed
    """
    print(f"\n⚠️  About to: {action}")
    return ask_yes_no("Continue?", default=False)


def show_progress(message: str, step: Optional[int] = None, 
                 total: Optional[int] = None):
    """Show progress message.
    
    Args:
        message: Progress message
        step: Current step number
        total: Total number of steps
    """
    if step is not None and total is not None:
        print(f"[{step}/{total}] {message}")
    else:
        print(f"⏳ {message}")

