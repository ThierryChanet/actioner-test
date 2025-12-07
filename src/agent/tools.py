"""LangChain tools for Notion extraction operations."""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

from ..orchestrator import NotionOrchestrator
from .state import AgentState
from .callbacks import ask_user_input, ask_yes_no, show_progress


SAVE_DIR_NAME = "saved_extractions"


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
            return json.dumps({
                "status": "sidebar_not_accessible",
                "message": "Sidebar not accessible. You can still extract content from the currently visible page using extract_page_content without a page_name.",
                "suggestion": "Use get_current_context to see what page is currently open, or extract_page_content() to extract the visible page."
            }, indent=2)
        
        # Cache in state
        self.state.available_pages = [p["name"] for p in pages]
        
        # Check if any page is marked as current
        current_pages = [p for p in pages if p.get("current")]
        
        if current_pages:
            output = {
                "status": "current_page_only",
                "message": "Sidebar not accessible, but current page detected",
                "current_page": current_pages[0]["name"],
                "total_pages": len(pages),
                "pages": [p["name"] for p in pages],
                "suggestion": "You can extract this page directly with extract_page_content()"
            }
        else:
            output = {
                "status": "success",
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


class SaveExtractionInput(BaseModel):
    """Input for save_extraction_result tool."""
    title: str = Field(description="Title to store with the extraction (used for filename)")
    content: str = Field(description="Extraction content to store (JSON or text)")


class SaveExtractionTool(BaseTool):
    """Tool for saving an extraction result to disk."""

    name: str = "save_extraction_result"
    description: str = (
        "Persist an extraction result to the saved_extractions folder under the agent output directory. "
        "Provide a title and the extraction content (JSON or text). "
        "Returns the saved file path."
    )
    args_schema: Type[BaseModel] = SaveExtractionInput

    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _slugify(self, text: str) -> str:
        """Create a filesystem-safe slug."""
        cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")
        return cleaned or "untitled"

    def _run(self, title: str, content: str) -> str:
        """Save extraction to a dedicated folder."""
        base_dir = Path(self.orchestrator.output_dir) / SAVE_DIR_NAME
        base_dir.mkdir(parents=True, exist_ok=True)

        slug = self._slugify(title)
        timestamp = int(time.time())
        filename = f"{timestamp}_{slug}.json"
        path = base_dir / filename

        payload = {
            "title": title,
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "content": content,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return json.dumps({
            "status": "success",
            "saved_path": str(path),
            "title": title
        }, indent=2)


class RetrieveSavedExtractionInput(BaseModel):
    """Input for retrieve_saved_extraction tool."""
    query: Optional[str] = Field(
        default=None,
        description="Optional title substring to filter saved extractions (case-insensitive). If omitted, returns most recent."
    )
    limit: int = Field(
        default=3,
        description="Maximum number of saved extractions to return (most recent first)"
    )


class RetrieveSavedExtractionTool(BaseTool):
    """Tool for retrieving saved extraction results."""

    name: str = "retrieve_saved_extraction"
    description: str = (
        "Retrieve saved extraction results from the saved_extractions folder under the agent output directory. "
        "Optionally filter by a title substring and control how many to return."
    )
    args_schema: Type[BaseModel] = RetrieveSavedExtractionInput

    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _run(self, query: Optional[str] = None, limit: int = 3) -> str:
        """Retrieve saved extractions."""
        base_dir = Path(self.orchestrator.output_dir) / SAVE_DIR_NAME
        if not base_dir.exists():
            return json.dumps({
                "status": "not_found",
                "message": f"No saved extractions. Folder does not exist at {base_dir}"
            }, indent=2)

        files = sorted(base_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

        if query:
            q = query.lower()
            files = [f for f in files if q in f.name.lower()]

        if not files:
            return json.dumps({
                "status": "empty",
                "message": "No saved extractions match the criteria",
                "query": query
            }, indent=2)

        results = []
        for file_path in files[: max(1, limit)]:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append({
                    "file": str(file_path),
                    "title": data.get("title"),
                    "saved_at": data.get("saved_at"),
                    "content": data.get("content"),
                })
            except Exception as exc:
                results.append({
                    "file": str(file_path),
                    "error": f"Failed to read file: {exc}"
                })

        return json.dumps({
            "status": "success",
            "count": len(results),
            "results": results
        }, indent=2)


class WipeSavedExtractionInput(BaseModel):
    """Input for wipe_saved_extractions tool."""
    confirm: bool = Field(
        default=False,
        description="Set to true to confirm wiping all saved extractions."
    )


class WipeSavedExtractionTool(BaseTool):
    """Tool for wiping the saved extractions folder."""

    name: str = "wipe_saved_extractions"
    description: str = (
        "Delete all files inside the saved_extractions folder under the agent output directory. "
        "Set confirm=true to proceed."
    )
    args_schema: Type[BaseModel] = WipeSavedExtractionInput

    orchestrator: NotionOrchestrator = Field(exclude=True)
    state: AgentState = Field(exclude=True)

    def _run(self, confirm: bool = False) -> str:
        """Wipe saved extractions."""
        if not confirm:
            return json.dumps({
                "status": "confirmation_required",
                "message": "Set confirm=true to delete all saved extractions."
            }, indent=2)

        base_dir = Path(self.orchestrator.output_dir) / SAVE_DIR_NAME
        if not base_dir.exists():
            return json.dumps({
                "status": "not_found",
                "message": f"No folder to wipe at {base_dir}"
            }, indent=2)

        deleted = 0
        for file_path in base_dir.glob("*"):
            try:
                file_path.unlink()
                deleted += 1
            except Exception as exc:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed after deleting {deleted} files. Error on {file_path}: {exc}"
                }, indent=2)

        return json.dumps({
            "status": "success",
            "deleted_files": deleted,
            "folder": str(base_dir)
        }, indent=2)


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
        SaveExtractionTool(orchestrator=orchestrator, state=state),
        RetrieveSavedExtractionTool(orchestrator=orchestrator, state=state),
        WipeSavedExtractionTool(orchestrator=orchestrator, state=state),
    ]

