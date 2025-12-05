#!/usr/bin/env python3
"""
Test script for the Notion Agent.

This script demonstrates the agent's capabilities and can be used
to verify the installation is working correctly.
"""

import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))


def check_environment():
    """Check if environment is properly configured."""
    print("\n" + "="*70)
    print("ENVIRONMENT CHECK")
    print("="*70 + "\n")
    
    issues = []
    
    # Check API keys
    # OpenAI is required for LLM, Anthropic for Computer Use
    if not os.environ.get('OPENAI_API_KEY'):
        issues.append("❌ OPENAI_API_KEY not found (required for LLM)")
    else:
        print("✅ OpenAI API key found (for LLM)")
    
    if os.environ.get('ANTHROPIC_API_KEY'):
        print("✅ Anthropic API key found (for Computer Use)")
    else:
        print("ℹ️  No Anthropic API key (Computer Use will be disabled)")
    
    # Check optional token
    if os.environ.get('NOTION_TOKEN'):
        print("✅ Notion API token found (faster database extraction)")
    else:
        print("ℹ️  No Notion API token (optional, can still use AX navigation)")
    
    # Check imports
    try:
        from src.agent import create_agent
        print("✅ Agent module imports successfully")
    except ImportError as e:
        issues.append(f"❌ Agent import failed: {e}")
    
    try:
        import langchain
        print("✅ LangChain installed")
    except ImportError:
        issues.append("❌ LangChain not installed (run: pip install -r requirements.txt)")
    
    try:
        from src.orchestrator import NotionOrchestrator
        print("✅ Orchestrator module imports successfully")
    except ImportError as e:
        issues.append(f"❌ Orchestrator import failed: {e}")
    
    print()
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease fix these issues before running tests.\n")
        return False
    else:
        print("✅ All checks passed! Environment is ready.\n")
        return True


def test_agent_creation():
    """Test creating an agent instance."""
    print("\n" + "="*70)
    print("TEST 1: Agent Creation")
    print("="*70 + "\n")
    
    try:
        from src.agent import create_agent
        
        # OpenAI is required for LLM
        if not os.environ.get('OPENAI_API_KEY'):
            print("❌ OPENAI_API_KEY required for agent creation")
            return False
        
        # Computer Use requires Anthropic key
        has_anthropic = bool(os.environ.get('ANTHROPIC_API_KEY'))
        computer_use = has_anthropic
        
        print(f"Creating agent (Computer Use: {'enabled' if computer_use else 'disabled'})...")
        agent = create_agent(
            output_dir="output",
            verbose=False,
            computer_use=computer_use
        )
        
        print("✅ Agent created successfully!")
        print(f"   State: {agent.get_state_summary()}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tools():
    """Test that tools are properly configured."""
    print("\n" + "="*70)
    print("TEST 2: Tool Configuration")
    print("="*70 + "\n")
    
    try:
        from src.agent import create_agent
        
        has_anthropic = bool(os.environ.get('ANTHROPIC_API_KEY'))
        agent = create_agent(verbose=False, computer_use=has_anthropic)
        
        tools = agent.tools
        print(f"Agent has {len(tools)} tools:\n")
        
        for tool in tools:
            print(f"  ✅ {tool.name}: {tool.description[:60]}...")
        
        print("\n✅ All tools configured correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Tool configuration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_orchestrator():
    """Test the orchestrator."""
    print("\n" + "="*70)
    print("TEST 3: Orchestrator")
    print("="*70 + "\n")
    
    try:
        from src.orchestrator import NotionOrchestrator
        
        print("Creating orchestrator...")
        orchestrator = NotionOrchestrator(
            output_dir="output",
            verbose=False
        )
        
        print("✅ Orchestrator created")
        
        # Try to ensure Notion is active (won't fail if Notion not running)
        print("Checking Notion app...")
        if orchestrator.ensure_notion_active():
            print("✅ Notion app is active and accessible")
            
            # Try to get current page
            current = orchestrator.get_current_page_title()
            if current:
                print(f"✅ Current page: {current}")
            else:
                print("ℹ️  No current page title detected")
        else:
            print("⚠️  Notion app not found or not accessible")
            print("   This is OK for testing - Notion doesn't need to be running")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_query():
    """Test a simple agent query (requires Notion to be running)."""
    print("\n" + "="*70)
    print("TEST 4: Simple Query (Optional - requires Notion)")
    print("="*70 + "\n")
    
    try:
        from src.agent import create_agent
        
        has_anthropic = bool(os.environ.get('ANTHROPIC_API_KEY'))
        
        print("Creating agent...")
        agent = create_agent(verbose=False, computer_use=has_anthropic)
        
        print("\nAsking: 'What is your current context?'\n")
        response = agent.run("What is your current context?")
        
        print("Agent response:")
        print(response)
        
        print("\n✅ Agent responded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        print("\nThis is expected if Notion is not running.")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("NOTION AGENT - TEST SUITE")
    print("="*70)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix issues and try again.\n")
        return 1
    
    # Run tests
    results = []
    
    results.append(("Agent Creation", test_agent_creation()))
    results.append(("Tool Configuration", test_tools()))
    results.append(("Orchestrator", test_orchestrator()))
    results.append(("Simple Query", test_simple_query()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70 + "\n")
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The agent is ready to use.\n")
        print("Try running:")
        print('  python -m src.agent --interactive')
        print('  python -m src.agent "list all my pages"')
        print()
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        print("Note: Some tests may fail if Notion is not running.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())

