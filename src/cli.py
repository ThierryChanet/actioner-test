"""Command-line interface for Notion AX Extractor."""

import click
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from .ax.client import AXClient
from .notion.detector import NotionDetector
from .notion.navigator import NotionNavigator
from .notion.extractor import NotionExtractor
from .notion.database_ax_extractor import DatabaseAXExtractor
from .notion.mouse_navigator import MouseNavigator
from .notion.keyboard_navigator import KeyboardNavigator
from .notion.ocr_navigator import OCRNavigator
from .ocr.fallback import OCRHandler
from .validation.notion_api import NotionAPIClient
from .validation.comparator import Comparator
from .validation.differ import Differ
from .output.json_writer import JSONWriter
from .output.csv_writer import CSVWriter
from .output.logger import create_logger


@click.group()
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--output-dir', default='output', help='Output directory')
@click.pass_context
def cli(ctx, verbose, output_dir):
    """Notion macOS AX Extractor - Extract content from Notion desktop app."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['output_dir'] = output_dir
    ctx.obj['logger'] = create_logger(f"{output_dir}/logs", verbose=verbose)


@cli.command()
@click.argument('page_name')
@click.option('--mode', type=click.Choice(['normal', 'dry-run', 'debug']), default='normal',
              help='Execution mode')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json',
              help='Output format')
@click.option('--no-ocr', is_flag=True, help='Disable OCR fallback')
@click.pass_context
def extract(ctx, page_name, mode, output, no_ocr):
    """Extract content from a single page."""
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    try:
        logger.info(f"Starting extraction of page: {page_name}")
        logger.info(f"Mode: {mode}, Output: {output}, OCR: {'disabled' if no_ocr else 'enabled'}")
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        extractor = NotionExtractor(detector)
        
        # Setup OCR if enabled
        if not no_ocr:
            ocr_handler = OCRHandler()
            if ocr_handler.is_available():
                extractor.set_ocr_handler(ocr_handler)
                logger.info(f"OCR enabled: {ocr_handler.get_active_handler()}")
            else:
                logger.warning("OCR not available")
        
        # Find and activate Notion
        logger.info("Looking for Notion app...")
        debug_mode = ctx.obj['verbose']
        if not detector.ensure_notion_active(debug=debug_mode):
            logger.error("Notion app not found or not accessible")
            if not debug_mode:
                logger.info("Run with --verbose flag for more details")
            return
        
        logger.info("Notion app found and activated")
        
        if mode == 'dry-run':
            logger.info("[DRY-RUN] Would navigate to page: {page_name}")
            logger.info("[DRY-RUN] Would extract content and save to output")
            return
        
        # Check if we're already on the right page
        current_title = detector.get_page_title()
        logger.info(f"Current page title: {current_title}")
        already_on_page = current_title and page_name.lower() in current_title.lower()
        
        if already_on_page:
            logger.info(f"Already on page: {current_title}")
        else:
            # Navigate to page
            logger.info(f"Navigating to page: {page_name}")
            if not navigator.navigate_to_page(page_name):
                logger.error(f"Failed to navigate to page: {page_name}")
                # Check if we ended up on a page with similar name
                current_title = detector.get_page_title()
                if current_title and page_name.lower() in current_title.lower():
                    logger.info(f"Navigation resulted in similar page: {current_title} - continuing")
                    already_on_page = True
                
                if not already_on_page:
                    return
            else:
                logger.info("Navigation successful")
        
        # Wait for page to stabilize
        detector.wait_for_page_load()
        
        # Extract content
        start_time = time.time()
        logger.log_extraction_start(page_name)
        
        result = extractor.extract_page(use_ocr=not no_ocr)
        
        duration = time.time() - start_time
        logger.log_extraction_complete(page_name, len(result.blocks), duration)
        
        # Write output
        if output in ['json', 'both']:
            json_writer = JSONWriter(output_dir)
            json_path = json_writer.write_extraction(result)
            logger.info(f"JSON output written to: {json_path}")
        
        if output in ['csv', 'both']:
            csv_writer = CSVWriter(output_dir)
            csv_path = csv_writer.write_extraction(result)
            logger.info(f"CSV output written to: {csv_path}")
        
        logger.info(f"Extraction complete: {len(result.blocks)} blocks extracted")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--mode', type=click.Choice(['normal', 'dry-run', 'debug']), default='normal',
              help='Execution mode')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json',
              help='Output format')
@click.option('--no-ocr', is_flag=True, help='Disable OCR fallback')
@click.pass_context
def extract_all(ctx, mode, output, no_ocr):
    """Extract content from all pages in the sidebar."""
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    try:
        logger.info("Starting extraction of all pages")
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        extractor = NotionExtractor(detector)
        
        # Setup OCR if enabled
        if not no_ocr:
            ocr_handler = OCRHandler()
            if ocr_handler.is_available():
                extractor.set_ocr_handler(ocr_handler)
                logger.info(f"OCR enabled: {ocr_handler.get_active_handler()}")
        
        # Find and activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion app not found or not accessible")
            return
        
        # Get list of pages
        pages = navigator.get_sidebar_pages()
        logger.info(f"Found {len(pages)} pages in sidebar")
        
        if mode == 'dry-run':
            for i, page in enumerate(pages, 1):
                logger.info(f"[DRY-RUN] Would extract page {i}/{len(pages)}: {page['name']}")
            return
        
        # Extract each page
        total_blocks = 0
        for i, page in enumerate(pages, 1):
            page_name = page['name']
            logger.info(f"Processing page {i}/{len(pages)}: {page_name}")
            
            try:
                # Navigate to page
                if not navigator.navigate_to_page(page_name):
                    logger.warning(f"Failed to navigate to: {page_name}")
                    continue
                
                # Extract
                result = extractor.extract_page(use_ocr=not no_ocr)
                total_blocks += len(result.blocks)
                
                # Write output
                if output in ['json', 'both']:
                    json_writer = JSONWriter(output_dir)
                    json_writer.write_extraction(result)
                
                if output in ['csv', 'both']:
                    csv_writer = CSVWriter(output_dir)
                    csv_writer.write_extraction(result)
                
                logger.info(f"Extracted {len(result.blocks)} blocks from {page_name}")
                
            except Exception as e:
                logger.error(f"Failed to extract {page_name}: {e}")
                continue
        
        logger.log_session_summary(len(pages), total_blocks)
        
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.argument('page_name')
@click.pass_context
def navigate(ctx, page_name):
    """Navigate to a page without extraction."""
    logger = ctx.obj['logger']
    
    try:
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        
        # Find and activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        # Navigate
        logger.info(f"Navigating to: {page_name}")
        success = navigator.navigate_to_page(page_name)
        
        if success:
            logger.info(f"Successfully navigated to: {page_name}")
            current_title = detector.get_page_title()
            logger.info(f"Current page: {current_title}")
        else:
            logger.error(f"Navigation failed")
        
    except Exception as e:
        logger.error(f"Navigation failed: {e}")


@cli.command()
@click.argument('page_name')
@click.option('--notion-token', envvar='NOTION_TOKEN', help='Notion API token')
@click.option('--page-id', help='Notion page ID (if known)')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json',
              help='Output format')
@click.pass_context
def validate(ctx, page_name, notion_token, page_id, output):
    """Compare AX extraction with API baseline."""
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    if not notion_token:
        logger.error("Notion API token required. Use --notion-token or set NOTION_TOKEN env var")
        return
    
    try:
        logger.info(f"Starting validation for: {page_name}")
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        extractor = NotionExtractor(detector)
        api_client = NotionAPIClient(notion_token)
        
        # Test API connection
        if not api_client.test_connection():
            logger.error("Failed to connect to Notion API")
            return
        
        logger.info("Connected to Notion API")
        
        # Get page ID if not provided
        if not page_id:
            logger.info(f"Searching for page: {page_name}")
            page_id = api_client.get_page_id_by_title(page_name)
            if not page_id:
                logger.error(f"Page not found in API: {page_name}")
                return
            logger.info(f"Found page ID: {page_id}")
        
        # Get gold standard from API
        logger.info("Fetching gold standard from API...")
        gold_result = api_client.page_to_extraction_result(page_id)
        logger.info(f"Gold standard: {len(gold_result.blocks)} blocks")
        
        # Extract from AX
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        logger.info(f"Navigating to page...")
        if not navigator.navigate_to_page(page_name):
            logger.error("Navigation failed")
            return
        
        logger.info("Extracting content via AX...")
        extracted_result = extractor.extract_page()
        logger.info(f"Extracted: {len(extracted_result.blocks)} blocks")
        
        # Compare
        logger.info("Comparing results...")
        comparator = Comparator()
        comparison = comparator.compare(gold_result, extracted_result)
        
        logger.log_comparison(
            comparison.accuracy * 100,
            len(comparison.missing_blocks),
            len(comparison.extra_blocks)
        )
        
        # Generate diff
        differ = Differ()
        report = differ.generate_report(comparison, detailed=True)
        print("\n" + report)
        
        # Write outputs
        json_diff = differ.generate_json_diff(comparison)
        
        if output in ['json', 'both']:
            json_writer = JSONWriter(output_dir)
            json_writer.write_comparison(json_diff)
            logger.info(f"Comparison JSON written to: {output_dir}")
        
        if output in ['csv', 'both']:
            csv_writer = CSVWriter(output_dir)
            csv_writer.write_comparison(json_diff)
            logger.info(f"Comparison CSV written to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.pass_context
def list_pages(ctx):
    """List all pages in the Notion sidebar."""
    logger = ctx.obj['logger']
    
    try:
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        
        # Find and activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        # Get pages
        pages = navigator.get_sidebar_pages()
        
        if not pages:
            logger.warning("No pages found in sidebar")
            return
        
        logger.info(f"Found {len(pages)} pages:")
        print("\nPages in sidebar:")
        print("-" * 60)
        for i, page in enumerate(pages, 1):
            print(f"{i:3d}. {page['name']}")
        print("-" * 60)
        
    except Exception as e:
        logger.error(f"Failed to list pages: {e}")


@cli.command()
@click.argument('database_id')
@click.option('--notion-token', envvar='NOTION_TOKEN', help='Notion API token')
@click.option('--limit', default=10, help='Number of pages to extract (default: 10)')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json',
              help='Output format')
@click.pass_context
def extract_database(ctx, database_id, notion_token, limit, output):
    """Extract content from first N pages of a database (e.g., Recipe database)."""
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    if not notion_token:
        logger.error("Notion API token required. Use --notion-token or set NOTION_TOKEN env var")
        return
    
    try:
        logger.info(f"Starting extraction from database: {database_id}")
        logger.info(f"Limit: {limit} pages")
        
        # Initialize API client
        api_client = NotionAPIClient(notion_token)
        
        # Test API connection
        if not api_client.test_connection():
            logger.error("Failed to connect to Notion API")
            return
        
        logger.info("Connected to Notion API")
        
        # Get database info
        try:
            database = api_client.get_database(database_id)
            db_title = database.get('title', [{}])[0].get('plain_text', 'Unknown')
            logger.info(f"Database: {db_title}")
        except Exception as e:
            logger.warning(f"Could not fetch database metadata: {e}")
        
        # Extract pages from database
        logger.info(f"Querying database for up to {limit} pages...")
        results = api_client.extract_database_pages(database_id, limit=limit)
        
        logger.info(f"Successfully extracted {len(results)} pages from database")
        
        # Write output for each page
        json_writer = JSONWriter(output_dir) if output in ['json', 'both'] else None
        csv_writer = CSVWriter(output_dir) if output in ['csv', 'both'] else None
        
        total_blocks = 0
        for i, result in enumerate(results, 1):
            logger.info(f"Processing page {i}/{len(results)}: {result.title}")
            total_blocks += len(result.blocks)
            
            if json_writer:
                json_path = json_writer.write_extraction(result)
                logger.info(f"  → JSON: {json_path}")
            
            if csv_writer:
                csv_path = csv_writer.write_extraction(result)
                logger.info(f"  → CSV: {csv_path}")
        
        # Summary
        print("\n" + "="*70)
        print("EXTRACTION SUMMARY")
        print("="*70)
        print(f"Database ID:    {database_id}")
        print(f"Pages extracted: {len(results)}")
        print(f"Total blocks:    {total_blocks}")
        print(f"Output format:   {output}")
        print(f"Output directory: {output_dir}")
        print("="*70 + "\n")
        
        logger.log_session_summary(len(results), total_blocks)
        
    except Exception as e:
        logger.error(f"Database extraction failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--limit', default=10, help='Number of pages to extract (default: 10)')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json',
              help='Output format')
@click.option('--no-ocr', is_flag=True, help='Disable OCR fallback')
@click.option('--navigation-delay', default=1.0, help='Delay after navigation (seconds)')
@click.pass_context
def extract_database_ax(ctx, limit, output, no_ocr, navigation_delay):
    """Extract database pages using AX navigation (navigate through rows).
    
    This command navigates to a database view, clicks through rows,
    and extracts content using Accessibility APIs - no API token needed!
    
    Make sure you have a database view open in Notion before running.
    """
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    try:
        logger.info("Starting AX-based database extraction")
        logger.info(f"Will extract up to {limit} pages")
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        extractor = NotionExtractor(detector)
        
        # Setup OCR if enabled
        if not no_ocr:
            ocr_handler = OCRHandler()
            if ocr_handler.is_available():
                extractor.set_ocr_handler(ocr_handler)
                logger.info(f"OCR enabled: {ocr_handler.get_active_handler()}")
        
        # Find and activate Notion
        logger.info("Looking for Notion app...")
        if not detector.ensure_notion_active(debug=ctx.obj['verbose']):
            logger.error("Notion app not found or not accessible")
            return
        
        logger.info("Notion app found and activated")
        
        # Check current page
        current_title = detector.get_page_title()
        logger.info(f"Current view: {current_title}")
        
        print("\n" + "="*70)
        print("DATABASE EXTRACTION (AX Navigation)")
        print("="*70)
        print(f"Database view: {current_title}")
        print(f"Extraction limit: {limit} pages")
        print(f"Navigation delay: {navigation_delay}s")
        print("="*70 + "\n")
        
        # Initialize database extractor
        db_extractor = DatabaseAXExtractor(detector, navigator, extractor)
        
        # Preview available rows
        preview = db_extractor.preview_database(limit=limit)
        logger.info(f"Found {len(preview)} rows in database view")
        
        if not preview:
            logger.error("No database rows found. Make sure you're on a database view.")
            return
        
        print("Rows to extract:")
        for item in preview:
            print(f"  {item['index']+1}. {item['title']}")
        print()
        
        # Extract pages
        logger.info("Starting extraction...")
        start_time = time.time()
        
        results = db_extractor.extract_database_pages(
            limit=limit,
            use_ocr=not no_ocr,
            navigation_delay=navigation_delay
        )
        
        duration = time.time() - start_time
        
        # Write outputs
        json_writer = JSONWriter(output_dir) if output in ['json', 'both'] else None
        csv_writer = CSVWriter(output_dir) if output in ['csv', 'both'] else None
        
        total_blocks = 0
        for result in results:
            total_blocks += len(result.blocks)
            
            if json_writer:
                json_path = json_writer.write_extraction(result)
                logger.info(f"Saved: {json_path}")
            
            if csv_writer:
                csv_path = csv_writer.write_extraction(result)
                logger.info(f"Saved: {csv_path}")
        
        # Summary
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"Pages extracted: {len(results)}/{len(preview)}")
        print(f"Total blocks: {total_blocks}")
        print(f"Duration: {duration:.1f}s")
        print(f"Output directory: {output_dir}")
        print("="*70 + "\n")
        
        logger.log_session_summary(len(results), total_blocks)
        
    except Exception as e:
        logger.error(f"Database extraction failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.pass_context
def list_database_rows(ctx):
    """List all rows in the current database view.
    
    Useful for seeing what pages are available before extraction.
    """
    logger = ctx.obj['logger']
    
    try:
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        
        # Find and activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        # Check current page
        current_title = detector.get_page_title()
        logger.info(f"Current view: {current_title}")
        
        # Get database rows
        rows = navigator.get_database_rows()
        
        if not rows:
            logger.warning("No database rows found")
            print("\n⚠️  No rows found. Make sure you're viewing a database.")
            return
        
        # Display rows
        print("\n" + "="*70)
        print(f"DATABASE ROWS: {current_title}")
        print("="*70 + "\n")
        
        for i, row in enumerate(rows, 1):
            print(f"{i:3d}. {row['title']}")
        
        print("\n" + "="*70)
        print(f"Total rows: {len(rows)}")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Failed to list database rows: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--max-depth', default=25, help='Maximum depth to search (default: 25)')
@click.option('--show-groups', is_flag=True, help='Show detailed info about groups')
@click.pass_context
def debug_database_view(ctx, max_depth, show_groups):
    """Debug: Show AX element structure of current database view.
    
    This helps understand what elements are available for navigation.
    """
    logger = ctx.obj['logger']
    
    try:
        from .ax.utils import find_elements_by_role
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        
        # Find and activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        # Get current page info
        current_title = detector.get_page_title()
        logger.info(f"Current view: {current_title}")
        
        # Get content area
        content_area = detector.get_content_area()
        if not content_area:
            logger.error("Could not find content area")
            return
        
        print("\n" + "="*70)
        print("DATABASE VIEW DEBUG")
        print("="*70)
        print(f"Page: {current_title}")
        print(f"Search depth: {max_depth}\n")
        
        # First, look for static text elements that might be recipe names
        print("\n" + "="*70)
        print("LOOKING FOR RECIPE NAMES (AXStaticText)")
        print("="*70)
        
        static_texts = find_elements_by_role(content_area, "AXStaticText", max_depth=max_depth)
        recipe_candidates = []
        
        for elem in static_texts:
            text = elem.get_text_content()
            if text and len(text.strip()) > 3:  # Meaningful text
                # Skip common UI elements
                skip_terms = ['close', 'back', 'forward', 'search', 'filter', 'sort', 'new']
                if not any(term in text.lower() for term in skip_terms):
                    recipe_candidates.append({
                        'text': text.strip(),
                        'element': elem
                    })
        
        if recipe_candidates:
            print(f"\nFound {len(recipe_candidates)} potential recipe names:")
            print("-" * 70)
            for i, candidate in enumerate(recipe_candidates[:20]):
                print(f"  {i+1}. {candidate['text'][:60]}")
                
                # Check if parent or element is clickable
                elem = candidate['element']
                actions = elem.get_actions()
                has_press = "AXPress" in actions
                
                print(f"     Pressable: {has_press}")
                
                # Check parent element
                try:
                    parent = elem.get_attribute("AXParent")
                    if parent:
                        from .ax.element import AXElement
                        parent_elem = AXElement(parent)
                        parent_actions = parent_elem.get_actions()
                        parent_has_press = "AXPress" in parent_actions
                        parent_role = parent_elem.role
                        print(f"     Parent: {parent_role}, Pressable: {parent_has_press}")
                except:
                    pass
            
            if len(recipe_candidates) > 20:
                print(f"  ... and {len(recipe_candidates) - 20} more")
        else:
            print("\n❌ No potential recipe names found")
        
        # Now search for clickable elements near recipe names
        print("\n" + "="*70)
        print("LOOKING FOR CLICKABLE ELEMENTS")
        print("="*70)
        
        # Search for various element types
        roles_to_check = [
            "AXRow",
            "AXLink", 
            "AXButton",
            "AXCell",
            "AXTable",
            "AXList"
        ]
        
        clickable_found = False
        for role in roles_to_check:
            elements = find_elements_by_role(content_area, role, max_depth=max_depth)
            
            if elements:
                clickable_found = True
                print(f"\n{role}: {len(elements)} found")
                print("-" * 70)
                
                # Show first 10 elements
                for i, elem in enumerate(elements[:10]):
                    title = elem.title or elem.get_text_content() or "(no text)"
                    # Truncate long text
                    if len(title) > 60:
                        title = title[:57] + "..."
                    
                    actions = elem.get_actions()
                    has_press = "AXPress" in actions
                    
                    print(f"  {i+1}. {title}")
                    print(f"     Pressable: {has_press}, Actions: {actions}")
                
                if len(elements) > 10:
                    print(f"  ... and {len(elements) - 10} more")
        
        if not clickable_found:
            print("\n❌ No standard clickable elements found")
        
        # Show groups if requested
        if show_groups:
            print("\n" + "="*70)
            print("GROUPS (with text content)")
            print("="*70)
            
            groups = find_elements_by_role(content_area, "AXGroup", max_depth=max_depth)
            groups_with_text = []
            
            for group in groups:
                text = group.get_text_content()
                if text and len(text.strip()) > 3:
                    groups_with_text.append({
                        'text': text.strip()[:60],
                        'element': group,
                        'actions': group.get_actions()
                    })
            
            if groups_with_text:
                print(f"\nFound {len(groups_with_text)} groups with text:")
                for i, g in enumerate(groups_with_text[:10]):
                    print(f"  {i+1}. {g['text']}")
                    print(f"     Pressable: {'AXPress' in g['actions']}")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--max-depth', default=25, help='Maximum depth to search')
@click.option('--dry-run', is_flag=True, help='Find but dont click')
@click.pass_context
def test_database_clicks(ctx, max_depth, dry_run):
    """Debug: Try clicking on potential database row elements.
    
    This finds clickable elements and tries clicking them to see what works.
    """
    logger = ctx.obj['logger']
    
    try:
        from .ax.utils import find_elements_by_role
        import time
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        navigator = NotionNavigator(detector)
        
        # Find and activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        # Get current state
        current_title = detector.get_page_title()
        logger.info(f"Current view: {current_title}")
        
        # Get content area
        content_area = detector.get_content_area()
        if not content_area:
            logger.error("Could not find content area")
            return
        
        print("\n" + "="*70)
        print("TESTING DATABASE CLICKS")
        print("="*70)
        print(f"Starting page: {current_title}\n")
        
        # Collect all potential clickable elements with meaningful text
        candidates = []
        
        # Look for various roles that might contain recipe rows
        roles = ["AXButton", "AXLink", "AXGroup", "AXStaticText", "AXCell"]
        
        for role in roles:
            elements = find_elements_by_role(content_area, role, max_depth=max_depth)
            
            for elem in elements:
                text = elem.get_text_content()
                if not text or len(text.strip()) < 3:
                    continue
                
                # Skip obvious UI elements
                skip_terms = ['close', 'back', 'forward', 'search', 'filter', 'sort', 
                             'new tab', 'sidebar', 'menu', 'settings']
                if any(term in text.lower() for term in skip_terms):
                    continue
                
                # Check if clickable
                actions = elem.get_actions()
                is_pressable = "AXPress" in actions
                
                # Also check parent if element isn't pressable
                parent_pressable = False
                if not is_pressable:
                    try:
                        parent = elem.get_attribute("AXParent")
                        if parent:
                            from .ax.element import AXElement
                            parent_elem = AXElement(parent)
                            parent_actions = parent_elem.get_actions()
                            parent_pressable = "AXPress" in parent_actions
                    except:
                        pass
                
                if is_pressable or parent_pressable:
                    candidates.append({
                        'text': text.strip()[:60],
                        'element': elem,
                        'role': role,
                        'pressable': is_pressable,
                        'parent_pressable': parent_pressable
                    })
        
        # Remove duplicates by text
        seen_texts = set()
        unique_candidates = []
        for c in candidates:
            if c['text'] not in seen_texts:
                seen_texts.add(c['text'])
                unique_candidates.append(c)
        
        if not unique_candidates:
            print("❌ No clickable elements with meaningful text found\n")
            print("Try scrolling the database view or switching to table view.")
            return
        
        print(f"Found {len(unique_candidates)} potential clickable elements:\n")
        
        for i, candidate in enumerate(unique_candidates[:15]):
            print(f"{i+1}. {candidate['text']}")
            print(f"   Role: {candidate['role']}, Direct press: {candidate['pressable']}, "
                  f"Parent press: {candidate['parent_pressable']}")
        
        if len(unique_candidates) > 15:
            print(f"... and {len(unique_candidates) - 15} more")
        
        if dry_run:
            print("\n[DRY-RUN] Not clicking. Remove --dry-run to test clicks.\n")
            return
        
        # Ask user which to try
        print("\n" + "="*70)
        response = input(f"Try clicking on elements 1-{min(5, len(unique_candidates))}? (y/n): ")
        
        if response.lower() != 'y':
            print("Cancelled.")
            return
        
        print("\nTesting clicks...\n")
        
        successful_clicks = []
        
        for i, candidate in enumerate(unique_candidates[:5]):
            print(f"\nTest {i+1}: {candidate['text']}")
            print("-" * 70)
            
            old_title = detector.get_page_title()
            
            # Try clicking
            success = False
            if candidate['pressable']:
                print("  Clicking element directly...")
                success = candidate['element'].press()
            
            if not success and candidate['parent_pressable']:
                print("  Trying parent element...")
                try:
                    parent = candidate['element']._ref.AXParent
                    from .ax.element import AXElement
                    parent_elem = AXElement(parent)
                    success = parent_elem.press()
                except:
                    pass
            
            if success:
                print("  ✅ Click succeeded!")
                
                # Wait and check if page changed
                time.sleep(1.0)
                new_title = detector.get_page_title()
                
                if new_title != old_title:
                    print(f"  🎉 PAGE CHANGED: {old_title} → {new_title}")
                    successful_clicks.append({
                        'text': candidate['text'],
                        'role': candidate['role'],
                        'new_title': new_title
                    })
                    
                    # Navigate back
                    print("  Navigating back...")
                    navigator.navigate_back(wait_for_load=True)
                    time.sleep(1.0)
                else:
                    print("  ⚠️  Click worked but page didn't change")
            else:
                print("  ❌ Click failed")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        if successful_clicks:
            print(f"\n✅ Found {len(successful_clicks)} working clicks:\n")
            for click in successful_clicks:
                print(f"  • {click['text']} ({click['role']}) → {click['new_title']}")
            print("\nThese elements can be used for database navigation!")
        else:
            print("\n❌ No successful clicks found that changed the page.")
            print("\nTroubleshooting:")
            print("  1. Make sure you're in table/list view (not board/gallery)")
            print("  2. Try scrolling to load more rows")
            print("  3. Check if rows are collapsed/hidden")
        
        print()
        
    except Exception as e:
        logger.error(f"Test clicks failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.option('--depth', default=50, help='Search depth (default: 50)')
@click.pass_context
def scan_all_text(ctx, depth):
    """Debug: Aggressively scan ALL text in the current view.
    
    This searches very deeply to find all text elements, including recipes.
    """
    logger = ctx.obj['logger']
    
    try:
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        current_title = detector.get_page_title()
        content_area = detector.get_content_area()
        
        if not content_area:
            logger.error("No content area found")
            return
        
        print("\n" + "="*70)
        print("AGGRESSIVE TEXT SCAN")
        print("="*70)
        print(f"Page: {current_title}")
        print(f"Depth: {depth}\n")
        
        def scan_element(elem, depth_left, indent=0):
            """Recursively scan element tree."""
            if depth_left <= 0:
                return []
            
            results = []
            
            # Get text from this element
            text = elem.get_text_content()
            if text and len(text.strip()) > 2:
                actions = elem.get_actions()
                results.append({
                    'text': text.strip(),
                    'role': elem.role,
                    'pressable': 'AXPress' in actions,
                    'indent': indent
                })
            
            # Get children
            try:
                children_ref = elem.get_attribute("AXChildren")
                if children_ref:
                    from .ax.element import AXElement
                    for child_ref in children_ref:
                        try:
                            child = AXElement(child_ref)
                            results.extend(scan_element(child, depth_left - 1, indent + 1))
                        except:
                            pass
            except:
                pass
            
            return results
        
        print("Scanning element tree (this may take a moment)...")
        all_text = scan_element(content_area, depth)
        
        # Filter and deduplicate
        seen = set()
        unique_text = []
        for item in all_text:
            if item['text'] not in seen and len(item['text']) > 3:
                seen.add(item['text'])
                unique_text.append(item)
        
        print(f"\nFound {len(unique_text)} unique text elements:\n")
        print("="*70)
        
        # Group by pressable status
        pressable = [t for t in unique_text if t['pressable']]
        not_pressable = [t for t in unique_text if not t['pressable']]
        
        if pressable:
            print(f"\n✅ PRESSABLE ({len(pressable)}):")
            print("-" * 70)
            for item in pressable[:30]:
                print(f"  • {item['text'][:60]} ({item['role']})")
        
        if not_pressable:
            print(f"\n📝 NOT DIRECTLY PRESSABLE ({len(not_pressable)}):")
            print("-" * 70)
            for item in not_pressable[:30]:
                print(f"  • {item['text'][:60]} ({item['role']})")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.argument('recipe_name', required=False)
@click.pass_context
def test_mouse_click(ctx, recipe_name):
    """Test clicking on database rows using mouse coordinates.
    
    This finds text elements by their position and clicks them using mouse events.
    You can track the mouse cursor to see what's being clicked!
    
    Examples:
        python -m src.cli test-mouse-click
        python -m src.cli test-mouse-click "Topinambours"
    """
    logger = ctx.obj['logger']
    
    try:
        # Initialize
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        mouse_nav = MouseNavigator(detector)
        navigator = NotionNavigator(detector)
        
        if not detector.ensure_notion_active():
            logger.error("Notion app not found")
            return
        
        current_title = detector.get_page_title()
        logger.info(f"Current view: {current_title}")
        
        print("\n" + "="*70)
        print("MOUSE-BASED CLICKING TEST")
        print("="*70)
        print(f"Current page: {current_title}")
        print("\nSearching for clickable text elements...\n")
        
        # Get all text positions
        text_positions = mouse_nav.get_all_visible_text_positions(min_length=5)
        
        if not text_positions:
            print("❌ No text elements found")
            return
        
        # Filter out UI elements
        skip_terms = ['close', 'back', 'forward', 'search', 'filter', 'sort',
                     'new tab', 'sidebar', 'menu', 'settings', 'share', 'more']
        
        candidates = []
        for text, (x, y) in text_positions:
            if not any(term in text.lower() for term in skip_terms):
                candidates.append((text, x, y))
        
        if not candidates:
            print("❌ No suitable text elements found (after filtering UI)")
            return
        
        print(f"Found {len(candidates)} potential recipe elements:\n")
        
        for i, (text, x, y) in enumerate(candidates[:20]):
            print(f"{i+1}. {text[:60]} at ({x}, {y})")
        
        if len(candidates) > 20:
            print(f"... and {len(candidates) - 20} more")
        
        # If recipe name provided, try to click it
        if recipe_name:
            print(f"\n🖱️  Looking for: {recipe_name}")
            success = mouse_nav.click_on_text(recipe_name, delay=1.5)
            
            if success:
                new_title = detector.get_page_title()
                if new_title != current_title:
                    print(f"\n🎉 SUCCESS! Page changed:")
                    print(f"   {current_title} → {new_title}")
                    
                    # Navigate back
                    print("\nNavigating back...")
                    navigator.navigate_back(wait_for_load=True)
                else:
                    print("\n⚠️  Clicked but page didn't change")
            else:
                print("\n❌ Click failed or text not found")
            
            return
        
        # Otherwise, ask which to click
        print("\n" + "="*70)
        choice = input(f"Enter number to click (1-{min(len(candidates), 5)}) or 'q' to quit: ")
        
        if choice.lower() == 'q':
            print("Cancelled.")
            return
        
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(candidates):
                print("Invalid choice")
                return
            
            text, x, y = candidates[idx]
            print(f"\n🖱️  Clicking on: {text}")
            print(f"   Position: ({x}, {y})")
            print(f"   Watch your mouse cursor move!")
            
            time.sleep(1)  # Give user time to see message
            
            old_title = detector.get_page_title()
            success = mouse_nav.click_at_position(x, y, delay=1.5)
            
            if success:
                new_title = detector.get_page_title()
                if new_title != old_title:
                    print(f"\n🎉 SUCCESS! Page changed:")
                    print(f"   {old_title} → {new_title}")
                    
                    # Navigate back
                    print("\nNavigating back...")
                    navigator.navigate_back(wait_for_load=True)
                else:
                    print("\n⚠️  Clicked but page didn't change")
                    print("   (Maybe it's not a clickable row?)")
            
        except ValueError:
            print("Invalid input")
            return
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.pass_context
def show_content_tree(ctx):
    """Show the raw AX element tree structure.
    
    Simple diagnostic to see what Notion exposes.
    """
    logger = ctx.obj['logger']
    
    try:
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        
        if not detector.ensure_notion_active():
            print("❌ Notion not found")
            return
        
        current_title = detector.get_page_title()
        print(f"\n📄 Current page: {current_title}\n")
        
        content = detector.get_content_area()
        if not content:
            print("❌ No content area")
            return
        
        print("✅ Content area found")
        print(f"   Role: {content.role}")
        print(f"   Position: {content.position}")
        print(f"   Size: {content.size}")
        
        # Get direct children
        try:
            children_ref = content.get_attribute("AXChildren")
            if children_ref:
                print(f"\n📦 Direct children: {len(children_ref)}")
                
                from .ax.element import AXElement
                for i, child_ref in enumerate(children_ref[:10]):
                    try:
                        child = AXElement(child_ref)
                        text = child.get_text_content()
                        print(f"\n  Child {i+1}:")
                        print(f"    Role: {child.role}")
                        print(f"    Text: {text[:100] if text else '(none)'}")
                        print(f"    Actions: {child.get_actions()}")
                        
                        # Check grandchildren
                        try:
                            grandchildren = child.get_attribute("AXChildren")
                            if grandchildren:
                                print(f"    Children: {len(grandchildren)}")
                                # Show first few grandchild roles
                                for j, gc_ref in enumerate(grandchildren[:3]):
                                    gc = AXElement(gc_ref)
                                    gc_text = gc.get_text_content()
                                    print(f"      [{j+1}] {gc.role}: {gc_text[:40] if gc_text else '(no text)'}")
                        except:
                            pass
                            
                    except Exception as e:
                        print(f"  Child {i+1}: Error - {e}")
                
                if len(children_ref) > 10:
                    print(f"\n  ... and {len(children_ref) - 10} more children")
                    
            # Special handling for AXWebArea
            if content.role == "AXWebArea":
                print("\n" + "="*70)
                print("🌐 WEB CONTENT DETECTED")
                print("="*70)
                print("This is an Electron web view. Recipes are in HTML/DOM.")
                print("Standard AX navigation may not work well.")
                print("\nTrying to access web content...")
                
                # Try VERY DEEP scan for web content
                print("\nScanning web content (depth=100)...")
                
                def deep_scan(elem, depth=100, results=None):
                    """Ultra-deep recursive scan."""
                    if results is None:
                        results = []
                    if depth <= 0:
                        return results
                    
                    # Get text
                    text = elem.get_text_content()
                    if text and len(text.strip()) > 3:
                        results.append({
                            'text': text.strip(),
                            'role': elem.role,
                            'actions': elem.get_actions()
                        })
                    
                    # Recurse into children
                    try:
                        children = elem.get_attribute("AXChildren")
                        if children:
                            from .ax.element import AXElement
                            for child_ref in children:
                                try:
                                    child = AXElement(child_ref)
                                    deep_scan(child, depth - 1, results)
                                except:
                                    pass
                    except:
                        pass
                    
                    return results
                
                all_elements = deep_scan(content, depth=100)
                
                if all_elements:
                    print(f"✅ Found {len(all_elements)} text elements total")
                    
                    # Deduplicate
                    seen = set()
                    unique = []
                    for elem in all_elements:
                        if elem['text'] not in seen:
                            seen.add(elem['text'])
                            unique.append(elem)
                    
                    # Filter to recipe-like
                    skip_terms = ['close', 'back', 'forward', 'search', 'filter', 'sort',
                                 'new', 'share', 'more', 'settings', 'menu', 'edit', 'all meals',
                                 'healthy', 'verification', 'owner', 'tags', 'empty', 'name',
                                 'ingredients', 'link', 'duration', 'reference', 'tips']
                    
                    recipes = []
                    for elem in unique:
                        text_lower = elem['text'].lower()
                        # Skip short or UI text
                        if len(elem['text']) < 5:
                            continue
                        if any(skip in text_lower for skip in skip_terms):
                            continue
                        recipes.append(elem)
                    
                    if recipes:
                        print(f"\n🍳 POTENTIAL RECIPES ({len(recipes)}):")
                        print("-" * 70)
                        for i, elem in enumerate(recipes[:30]):
                            pressable = 'AXPress' in elem['actions']
                            icon = "✅" if pressable else "📝"
                            print(f"  {icon} {i+1}. {elem['text'][:60]} ({elem['role']})")
                        
                        if len(recipes) > 30:
                            print(f"\n  ... and {len(recipes) - 30} more")
                    else:
                        print("\n❌ No recipe-like text found after filtering")
                else:
                    print("❌ No text elements found in deep scan")
                    
        except Exception as e:
            print(f"\n❌ Could not get children: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option('--limit', default=10, help='Number of pages to extract')
@click.option('--tabs-to-first', default=5, help='Tab presses to reach first row')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json')
@click.option('--no-ocr', is_flag=True)
@click.pass_context
def extract_database_keyboard(ctx, limit, tabs_to_first, output, no_ocr):
    """Extract database using KEYBOARD navigation (Tab + Enter).
    
    This method works when AX detection fails. It:
    1. Tabs through the database rows
    2. Presses Enter to open each row
    3. Extracts content
    4. Goes back (Cmd+[)
    5. Repeats
    
    Make sure your database view is open and focused before running!
    """
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    try:
        logger.info("Starting keyboard-based database extraction")
        
        # Initialize
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        extractor = NotionExtractor(detector)
        keyboard_nav = KeyboardNavigator(detector)
        
        # Setup OCR
        if not no_ocr:
            ocr_handler = OCRHandler()
            if ocr_handler.is_available():
                extractor.set_ocr_handler(ocr_handler)
        
        # Activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion not found")
            return
        
        database_title = detector.get_page_title()
        
        print("\n" + "="*70)
        print("KEYBOARD-BASED DATABASE EXTRACTION")
        print("="*70)
        print(f"Database: {database_title}")
        print(f"Limit: {limit} pages")
        print(f"Tabs to first row: {tabs_to_first}")
        print("\n⚠️  IMPORTANT: Click on the Notion window now!")
        print("   The database view must be focused.")
        print("="*70)
        
        response = input("\nReady? Press Enter to start (or 'q' to quit): ")
        if response.lower() == 'q':
            print("Cancelled.")
            return
        
        # Extract using keyboard
        results = keyboard_nav.extract_database_pages_keyboard(
            limit=limit,
            tabs_to_first_row=tabs_to_first,
            extractor=extractor
        )
        
        # Save results
        json_writer = JSONWriter(output_dir) if output in ['json', 'both'] else None
        csv_writer = CSVWriter(output_dir) if output in ['csv', 'both'] else None
        
        total_blocks = 0
        for result in results:
            total_blocks += len(result.blocks)
            
            if json_writer:
                json_path = json_writer.write_extraction(result)
                logger.info(f"Saved: {json_path}")
            
            if csv_writer:
                csv_path = csv_writer.write_extraction(result)
                logger.info(f"Saved: {csv_path}")
        
        # Summary
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"Pages extracted: {len(results)}/{limit}")
        print(f"Total blocks: {total_blocks}")
        print(f"Output directory: {output_dir}")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.argument('recipe_name', required=False)
@click.option('--fuzzy-threshold', default=0.75, type=float,
              help='Fuzzy matching threshold (0.0-1.0, default: 0.75)')
@click.pass_context
def test_ocr_click(ctx, recipe_name, fuzzy_threshold):
    """Test OCR-based clicking - screenshot database, find recipe names, click them.
    
    This uses OCR to find text on screen and click it!
    Uses fuzzy matching to handle OCR errors and typos.
    
    Examples:
        python -m src.cli test-ocr-click
        python -m src.cli test-ocr-click "Topinambours"
        python -m src.cli test-ocr-click "Aheebakjan" --fuzzy-threshold 0.70
    """
    logger = ctx.obj['logger']
    
    try:
        # Initialize
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        ocr_nav = OCRNavigator(detector)
        navigator = NotionNavigator(detector)
        
        if not detector.ensure_notion_active():
            logger.error("Notion not found")
            return
        
        database_title = detector.get_page_title()
        
        print("\n" + "="*70)
        print("OCR-BASED CLICKING TEST")
        print("="*70)
        print(f"Database: {database_title}\n")
        
        if recipe_name:
            # Search for specific recipe
            print(f"🔍 Looking for: {recipe_name}\n")
            success = ocr_nav.find_and_click_text(
                recipe_name, 
                delay=1.5,
                fuzzy=True,
                fuzzy_threshold=fuzzy_threshold
            )
            
            if success:
                # Wait a bit for the page to fully expand
                print("\n⏳ Waiting for page to fully load...")
                time.sleep(2.0)
                
                new_title = detector.get_page_title()
                print(f"📄 Current page title: {new_title}")
                
                if new_title != database_title:
                    print(f"🎉 SUCCESS! Page opened and expanded!")
                    print(f"   Database: {database_title}")
                    print(f"   Recipe: {new_title}")
                    
                    # Show that we can now extract content
                    print("\n✅ Page is ready for content extraction")
                    
                    # Go back
                    print("\n🔙 Going back to database...")
                    navigator.navigate_back(wait_for_load=True)
                else:
                    print(f"\n⚠️  Page title unchanged (still: {database_title})")
                    print("   This might be expected for side panel views.")
                    print("   The page should still be accessible for extraction.")
            else:
                print("\n❌ Click failed")
            
            return
        
        # Scan for all recipes
        recipes = ocr_nav.scan_database_rows()
        
        if not recipes:
            print("❌ No recipes found via OCR")
            print("\nTroubleshooting:")
            print("  - Make sure database is visible")
            print("  - Try scrolling to load more rows")
            print("  - Check if recipes have text (not just icons)")
            return
        
        print(f"\n✅ Found {len(recipes)} potential recipes:\n")
        
        for i, recipe in enumerate(recipes[:15]):
            print(f"{i+1}. {recipe['text'][:60]}")
            print(f"   Position: ({recipe['x']}, {recipe['y']})")
            print(f"   Confidence: {recipe['confidence']:.2f}")
        
        if len(recipes) > 15:
            print(f"\n... and {len(recipes) - 15} more")
        
        # Ask which to click
        print("\n" + "="*70)
        choice = input(f"Enter number to click (1-{min(5, len(recipes))}) or 'q': ")
        
        if choice.lower() == 'q':
            print("Cancelled.")
            return
        
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(recipes):
                print("Invalid choice")
                return
            
            recipe = recipes[idx]
            
            # Click on center
            click_x = int(recipe['x'] + recipe['width'] / 2)
            click_y = int(recipe['y'] + recipe['height'] / 2)
            
            print(f"\n🖱️  Clicking: {recipe['text']}")
            print(f"   Position: ({click_x}, {click_y})")
            
            time.sleep(1)  # Give user time to see
            
            success = ocr_nav.click_at_position(click_x, click_y, delay=1.5)
            
            if success:
                new_title = detector.get_page_title()
                if new_title != database_title:
                    print(f"\n🎉 SUCCESS! Opened: {new_title}")
                    
                    # Go back
                    print("\n🔙 Going back...")
                    navigator.navigate_back(wait_for_load=True)
                else:
                    print("\n⚠️  Clicked but page didn't change")
                    print("   (Maybe need to adjust click position?)")
        
        except ValueError:
            print("Invalid input")
            return
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.argument('recipe_name')
@click.option('--output', type=click.Choice(['json', 'csv', 'both']), default='json',
              help='Output format')
@click.option('--no-ocr', is_flag=True, help='Disable OCR fallback for extraction')
@click.option('--go-back', is_flag=True, help='Navigate back to database after extraction')
@click.option('--fuzzy-threshold', default=0.75, type=float,
              help='Fuzzy matching threshold for finding recipes (0.0-1.0, default: 0.75)')
@click.pass_context
def extract_with_ocr_nav(ctx, recipe_name, output, no_ocr, go_back, fuzzy_threshold):
    """Extract recipe content using OCR navigation.
    
    This command uses OCR to find and click on a recipe in the database,
    then extracts all its content. No API token needed!
    
    Fuzzy matching helps handle OCR errors and typos in recipe names.
    Lower threshold = more lenient matching.
    
    Examples:
        python -m src.cli extract-with-ocr-nav "Topinambours au vinaigre"
        python -m src.cli extract-with-ocr-nav "Thai omelet" --output both
        python -m src.cli extract-with-ocr-nav "Aheebakjan" --fuzzy-threshold 0.70
    """
    logger = ctx.obj['logger']
    output_dir = ctx.obj['output_dir']
    
    try:
        print("\n" + "="*70)
        print("OCR-BASED RECIPE EXTRACTION")
        print("="*70)
        print(f"Recipe: {recipe_name}")
        print(f"Output: {output}")
        print("="*70 + "\n")
        
        # Initialize components
        ax_client = AXClient()
        detector = NotionDetector(ax_client)
        ocr_nav = OCRNavigator(detector)
        navigator = NotionNavigator(detector)
        extractor = NotionExtractor(detector)
        
        # Setup OCR for extraction if enabled
        if not no_ocr:
            ocr_handler = OCRHandler()
            if ocr_handler.is_available():
                extractor.set_ocr_handler(ocr_handler)
                logger.info(f"OCR enabled for extraction: {ocr_handler.get_active_handler()}")
        
        # Activate Notion
        if not detector.ensure_notion_active():
            logger.error("Notion not found")
            return
        
        database_title = detector.get_page_title()
        logger.info(f"Starting from database: {database_title}")
        
        # Use OCR to navigate to the recipe
        print(f"🔍 Navigating to recipe using OCR...")
        success = ocr_nav.find_and_click_text(
            recipe_name, 
            delay=1.5,
            fuzzy=True,
            fuzzy_threshold=fuzzy_threshold
        )
        
        if not success:
            logger.error(f"Failed to navigate to recipe: {recipe_name}")
            print("\n❌ Could not find or click on the recipe")
            return
        
        # Wait for page to load and stabilize
        print("⏳ Waiting for page to load...")
        time.sleep(2.0)
        detector.wait_for_page_load()
        
        current_title = detector.get_page_title()
        logger.info(f"Current page: {current_title}")
        
        print(f"📄 Now on page: {current_title}")
        
        # Extract content
        print(f"\n📝 Extracting content...")
        start_time = time.time()
        logger.log_extraction_start(recipe_name)
        
        result = extractor.extract_page(use_ocr=not no_ocr)
        
        duration = time.time() - start_time
        logger.log_extraction_complete(recipe_name, len(result.blocks), duration)
        
        print(f"✅ Extracted {len(result.blocks)} blocks in {duration:.1f}s")
        
        # Write output
        if output in ['json', 'both']:
            json_writer = JSONWriter(output_dir)
            json_path = json_writer.write_extraction(result)
            logger.info(f"JSON written to: {json_path}")
            print(f"💾 JSON: {json_path}")
        
        if output in ['csv', 'both']:
            csv_writer = CSVWriter(output_dir)
            csv_path = csv_writer.write_extraction(result)
            logger.info(f"CSV written to: {csv_path}")
            print(f"💾 CSV: {csv_path}")
        
        # Go back to database if requested
        if go_back:
            print(f"\n🔙 Navigating back to database...")
            navigator.navigate_back(wait_for_load=True)
            print(f"✅ Back to: {detector.get_page_title()}")
        
        print("\n" + "="*70)
        print("EXTRACTION COMPLETE")
        print("="*70)
        print(f"Recipe: {recipe_name}")
        print(f"Blocks extracted: {len(result.blocks)}")
        print(f"Duration: {duration:.1f}s")
        print(f"Output directory: {output_dir}")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()


@cli.command()
@click.pass_context
def list_apps(ctx):
    """List all running applications to help identify Notion."""
    import sys
    
    try:
        ax_client = AXClient(check_permissions=False)
        apps = ax_client.get_running_applications()
        
        print("\n" + "="*70)
        print("RUNNING APPLICATIONS")
        print("="*70 + "\n")
        
        # Filter for relevant apps (not system background processes)
        visible_apps = [
            app for app in apps 
            if app['name'] and not app['name'].startswith('com.apple')
        ]
        
        # Sort by name
        visible_apps.sort(key=lambda x: x['name'].lower())
        
        print(f"Found {len(visible_apps)} applications:\n")
        
        notion_found = False
        for i, app in enumerate(visible_apps, 1):
            line = f"{i:3d}. {app['name']:<30}"
            if app['bundle_id']:
                line += f" (bundle: {app['bundle_id']})"
            line += f" [PID: {app['pid']}]"
            
            # Highlight if it might be Notion
            if 'notion' in app['name'].lower() or (app['bundle_id'] and 'notion' in app['bundle_id'].lower()):
                line += " ← 🎯 NOTION"
                notion_found = True
            
            print(line)
        
        print("\n" + "="*70)
        
        if notion_found:
            print("\n✅ Notion appears to be running!")
        else:
            print("\n⚠️  Notion not found. Make sure Notion is running and try again.")
            print("   If Notion is running, check the list above for similar names.")
        
        print()
        
    except Exception as e:
        print(f"Error listing apps: {e}")
        if ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()


@cli.command()
@click.pass_context
def check_permissions(ctx):
    """Check if accessibility permissions are properly configured."""
    import sys
    
    print("\n" + "="*70)
    print("ACCESSIBILITY PERMISSIONS CHECK")
    print("="*70 + "\n")
    
    # Check if process is trusted
    trusted = AXClient.is_trusted()
    
    print(f"Python executable: {sys.executable}")
    print(f"Process trusted: {trusted}\n")
    
    if trusted:
        print("✅ SUCCESS! Accessibility permissions are granted.\n")
        print("You should be able to run extraction commands now.\n")
        
        # Try to find Notion
        try:
            ax_client = AXClient(check_permissions=False)
            detector = NotionDetector(ax_client)
            
            pid = ax_client.find_application(name="Notion")
            if pid:
                print(f"✅ Notion app found (PID: {pid})\n")
            else:
                print("⚠️  Notion app not found. Make sure Notion is running.\n")
        except Exception as e:
            print(f"⚠️  Error checking Notion: {e}\n")
    else:
        print("❌ FAILED: Accessibility permissions are NOT granted.\n")
        print("To fix this:\n")
        print("1. Open: System Settings > Privacy & Security > Accessibility")
        print("2. Click the lock icon to make changes")
        print("3. Look for one of these apps:")
        print(f"   - Your terminal app (Cursor, Terminal, Warp, etc.)")
        print(f"   - Python: {sys.executable}")
        print("4. Check the box next to it to enable")
        print("5. If not listed, click '+' and add it")
        print("6. IMPORTANT: Close and restart your terminal completely")
        print("7. Run this command again to verify\n")
        
        # Offer to request permissions
        print("Attempting to trigger permissions prompt...")
        AXClient.request_permissions()
        print("A system dialog should appear. Click 'Open System Settings'")
        print("and follow the steps above.\n")
    
    print("="*70 + "\n")


def main():
    """Entry point for the CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()

