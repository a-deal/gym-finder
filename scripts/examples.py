#!/usr/bin/env python3
"""
GymIntel Examples - Demonstrating specific features and capabilities
"""

import json
<<<<<<< HEAD:scripts/examples.py
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
=======
>>>>>>> origin/main:examples.py

from google_places_service import GooglePlacesService
from gym_finder import GymFinder
from run_gym_search import display_results_summary, run_gym_search
from yelp_service import YelpService


def example_basic_search():
    """Example 1: Basic gym search"""
    print("🎯 Example 1: Basic Gym Search")
    print("=" * 50)

    results = run_gym_search("10001", radius=2, export_format="json")
    display_results_summary(results)

    return results


def example_yelp_only_search():
    """Example 2: Yelp-only search using service module"""
    print("\n🎯 Example 2: Yelp-Only Search")
    print("=" * 50)

    yelp_service = YelpService()

    # Convert zipcode to coordinates manually for this example
    gym_finder = GymFinder()
    lat, lng = gym_finder.zipcode_to_coords("10003")  # East Village

    if lat and lng:
        print(f"📍 Searching East Village: {lat:.4f}, {lng:.4f}")
        gyms = yelp_service.search_gyms(lat, lng, radius_miles=1)

        print(f"✅ Found {len(gyms)} gyms from Yelp only")

        # Display top 5
        for i, gym in enumerate(gyms[:5], 1):
            print(f"{i}. {gym['name']} - {gym['rating']} stars ({gym['review_count']} reviews)")

    return gyms if "gyms" in locals() else []


def example_google_only_search():
    """Example 3: Google Places-only search using service module"""
    print("\n🎯 Example 3: Google Places-Only Search")
    print("=" * 50)

    google_service = GooglePlacesService()

    # Convert zipcode to coordinates manually for this example
    gym_finder = GymFinder()
    lat, lng = gym_finder.zipcode_to_coords("10011")  # Chelsea

    if lat and lng:
        print(f"📍 Searching Chelsea: {lat:.4f}, {lng:.4f}")
        gyms = google_service.search_gyms(lat, lng, radius_miles=1)

        print(f"✅ Found {len(gyms)} gyms from Google Places only")

        # Display top 5 with Google-specific data
        for i, gym in enumerate(gyms[:5], 1):
            place_id = gym.get("place_id", "N/A")
            types = ", ".join(gym.get("types", [])[:3])  # First 3 types
            print(f"{i}. {gym['name']} - {gym['rating']} stars")
            print(f"   Types: {types}")
            print(f"   Place ID: {place_id[:20]}...")

    return gyms if "gyms" in locals() else []


def example_confidence_scoring_analysis():
    """Example 4: Detailed confidence scoring analysis"""
    print("\n🎯 Example 4: Confidence Scoring Analysis")
    print("=" * 50)

    results = run_gym_search("10001", radius=2, quiet=True)

    if "gyms" in results:
        gyms = results["gyms"]
        merged_gyms = [gym for gym in gyms if gym.get("match_confidence", 0) > 0]

        print(f"📊 Found {len(merged_gyms)} merged gyms out of {len(gyms)} total")

        # Analyze confidence factors
        print(f"\n🔍 Top 3 Highest Confidence Matches:")
        sorted_gyms = sorted(merged_gyms, key=lambda x: x["match_confidence"], reverse=True)

        for i, gym in enumerate(sorted_gyms[:3], 1):
            conf = gym["match_confidence"]
            sources = ", ".join(gym.get("sources", []))

            print(f"\n{i}. {gym['name']}")
            print(f"   Confidence: {conf:.1%}")
            print(f"   Sources: {sources}")
            print(f"   Address: {gym['address']}")
            print(f"   Phone: {gym['phone']}")
            print(f"   Rating: {gym['rating']} ({gym['review_count']} reviews)")

            # Show what likely contributed to high confidence
            factors = []
            if "Yelp" in sources and "Google" in sources:
                factors.append("✅ Multi-source match")
            if conf > 0.8:
                factors.append("✅ Excellent name similarity")
            if gym["phone"] != "N/A":
                factors.append("✅ Phone number available")
            if gym.get("website"):
                factors.append("✅ Website available")

            print(f"   Likely factors: {', '.join(factors)}")

    return merged_gyms if "merged_gyms" in locals() else []


