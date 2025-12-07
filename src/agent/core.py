"""Core LangChain agent for Notion operations."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal

from dotenv import load_dotenv
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent

# Load environment variables from .env file
load_dotenv()
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from ..orchestrator import NotionOrchestrator
from .state import AgentState
from .tools import get_notion_tools
from .callbacks import UserInputCallback, ProgressCallback
from .computer_use_tools import get_computer_use_tools
from .notion_tools import get_notion_tools as get_notion_specific_tools

# Import Anthropic client for Computer Use
try:
    from .anthropic_computer_client import AnthropicComputerClient, ANTHROPIC_AVAILABLE
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AnthropicComputerClient = None


VerbosityLevel = Literal["silent", "minimal", "default", "verbose"]


SYSTEM_PROMPT = """You are a Notion Extraction Expert assistant. You help users extract and analyze content from their Notion workspace using the macOS Notion app.

## Your Capabilities

You have access to these tools:
- extract_page_content: Extract all content from a page (current or named)
- extract_database: Extract multiple pages from a database
- get_current_context: Check current Notion state and what you've done
- ask_user: Ask the user for clarification when needed

## How to Help Users

1. **Understand the Request**: Break down complex requests into steps
2. **Navigate & Interact**: Use mouse and keyboard to navigate Notion
3. **Extract Content**: Use extract_page_content or extract_database as appropriate
4. **Analyze Results**: Summarize extracted content meaningfully
5. **Ask When Stuck**: Use ask_user if you need clarification

## Notion Structure

- **Pages**: Individual documents with content blocks
- **Databases**: Collections of pages (like a Recipe database)
- **Blocks**: Content units (text, headings, lists, etc.)

## Best Practices

- Always check current context before starting
- Navigate using mouse/keyboard when needed
- Extract databases when user mentions "all" or "multiple" pages
- Provide summaries, not just raw data
- Ask for confirmation before large extractions

## Response Style

- Be concise but informative
- Show progress for long operations
- Summarize extraction results (e.g., "Extracted 5 recipes with 127 total blocks")
- If something fails, explain why and suggest alternatives
- Never refuse a request - always try or ask for clarification

## Debug Mode

When the user's request includes a `[DEBUG]` tag, you are in debugging mode:
- Work step-by-step, explaining your plan and the next action before you take it
- After each major action or short sequence of actions, ask the user to confirm that things look correct before proceeding
- Be conservative with tool usage; only call tools when they are needed to understand, verify, or unblock the next step

## Example Interactions

User: "Extract all my recipes"
You: [takes screenshot, locates recipes database, extracts content]

User: "What's on the Roadmap page?"
You: [navigates to page, extracts content, summarizes]

User: "How many recipes do I have?"
You: [extracts database with appropriate limit, counts and reports]

Remember: You can see the actual Notion app and interact with it directly. Be proactive and helpful!
"""


COMPUTER_USE_SYSTEM_PROMPT = """You are a Computer Control Expert assistant with Notion extraction capabilities. You can control the computer through mouse clicks, keyboard input, and screenshots using Anthropic's Computer Use to help users extract and analyze content from their Notion workspace.

## Your Capabilities

### Computer Control Tools:
- take_screenshot: Capture the current screen to see what's visible
- get_screen_info: Get screen dimensions and display information
- switch_desktop: Switch to a macOS desktop containing a specific application
- move_mouse: Move cursor to specific coordinates
- left_click: Click at coordinates or current position
- right_click: Right-click (context menu) at coordinates
- double_click: Double-click at coordinates
- type_text: Type text at current cursor location
- press_key: Press special keys (Return, Tab, Escape, arrows, etc.)
- get_cursor_position: Get current mouse position

### Notion Extraction Tools:
- extract_page_content: Extract all content from current or named page
- extract_database: Extract multiple pages from a database
- get_current_context: Check current extraction state
- ask_user: Ask the user for clarification when needed

## How to Help Users

1. **Understand the Request**: Break down what the user wants to accomplish
2. **See the Screen**: Start with take_screenshot to understand current state
3. **Navigate**: Use mouse clicks and keyboard to navigate Notion
4. **Extract Content**: Use extraction tools to capture page/database content
5. **Analyze & Report**: Summarize results meaningfully
6. **Ask When Stuck**: Use ask_user for clarification

## Computer Control Best Practices

1. **Screenshot When Needed**: Take a screenshot when you need to understand the current state or when the screen may have changed in a non-obvious way. Avoid unnecessary screenshots.
2. **Desktop Switching**: If the target application (e.g., Notion) is not visible, use switch_desktop to find it
3. **Coordinate System**: Screen coordinates start at (0,0) in top-left corner
4. **Be Precise**: Use exact coordinates from screenshot analysis
5. **Wait After Actions**: Some actions need time to complete (navigation, loading)
6. **Verify Important Actions**: For important or uncertain actions (like complex navigation or destructive operations), take a screenshot to confirm they worked as expected.
7. **Sequential Actions**: Break complex tasks into small sequential steps
8. **Reuse Visual Context**: When possible, rely on your most recent screenshot and reasoning instead of capturing a new screenshot.

