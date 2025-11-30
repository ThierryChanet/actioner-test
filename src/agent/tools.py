"""LangChain tools for Notion extraction operations."""

import json
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from ..orchestrator import NotionOrchestrator
from .state import AgentState
from .callbacks import ask_user_input, ask_yes_no, show_progress


class NavigateToPageInput(BaseModel):
    """Input for navigate_to_page tool."""
    page_name: str = Field(description="Name of the page to navigate to")


class NavigateToPageTool(BaseTool):
    """Tool for navigating to a Notion page by name."""
    
    name: str = "navigate_to_page"
    description: str = (
        "Navigate to a Notion page by its name. "
        "Use this when you need to open a specific page. "
        "Returns success status and current page title."
    )
    args_schema: Type[BaseModel] = NavigateToPageInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, page_name: str) -> str:
        """Navigate to a page."""
        show_progress(f"Navigating to: {page_name}")
        
        success = self.orchestrator.navigate_to_page(page_name)
        
        if success:
            current = self.orchestrator.get_current_page_title()
            self.state.update_current_page(current or page_name)
            return f"Successfully navigated to: {current}"
        else:
            return f"Failed to navigate to: {page_name}. Page may not exist or is not accessible."


class ExtractPageContentInput(BaseModel):
    """Input for extract_page_content tool."""
    page_name: Optional[str] = Field(
        default=None,
        description="Name of page to extract. If None, extracts current page."
    )
    use_ocr: bool = Field(
        default=True,
        description="Whether to use OCR as fallback for inaccessible elements"
    )


class ExtractPageContentTool(BaseTool):
    """Tool for extracting content from a Notion page."""
    
    name: str = "extract_page_content"
    description: str = (
        "Extract all content from a Notion page. "
        "If page_name is provided, navigates to it first. "
        "Returns extracted blocks with text content, types, and metadata. "
        "Use this to read page content."
    )
    args_schema: Type[BaseModel] = ExtractPageContentInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, page_name: Optional[str] = None, use_ocr: bool = True) -> str:
        """Extract page content."""
        if page_name:
            show_progress(f"Extracting page: {page_name}")
            result = self.orchestrator.extract_page(page_name, use_ocr=use_ocr)
        else:
            current = self.orchestrator.get_current_page_title()
            show_progress(f"Extracting current page: {current}")
            result = self.orchestrator.extract_current_page(use_ocr=use_ocr)
        
        if not result:
            return "Failed to extract page content. Make sure Notion is open and page is accessible."
        
        # Record extraction
        self.state.record_extraction(result.title, len(result.blocks))
        
        # Format result
        output = {
            "title": result.title,
            "total_blocks": len(result.blocks),
            "blocks": [
                {
                    "type": b.block_type,
                    "content": b.content[:200],  # Truncate for LLM
                    "source": b.source,
                }
                for b in result.blocks[:50]  # Limit to first 50 blocks
            ]
        }
        
        if len(result.blocks) > 50:
            output["note"] = f"Showing first 50 of {len(result.blocks)} blocks"
        
        return json.dumps(output, indent=2)


class ExtractDatabaseInput(BaseModel):
    """Input for extract_database tool."""
    database_id: Optional[str] = Field(
        default=None,
        description="Database ID (for API extraction) or None for current database view"
    )
    limit: int = Field(
        default=10,
        description="Maximum number of pages to extract from database"
    )


class ExtractDatabaseTool(BaseTool):
    """Tool for extracting pages from a Notion database."""
    
    name: str = "extract_database"
    description: str = (
        "Extract multiple pages from a Notion database. "
        "If database_id is provided and API token is available, uses fast API extraction. "
        "Otherwise, navigates through current database view. "
        "Returns list of extracted pages with their content."
    )
    args_schema: Type[BaseModel] = ExtractDatabaseInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, database_id: Optional[str] = None, limit: int = 10) -> str:
        """Extract database pages."""
        if database_id:
            show_progress(f"Extracting {limit} pages from database: {database_id}")
        else:
            current = self.orchestrator.get_current_page_title()
            show_progress(f"Extracting {limit} pages from current view: {current}")
        
        results = self.orchestrator.extract_database_pages(
            database_id=database_id,
            limit=limit
        )
        
        if not results:
            return "Failed to extract database. Make sure you're on a database view or provide valid database_id."
        
        # Format output
        output = {
            "total_pages": len(results),
            "pages": [
                {
                    "title": r.title,
                    "blocks": len(r.blocks),
                    "preview": r.blocks[0].content[:100] if r.blocks else ""
                }
                for r in results
            ]
        }
        
        # Update state
        for r in results:
            self.state.record_extraction(r.title, len(r.blocks))
        
        return json.dumps(output, indent=2)


