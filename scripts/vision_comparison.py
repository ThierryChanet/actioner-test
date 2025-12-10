#!/usr/bin/env python3
"""
Vision API Comparison Test

Compares OpenAI GPT-4o Vision vs Anthropic Claude Computer Use
for screenshot analysis and UI element detection.
"""

import os
import base64
import time
import json
from typing import Dict, Any, Tuple
import Quartz
import Cocoa


def take_screenshot() -> str:
    """Capture current screen and return as base64 PNG."""
    # Get main display
    display_id = Quartz.CGMainDisplayID()

    # Capture screenshot
    image = Quartz.CGDisplayCreateImage(display_id)
    if not image:
        raise Exception("Failed to capture screenshot")

    # Convert to NSImage
    width = Quartz.CGImageGetWidth(image)
    height = Quartz.CGImageGetHeight(image)
    ns_image = Cocoa.NSImage.alloc().initWithCGImage_size_(
        image,
        Cocoa.NSMakeSize(width, height)
    )

    # Convert to PNG data
    tiff_data = ns_image.TIFFRepresentation()
    bitmap = Cocoa.NSBitmapImageRep.imageRepWithData_(tiff_data)
    png_data = bitmap.representationUsingType_properties_(
        Cocoa.NSBitmapImageFileTypePNG,
        None
    )

    # Encode as base64
    return base64.b64encode(bytes(png_data)).decode('utf-8')


