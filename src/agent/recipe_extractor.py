#!/usr/bin/env python3
"""Recipe extraction tool using Computer Vision.

This module provides a reliable workflow for extracting recipe data from Notion
using Claude Vision with proper coordinate scaling.

Workflow:
1. Use Computer Vision to scan and identify recipes
2. Hover over a recipe row, wait for OPEN button to appear
3. Click the OPEN button (if not found, press Escape and retry)
4. Extract ingredients from the side panel using Vision
5. Press Escape to close panel, verify with Vision
6. Repeat for next recipe
"""

import time
import json
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result from extracting a single recipe."""
    recipe_name: str
    ingredients: List[str]
    success: bool
    error: Optional[str] = None


class NotionRecipeExtractor:
    """Extract recipes from Notion using Computer Vision workflow.

    This class implements a robust workflow that:
    - Uses CV to identify targets before clicking
    - Hovers to reveal OPEN buttons
    - Verifies actions completed using CV
    - Handles failures gracefully with retries
    """

    def __init__(self, client, verbose: bool = True):
        """Initialize the extractor.

        Args:
            client: AnthropicComputerClient instance
            verbose: Print progress messages
        """
        self.client = client
        self.verbose = verbose
        self._last_screenshot: Optional[str] = None

    def log(self, message: str):
        """Print a log message if verbose mode is enabled."""
        if self.verbose:
            print(message)

    def _take_screenshot(self) -> str:
        """Take a fresh screenshot and store it."""
        self._last_screenshot = self.client.take_screenshot(use_cache=False)
        return self._last_screenshot

    def _ask_vision(self, screenshot: str, prompt: str, max_tokens: int = 500) -> str:
        """Ask Claude Vision a question about a screenshot."""
        response = self.client.client.messages.create(
            model=self.client.model,
            max_tokens=max_tokens,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": screenshot
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }],
            temperature=0
        )
        return response.content[0].text.strip()

    def _scale_and_click(self, claude_x: int, claude_y: int) -> bool:
        """Scale Claude Vision coordinates and execute a click.

        Args:
            claude_x, claude_y: Coordinates in Claude Vision space

        Returns:
            True if click was executed successfully
        """
        # Scale from Claude Vision space to screenshot space
        screenshot_x, screenshot_y = self.client._scale_claude_vision_coordinates(claude_x, claude_y)

        # Scale from screenshot space to logical space for clicking
        click_x, click_y = self.client._scale_coordinates_for_click(screenshot_x, screenshot_y)

        self.log(f"    Coords: Claude({claude_x},{claude_y}) -> Screenshot({screenshot_x},{screenshot_y}) -> Click({click_x},{click_y})")

        # Execute the click
        self.client._execute_click(click_x, click_y)
        return True

    def _scale_and_move(self, claude_x: int, claude_y: int) -> bool:
        """Scale Claude Vision coordinates and move mouse (hover).

        Args:
            claude_x, claude_y: Coordinates in Claude Vision space

        Returns:
            True if move was executed successfully
        """
        # Scale from Claude Vision space to screenshot space
        screenshot_x, screenshot_y = self.client._scale_claude_vision_coordinates(claude_x, claude_y)

        # Scale from screenshot space to logical space
        move_x, move_y = self.client._scale_coordinates_for_click(screenshot_x, screenshot_y)

        self.log(f"    Coords: Claude({claude_x},{claude_y}) -> Screenshot({screenshot_x},{screenshot_y}) -> Move({move_x},{move_y})")

        # Execute the move
        self.client._execute_mouse_move(move_x, move_y)
        return True

    def _press_escape(self):
        """Press the Escape key."""
        self.client.execute_action("key", text="Escape")
        time.sleep(0.5)

    # =========================================================================
    # STEP 1: Scan screen for recipe names
    # =========================================================================

    def scan_recipes(self, count: int = 5) -> List[str]:
        """Scan the screen and identify recipe names.

        Args:
            count: Maximum number of recipes to find

        Returns:
            List of recipe names visible on screen
        """
        self.log(f"\n[STEP 1] Scanning for {count} recipes...")

        screenshot = self._take_screenshot()

        prompt = f"""Look at this Notion screenshot showing a recipe database.

List the FIRST {count} recipe names you can see in the table/list, in order from top to bottom.

Return ONLY a JSON array of recipe names, nothing else:
["Recipe 1", "Recipe 2", "Recipe 3", ...]

If you see fewer than {count} recipes, return all that you can see."""

        response = self._ask_vision(screenshot, prompt)
        self.log(f"  Response: {response[:100]}...")

        # Parse JSON array
        try:
            if response.startswith('['):
                recipes = json.loads(response)
            else:
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    recipes = json.loads(json_match.group(0))
                else:
                    self.log("  ERROR: Could not parse recipe list")
                    return []

            recipes = recipes[:count]
            self.log(f"  Found {len(recipes)} recipes: {recipes}")
            return recipes

        except json.JSONDecodeError as e:
            self.log(f"  ERROR: JSON parse failed: {e}")
            return []

    # =========================================================================
    # STEP 2: Hover over recipe to reveal OPEN button
    # =========================================================================

    def _find_recipe_coordinates(self, recipe_name: str) -> Optional[tuple]:
        """Find the coordinates of a recipe name on screen.

        Returns:
            (claude_x, claude_y) or None if not found
        """
        screenshot = self._take_screenshot()

        prompt = f"""Find "{recipe_name}" in this Notion screenshot.

