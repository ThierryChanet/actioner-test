"""Database extraction using vision/AI to identify rows."""

import time
import json
from typing import List, Optional, Dict, Any
from openai import OpenAI


class VisionDatabaseExtractor:
    """Extracts database using vision AI to identify clickable rows."""
    
    def __init__(self, responses_client, detector, extractor, logger):
        """Initialize the vision database extractor.
        
        Args:
            responses_client: ResponsesAPIClient for taking screenshots and mouse control
            detector: NotionDetector instance
            extractor: NotionExtractor for page content extraction
            logger: Logger instance
        """
        self.responses_client = responses_client
        self.detector = detector
        self.extractor = extractor
        self.logger = logger
        self.client = OpenAI()
    
    def extract_database_pages(self, limit: int = 10) -> List:
        """Extract database pages using vision.
        
        Args:
            limit: Maximum number of pages to extract
            
        Returns:
            List of ExtractionResult objects
        """
        self.logger.info("🔍 Using vision to identify database rows...")
        
        # Take screenshot
        try:
            screenshot_b64 = self.responses_client.take_screenshot(use_cache=False)
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return []
        
        # Ask vision LLM to identify rows
        rows = self._identify_database_rows(screenshot_b64)
        
        if not rows:
            self.logger.warning("Vision: No rows identified in the screenshot")
            return []
        
        self.logger.info(f"Vision: Found {len(rows)} potential database rows")
        
        # Click and extract each row
        results = []
        for i, row in enumerate(rows[:limit]):
            title = row.get('title', 'Unknown')
            confidence = row.get('confidence', 'unknown')
            
            self.logger.info(f"Processing row {i+1}/{min(len(rows), limit)}: {title} (confidence: {confidence})")
            
            try:
                # Click on row
                coord = (row['x'], row['y'])
                self.responses_client.execute_action("left_click", coordinate=coord)
                time.sleep(1.5)  # Wait for page load
                
                # Extract content
                result = self.extractor.extract_page(use_ocr=True)
                
                # Set title if not detected
                if not result.title or result.title == "Unknown":
                    result.title = title
                
                result.metadata['source'] = 'vision_navigation'
                result.metadata['vision_confidence'] = confidence
                results.append(result)
                
                self.logger.info(f"  ✅ Extracted: {result.title} ({len(result.blocks)} blocks)")
                
                # Navigate back using keyboard
                self.responses_client.execute_action("key", text="escape")
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"  ❌ Failed to extract row '{title}': {e}")
                continue
        
        return results
    
    def _identify_database_rows(self, screenshot_b64: str) -> List[Dict[str, Any]]:
        """Use vision LLM to identify clickable database rows.
        
        Args:
            screenshot_b64: Base64-encoded screenshot
            
        Returns:
            List of dictionaries with row information
        """
        prompt = """You are viewing a Notion database. Identify all the database entry rows that are visible.

For each row, provide:
1. The title/name of the entry
2. The approximate X,Y pixel coordinates where I should click to open it (center of the clickable area)
3. Confidence level (high/medium/low)

Return ONLY a valid JSON array, no markdown formatting:
[
  {"title": "Entry Name", "x": 400, "y": 250, "confidence": "high"},
  ...
]

Important:
- Only include actual database entries, not navigation buttons, sidebars, or headers
- Focus on the main content area with the database entries
- Provide accurate click coordinates (not top-left corner, but center of clickable area)
- If you see table rows, board cards, or gallery items, those are database entries"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/png;base64,{screenshot_b64}",
                            "detail": "high"
                        }}
                    ]
                }],
                max_tokens=2000,
                temperature=0
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            rows = json.loads(content.strip())
            
            # Validate structure
            if not isinstance(rows, list):
                self.logger.warning("Vision response is not a list")
                return []
            
            # Filter and validate each row
            valid_rows = []
            for row in rows:
                if all(key in row for key in ['title', 'x', 'y']):
                    valid_rows.append(row)
                else:
                    self.logger.warning(f"Invalid row structure: {row}")
            
            return valid_rows
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse vision response as JSON: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Vision identification failed: {e}")
            return []

