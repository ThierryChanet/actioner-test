"""Core LangChain agent for Notion operations."""

import os
from typing import Optional, List, Dict, Any

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from ..orchestrator import NotionOrchestrator
from .state import AgentState
from .tools import get_notion_tools
from .callbacks import UserInputCallback, ProgressCallback


SYSTEM_PROMPT = """You are a Notion Extraction Expert assistant. You help users extract and analyze content from their Notion workspace using the macOS Notion app.

## Your Capabilities

You have access to these tools:
- navigate_to_page: Navigate to a specific page by name
- extract_page_content: Extract all content from a page (current or named)
- extract_database: Extract multiple pages from a database
- list_available_pages: List all pages in the sidebar
- search_pages: Search for pages by name
- get_current_context: Check current Notion state and what you've done
- ask_user: Ask the user for clarification when needed

## How to Help Users

1. **Understand the Request**: Break down complex requests into steps
2. **Explore First**: Use list_available_pages or search_pages to find what exists
3. **Navigate Wisely**: Navigate to pages before extracting them
4. **Extract Content**: Use extract_page_content or extract_database as appropriate
5. **Analyze Results**: Summarize extracted content meaningfully
6. **Ask When Stuck**: Use ask_user if you need database IDs, can't find pages, or need clarification

## Notion Structure

- **Pages**: Individual documents with content blocks
- **Databases**: Collections of pages (like a Recipe database)
- **Blocks**: Content units (text, headings, lists, etc.)

## Best Practices

- Always check current context before starting
- List available pages if user's request is vague
- Extract databases when user mentions "all" or "multiple" pages
- Provide summaries, not just raw data
- Ask for confirmation before large extractions
- If navigation fails, try searching or ask user for exact name

## Response Style

- Be concise but informative
- Show progress for long operations
- Summarize extraction results (e.g., "Extracted 5 recipes with 127 total blocks")
- If something fails, explain why and suggest alternatives
- Never refuse a request - always try or ask for clarification

## Example Interactions

User: "Extract all my recipes"
You: First, let me check what's available... [uses list_pages or search_pages, then extract_database]

User: "What's on the Roadmap page?"
You: [uses navigate_to_page, then extract_page_content, then summarizes the content]

User: "How many recipes do I have?"
You: [uses extract_database with appropriate limit, then counts and reports]

Remember: You can see the actual Notion app and interact with it directly. Be proactive and helpful!
"""


class NotionAgent:
    """LangChain-powered agent for Notion extraction."""
    
    def __init__(
        self,
        notion_token: Optional[str] = None,
        output_dir: str = "output",
        llm_provider: str = "openai",
        model: Optional[str] = None,
        temperature: float = 0,
        verbose: bool = False
    ):
        """Initialize the Notion agent.
        
        Args:
            notion_token: Optional Notion API token
            output_dir: Directory for output files
            llm_provider: LLM provider ('openai' or 'anthropic')
            model: Specific model to use (auto-selects if None)
            temperature: LLM temperature (0 = deterministic)
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.output_dir = output_dir
        
        # Initialize orchestrator
        self.orchestrator = NotionOrchestrator(
            notion_token=notion_token,
            output_dir=output_dir,
            verbose=verbose
        )
        
        # Initialize state
        self.state = AgentState()
        
        # Initialize LLM
        self.llm = self._init_llm(llm_provider, model, temperature)
        
        # Initialize tools
        self.tools = get_notion_tools(self.orchestrator, self.state)
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Initialize agent
        self.agent_executor = self._create_agent()
    
    def _init_llm(self, provider: str, model: Optional[str], temperature: float):
        """Initialize LLM based on provider.
        
        Args:
            provider: 'openai' or 'anthropic'
            model: Model name or None for default
            temperature: Temperature setting
            
        Returns:
            LLM instance
        """
        if provider == "openai":
            model = model or "gpt-4-turbo-preview"
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable required for OpenAI"
                )
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
        
        elif provider == "anthropic":
            model = model or "claude-3-5-sonnet-20241022"
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "ANTHROPIC_API_KEY environment variable required for Anthropic"
                )
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                api_key=api_key
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _create_agent(self) -> AgentExecutor:
        """Create the agent executor.
        
        Returns:
            AgentExecutor instance
        """
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
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
    llm_provider: str = "openai",
    model: Optional[str] = None,
    notion_token: Optional[str] = None,
    output_dir: str = "output",
    verbose: bool = False
) -> NotionAgent:
    """Create a Notion agent instance.
    
    Args:
        llm_provider: 'openai' or 'anthropic'
        model: Specific model name or None for default
        notion_token: Optional Notion API token
        output_dir: Output directory
        verbose: Enable verbose logging
        
    Returns:
        NotionAgent instance
    """
    return NotionAgent(
        notion_token=notion_token,
        output_dir=output_dir,
        llm_provider=llm_provider,
        model=model,
        verbose=verbose
    )

