#!/usr/bin/env python3
"""
COMPARISON TOOL: Compare Computer Use extraction vs API Gold Standard

Compares ingredients extracted via Computer Use against the Notion API gold standard.
"""

import json
import sys
from typing import Dict, List, Set
from difflib import SequenceMatcher


def load_gold_standard(filepath: str = 'gold_standard_recipes.json') -> Dict:
    """Load gold standard from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Gold standard file not found: {filepath}")
        print("\nRun gold_standard_extraction.py first to create it.")
        sys.exit(1)


def normalize_ingredient(text: str) -> str:
    """Normalize ingredient text for comparison."""
    # Lowercase and strip
    text = text.lower().strip()
    # Remove common punctuation
    text = text.replace('.', '').replace(',', '')
    return text


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """Check if two strings match with fuzzy matching."""
    normalized1 = normalize_ingredient(str1)
    normalized2 = normalize_ingredient(str2)

    # Exact match after normalization
    if normalized1 == normalized2:
        return True

    # Fuzzy match using SequenceMatcher
    ratio = SequenceMatcher(None, normalized1, normalized2).ratio()
    return ratio >= threshold


def find_matching_ingredient(
    ingredient: str,
    candidate_list: List[str],
    threshold: float = 0.8
) -> str:
    """Find a matching ingredient in the candidate list."""
    for candidate in candidate_list:
        if fuzzy_match(ingredient, candidate, threshold):
            return candidate
    return None


def compare_recipe(
    recipe_name: str,
    computer_use_ingredients: List[str],
    gold_standard_ingredients: List[str]
) -> Dict:
    """Compare ingredients from two sources for a single recipe.

    Returns:
        Dictionary with comparison metrics
    """
    # Normalize all ingredients
    cu_set = set(normalize_ingredient(ing) for ing in computer_use_ingredients)
    gs_set = set(normalize_ingredient(ing) for ing in gold_standard_ingredients)

    # Find matches, missing, and extra
    matched = cu_set & gs_set
    missing = gs_set - cu_set  # In gold standard but not in Computer Use
    extra = cu_set - gs_set    # In Computer Use but not in gold standard

    # Calculate metrics
    precision = len(matched) / len(cu_set) if cu_set else 0
    recall = len(matched) / len(gs_set) if gs_set else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'recipe_name': recipe_name,
        'computer_use_count': len(computer_use_ingredients),
        'gold_standard_count': len(gold_standard_ingredients),
        'matched_count': len(matched),
        'missing_count': len(missing),
        'extra_count': len(extra),
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'matched': list(matched),
        'missing': list(missing),
        'extra': list(extra)
    }


def compare_extractions(
    computer_use_results: Dict[str, List[str]],
    gold_standard_file: str = 'gold_standard_recipes.json'
) -> None:
    """Compare Computer Use results against gold standard.

    Args:
        computer_use_results: Dict mapping recipe names to ingredient lists
        gold_standard_file: Path to gold standard JSON
    """
    print("="*70)
    print("EXTRACTION COMPARISON: Computer Use vs API Gold Standard")
    print("="*70)
    print()

    # Load gold standard
    gold_data = load_gold_standard(gold_standard_file)
    gold_recipes = {r['name']: r['ingredients'] for r in gold_data['recipes']}

    print(f"Gold Standard: {len(gold_recipes)} recipes")
    print(f"Computer Use:  {len(computer_use_results)} recipes")
    print()

    # Compare each recipe
    comparisons = []

    for recipe_name in computer_use_results.keys():
        cu_ingredients = computer_use_results[recipe_name]

        # Find matching recipe in gold standard
        if recipe_name in gold_recipes:
            gs_ingredients = gold_recipes[recipe_name]
        else:
            print(f"⚠️  Warning: '{recipe_name}' not found in gold standard")
            continue

        comparison = compare_recipe(recipe_name, cu_ingredients, gs_ingredients)
        comparisons.append(comparison)

    # Print detailed results
    print("="*70)
    print("DETAILED COMPARISON")
    print("="*70)

    for comp in comparisons:
        status = '✅' if comp['f1_score'] >= 0.9 else '⚠️' if comp['f1_score'] >= 0.7 else '❌'

        print(f"\n{status} {comp['recipe_name']}")
        print(f"  Computer Use: {comp['computer_use_count']} ingredients")
        print(f"  Gold Standard: {comp['gold_standard_count']} ingredients")
        print(f"  Matched: {comp['matched_count']}")
        print(f"  Precision: {comp['precision']:.2%}")
        print(f"  Recall: {comp['recall']:.2%}")
        print(f"  F1 Score: {comp['f1_score']:.2%}")

        if comp['missing']:
            print(f"\n  Missing ingredients (in gold standard but not extracted):")
            for ing in comp['missing']:
                print(f"    - {ing}")

        if comp['extra']:
            print(f"\n  Extra ingredients (extracted but not in gold standard):")
            for ing in comp['extra']:
                print(f"    + {ing}")

    # Overall summary
    if comparisons:
        avg_precision = sum(c['precision'] for c in comparisons) / len(comparisons)
        avg_recall = sum(c['recall'] for c in comparisons) / len(comparisons)
        avg_f1 = sum(c['f1_score'] for c in comparisons) / len(comparisons)

        print("\n" + "="*70)
        print("OVERALL METRICS")
        print("="*70)
        print(f"Recipes compared:   {len(comparisons)}")
        print(f"Average Precision:  {avg_precision:.2%}")
        print(f"Average Recall:     {avg_recall:.2%}")
        print(f"Average F1 Score:   {avg_f1:.2%}")
        print("="*70)


def main():
    """Example usage of comparison tool."""
    # Example: Load Computer Use results from recipe_extraction_comprehensive.py output
    # In practice, you'd modify recipe_extraction_comprehensive.py to save results to JSON

    print("This is a comparison utility.")
    print("\nTo use it:")
    print("1. Run: python3 scripts/gold_standard_extraction.py")
    print("2. Run: python3 scripts/recipe_extraction_comprehensive.py (modify to save results)")
    print("3. Call compare_extractions() with your Computer Use results")
    print()

    # Example data structure
    example_cu_results = {
        'Topinambours au vinaigre': [
            'Rice vinegar / Vinaigre de riz',
            'Sugar / Sucre',
            'Beurre / Butter',
            'Topinambours / Jerusalem artichokes'
        ],
        'Velouté Potimarron': [
            'Potimarron / Red kuri squash',
            'Oignon / Onion',
            'All / Garlic',
            'Gingembre / Ginger',
            'Lait de soja / Soy milk'
        ]
    }

    print("Example comparison:")
    print()
    # Uncomment to run example:
    # compare_extractions(example_cu_results)


if __name__ == "__main__":
    main()
