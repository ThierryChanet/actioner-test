"""Command-line interface for Notion AX Extractor."""

import click
import time
import os
from pathlib import Path

from .ax.client import AXClient
from .notion.detector import NotionDetector
from .notion.navigator import NotionNavigator
from .notion.extractor import NotionExtractor
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
        print(f"   - Your Terminal app (Terminal, iTerm2, Warp, etc.)")
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