Return ONLY the coordinates of the CENTER of the recipe name text:
COORDINATES: (x, y)

If not found, return: NOT_FOUND"""

        response = self._ask_vision(screenshot, prompt, max_tokens=100)

        if "NOT_FOUND" in response:
            return None

        match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        return None

    def hover_recipe(self, recipe_name: str) -> bool:
        """Hover over a recipe row to reveal the OPEN button.

        Args:
            recipe_name: Name of the recipe to hover over

        Returns:
            True if hover was successful
        """
        self.log(f"\n[STEP 2] Hovering over '{recipe_name}'...")

        coords = self._find_recipe_coordinates(recipe_name)
        if not coords:
            self.log(f"  ERROR: Could not find '{recipe_name}' on screen")
            return False

        self.log(f"  Found at Claude coords: {coords}")
        self._scale_and_move(coords[0], coords[1])

        # Wait for OPEN button to appear
        time.sleep(0.5)
        self.log("  Waiting for OPEN button...")

        return True

    # =========================================================================
    # STEP 3: Find and click OPEN button
    # =========================================================================

    def _find_open_button(self, recipe_name: str) -> Optional[tuple]:
        """Find the OPEN button that appeared after hovering.

        Returns:
            (claude_x, claude_y) or None if not found
        """
        screenshot = self._take_screenshot()

        prompt = f"""Look at this Notion screenshot. I just hovered over "{recipe_name}".

Find the "OPEN" button that should have appeared on the same row.
The OPEN button is typically:
- A small button with text "OPEN"
- On the same horizontal line as the recipe name
- Usually appears to the LEFT of the recipe name when hovering

Return the CENTER coordinates of the OPEN button:
COORDINATES: (x, y)

If you cannot find an OPEN button, return: NOT_FOUND"""

        response = self._ask_vision(screenshot, prompt, max_tokens=100)

        if "NOT_FOUND" in response:
            return None

        match = re.search(r'COORDINATES:\s*\((\d+),\s*(\d+)\)', response)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        return None

    def click_open_button(self, recipe_name: str, max_retries: int = 2) -> bool:
        """Find and click the OPEN button for a recipe.

        Args:
            recipe_name: Name of the recipe (for context)
            max_retries: Number of times to retry if button not found

        Returns:
            True if OPEN button was clicked successfully
        """
        self.log(f"\n[STEP 3] Clicking OPEN button...")

        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"  Retry {attempt + 1}/{max_retries}...")
                # Press Escape and re-hover
                self._press_escape()
                time.sleep(0.5)
                if not self.hover_recipe(recipe_name):
                    continue

            coords = self._find_open_button(recipe_name)
            if coords:
                self.log(f"  Found OPEN button at Claude coords: {coords}")
                self._scale_and_click(coords[0], coords[1])
                time.sleep(1.5)  # Wait for side panel to open
                return True
            else:
                self.log(f"  OPEN button not found")

        self.log(f"  ERROR: Could not find OPEN button after {max_retries} attempts")
        return False

    # =========================================================================
    # STEP 4: Extract ingredients from side panel
    # =========================================================================

    def extract_ingredients(self, recipe_name: str) -> List[str]:
        """Extract ingredients from the currently open side panel.

        Args:
            recipe_name: Name of the recipe (for context)

        Returns:
            List of ingredient strings
        """
        self.log(f"\n[STEP 4] Extracting ingredients from side panel...")

        screenshot = self._take_screenshot()

        prompt = f"""Look at this Notion screenshot showing recipe "{recipe_name}" in a side panel.

The side panel is on the RIGHT side of the screen.

Extract ALL ingredients from the recipe. Look for:
- A section titled "Ingredients" or similar
- A bulleted or numbered list of ingredients
- Items that look like food ingredients with quantities

Return as JSON:
{{"ingredients": ["ingredient 1", "ingredient 2", ...]}}

If no ingredients found, return:
{{"ingredients": []}}"""

        response = self._ask_vision(screenshot, prompt, max_tokens=1000)
        self.log(f"  Response: {response[:150]}...")

        # Parse JSON
        try:
            # Extract JSON from response
            json_text = response
            if '```json' in response:
                json_text = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_text = response.split('```')[1].split('```')[0].strip()
            else:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)

            data = json.loads(json_text)
            ingredients = data.get('ingredients', [])
            self.log(f"  Extracted {len(ingredients)} ingredients")
            return ingredients

        except json.JSONDecodeError as e:
            self.log(f"  ERROR: JSON parse failed: {e}")
            return []

    # =========================================================================
    # STEP 5: Close side panel and verify
    # =========================================================================

    def close_panel(self, max_retries: int = 3) -> bool:
        """Close the side panel and verify it closed.

        Args:
            max_retries: Number of times to retry closing

        Returns:
            True if panel was closed successfully
        """
        self.log(f"\n[STEP 5] Closing side panel...")

        # Take screenshot before closing for comparison
        before_screenshot = self._take_screenshot()

        for attempt in range(max_retries):
            if attempt > 0:
                self.log(f"  Retry {attempt + 1}/{max_retries}...")

            # Press Escape
            self._press_escape()
            time.sleep(0.5)

            # Take screenshot after and verify
            after_screenshot = self._take_screenshot()

            prompt = """Compare the current view to determine if the side panel is closed.

