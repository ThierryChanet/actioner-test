"""
Example: Hover Caching for Faster Database Navigation

This example demonstrates how caching hover button locations
speeds up repeated interactions with database rows.

Based on the successful hover → detect → click workflow from testing.
"""

import time
from typing import Dict, Any, Tuple


class HoverCache:
    """Cache for hover-sensitive UI elements and their button locations."""

    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}

    def get(self, element_name: str) -> Dict[str, Any] | None:
        """Get cached hover information."""
        if element_name not in self.cache:
            return None

        cached = self.cache[element_name]
        cache_age = time.time() - cached.get("last_successful", 0)

        # Cache expires after 5 minutes
        if cache_age > 300:
            return None

        return cached

    def set(
        self,
        element_name: str,
        element_coords: Tuple[int, int, int, int],
        open_button_coords: Tuple[int, int]
    ):
        """Cache hover button location."""
        self.cache[element_name] = {
            "element_coords": element_coords,
            "open_button_coords": open_button_coords,
            "last_successful": time.time(),
            "success_count": 1
        }

    def increment_success(self, element_name: str):
        """Increment success counter for cached element."""
        if element_name in self.cache:
            self.cache[element_name]["success_count"] += 1
            self.cache[element_name]["last_successful"] = time.time()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "total_cached": len(self.cache),
            "total_successes": sum(c.get("success_count", 0) for c in self.cache.values()),
            "cached_elements": list(self.cache.keys())
        }


def simulate_ocr_navigation(recipe_name: str, use_cache: bool = False) -> float:
    """Simulate OCR-based navigation with and without caching."""

    print(f"\n🔍 Navigating to: {recipe_name}")

    if use_cache:
        print("   💾 Checking cache...")
        time.sleep(0.05)  # Fast cache lookup
        print("   ✅ Found in cache!")
        print("   🖱️  Clicking cached OPEN button location...")
        time.sleep(0.1)  # Direct click
        total_time = 0.15
    else:
        print("   📸 Taking screenshot...")
        time.sleep(0.3)  # Screenshot time

        print("   🔍 Running OCR to find recipe...")
        time.sleep(0.5)  # OCR processing

        print("   ✅ Found recipe at (126, 401)")
        print("   🖱️  Hovering to reveal OPEN button...")
        time.sleep(0.5)  # Hover wait time

        print("   📸 Taking another screenshot...")
        time.sleep(0.3)  # Screenshot for OPEN button

        print("   🔍 Running OCR to find OPEN button...")
        time.sleep(0.5)  # OCR processing

        print("   ✅ Found OPEN button at (366, 400)")
        print("   🖱️  Clicking OPEN...")
        time.sleep(0.1)  # Click

        total_time = 2.2

    print(f"   ⏱️  Total time: {total_time:.2f}s")
    return total_time


def demo_without_caching():
    """Demonstrate repeated navigation without caching (slow)."""
    print("=" * 70)
    print("SCENARIO 1: Without Hover Caching (Current Implementation)")
    print("=" * 70)

    recipes = ["Velouté Potimarron", "Poulet rôti", "Ratatouille", "Velouté Potimarron"]

    total_time = 0
    for i, recipe in enumerate(recipes, 1):
        print(f"\n--- Navigation {i}/4 ---")
        nav_time = simulate_ocr_navigation(recipe, use_cache=False)
        total_time += nav_time

    print("\n" + "=" * 70)
    print(f"Total time: {total_time:.2f}s")
    print(f"Average per navigation: {total_time/len(recipes):.2f}s")
    print("=" * 70)


def demo_with_caching():
    """Demonstrate repeated navigation with caching (fast)."""
    print("\n\n" + "=" * 70)
    print("SCENARIO 2: With Hover Caching (Proposed Enhancement)")
    print("=" * 70)

    cache = HoverCache()
    recipes = ["Velouté Potimarron", "Poulet rôti", "Ratatouille", "Velouté Potimarron"]

    total_time = 0
    cache_hits = 0

    for i, recipe in enumerate(recipes, 1):
        print(f"\n--- Navigation {i}/4 ---")

        # Check cache
        cached = cache.get(recipe)

        if cached:
            # Use cached location (fast)
            nav_time = simulate_ocr_navigation(recipe, use_cache=True)
            cache.increment_success(recipe)
            cache_hits += 1
        else:
            # First time - do full OCR (slow)
            nav_time = simulate_ocr_navigation(recipe, use_cache=False)

            # Cache the result
            cache.set(
                recipe,
                element_coords=(126, 401, 100, 20),
                open_button_coords=(366, 400)
            )
            print(f"   💾 Cached hover location for future use")

        total_time += nav_time

    print("\n" + "=" * 70)
    print(f"Total time: {total_time:.2f}s")
    print(f"Average per navigation: {total_time/len(recipes):.2f}s")
    print(f"Cache hit rate: {cache_hits}/{len(recipes)} ({cache_hits/len(recipes)*100:.0f}%)")
    print("=" * 70)

    print("\n📊 Cache Statistics:")
    stats = cache.get_stats()
    print(f"   Cached elements: {stats['total_cached']}")
    print(f"   Total successful uses: {stats['total_successes']}")
    print(f"   Elements: {', '.join(stats['cached_elements'])}")


