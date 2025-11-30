"""Helper functions for extracting content from Notion databases."""

from typing import List, Optional, Dict, Any
from .validation.notion_api import NotionAPIClient
from .notion.extractor import ExtractionResult
from .output.json_writer import JSONWriter
from .output.csv_writer import CSVWriter


def extract_database_pages(
    database_id: str,
    notion_token: str,
    limit: int = 10,
    output_dir: Optional[str] = None,
    output_format: str = 'json',
    verbose: bool = False
) -> List[ExtractionResult]:
    """Extract content from the first N pages of a Notion database.
    
    This is a high-level function that queries a database, retrieves pages,
    and extracts their content using the Notion API. Perfect for extracting
    recipes from a Recipe database or any other structured content.
    
    Args:
        database_id: The Notion database ID (with or without hyphens)
        notion_token: Your Notion integration token
        limit: Maximum number of pages to extract (default: 10)
        output_dir: Directory to save output files (optional)
        output_format: Output format: 'json', 'csv', or 'both'
        verbose: Print detailed progress information
        
    Returns:
        List of ExtractionResult objects, one per page
        
    Raises:
        RuntimeError: If API connection fails or extraction errors occur
        
    Example:
        >>> # Extract first 10 recipes from a Recipe database
        >>> token = "secret_ABC123..."
        >>> db_id = "abc123def456"
        >>> results = extract_database_pages(db_id, token, limit=10)
        >>> 
        >>> # Print titles
        >>> for result in results:
        ...     print(f"{result.title}: {len(result.blocks)} blocks")
        >>>
        >>> # Extract and save to files
        >>> results = extract_database_pages(
        ...     db_id,
        ...     token,
        ...     limit=10,
        ...     output_dir='output',
        ...     output_format='both'
        ... )
    """
    # Initialize API client
    api_client = NotionAPIClient(notion_token)
    
    # Test connection
    if verbose:
        print(f"Connecting to Notion API...")
    
    if not api_client.test_connection():
        raise RuntimeError("Failed to connect to Notion API. Check your token.")
    
    if verbose:
        print("✓ Connected to Notion API")
    
    # Get database metadata
    try:
        database = api_client.get_database(database_id)
        db_title = database.get('title', [{}])[0].get('plain_text', 'Unknown Database')
        if verbose:
            print(f"Database: {db_title}")
    except Exception as e:
        if verbose:
            print(f"Warning: Could not fetch database metadata: {e}")
    
    # Extract pages
    if verbose:
        print(f"Querying database for up to {limit} pages...")
    
    results = api_client.extract_database_pages(database_id, limit=limit)
    
    if verbose:
        print(f"✓ Extracted {len(results)} pages")
    
    # Save to files if output directory specified
    if output_dir:
        save_results(results, output_dir, output_format, verbose)
    
    return results


def save_results(
    results: List[ExtractionResult],
    output_dir: str,
    output_format: str = 'json',
    verbose: bool = False
) -> None:
    """Save extraction results to files.
    
    Args:
        results: List of ExtractionResult objects
        output_dir: Directory to save files
        output_format: 'json', 'csv', or 'both'
        verbose: Print file paths
    """
    json_writer = JSONWriter(output_dir) if output_format in ['json', 'both'] else None
    csv_writer = CSVWriter(output_dir) if output_format in ['csv', 'both'] else None
    
    for i, result in enumerate(results, 1):
        if verbose:
            print(f"Saving page {i}/{len(results)}: {result.title}")
        
        if json_writer:
            json_path = json_writer.write_extraction(result)
            if verbose:
                print(f"  → {json_path}")
        
        if csv_writer:
            csv_path = csv_writer.write_extraction(result)
            if verbose:
                print(f"  → {csv_path}")


def get_database_pages_list(
    database_id: str,
    notion_token: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """Get a list of pages from a database without extracting full content.
    
    Useful for previewing what's in a database before doing full extraction.
    
    Args:
        database_id: The Notion database ID
        notion_token: Your Notion integration token
        limit: Maximum number of pages to retrieve (default: 10)
        
    Returns:
        List of page objects with basic metadata
        
    Example:
        >>> pages = get_database_pages_list(db_id, token, limit=10)
        >>> for page in pages:
        ...     title = page.get('properties', {}).get('Name', {})
        ...     print(f"Page ID: {page['id']}")
    """
    api_client = NotionAPIClient(notion_token)
    
    if not api_client.test_connection():
        raise RuntimeError("Failed to connect to Notion API")
    
    return api_client.query_database(database_id, page_size=limit)


def extract_single_page(
    page_id: str,
    notion_token: str,
    output_dir: Optional[str] = None,
    output_format: str = 'json',
    verbose: bool = False
) -> ExtractionResult:
    """Extract content from a single Notion page.
    
    Args:
        page_id: The Notion page ID
        notion_token: Your Notion integration token
        output_dir: Directory to save output file (optional)
        output_format: 'json', 'csv', or 'both'
        verbose: Print detailed information
        
    Returns:
        ExtractionResult object
        
    Example:
        >>> result = extract_single_page(page_id, token)
        >>> print(f"{result.title}")
        >>> print(f"Blocks: {len(result.blocks)}")
    """
    api_client = NotionAPIClient(notion_token)
    
    if verbose:
        print(f"Connecting to Notion API...")
    
    if not api_client.test_connection():
        raise RuntimeError("Failed to connect to Notion API")
    
    if verbose:
        print(f"Extracting page: {page_id}")
    
    result = api_client.page_to_extraction_result(page_id)
    
    if verbose:
        print(f"✓ Extracted: {result.title}")
        print(f"  Blocks: {len(result.blocks)}")
    
    # Save to file if output directory specified
    if output_dir:
        save_results([result], output_dir, output_format, verbose)
    
    return result

