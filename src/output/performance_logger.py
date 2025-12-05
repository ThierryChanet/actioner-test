"""Performance logging utility for tracking action timing."""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class PerformanceLogger:
    """Logger for tracking performance metrics of computer use actions."""
    
    def __init__(self, output_dir: str = "output/logs"):
        """Initialize the performance logger.
        
        Args:
            output_dir: Directory to store performance logs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.output_dir / f"performance_{timestamp}.jsonl"
        
        # Initialize log file
        self._write_header()
    
    def _write_header(self):
        """Write header information to the log file."""
        header = {
            "type": "header",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0",
            "format": "jsonl"
        }
        with open(self.log_file, 'w') as f:
            f.write(json.dumps(header) + '\n')
    
    def log_action(
        self,
        action_type: str,
        duration_ms: float,
        success: bool = True,
        context: Optional[Dict[str, Any]] = None
    ):
        """Log a single action with timing information.
        
        Args:
            action_type: Type of action (e.g., "screenshot", "left_click")
            duration_ms: Duration in milliseconds
            success: Whether the action succeeded
            context: Additional context (coordinates, text, etc.)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_type": action_type,
            "duration_ms": round(duration_ms, 2),
            "success": success,
        }
        
        if context:
            entry["context"] = context
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of logged performance metrics.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.log_file.exists():
            return {}
        
        actions = []
        with open(self.log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("type") != "header":
                    actions.append(entry)
        
        if not actions:
            return {}
        
        # Calculate statistics
        total_actions = len(actions)
        total_duration = sum(a["duration_ms"] for a in actions)
        avg_duration = total_duration / total_actions if total_actions > 0 else 0
        
        # Group by action type
        by_type = {}
        for action in actions:
            action_type = action["action_type"]
            if action_type not in by_type:
                by_type[action_type] = {
                    "count": 0,
                    "total_ms": 0,
                    "avg_ms": 0,
                    "min_ms": float('inf'),
                    "max_ms": 0
                }
            
            stats = by_type[action_type]
            stats["count"] += 1
            stats["total_ms"] += action["duration_ms"]
            stats["min_ms"] = min(stats["min_ms"], action["duration_ms"])
            stats["max_ms"] = max(stats["max_ms"], action["duration_ms"])
        
        # Calculate averages
        for stats in by_type.values():
            stats["avg_ms"] = round(stats["total_ms"] / stats["count"], 2)
            stats["total_ms"] = round(stats["total_ms"], 2)
            stats["min_ms"] = round(stats["min_ms"], 2)
            stats["max_ms"] = round(stats["max_ms"], 2)
        
        return {
            "total_actions": total_actions,
            "total_duration_ms": round(total_duration, 2),
            "avg_duration_ms": round(avg_duration, 2),
            "by_action_type": by_type,
            "log_file": str(self.log_file)
        }
    
    def print_summary(self):
        """Print a formatted summary of performance metrics."""
        summary = self.get_summary()
        
        if not summary:
            print("No performance data logged yet.")
            return
        
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Total Actions: {summary['total_actions']}")
        print(f"Total Duration: {summary['total_duration_ms']:.1f}ms")
        print(f"Average Duration: {summary['avg_duration_ms']:.1f}ms")
        print(f"\nLog File: {summary['log_file']}")
        
        print("\n" + "-"*60)
        print("BY ACTION TYPE")
        print("-"*60)
        
        for action_type, stats in sorted(summary['by_action_type'].items()):
            print(f"\n{action_type}:")
            print(f"  Count: {stats['count']}")
            print(f"  Average: {stats['avg_ms']:.1f}ms")
            print(f"  Min: {stats['min_ms']:.1f}ms")
            print(f"  Max: {stats['max_ms']:.1f}ms")
            print(f"  Total: {stats['total_ms']:.1f}ms")
        
        print("\n" + "="*60 + "\n")


# Global logger instance
_global_logger: Optional[PerformanceLogger] = None


def get_logger(output_dir: str = "output/logs") -> PerformanceLogger:
    """Get or create the global performance logger instance.
    
    Args:
        output_dir: Directory to store performance logs
        
    Returns:
        PerformanceLogger instance
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = PerformanceLogger(output_dir)
    return _global_logger


def log_action(action_type: str, duration_ms: float, success: bool = True, context: Optional[Dict[str, Any]] = None):
    """Convenience function to log an action using the global logger.
    
    Args:
        action_type: Type of action
        duration_ms: Duration in milliseconds
        success: Whether the action succeeded
        context: Additional context
    """
    logger = get_logger()
    logger.log_action(action_type, duration_ms, success, context)

