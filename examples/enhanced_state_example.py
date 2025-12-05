"""
Example: Enhanced State Management to Prevent Iteration Loops

This example demonstrates how the improved AgentState with action history
prevents the agent from getting stuck in infinite loops.

Run this to see how action deduplication works.
"""

from typing import Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import time


@dataclass
class ActionRecord:
    """Record of a single action attempt."""
    timestamp: datetime
    action_type: str
    parameters: Dict[str, Any]
    result: str
    error_message: str = None


@dataclass
class EnhancedAgentState:
    """Enhanced state with action history and deduplication."""

    current_page: str = None
    action_history: List[ActionRecord] = field(default_factory=list)
    retry_counts: Dict[str, int] = field(default_factory=dict)
    max_retries_per_action: int = 3

    def _action_key(self, action_type: str, parameters: Dict[str, Any]) -> str:
        """Generate a unique key for an action."""
        param_str = str(sorted(parameters.items()))
        key_str = f"{action_type}:{param_str}"
        return hashlib.md5(key_str.encode()).hexdigest()[:16]

    def should_retry_action(self, action_type: str, parameters: Dict[str, Any]) -> bool:
        """Check if an action should be retried or if max retries reached."""
        action_key = self._action_key(action_type, parameters)
        retry_count = self.retry_counts.get(action_key, 0)
        return retry_count < self.max_retries_per_action

    def has_tried_recently(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        within_last_n: int = 5
    ) -> bool:
        """Check if an action was tried in the last N actions."""
        action_key = self._action_key(action_type, parameters)

        recent_actions = self.action_history[-within_last_n:]
        for record in recent_actions:
            if self._action_key(record.action_type, record.parameters) == action_key:
                return True
        return False

    def record_action(
        self,
        action_type: str,
        parameters: Dict[str, Any],
        result: str,
        error_message: str = None
    ) -> ActionRecord:
        """Record an action attempt."""
        record = ActionRecord(
            timestamp=datetime.now(),
            action_type=action_type,
            parameters=parameters,
            result=result,
            error_message=error_message
        )

        self.action_history.append(record)

        # Update retry counts
        action_key = self._action_key(action_type, parameters)
        if result == "failed":
            self.retry_counts[action_key] = self.retry_counts.get(action_key, 0) + 1
        elif result == "success":
            self.retry_counts[action_key] = 0

        return record

    def get_action_summary(self) -> str:
        """Get a summary of recent actions."""
        if not self.action_history:
            return "No actions taken yet."

        recent = self.action_history[-10:]
        lines = ["Recent actions:"]
        for i, record in enumerate(recent, 1):
            icon = "✅" if record.result == "success" else "❌"
            params = str(record.parameters)[:40]
            lines.append(f"{i}. {icon} {record.action_type} {params}")
            if record.error_message:
                lines.append(f"   Error: {record.error_message}")

        return "\n".join(lines)


def simulate_agent_with_old_state():
    """Simulate agent behavior WITHOUT action history (gets stuck in loop)."""
    print("=" * 70)
    print("SIMULATION 1: Old Agent (No Action History)")
    print("=" * 70)

    # Agent tries to click same button repeatedly
    for i in range(10):
        print(f"\nIteration {i + 1}:")
        print("  Trying to click at (100, 250)...")

        # Simulate failure
        time.sleep(0.1)
        print("  ❌ Click failed!")

        # Old agent has no memory - keeps trying same action
        print("  → Agent will try same action again...")

    print("\n⚠️  Result: Agent wasted 10 iterations on same failed action!")
    print()