def example_address_normalization():
    """Example 5: Address normalization capabilities"""
    print("\n🎯 Example 5: Address Normalization")
    print("=" * 50)

    gym_finder = GymFinder()

    test_addresses = [
        "123 Main Street, Suite 456, New York, NY 10001",
        "789 First Avenue, Floor 3, Manhattan, NY",
        "456 West 42nd St., New York",
        "321 Park Avenue South, Apartment 5B, NYC",
        "555 Broadway, Room 101, New York, New York",
    ]

    print("Original Address → Normalized Address")
    print("-" * 80)

    for addr in test_addresses:
        normalized = gym_finder.normalize_address(addr)
        print(f"{addr:<45} → {normalized}")

    return test_addresses


def example_semantic_matching():
    """Example 6: Semantic name matching"""
    print("\n🎯 Example 6: Semantic Name Matching")
    print("=" * 50)

    gym_finder = GymFinder()

    test_cases = [
        ("Karate Dojo NYC", "Kung Fu Academy Manhattan"),
        ("CrossFit Box", "CrossFit Training Center"),
        ("Yoga Studio", "Pilates Barre Studio"),
        ("Boxing Gym", "MMA Fight Club"),
        ("Planet Fitness", "Equinox Fitness"),
    ]

    print("Name 1 vs Name 2 → Semantic Similarity")
    print("-" * 60)

    for name1, name2 in test_cases:
        similarity = gym_finder.semantic_name_similarity(name1, name2)
        print(f"{name1:<25} vs {name2:<25} → {similarity:.1%}")

    return test_cases


def example_coordinate_estimation():
    """Example 7: ZIP code coordinate estimation"""
    print("\n🎯 Example 7: ZIP Code Coordinate Estimation")
    print("=" * 50)

    gym_finder = GymFinder()

    test_addresses = [
        "123 Main St, New York, NY 10001",
        "456 Broadway, NY 10003",
        "789 Park Ave, Manhattan, NY 10016",
        "321 8th Ave, New York, NY 10011",
        "555 No ZIP Code Street, NYC",
    ]

    print("Address → Estimated Coordinates")
    print("-" * 60)

    for addr in test_addresses:
        lat, lng = gym_finder.estimate_coordinates_from_address(addr)
        if lat and lng:
            print(f"{addr:<40} → {lat:.4f}, {lng:.4f}")
        else:
            print(f"{addr:<40} → No coordinates found")

    return test_addresses


def example_export_formats():
    """Example 8: Different export formats"""
    print("\n🎯 Example 8: Export Format Demonstration")
    print("=" * 50)

    # Search and export in both formats
    results = run_gym_search("10001", radius=1, export_format="both", quiet=True)

    if "gyms" in results:
        print(f"✅ Search completed: {len(results['gyms'])} gyms found")
        print(f"📁 Exported to both CSV and JSON formats")

        # Show sample JSON structure
        sample_gym = results["gyms"][0] if results["gyms"] else {}
        print(f"\n📄 Sample JSON structure:")
        print(json.dumps(sample_gym, indent=2)[:500] + "...")

    return results


def run_all_examples():
    """Run all examples in sequence"""
    print("🚀 GymIntel Feature Examples")
    print("=" * 60)

    examples = [
        example_basic_search,
        example_yelp_only_search,
        example_google_only_search,
        example_confidence_scoring_analysis,
        example_address_normalization,
        example_semantic_matching,
        example_coordinate_estimation,
        example_export_formats,
    ]

    results = {}

    for example_func in examples:
        try:
            result = example_func()
            results[example_func.__name__] = result
        except Exception as e:
            print(f"❌ Error in {example_func.__name__}: {e}")
            results[example_func.__name__] = None

    print(f"\n✅ All examples completed!")
    print(f"📊 {len([r for r in results.values() if r is not None])}/{len(examples)} examples ran successfully")

    return results


if __name__ == "__main__":
    # Run all examples
    results = run_all_examples()