def test_openai_vision(screenshot_b64: str) -> Tuple[Dict[str, Any], float]:
    """Test OpenAI GPT-4o vision analysis."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OPENAI_API_KEY not set"}, 0

    client = OpenAI(api_key=api_key)

    start_time = time.time()

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot in detail. "
                                "List ALL visible UI elements with their approximate positions. "
                                "Include: application name, buttons, menus, sidebars, text content, "
                                "clickable items. "
                                "For each element, specify its location (top/bottom/left/right/center) "
                                "and estimate pixel coordinates if possible. "
                                "Be extremely detailed and precise."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}",
                                "detail": "high"  # High detail for better analysis
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,  # Allow detailed response
            temperature=0
        )

        duration = time.time() - start_time

        return {
            "provider": "OpenAI GPT-4o",
            "model": "gpt-4o",
            "response": response.choices[0].message.content,
            "tokens_used": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }, duration

    except Exception as e:
        duration = time.time() - start_time
        return {"error": str(e)}, duration


def test_anthropic_computer_use(screenshot_b64: str) -> Tuple[Dict[str, Any], float]:
    """Test Anthropic Claude Computer Use vision analysis."""
    try:
        from anthropic import Anthropic
    except ImportError:
        return {
            "error": "Anthropic package not installed",
            "note": "Install with: pip install anthropic"
        }, 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}, 0

    client = Anthropic(api_key=api_key)

    start_time = time.time()

    try:
        # Anthropic Computer Use requires specific message format
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # Latest model with computer use
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot in detail. "
                                "List ALL visible UI elements with their approximate positions. "
                                "Include: application name, buttons, menus, sidebars, text content, "
                                "clickable items. "
                                "For each element, specify its location (top/bottom/left/right/center) "
                                "and estimate pixel coordinates if possible. "
                                "Be extremely detailed and precise."
                            )
                        }
                    ]
                }
            ]
        )

        duration = time.time() - start_time

        # Extract text from response
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        return {
            "provider": "Anthropic Claude",
            "model": "claude-3-5-sonnet-20241022",
            "response": text_content,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens
        }, duration

    except Exception as e:
        duration = time.time() - start_time
        return {"error": str(e)}, duration


def compare_ui_element_detection(openai_result: Dict, anthropic_result: Dict) -> Dict[str, Any]:
    """Compare how well each API detected specific UI elements."""

    # Test elements to look for (customize based on what's on your screen)
    test_elements = [
        "sidebar",
        "recipe",
        "database",
        "tab",
        "close button",
        "menu",
        "scroll",
        "search",
        "ingredients"
    ]

    comparison = {
        "test_elements": test_elements,
        "openai_detected": {},
        "anthropic_detected": {}
    }

    # Check OpenAI
    openai_text = openai_result.get("response", "").lower()
    for element in test_elements:
        comparison["openai_detected"][element] = element in openai_text

    # Check Anthropic
    anthropic_text = anthropic_result.get("response", "").lower()
    for element in test_elements:
        comparison["anthropic_detected"][element] = element in anthropic_text

    # Calculate detection rates
    openai_count = sum(comparison["openai_detected"].values())
    anthropic_count = sum(comparison["anthropic_detected"].values())

    comparison["openai_detection_rate"] = f"{openai_count}/{len(test_elements)}"
    comparison["anthropic_detection_rate"] = f"{anthropic_count}/{len(test_elements)}"

    return comparison


def main():
    """Run comparison test."""
    print("=" * 80)
    print("VISION API COMPARISON TEST")
    print("=" * 80)
    print()

    # Take screenshot
    print("📸 Capturing screenshot...")
    try:
        screenshot_b64 = take_screenshot()
        screenshot_size = len(screenshot_b64) / 1024  # KB
        print(f"✓ Screenshot captured ({screenshot_size:.1f} KB base64)")
    except Exception as e:
        print(f"✗ Failed to capture screenshot: {e}")
        return

    print()

    # Test OpenAI
    print("-" * 80)
    print("TESTING OPENAI GPT-4o VISION")
    print("-" * 80)
    openai_result, openai_duration = test_openai_vision(screenshot_b64)

    if "error" in openai_result:
        print(f"✗ Error: {openai_result['error']}")
    else:
        print(f"✓ Provider: {openai_result['provider']}")
        print(f"✓ Model: {openai_result['model']}")
        print(f"✓ Duration: {openai_duration:.2f}s")
        print(f"✓ Tokens: {openai_result['tokens_used']} ({openai_result['prompt_tokens']} prompt + {openai_result['completion_tokens']} completion)")
        print(f"\nResponse preview:")
        print(openai_result['response'][:500] + "..." if len(openai_result['response']) > 500 else openai_result['response'])

    print()

    # Test Anthropic
    print("-" * 80)
    print("TESTING ANTHROPIC CLAUDE COMPUTER USE")
    print("-" * 80)
    anthropic_result, anthropic_duration = test_anthropic_computer_use(screenshot_b64)

    if "error" in anthropic_result:
        print(f"✗ Error: {anthropic_result['error']}")
        if "note" in anthropic_result:
            print(f"  Note: {anthropic_result['note']}")
    else:
        print(f"✓ Provider: {anthropic_result['provider']}")
        print(f"✓ Model: {anthropic_result['model']}")
        print(f"✓ Duration: {anthropic_duration:.2f}s")
        print(f"✓ Tokens: {anthropic_result['tokens_used']} ({anthropic_result['input_tokens']} input + {anthropic_result['output_tokens']} output)")
        print(f"\nResponse preview:")
        print(anthropic_result['response'][:500] + "..." if len(anthropic_result['response']) > 500 else anthropic_result['response'])

    print()

    # Comparison
    if "error" not in openai_result and "error" not in anthropic_result:
        print("-" * 80)
        print("COMPARISON")
        print("-" * 80)

        comparison = compare_ui_element_detection(openai_result, anthropic_result)

        print("\nUI Element Detection:")
        print(f"  OpenAI:    {comparison['openai_detection_rate']}")
        print(f"  Anthropic: {comparison['anthropic_detection_rate']}")

        print("\nDetailed comparison:")
        for element in comparison['test_elements']:
            openai_found = "✓" if comparison['openai_detected'][element] else "✗"
            anthropic_found = "✓" if comparison['anthropic_detected'][element] else "✗"
            print(f"  {element:20} | OpenAI: {openai_found} | Anthropic: {anthropic_found}")

        print("\nPerformance:")
        print(f"  OpenAI:    {openai_duration:.2f}s")
        print(f"  Anthropic: {anthropic_duration:.2f}s")

        faster = "OpenAI" if openai_duration < anthropic_duration else "Anthropic"
        speedup = max(openai_duration, anthropic_duration) / min(openai_duration, anthropic_duration)
        print(f"  Winner:    {faster} ({speedup:.1f}x faster)")

        # Save full results
        results = {
            "timestamp": time.time(),
            "screenshot_size_kb": screenshot_size,
            "openai": openai_result,
            "openai_duration": openai_duration,
            "anthropic": anthropic_result,
            "anthropic_duration": anthropic_duration,
            "comparison": comparison
        }

        output_file = "vision_comparison_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Full results saved to {output_file}")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
