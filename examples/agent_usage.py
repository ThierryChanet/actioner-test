#!/usr/bin/env python3
"""
Example usage of the Notion Agent.

This shows how to use the agent programmatically in your own scripts.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import create_agent


def example_one_shot_query():
    """Example: Ask a single question."""
    print("\n" + "="*70)
    print("EXAMPLE 1: One-shot Query")
    print("="*70 + "\n")
    
    # Create agent
    agent = create_agent(
        llm_provider="openai",  # or "anthropic"
        verbose=False
    )
    
    # Ask a question
    response = agent.run("List all available pages in my Notion")
    
    print(f"Agent response:\n{response}\n")


def example_extraction():
    """Example: Extract content from a page."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Extract Page Content")
    print("="*70 + "\n")
    
    agent = create_agent(llm_provider="openai")
    
    # Extract a specific page
    response = agent.run("Extract content from the Roadmap page")
    
    print(f"Agent response:\n{response}\n")


def example_database_extraction():
    """Example: Extract from database."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Database Extraction")
    print("="*70 + "\n")
    
    agent = create_agent(
        llm_provider="openai",
        notion_token=os.environ.get('NOTION_TOKEN')
    )
    
    # Extract database pages
    response = agent.run("Extract 5 recipes from my database")
    
    print(f"Agent response:\n{response}\n")


def example_multi_turn_conversation():
    """Example: Multi-turn conversation."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Multi-turn Conversation")
    print("="*70 + "\n")
    
    agent = create_agent(llm_provider="openai")
    
    # First query
    response1 = agent.chat("What pages do I have?")
    print(f"Agent: {response1}\n")
    
    # Follow-up (agent remembers context)
    response2 = agent.chat("Extract the first one")
    print(f"Agent: {response2}\n")


def example_with_state():
    """Example: Access agent state."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Agent State")
    print("="*70 + "\n")
    
    agent = create_agent(llm_provider="openai")
    
    # Run some queries
    agent.run("List my pages")
    agent.run("Extract the Roadmap page")
    
    # Check state
    print("Agent state:")
    print(agent.get_state_summary())
    print()
    
    # Reset if needed
    agent.reset()
    print("Agent reset!")


def example_custom_config():
    """Example: Custom configuration."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Custom Configuration")
    print("="*70 + "\n")
    
    agent = create_agent(
        llm_provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        notion_token=os.environ.get('NOTION_TOKEN'),
        output_dir="custom_output",
        verbose=True
    )
    
    response = agent.run("Extract recipes")
    print(f"Agent: {response}\n")


def main():
    """Run examples."""
    print("\n" + "="*70)
    print("NOTION AGENT - PROGRAMMATIC USAGE EXAMPLES")
    print("="*70)
    
    # Make sure API key is set
    if not os.environ.get('OPENAI_API_KEY') and not os.environ.get('ANTHROPIC_API_KEY'):
        print("\n❌ Error: Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        print("   export OPENAI_API_KEY='your-key'")
        return
    
    print("\nRunning examples...\n")
    
    try:
        # Run examples
        example_one_shot_query()
        
        # Uncomment to run more examples:
        # example_extraction()
        # example_database_extraction()
        # example_multi_turn_conversation()
        # example_with_state()
        # example_custom_config()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

