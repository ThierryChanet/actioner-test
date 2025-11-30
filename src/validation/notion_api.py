"""Notion API client for gold standard baseline extraction."""

from typing import Optional, List, Dict, Any
from notion_client import Client
from ..notion.extractor import Block, ExtractionResult


class NotionAPIClient:
    """Client for accessing Notion API to get gold standard content."""

    def __init__(self, auth_token: str):
        """Initialize the Notion API client.
        
        Args:
            auth_token: Notion integration token
        """
        self.client = Client(auth=auth_token)

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get a page by ID.
        
        Args:
            page_id: The page ID (with or without hyphens)
            
        Returns:
            Page object from Notion API
        """
        # Remove hyphens if present
        page_id = page_id.replace("-", "")
        
        try:
            return self.client.pages.retrieve(page_id=page_id)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve page: {e}")

    def get_blocks(self, block_id: str) -> List[Dict[str, Any]]:
        """Get child blocks for a block/page.
        
        Args:
            block_id: The block or page ID
            
        Returns:
            List of block objects
        """
        # Remove hyphens if present
        block_id = block_id.replace("-", "")
        
        try:
            blocks = []
            has_more = True
            start_cursor = None
            
            while has_more:
                response = self.client.blocks.children.list(
                    block_id=block_id,
                    start_cursor=start_cursor,
                    page_size=100
                )
                
                blocks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")
            
            return blocks
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve blocks: {e}")

    def get_all_blocks_recursive(self, block_id: str) -> List[Dict[str, Any]]:
        """Get all blocks recursively, including nested blocks.
        
        Args:
            block_id: The block or page ID
            
        Returns:
            Flattened list of all blocks
        """
        all_blocks = []
        
        blocks = self.get_blocks(block_id)
        
        for block in blocks:
            all_blocks.append(block)
            
            # Check if block has children
            if block.get("has_children", False):
                child_blocks = self.get_all_blocks_recursive(block["id"])
                all_blocks.extend(child_blocks)
        
        return all_blocks

    def extract_text_from_block(self, block: Dict[str, Any]) -> Optional[str]:
        """Extract text content from a block.
        
        Args:
            block: Block object from Notion API
            
        Returns:
            Text content or None
        """
        block_type = block.get("type")
        if not block_type:
            return None
        
        block_data = block.get(block_type, {})
        
        # Most blocks have a "rich_text" array
        rich_text = block_data.get("rich_text", [])
        if rich_text:
            return "".join([text.get("plain_text", "") for text in rich_text])
        
        # Some blocks have "text" directly
        text = block_data.get("text")
        if text:
            return text
        
        # Code blocks have "caption" and "rich_text"
        if block_type == "code":
            return "".join([text.get("plain_text", "") for text in rich_text])
        
        # Equations have "expression"
        if block_type == "equation":
            return block_data.get("expression", "")
        
        return None

    def page_to_extraction_result(self, page_id: str) -> ExtractionResult:
        """Convert a Notion page to an ExtractionResult for comparison.
        
        Args:
            page_id: The page ID
            
        Returns:
            ExtractionResult with normalized content
        """
        # Get page info
        page = self.get_page(page_id)
        
        # Extract title
        title = self._extract_page_title(page)
        
        # Create result
        result = ExtractionResult(page_id=page_id, title=title)
        result.metadata["source"] = "notion_api"
        
        # Get all blocks
        blocks = self.get_all_blocks_recursive(page_id)
        
        # Convert to Block objects
        for i, block in enumerate(blocks):
            text = self.extract_text_from_block(block)
            if text and text.strip():
                block_type = self._map_block_type(block.get("type", "paragraph"))
                
                result_block = Block(
                    content=text.strip(),
                    block_type=block_type,
                    source="api",
                    order=i,
                    metadata={
                        "block_id": block.get("id"),
                        "type": block.get("type"),
                    }
                )
                result.add_block(result_block)
        
        result.metadata["block_count"] = len(result.blocks)
        
        return result

    def _extract_page_title(self, page: Dict[str, Any]) -> str:
        """Extract title from a page object.
        
        Args:
            page: Page object from API
            
        Returns:
            Page title
        """
        # Try to get title from properties
        properties = page.get("properties", {})
        
        # Look for "title" property
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return "".join([t.get("plain_text", "") for t in title_array])
        
        # Fallback to page ID
        return page.get("id", "Untitled")

    def _map_block_type(self, notion_type: str) -> str:
        """Map Notion block type to our block type.
        
        Args:
            notion_type: Notion block type
            
        Returns:
            Normalized block type
        """
        type_mapping = {
            "paragraph": "text",
            "heading_1": "heading",
            "heading_2": "heading",
            "heading_3": "heading",
            "bulleted_list_item": "list",
            "numbered_list_item": "list",
            "to_do": "list",
            "toggle": "text",
            "quote": "text",
            "code": "code",
            "equation": "equation",
            "callout": "text",
        }
        
        return type_mapping.get(notion_type, "text")

    def search_pages(self, query: str) -> List[Dict[str, Any]]:
        """Search for pages by title.
        
        Args:
            query: Search query
            
        Returns:
            List of matching page objects
        """
        try:
            response = self.client.search(
                query=query,
                filter={"property": "object", "value": "page"}
            )
            return response.get("results", [])
        except Exception as e:
            raise RuntimeError(f"Search failed: {e}")

    def get_page_id_by_title(self, title: str) -> Optional[str]:
        """Get page ID by title.
        
        Args:
            title: Page title to search for
            
        Returns:
            Page ID or None if not found
        """
        pages = self.search_pages(title)
        
        for page in pages:
            page_title = self._extract_page_title(page)
            if page_title.lower() == title.lower():
                return page.get("id")
        
        return None

    def query_database(
        self,
        database_id: str,
        page_size: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Query a database and return pages.
        
        Args:
            database_id: The database ID (with or without hyphens)
            page_size: Number of pages to retrieve (default: 10, max: 100)
            filter_dict: Optional filter criteria
            sorts: Optional sort criteria
            
        Returns:
            List of page objects from the database
        """
        # Remove hyphens if present
        database_id = database_id.replace("-", "")
        
        try:
            query_params = {
                "database_id": database_id,
                "page_size": min(page_size, 100)  # Notion API max is 100
            }
            
            if filter_dict:
                query_params["filter"] = filter_dict
            
            if sorts:
                query_params["sorts"] = sorts
            
            response = self.client.databases.query(**query_params)
            return response.get("results", [])
            
        except Exception as e:
            raise RuntimeError(f"Failed to query database: {e}")
    
    def get_database(self, database_id: str) -> Dict[str, Any]:
        """Get database metadata.
        
        Args:
            database_id: The database ID
            
        Returns:
            Database object from Notion API
        """
        # Remove hyphens if present
        database_id = database_id.replace("-", "")
        
        try:
            return self.client.databases.retrieve(database_id=database_id)
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve database: {e}")
    
    def extract_database_pages(
        self,
        database_id: str,
        limit: int = 10
    ) -> List[ExtractionResult]:
        """Extract content from multiple pages in a database.
        
        Args:
            database_id: The database ID
            limit: Maximum number of pages to extract (default: 10)
            
        Returns:
            List of ExtractionResult objects
        """
        try:
            # Query the database for pages
            pages = self.query_database(database_id, page_size=limit)
            
            results = []
            for page in pages:
                page_id = page.get("id")
                if page_id:
                    try:
                        result = self.page_to_extraction_result(page_id)
                        results.append(result)
                    except Exception as e:
                        # Log error but continue with other pages
                        print(f"Warning: Failed to extract page {page_id}: {e}")
                        continue
            
            return results
            
        except Exception as e:
            raise RuntimeError(f"Failed to extract database pages: {e}")

    def test_connection(self) -> bool:
        """Test if the API connection is working.
        
        Returns:
            True if connection is successful
        """
        try:
            # Try to list users as a connection test
            self.client.users.list()
            return True
        except Exception:
            return False

