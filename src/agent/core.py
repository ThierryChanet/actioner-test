"""Core LangChain agent for Notion operations."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any

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
from .computer_use_client import ComputerUseClient
from .computer_use_tools import get_computer_use_tools


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

## Example Interactions

User: "Extract all my recipes"
You: [takes screenshot, locates recipes database, extracts content]

User: "What's on the Roadmap page?"
You: [navigates to page, extracts content, summarizes]

User: "How many recipes do I have?"
You: [extracts database with appropriate limit, counts and reports]

Remember: You can see the actual Notion app and interact with it directly. Be proactive and helpful!
"""


COMPUTER_USE_SYSTEM_PROMPT = """You are a Computer Control Expert assistant with Notion extraction capabilities. You can control the computer through mouse clicks, keyboard input, and screenshots using OpenAI's Computer Control Tools to help users extract and analyze content from their Notion workspace.

## Your Capabilities

### Computer Control Tools:
- take_screenshot: Capture the current screen to see what's visible
- get_screen_info: Get screen dimensions and display information
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

1. **Always Screenshot First**: Before taking actions, take a screenshot to see what's on screen
2. **Coordinate System**: Screen coordinates start at (0,0) in top-left corner
3. **Be Precise**: Use exact coordinates from screenshot analysis
4. **Wait After Actions**: Some actions need time to complete (navigation, loading)
5. **Verify Success**: Take another screenshot after major actions to confirm
6. **Sequential Actions**: Break complex tasks into small sequential steps

## Navigation Workflow

1. Take screenshot to see current screen
2. Identify target UI elements and their coordinates
3. Click on elements (sidebar items, buttons, links)
4. Type text if needed (search, filters)
5. Press keys for special actions (Return, Escape, arrows)
6. Verify with another screenshot

## Extraction Workflow

1. Navigate to the target page/database
2. Wait for content to load
3. Use extract_page_content or extract_database
4. Summarize the extracted content
5. Report results to user

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
- Wait for page to load
- Use extract_page_content
- Summarize key points from the content

User: "Search for pages about meetings"
You:
- Take screenshot
- Click on search box
- Type "meetings"
- Press Return
- Click on relevant results
- Extract content

## Response Style

- Be concise and clear
- Explain what you're seeing in screenshots
- Show progress for multi-step operations
- Provide meaningful summaries of extracted content
- If actions fail, explain what went wrong and try alternatives

Remember: You have full computer control using OpenAI's Computer Control Tools. Take screenshots frequently to understand state, and use precise coordinates for reliable interactions!
"""


class NotionAgent:
    """LangChain-powered agent for Notion extraction."""
    
    def __init__(
        self,
        notion_token: Optional[str] = None,
        output_dir: str = "output",
        model: Optional[str] = None,
        temperature: float = 0,
        verbose: bool = False,
        computer_use: bool = True,
        display_num: int = 1,
    ):
        """Initialize the Notion agent.
        
        Args:
            notion_token: Optional Notion API token
            output_dir: Directory for output files
            model: Specific model to use (auto-selects if None)
            temperature: LLM temperature (0 = deterministic)
            verbose: Enable verbose logging
            computer_use: Enable Computer Use API for screen control (default: True)
            display_num: Display number for Computer Use (1-based)
        """
        self.verbose = verbose
        self.output_dir = output_dir
        self.computer_use = computer_use
        
        # Initialize orchestrator
        self.orchestrator = NotionOrchestrator(
            notion_token=notion_token,
            output_dir=output_dir,
            verbose=verbose
        )
        
        # Initialize state
        self.state = AgentState()
        
        # Initialize Computer Use client if enabled
        self.computer_client = None
        if computer_use:
            try:
                self.computer_client = ComputerUseClient(display_num=display_num)
            except Exception as e:
                if verbose:
                    print(f"Warning: Computer Use initialization failed: {e}")
                    print("Falling back to standard tools")
                self.computer_use = False
        
        # Initialize LLM (OpenAI only)
        self.llm = self._init_llm(model, temperature)
        
        # Initialize tools (computer use or standard)
        if self.computer_use and self.computer_client:
            # Computer use tools + extraction tools
            from .tools import ExtractPageContentTool, ExtractDatabaseTool, GetCurrentContextTool, AskUserTool
            computer_tools = get_computer_use_tools(self.computer_client, self.state)
            extraction_tools = [
                ExtractPageContentTool(orchestrator=self.orchestrator, state=self.state),
                ExtractDatabaseTool(orchestrator=self.orchestrator, state=self.state),
                GetCurrentContextTool(orchestrator=self.orchestrator, state=self.state),
                AskUserTool(orchestrator=self.orchestrator, state=self.state),
            ]
            self.tools = computer_tools + extraction_tools
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
    
    def _init_llm(self, model: Optional[str], temperature: float):
        """Initialize OpenAI LLM.
        
        Args:
            model: Model name or None for default
            temperature: Temperature setting
            
        Returns:
            LLM instance
        """
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
            result = self.agent_executor.invoke({"input": query})
            return result.get("output", "No response generated")
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
        if self.computer_use and self.computer_client:
            from .tools import ExtractPageContentTool, ExtractDatabaseTool, GetCurrentContextTool, AskUserTool
            computer_tools = get_computer_use_tools(self.computer_client, self.state)
            extraction_tools = [
                ExtractPageContentTool(orchestrator=self.orchestrator, state=self.state),
                ExtractDatabaseTool(orchestrator=self.orchestrator, state=self.state),
                GetCurrentContextTool(orchestrator=self.orchestrator, state=self.state),
                AskUserTool(orchestrator=self.orchestrator, state=self.state),
            ]
            self.tools = computer_tools + extraction_tools
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
    computer_use: bool = True,
    display_num: int = 1,
) -> NotionAgent:
    """Create a Notion agent instance.
    
    Args:
        model: Specific model name or None for default (uses OpenAI)
        notion_token: Optional Notion API token
        output_dir: Output directory
        verbose: Enable verbose logging
        computer_use: Enable Computer Use API for screen control (default: True)
        display_num: Display number for Computer Use (1-based)
        
    Returns:
        NotionAgent instance
    """
    return NotionAgent(
        notion_token=notion_token,
        output_dir=output_dir,
        model=model,
        verbose=verbose,
        computer_use=computer_use,
        display_num=display_num,
    )

