#!/usr/bin/env python3
"""
Example usage of the Notion Agent.

This shows how to use the agent programmatically in your own scripts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agent import create_agent


def example_one_shot_query():
    """Example: Ask a single question."""
    print("\n" + "="*70)
    print("EXAMPLE 1: One-shot Query")
    print("="*70 + "\n")
    
    # Create agent (uses OpenAI)
    agent = create_agent(
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
    
    agent = create_agent()
    
    # Extract a specific page
    response = agent.run("Extract content from the Roadmap page")
    
    print(f"Agent response:\n{response}\n")


def example_database_extraction():
    """Example: Extract from database."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Database Extraction")
    print("="*70 + "\n")
    
    agent = create_agent(
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
    
    agent = create_agent()
    
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
    
    agent = create_agent()
    
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
        model="gpt-4",
        notion_token=os.environ.get('NOTION_TOKEN'),
        output_dir="custom_output",
        verbose=True
    )
    
    response = agent.run("Extract recipes")
    print(f"Agent: {response}\n")


def example_computer_use():
    """Example: Computer Use mode with screen control."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Computer Use Mode (Screen Control)")
    print("="*70 + "\n")
    
    # Requires OPENAI_API_KEY
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Skipped: Requires OPENAI_API_KEY for Computer Use")
        return
    
    agent = create_agent(
        computer_use=True,
        verbose=True
    )
    
    # Agent will use mouse/keyboard to navigate
    response = agent.run("Take a screenshot and tell me what you see on the screen")
    print(f"Agent: {response}\n")


def example_computer_use_navigation():
    """Example: Computer Use for navigation."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Computer Use Navigation")
    print("="*70 + "\n")
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Skipped: Requires OPENAI_API_KEY for Computer Use")
        return
    
    agent = create_agent(
        computer_use=True,
        verbose=True
    )
    
    # Agent will click and navigate using the screen
    response = agent.run(
        "Navigate to the recipes page in Notion by clicking on it in the sidebar"
    )
    print(f"Agent: {response}\n")


def example_computer_use_with_extraction():
    """Example: Computer Use for navigation + extraction."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Computer Use + Extraction")
    print("="*70 + "\n")
    
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Skipped: Requires OPENAI_API_KEY for Computer Use")
        return
    
    agent = create_agent(
        computer_use=True,
        verbose=True
    )
    
    # Combines navigation and extraction
    response = agent.run(
        "Find and click on the Roadmap page, then extract its content"
    )
    print(f"Agent: {response}\n")


def main():
    """Run examples."""
    print("\n" + "="*70)
    print("NOTION AGENT - PROGRAMMATIC USAGE EXAMPLES")
    print("="*70)
    
    # Make sure API key is set
    if not os.environ.get('OPENAI_API_KEY'):
        print("\n❌ Error: Set OPENAI_API_KEY")
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
        
        # Computer Use examples (require OPENAI_API_KEY):
        # example_computer_use()
        # example_computer_use_navigation()
        # example_computer_use_with_extraction()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

