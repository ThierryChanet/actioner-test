# Notion macOS Direct-Action Extractor

A macOS tool that extracts text content from the Notion desktop app using **direct Accessibility (AX) actions** instead of simulated mouse or keyboard input. The extractor navigates between pages, captures all visible content, and uses OCR only as a fallback.

## Features

- Direct AX-based text extraction  
- Programmatic navigation between Notion pages  
- Deterministic scrolling and full-page traversal  
- OCR fallback for inaccessible elements  
- Notion API “gold standard” comparison for testing  
- Normal, dry-run, and debug modes

## Output

- JSON and CSV exports  
- Diff reports comparing AX/OCR output to API baseline  
- Optional debug visuals (bounding boxes, screenshots)

## Purpose

Provides a reliable, repeatable way to extract structured content from the Notion desktop app, with accuracy validated against the Notion API.

## Status

Work in progress. See the included PRD for project intent.

## License

MIT License