def show_comparison():
    """Show side-by-side comparison."""
    print("\n\n" + "=" * 70)
    print("PERFORMANCE COMPARISON")
    print("=" * 70)

    print("\nNavigating to 4 recipes (including 1 repeat):\n")

    print("Without caching:")
    print("   Recipe 1: 2.2s  (OCR + hover + OCR)")
    print("   Recipe 2: 2.2s  (OCR + hover + OCR)")
    print("   Recipe 3: 2.2s  (OCR + hover + OCR)")
    print("   Recipe 4: 2.2s  (OCR + hover + OCR) ← Repeat!")
    print("   -" * 35)
    print("   TOTAL: 8.8s")

    print("\nWith caching:")
    print("   Recipe 1: 2.2s  (OCR + hover + OCR) → Cache miss")
    print("   Recipe 2: 2.2s  (OCR + hover + OCR) → Cache miss")
    print("   Recipe 3: 2.2s  (OCR + hover + OCR) → Cache miss")
    print("   Recipe 4: 0.15s (Direct click!)     ← Cache hit! ✨")
    print("   -" * 35)
    print("   TOTAL: 6.75s")

    print("\n✅ Speed improvement: 23% faster")
    print("✅ For 10 recipes with 50% cache hits: ~50% faster")
    print("✅ For bulk extraction: Significant time savings")


def demonstrate_cache_invalidation():
    """Show how cache handles stale entries."""
    print("\n\n" + "=" * 70)
    print("SCENARIO 3: Cache Invalidation")
    print("=" * 70)

    cache = HoverCache()

    # Add entry
    print("\n1. Caching hover location for 'Poulet rôti'...")
    cache.set("Poulet rôti", (100, 200, 50, 20), (300, 200))
    print("   ✅ Cached")

    # Use it successfully
    print("\n2. Using cached location (3 seconds later)...")
    time.sleep(0.1)  # Simulate
    cached = cache.get("Poulet rôti")
    if cached:
        print(f"   ✅ Cache hit! Using location {cached['open_button_coords']}")

    # Simulate window resize or page change
    print("\n3. Simulating cache expiration (5 min later)...")
    cache.cache["Poulet rôti"]["last_successful"] = time.time() - 301  # Expired

    cached = cache.get("Poulet rôti")
    if not cached:
        print("   ⏰ Cache expired - will perform fresh OCR")
        print("   💡 This prevents using stale coordinates after UI changes")


if __name__ == "__main__":
    print("\n🚀 Hover Caching Performance Demo\n")

    # Show scenario without caching
    demo_without_caching()

    input("\nPress Enter to see WITH caching...\n")

    # Show scenario with caching
    demo_with_caching()

    input("\nPress Enter to see performance comparison...\n")

    # Show comparison
    show_comparison()

    input("\nPress Enter to see cache invalidation...\n")

    # Show cache invalidation
    demonstrate_cache_invalidation()

    print("\n\n" + "=" * 70)
    print("Key Benefits of Hover Caching:")
    print("=" * 70)
    print("""
1. ✅ Speed: 15x faster for cached items (0.15s vs 2.2s)
2. ✅ Reliability: Uses proven coordinates from previous success
3. ✅ Efficiency: Reduces OCR calls by ~50% for repeated items
4. ✅ Smart expiration: Cache expires after 5 min to handle UI changes
5. ✅ Success tracking: Records which locations work consistently

Perfect for:
- Database extraction with many similar items
- Repeatedly accessing the same recipes/pages
- Bulk operations where items are accessed multiple times
    """)

    print("\n💡 Implementation tip:")
    print("   Cache is shared across agent session, so benefits accumulate")
    print("   as the agent learns which elements are hover-sensitive.\n")