Look at the RIGHT side of the screen:
- If there's a recipe detail panel open on the right: respond PANEL_OPEN
- If the database/table view fills the full width: respond PANEL_CLOSED

Respond with ONLY one of: PANEL_OPEN or PANEL_CLOSED"""

            response = self._ask_vision(after_screenshot, prompt, max_tokens=50)

            if "PANEL_CLOSED" in response:
                self.log("  Panel closed successfully")
                return True
            else:
                self.log(f"  Panel still open (response: {response})")

        self.log(f"  ERROR: Could not close panel after {max_retries} attempts")
        return False

    # =========================================================================
    # MAIN EXTRACTION WORKFLOW
    # =========================================================================

    def extract_recipe(self, recipe_name: str) -> ExtractionResult:
        """Extract ingredients from a single recipe.

        This executes the full workflow:
        1. Hover over recipe
        2. Click OPEN button
        3. Extract ingredients
        4. Close panel

        Args:
            recipe_name: Name of the recipe to extract

        Returns:
            ExtractionResult with ingredients or error
        """
        self.log(f"\n{'='*60}")
        self.log(f"EXTRACTING: {recipe_name}")
        self.log('='*60)

        # Step 2: Hover over recipe
        if not self.hover_recipe(recipe_name):
            return ExtractionResult(
                recipe_name=recipe_name,
                ingredients=[],
                success=False,
                error="Could not find recipe on screen"
            )

        # Step 3: Click OPEN button
        if not self.click_open_button(recipe_name):
            self._press_escape()  # Clean up
            return ExtractionResult(
                recipe_name=recipe_name,
                ingredients=[],
                success=False,
                error="Could not click OPEN button"
            )

        # Step 4: Extract ingredients
        ingredients = self.extract_ingredients(recipe_name)

        # Step 5: Close panel
        panel_closed = self.close_panel()
        if not panel_closed:
            return ExtractionResult(
                recipe_name=recipe_name,
                ingredients=ingredients,
                success=False,
                error="Could not close panel - manual intervention needed"
            )

        return ExtractionResult(
            recipe_name=recipe_name,
            ingredients=ingredients,
            success=True
        )

    def extract_multiple(self, recipe_names: List[str]) -> List[ExtractionResult]:
        """Extract ingredients from multiple recipes.

        Args:
            recipe_names: List of recipe names to extract

        Returns:
            List of ExtractionResult objects
        """
        results = []

        for idx, recipe_name in enumerate(recipe_names, 1):
            self.log(f"\n[{idx}/{len(recipe_names)}] Processing: {recipe_name}")

            result = self.extract_recipe(recipe_name)
            results.append(result)

            # If panel couldn't close, stop and ask for help
            if not result.success and "panel" in (result.error or "").lower():
                self.log(f"\n⚠️  STOPPING: Panel issue detected. Please check the screen.")
                break

            # Small delay between recipes
            time.sleep(0.5)

        return results


def main():
    """Run the recipe extraction workflow."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    from dotenv import load_dotenv
    load_dotenv()

    from src.agent.anthropic_computer_client import AnthropicComputerClient

    # Initialize
    print("Initializing...")
    client = AnthropicComputerClient(verbose=True)
    extractor = NotionRecipeExtractor(client, verbose=True)

    # Calibrate Claude Vision dimensions
    print("\nCalibrating Claude Vision dimensions...")
    screenshot = client.take_screenshot(use_cache=False)
    client._detect_claude_vision_dimensions(screenshot)

    # Switch to Notion
    print("\nSwitching to Notion...")
    client.execute_action("switch_desktop", text="Notion")
    time.sleep(2)

    # Step 1: Scan for recipes
    recipes = extractor.scan_recipes(count=5)
    if not recipes:
        print("ERROR: No recipes found")
        client.execute_action("switch_desktop", text="iTerm")
        return

    # Extract from each recipe
    results = extractor.extract_multiple(recipes)

    # Switch back to iTerm
    print("\n\nSwitching back to iTerm...")
    client.execute_action("switch_desktop", text="iTerm")
    time.sleep(0.5)

    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION RESULTS")
    print("="*60)

    success_count = 0
    for result in results:
        status = "✓" if result.success else "✗"
        print(f"\n{status} {result.recipe_name}:")
        if result.ingredients:
            for ing in result.ingredients:
                print(f"    • {ing}")
        elif result.error:
            print(f"    ERROR: {result.error}")
        else:
            print(f"    (no ingredients found)")

        if result.success:
            success_count += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY: {success_count}/{len(results)} recipes extracted successfully")
    print("="*60)


if __name__ == "__main__":
    main()