def simulate_agent_with_enhanced_state():
    """Simulate agent behavior WITH action history (prevents loops)."""
    print("=" * 70)
    print("SIMULATION 2: Enhanced Agent (With Action History)")
    print("=" * 70)

    state = EnhancedAgentState()
    action_type = "click_button"
    parameters = {"x": 100, "y": 250, "target": "recipe"}

    for i in range(10):
        print(f"\nIteration {i + 1}:")

        # Check if we should retry this action
        if not state.should_retry_action(action_type, parameters):
            print(f"  🛑 STOP! Tried this action {state.max_retries_per_action} times already.")
            print("  💡 Agent should try a DIFFERENT strategy instead.")
            print("\n✅ Result: Agent stopped after 3 attempts and will try different approach!")
            break

        # Check if tried very recently
        if state.has_tried_recently(action_type, parameters, within_last_n=2):
            print(f"  ⚠️  WARNING: Just tried this action in last 2 iterations!")
            print("  💡 Consider trying something else...")

        print(f"  Trying to click at (100, 250)...")

        # Simulate failure
        time.sleep(0.1)

        # Record the attempt
        state.record_action(
            action_type=action_type,
            parameters=parameters,
            result="failed",
            error_message="Element not found at coordinates"
        )

        print("  ❌ Click failed!")
        print(f"  📝 Recorded in action history (retry count: {state.retry_counts[state._action_key(action_type, parameters)]})")

    print("\n" + "=" * 70)
    print("Action History Summary:")
    print("=" * 70)
    print(state.get_action_summary())
    print()


def demonstrate_strategy_switching():
    """Demonstrate how agent switches strategies after failures."""
    print("=" * 70)
    print("SIMULATION 3: Strategy Switching After Failures")
    print("=" * 70)

    state = EnhancedAgentState()

    strategies = [
        {"name": "hover_and_click_open", "params": {"target": "recipe", "method": "hover"}},
        {"name": "direct_click", "params": {"target": "recipe", "method": "direct"}},
        {"name": "keyboard_navigation", "params": {"target": "recipe", "method": "keyboard"}},
    ]

    current_strategy_idx = 0

    for i in range(7):
        print(f"\nIteration {i + 1}:")

        strategy = strategies[current_strategy_idx]
        action_type = strategy["name"]
        parameters = strategy["params"]

        print(f"  🎯 Current strategy: {action_type}")

        # Check if max retries for this strategy
        if not state.should_retry_action(action_type, parameters):
            print(f"  🛑 Strategy '{action_type}' failed {state.max_retries_per_action} times")

            current_strategy_idx += 1
            if current_strategy_idx >= len(strategies):
                print("  ❌ All strategies exhausted!")
                break

            print(f"  🔄 Switching to next strategy: {strategies[current_strategy_idx]['name']}")
            continue

        # Simulate attempt (all fail for this demo)
        time.sleep(0.1)

        state.record_action(
            action_type=action_type,
            parameters=parameters,
            result="failed",
            error_message=f"Strategy {action_type} did not work"
        )

        print(f"  ❌ Failed (retry count: {state.retry_counts[state._action_key(action_type, parameters)]})")

    print("\n" + "=" * 70)
    print("Final State:")
    print("=" * 70)
    print(state.get_action_summary())
    print()
    print("✅ Agent tried 3 different strategies instead of getting stuck on one!")
    print()


if __name__ == "__main__":
    print("\n" + "🤖 Enhanced Agent State Management Demo" + "\n")

    # Show the problem
    simulate_agent_with_old_state()

    input("Press Enter to see the solution...\n")

    # Show the solution
    simulate_agent_with_enhanced_state()

    input("Press Enter to see strategy switching...\n")

    # Show strategy switching
    demonstrate_strategy_switching()

    print("\n" + "=" * 70)
    print("Summary:")
    print("=" * 70)
    print("""
The enhanced state management provides:

1. ✅ Action deduplication - prevents repeating failed actions
2. ✅ Retry limits - stops after N attempts per action
3. ✅ Recency detection - warns about recently tried actions
4. ✅ Strategy switching - tries different approaches
5. ✅ Action history - full audit trail for debugging

This solves the "max iterations" problem from testing!
    """)