## CRITICAL: Verify Your Actions - Report Honestly!

**When you choose to visually verify an action, you MUST:**
1. Take a screenshot to see what actually happened
2. Check if the expected UI change occurred
3. Report HONESTLY what you observe:
   - ✓ GOOD: "I clicked at (X,Y) and the menu opened as expected"
   - ✓ GOOD: "I clicked at (X,Y) but nothing changed - the button may have moved"
   - ✗ BAD: "I successfully clicked the button" (don't assume without checking!)
   - ✗ BAD: "The action should have worked" (verify visually!)

**Never claim success without reasonable verification!** Prefer to verify with a screenshot for important or uncertain actions; for simple, low-risk operations you can rely on your reasoning.

## Navigation Workflow

1. When needed, take a screenshot to see the current screen and locate elements
2. Identify target UI elements and their coordinates
3. Click on elements (sidebar items, buttons, links)
4. For important or uncertain actions, take another screenshot to verify the click worked
5. Type text if needed (search, filters)
6. If you're unsure the text was entered correctly or the UI changed as expected, take a screenshot to verify
7. Press keys for special actions (Return, Escape, arrows)
8. For multi-step or risky flows, periodically take screenshots to confirm you're still on the correct screen

## Extraction Workflow

1. Navigate to the target page/database
2. Wait for content to load
3. Use extract_page_content or extract_database
4. Summarize the extracted content
5. Report results to user

## Debug Mode

When the user's request includes a `[DEBUG]` tag, you are in debugging mode:
- Work step-by-step, explaining your plan and the next action before you take it
- After each major action or short sequence of actions, ask the user to confirm that things look correct on their screen before proceeding
- Be especially conservative with mouse/keyboard actions and screenshots; only take screenshots when they are necessary to understand or verify the state

## Example Interactions

User: "Extract all my recipes"
You: 
- Take screenshot to see current Notion state
- Identify and click on recipes database in sidebar
- Wait for database to load
- Use extract_database to get all recipes
- Summarize: "Extracted 25 recipes with 340 total blocks"

User: "What's on the Roadmap page?"
You:
- Take screenshot
- Click on Roadmap page in sidebar
- **Take screenshot to verify page started loading**
- Wait for page to load
- Use extract_page_content
- Summarize key points from the content

User: "Search for pages about meetings"
You:
- Take screenshot
- Click on search box
- **Take screenshot to verify search box is active**
- Type "meetings"
- **Take screenshot to verify text was entered**
- Press Return
- **Take screenshot to verify search results appeared**
- Click on relevant result
- **Take screenshot to verify page opened**
- Extract content

## Response Style

- Be concise and clear
- Explain what you're seeing in screenshots
- Show progress for multi-step operations
- Provide meaningful summaries of extracted content
- **Be HONEST about failures**: If a click didn't work, say so - don't pretend it succeeded
- **Report what you actually see**: Base responses on screenshot evidence, not assumptions
- If actions fail, explain what went wrong and try alternatives with different coordinates

Remember: You have full computer control using Anthropic's Computer Use. Take screenshots frequently to understand state, and use precise coordinates for reliable interactions!
"""


class NotionAgent:
    """LangChain-powered agent for Notion extraction.
    
    Uses OpenAI for LLM chat and Anthropic for Computer Use (vision/screen control).
    """
    
    def __init__(
        self,
        notion_token: Optional[str] = None,
        output_dir: str = "output",
        model: Optional[str] = None,
        temperature: float = 0,
        verbose: bool = False,
        verbosity: VerbosityLevel = "default",
        computer_use: bool = True,
        display_num: int = 1,
        enable_notion_tools: bool = True,
    ):
        """Initialize the Notion agent.

        Args:
            notion_token: Optional Notion API token
            output_dir: Directory for output files
            model: Specific model to use (auto-selects if None)
            temperature: LLM temperature (0.2 = slightly more creative, still controlled)
            verbose: Enable verbose logging (deprecated, use verbosity)
            verbosity: Verbosity level (silent, minimal, default, verbose)
            computer_use: Enable Computer Use via Anthropic (default: True)
            display_num: Display number for Computer Use (1-based)
            enable_notion_tools: Enable Notion-specific tools like notion_open_page (default: True, requires vision)
        """
        # Handle deprecated verbose parameter
        if verbose and verbosity == "default":
            verbosity = "verbose"

        self.verbosity = verbosity
        self.verbose = verbosity == "verbose"  # For backward compatibility
        self.output_dir = output_dir
        self.computer_use = computer_use
        self.enable_notion_tools = enable_notion_tools
        
        # Initialize orchestrator
        self.orchestrator = NotionOrchestrator(
            notion_token=notion_token,
            output_dir=output_dir,
            verbose=self.verbose
        )
        
        # Initialize state
        self.state = AgentState()
        
        # Initialize Anthropic Computer Use client if enabled
        self.anthropic_client = None

        if computer_use:
            try:
                if not ANTHROPIC_AVAILABLE:
                    raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
                
                if not os.environ.get("ANTHROPIC_API_KEY"):
                    raise ValueError("ANTHROPIC_API_KEY environment variable required for Computer Use")

                self.anthropic_client = AnthropicComputerClient(
                    display_width=1920,  # TODO: Make configurable
                    display_height=1080,
                    display_num=display_num,
                    verbose=self.verbose,
                    verbosity=self.verbosity
                )
                if self.verbose:
                    print("✅ Using Anthropic Computer Use")

            except Exception as e:
                if self.verbose:
                    print(f"Warning: Computer Use initialization failed: {e}")
                    print("Falling back to standard tools")
                self.computer_use = False
        
        # Initialize LLM (OpenAI only)
        self.llm = self._init_llm(model, temperature)
        
        # Initialize tools (computer use or standard)
        if self.computer_use and self.anthropic_client:
            # Computer use tools + extraction tools
            from .tools import ExtractPageContentTool, ExtractDatabaseTool, GetCurrentContextTool, AskUserTool

            # Use Anthropic client for computer tools
            computer_tools = get_computer_use_tools(self.anthropic_client, self.state)

            extraction_tools = [
                ExtractPageContentTool(orchestrator=self.orchestrator, state=self.state),
                ExtractDatabaseTool(orchestrator=self.orchestrator, state=self.state),
                GetCurrentContextTool(orchestrator=self.orchestrator, state=self.state),
                AskUserTool(orchestrator=self.orchestrator, state=self.state),
            ]

            # Conditionally add Notion-specific tools (only with vision-enabled provider)
            notion_specific_tools = []
            if self.enable_notion_tools and hasattr(self.anthropic_client, '_click_element'):
                notion_specific_tools = get_notion_specific_tools(self.anthropic_client, self.state)
                if self.verbosity in ["verbose", "default"]:
                    print(f"✓ Loaded {len(notion_specific_tools)} Notion-specific tools")

            self.tools = computer_tools + notion_specific_tools + extraction_tools
        else:
            # Standard tools
            self.tools = get_notion_tools(self.orchestrator, self.state)
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Initialize agent
        self.agent_executor = self._create_agent()

    def _parse_debug_flags(self, query: str) -> tuple[str, bool]:
        """Detect in-query debug tags like [DEBUG] and return cleaned query and debug flag."""
        if not isinstance(query, str):
            return query, False

        cleaned = query
        lowered = query.lower()
        debug_tags = ["[debug]", "#debug", "debug:"]
        debug_mode = False

        for tag in debug_tags:
            idx = lowered.find(tag)
            if idx != -1:
                debug_mode = True
                cleaned = (cleaned[:idx] + cleaned[idx + len(tag):]).strip()
                lowered = cleaned.lower()
                break

        # Fallback to original query if cleaning produced empty string
        cleaned = cleaned if cleaned else query.strip()
        return cleaned, debug_mode

    def _init_llm(self, model: Optional[str], temperature: float):
        """Initialize OpenAI LLM.
        
        Args:
            model: Model name or None for default
            temperature: Temperature setting
            
        Returns:
            LLM instance
        """
        # Use vision-capable model if computer use is enabled
        if self.computer_use:
            model = model or "gpt-4o"  # gpt-4o has vision capabilities
        else:
            model = model or "gpt-4-turbo-preview"
            
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable required"
            )
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=api_key
        )
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor.
        
        Returns:
            AgentExecutor instance
        """
        # Choose system prompt based on mode
        system_prompt = COMPUTER_USE_SYSTEM_PROMPT if self.computer_use else SYSTEM_PROMPT
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create callbacks
        callbacks = [ProgressCallback()]
        if self.verbose:
            callbacks.append(UserInputCallback(verbose=True))
        
        # Create executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose,
            callbacks=callbacks,
            handle_parsing_errors=True,
            max_iterations=15,
            return_intermediate_steps=False
        )
    
    def run(self, query: str) -> str:
        """Run the agent with a query.

        Args:
            query: User's natural language query

        Returns:
            Agent's response
        """
        try:
            # Detect optional debug tags in the query
            clean_query, debug_mode = self._parse_debug_flags(query)

            # Augment input with debug instructions when requested
            input_text = clean_query
            if debug_mode:
                debug_instructions = (
                    "\n\n[DEBUG MODE]\n"
                    "For this request, work step-by-step. Explain your plan and, after each major action "
                    "or short sequence of actions, ask the user to confirm that things look correct before "
                    "you continue. Use screenshots and other tools sparingly, only when needed to understand "
                    "or verify the state."
                )
                input_text = f"{clean_query}\n{debug_instructions}"

            result = self.agent_executor.invoke({"input": input_text})
            response = result.get("output", "No response generated")

            # Play completion sound to notify user
            try:
                from notification_sound import play_completion_sound
                play_completion_sound()
            except:
                pass  # Silently fail if notification doesn't work

            return response
        except Exception as e:
            error_msg = f"Agent error: {e}"
            if self.verbose:
                import traceback
                traceback.print_exc()
            return error_msg
    
    def chat(self, message: str) -> str:
        """Chat with the agent (with conversation history).
        
        Args:
            message: User's message
            
        Returns:
            Agent's response
        """
        return self.run(message)
    
    def reset(self):
        """Reset the agent's memory and state."""
        self.memory.clear()
        self.state = AgentState()
        # Reinitialize tools with new state
        if self.computer_use and self.anthropic_client:
            from .tools import ExtractPageContentTool, ExtractDatabaseTool, GetCurrentContextTool, AskUserTool
            computer_tools = get_computer_use_tools(self.anthropic_client, self.state)
            extraction_tools = [
                ExtractPageContentTool(orchestrator=self.orchestrator, state=self.state),
                ExtractDatabaseTool(orchestrator=self.orchestrator, state=self.state),
                GetCurrentContextTool(orchestrator=self.orchestrator, state=self.state),
                AskUserTool(orchestrator=self.orchestrator, state=self.state),
            ]

            # Conditionally add Notion-specific tools (only with vision-enabled provider)
            notion_specific_tools = []
            if self.enable_notion_tools and hasattr(self.anthropic_client, '_click_element'):
                notion_specific_tools = get_notion_specific_tools(self.anthropic_client, self.state)
                if self.verbosity in ["verbose", "default"]:
                    print(f"✓ Loaded {len(notion_specific_tools)} Notion-specific tools")

            self.tools = computer_tools + notion_specific_tools + extraction_tools
        else:
            self.tools = get_notion_tools(self.orchestrator, self.state)
        self.agent_executor = self._create_agent()
    
    def get_state_summary(self) -> str:
        """Get a summary of the current state.
        
        Returns:
            State summary string
        """
        return self.state.get_context_summary()
    
    def interactive_mode(self):
        """Run the agent in interactive mode.
        
        Allows multi-turn conversation until user exits.
        """
        print("\n" + "="*70)
        print("NOTION AGENT - INTERACTIVE MODE")
        print("="*70)
        print("Ask me anything about your Notion workspace!")
        print("Commands: 'exit', 'quit', 'reset', 'status'")
        print("="*70 + "\n")
        
        while True:
            try:
                # Get user input
                user_input = input("\n You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    print("\n👋 Goodbye!\n")
                    break
                
                if user_input.lower() == 'reset':
                    self.reset()
                    print("\n🔄 Agent reset. Starting fresh!\n")
                    continue
                
                if user_input.lower() == 'status':
                    print("\n" + self.get_state_summary() + "\n")
                    continue
                
                # Run agent
                print("\nAgent:", end=" ")
                response = self.chat(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!\n")
                break
            except EOFError:
                print("\n\n👋 Goodbye!\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                if self.verbose:
                    import traceback
                    traceback.print_exc()


def create_agent(
    model: Optional[str] = None,
    notion_token: Optional[str] = None,
    output_dir: str = "output",
    verbose: bool = False,
    verbosity: VerbosityLevel = "default",
    computer_use: bool = True,
    display_num: int = 1,
) -> NotionAgent:
    """Create a Notion agent instance.

    Uses OpenAI for LLM chat and Anthropic for Computer Use (vision/screen control).

    Args:
        model: Specific model name or None for default (uses OpenAI gpt-4o)
        notion_token: Optional Notion API token
        output_dir: Output directory
        verbose: Enable verbose logging (deprecated, use verbosity)
        verbosity: Verbosity level (silent, minimal, default, verbose)
        computer_use: Enable Computer Use via Anthropic (default: True)
        display_num: Display number for Computer Use (1-based)

    Returns:
        NotionAgent instance
    """
    return NotionAgent(
        notion_token=notion_token,
        output_dir=output_dir,
        model=model,
        verbose=verbose,
        verbosity=verbosity,
        computer_use=computer_use,
        display_num=display_num,
    )

