"""Command-line interface for the Notion agent."""

import sys
import os
import click
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .core import create_agent


@click.group(invoke_without_command=True)
@click.argument('query', nargs=-1, required=False)
@click.option('--interactive', '-i', is_flag=True, 
              help='Start interactive mode')
@click.option('--model', '-m',
              help='Specific OpenAI model to use (default: gpt-4-turbo-preview)')
@click.option('--notion-token', envvar='NOTION_TOKEN',
              help='Notion API token (or set NOTION_TOKEN env var)')
@click.option('--output-dir', '-o',
              default='output',
              help='Output directory (default: output)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
@click.option('--no-computer-use', is_flag=True,
              help='Disable Computer Use API (use standard AX navigation)')
@click.option('--display', '-d',
              type=int,
              default=1,
              help='Display number for Computer Use (default: 1)')
@click.pass_context
def cli(ctx, query, interactive, model, notion_token, output_dir, verbose, 
        no_computer_use, display):
    """Notion Agent - Intelligent extraction assistant (powered by OpenAI).
    
    Computer Use is ENABLED by default for screen control via clicks/keyboard.
    
    Examples:
    
        # One-shot query (Computer Use enabled by default)
        python -m src.agent "extract all recipes from my database"
        
        # Interactive mode
        python -m src.agent --interactive
        
        # Disable Computer Use (use standard AX navigation)
        python -m src.agent --no-computer-use "navigate to recipes"
        
        # With specific model
        python -m src.agent --model gpt-4 "what's on the roadmap page?"
        
        # Help
        python -m src.agent --help
    """
    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        click.echo("❌ Error: OPENAI_API_KEY environment variable required")
        click.echo("   Set it with: export OPENAI_API_KEY='your-key'")
        sys.exit(1)
    
    # Computer Use is enabled by default
    computer_use = not no_computer_use
    
    # Show Computer Use status in verbose mode
    if verbose:
        if computer_use:
            click.echo(f"🖥️  Computer Use enabled (display {display})")
        else:
            click.echo("📋 Using standard AX navigation")
    
    # Create agent
    try:
        agent = create_agent(
            model=model,
            notion_token=notion_token,
            output_dir=output_dir,
            verbose=verbose,
            computer_use=computer_use,
            display_num=display,
        )
    except Exception as e:
        click.echo(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Interactive mode
    if interactive:
        agent.interactive_mode()
        return
    
    # One-shot query
    if query:
        query_str = ' '.join(query)
        
        click.echo(f"\n📝 Query: {query_str}\n")
        
        try:
            response = agent.run(query_str)
            click.echo(f"\n🤖 Agent: {response}\n")
        except Exception as e:
            click.echo(f"\n❌ Error: {e}\n")
            if verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)
        
        return
    
    # No arguments - show help
    click.echo(ctx.get_help())


@cli.command()
@click.option('--model', '-m',
              help='Specific OpenAI model to use')
@click.option('--notion-token', envvar='NOTION_TOKEN')
@click.option('--output-dir', '-o', default='output')
@click.option('--verbose', '-v', is_flag=True)
@click.option('--no-computer-use', is_flag=True,
              help='Disable Computer Use API (use standard AX navigation)')
@click.option('--display', '-d', type=int, default=1,
              help='Display number for Computer Use')
def interactive(model, notion_token, output_dir, verbose, no_computer_use, display):
    """Start interactive chat mode (Computer Use enabled by default)."""
    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        click.echo("❌ Error: OPENAI_API_KEY required")
        sys.exit(1)
    
    agent = create_agent(
        model=model,
        notion_token=notion_token,
        output_dir=output_dir,
        verbose=verbose,
        computer_use=not no_computer_use,
        display_num=display,
    )
    
    agent.interactive_mode()


@cli.command()
@click.argument('query')
@click.option('--model', '-m',
              help='Specific OpenAI model to use')
@click.option('--notion-token', envvar='NOTION_TOKEN')
@click.option('--output-dir', '-o', default='output')
@click.option('--verbose', '-v', is_flag=True)
@click.option('--no-computer-use', is_flag=True,
              help='Disable Computer Use API (use standard AX navigation)')
@click.option('--display', '-d', type=int, default=1,
              help='Display number for Computer Use')
def ask(query, model, notion_token, output_dir, verbose, no_computer_use, display):
    """Ask the agent a single question (Computer Use enabled by default)."""
    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        click.echo("❌ Error: OPENAI_API_KEY required")
        sys.exit(1)
    
    agent = create_agent(
        model=model,
        notion_token=notion_token,
        output_dir=output_dir,
        verbose=verbose,
        computer_use=not no_computer_use,
        display_num=display,
    )
    
    click.echo(f"\n📝 Query: {query}\n")
    
    response = agent.run(query)
    
    click.echo(f"\n🤖 Agent: {response}\n")


@cli.command()
def examples():
    """Show usage examples."""
    examples_text = """
NOTION AGENT - USAGE EXAMPLES
======================================================================

Note: Computer Use (screen control) is ENABLED BY DEFAULT!

Basic Extraction (Computer Use enabled):
  python -m src.agent "extract all recipes"
  python -m src.agent "what's on the roadmap page?"
  python -m src.agent "get content from the meeting notes page"

Database Operations:
  python -m src.agent "extract 20 pages from my recipe database"
  python -m src.agent "how many recipes do I have?"
  
Screen Control (Computer Use - DEFAULT):
  python -m src.agent "click on the recipes database"
  python -m src.agent "navigate to roadmap page and extract it"
  python -m src.agent "take a screenshot and describe what you see"

Disable Computer Use (use standard AX navigation):
  python -m src.agent --no-computer-use "extract all recipes"

Interactive Mode:
  python -m src.agent --interactive
  python -m src.agent -i

With Specific Model:
  python -m src.agent --model gpt-4 "analyze my pages"
  python -m src.agent --model gpt-4o "extract recipes"

Verbose Mode (see tool calls):
  python -m src.agent --verbose "extract database"

Environment Variables:
  export OPENAI_API_KEY="sk-..."         # Required
  export NOTION_TOKEN="secret_..."       # Optional, for API extraction

======================================================================
"""
    click.echo(examples_text)


@cli.command()
def check():
    """Check if environment is properly configured."""
    click.echo("\n" + "="*70)
    click.echo("ENVIRONMENT CHECK")
    click.echo("="*70 + "\n")
    
    checks = []
    
    # Check for API keys
    openai_key = os.environ.get('OPENAI_API_KEY')
    notion_token = os.environ.get('NOTION_TOKEN')
    
    checks.append(("OpenAI API Key (Required)", bool(openai_key)))
    checks.append(("Notion API Token (Optional)", bool(notion_token)))
    
    # Check Python packages
    try:
        import langchain
        checks.append(("LangChain installed", True))
    except ImportError:
        checks.append(("LangChain installed", False))
    
    try:
        import langchain_openai
        checks.append(("LangChain OpenAI installed", True))
    except ImportError:
        checks.append(("LangChain OpenAI installed", False))
    
    try:
        import openai
        checks.append(("OpenAI SDK installed", True))
    except ImportError:
        checks.append(("OpenAI SDK installed", False))
    
    # Display results
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        click.echo(f"{status} {check_name}")
    
    click.echo("\n" + "="*70)
    
    # Summary - only count required checks
    required_checks = [checks[0]] + checks[2:]  # OpenAI key + packages
    total = len(required_checks)
    passed = sum(1 for _, p in required_checks if p)
    
    if passed == total:
        click.echo("\n✅ All required checks passed! You're ready to use the agent.\n")
    else:
        click.echo(f"\n⚠️  {total - passed} required checks failed. Please fix the issues above.\n")
        
        # Provide help
        if not openai_key:
            click.echo("To use the agent, set your OpenAI API key:")
            click.echo("  export OPENAI_API_KEY='your-key'")
        
        if not all(p for _, p in checks[2:]):
            click.echo("\nTo install missing packages:")
            click.echo("  pip install -r requirements.txt")
        
        click.echo()


def main():
    """Entry point for the agent CLI."""
    cli()


if __name__ == '__main__':
    main()