class ListPagesInput(BaseModel):
    """Input for list_pages tool."""
    pass


class ListPagesTool(BaseTool):
    """Tool for listing available pages."""
    
    name: str = "list_available_pages"
    description: str = (
        "List all pages available in the Notion sidebar. "
        "Use this to discover what pages exist before navigating or extracting."
    )
    args_schema: Type[BaseModel] = ListPagesInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """List available pages."""
        show_progress("Listing available pages...")
        
        pages = self.orchestrator.list_available_pages()
        
        if not pages:
            return "No pages found in sidebar. Make sure Notion is open."
        
        # Cache in state
        self.state.available_pages = [p["name"] for p in pages]
        
        output = {
            "total_pages": len(pages),
            "pages": [p["name"] for p in pages]
        }
        
        return json.dumps(output, indent=2)


class SearchPagesInput(BaseModel):
    """Input for search_pages tool."""
    query: str = Field(description="Search query to match against page names")


class SearchPagesTool(BaseTool):
    """Tool for searching pages."""
    
    name: str = "search_pages"
    description: str = (
        "Search for pages whose names contain the query string. "
        "Case-insensitive search. Returns matching page names."
    )
    args_schema: Type[BaseModel] = SearchPagesInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, query: str) -> str:
        """Search for pages."""
        show_progress(f"Searching for pages matching: {query}")
        
        matches = self.orchestrator.search_pages(query)
        
        if not matches:
            return f"No pages found matching: {query}"
        
        output = {
            "query": query,
            "matches": len(matches),
            "pages": [p["name"] for p in matches]
        }
        
        return json.dumps(output, indent=2)


class GetCurrentContextInput(BaseModel):
    """Input for get_current_context tool."""
    pass


class GetCurrentContextTool(BaseTool):
    """Tool for getting current Notion context."""
    
    name: str = "get_current_context"
    description: str = (
        "Get information about the current Notion state: "
        "current page, recent activity, extraction count. "
        "Use this to understand what's already been done."
    )
    args_schema: Type[BaseModel] = GetCurrentContextInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self) -> str:
        """Get current context."""
        current_page = self.orchestrator.get_current_page_title()
        
        context = {
            "current_page": current_page,
            "extractions_this_session": self.state.extraction_count,
            "last_extraction": self.state.last_extraction,
            "summary": self.state.get_context_summary()
        }
        
        return json.dumps(context, indent=2)


class AskUserInput(BaseModel):
    """Input for ask_user tool."""
    question: str = Field(description="Question to ask the user")
    default: Optional[str] = Field(
        default=None,
        description="Default answer if user presses enter"
    )


class AskUserTool(BaseTool):
    """Tool for asking user for input when stuck."""
    
    name: str = "ask_user"
    description: str = (
        "Ask the user for clarification or additional information. "
        "Use this when you need: database IDs, page names you can't find, "
        "or clarification on ambiguous requests. "
        "The user will type their response."
    )
    args_schema: Type[BaseModel] = AskUserInput
    
    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)
    
    def _run(self, question: str, default: Optional[str] = None) -> str:
        """Ask user for input."""
        print(f"\n❓ {question}")
        response = ask_user_input("Your answer", default=default)
        return response


def get_notion_tools(
    orchestrator: NotionOrchestrator,
    state: AgentState
) -> List[BaseTool]:
    """Get all Notion tools for the agent.
    
    Args:
        orchestrator: NotionOrchestrator instance
        state: AgentState instance
        
    Returns:
        List of LangChain tools
    """
    return [
        NavigateToPageTool(orchestrator=orchestrator, state=state),
        ExtractPageContentTool(orchestrator=orchestrator, state=state),
        ExtractDatabaseTool(orchestrator=orchestrator, state=state),
        ListPagesTool(orchestrator=orchestrator, state=state),
        SearchPagesTool(orchestrator=orchestrator, state=state),
        GetCurrentContextTool(orchestrator=orchestrator, state=state),
        AskUserTool(orchestrator=orchestrator, state=state),
    ]

