#!/usr/bin/env python3
"""
Script Runner for GymIntel - Execute gym searches programmatically
"""

import sys
from datetime import datetime

from gym_finder import GymFinder


def run_gym_search(zipcode, radius=10, export_format=None, use_google=True, quiet=False):
    """
    Run gym search programmatically without CLI

    Args:
        zipcode (str): ZIP code to search
        radius (int): Search radius in miles
        export_format (str): Export format ('csv', 'json', 'both', or None)
        use_google (bool): Whether to use Google Places API
        quiet (bool): Whether to suppress output

    Returns:
        dict: Search results with metadata
    """

    # Initialize gym finder
    gym_finder = GymFinder()

    # Convert zipcode to coordinates
    lat, lng = gym_finder.zipcode_to_coords(zipcode)
    if not lat or not lng:
        return {"error": f"Could not find coordinates for zipcode {zipcode}", "results": []}

    if not quiet:
        print(f"🏋️  Searching for gyms near {zipcode}...")
        print(f"📍 Location: {lat:.4f}, {lng:.4f}")

    # Search multiple data sources
    all_gyms = []

    # Search Yelp
    if not quiet:
        print("🔍 Searching Yelp...")
    yelp_gyms = gym_finder.search_yelp_gyms(lat, lng, radius)

    # Search Google Places if enabled
    google_gyms = []
    if use_google and gym_finder.google_api_key and gym_finder.google_api_key != "your_google_places_api_key_here":
        if not quiet:
            print("🔍 Searching Google Places...")
        google_gyms = gym_finder.search_google_places_gyms(lat, lng, radius)

    # Perform advanced data merging if we have both sources
    if yelp_gyms and google_gyms:
        if not quiet:
            print("🔗 Merging data from multiple sources...")
        all_gyms = gym_finder.fuzzy_match_gyms(yelp_gyms, google_gyms)
    else:
        # Fallback to simple combination if only one source
        all_gyms = yelp_gyms + google_gyms
        for gym in all_gyms:
            if "sources" not in gym:
                gym["sources"] = [gym["source"]]
            gym["match_confidence"] = 0.0

    if not all_gyms:
        return {"error": "No gyms found from any source", "results": []}

    if not quiet:
        print(f"✅ Found {len(yelp_gyms)} Yelp + {len(google_gyms)} Google Places = {len(all_gyms)} total gyms")

    # Enrich with Instagram handles
    if not quiet:
        print("📱 Detecting Instagram handles...")
    for gym in all_gyms:
        if "instagram" not in gym or gym["instagram"] == "N/A":
            gym["instagram"] = gym_finder.detect_instagram_handle(gym["name"])
        if "membership_fee" not in gym:
            gym["membership_fee"] = "TBD"  # Placeholder for future implementation

    # Calculate statistics
    merged_count = sum(1 for gym in all_gyms if gym.get("match_confidence", 0) > 0)
    avg_confidence = 0.0
    if merged_count > 0:
        avg_confidence = (
            sum(gym.get("match_confidence", 0) for gym in all_gyms if gym.get("match_confidence", 0) > 0) / merged_count
        )

    # Prepare results
    results = {
        "search_info": {
            "zipcode": zipcode,
            "coordinates": {"lat": lat, "lng": lng},
            "radius_miles": radius,
            "timestamp": datetime.now().isoformat(),
            "total_results": len(all_gyms),
            "yelp_results": len(yelp_gyms),
            "google_results": len(google_gyms),
            "merged_count": merged_count,
            "avg_confidence": f"{avg_confidence:.1%}" if avg_confidence > 0 else "N/A",
            "use_google": use_google,
        },
        "gyms": all_gyms,
    }

    # Export if requested
    if export_format:
        if export_format in ["csv", "both"]:
            filename = gym_finder.export_to_csv(all_gyms, zipcode)
            if not quiet:
                print(f"📁 CSV exported to: {filename}")

        if export_format in ["json", "both"]:
            filename = gym_finder.export_to_json(all_gyms, zipcode)
            if not quiet:
                print(f"📁 JSON exported to: {filename}")

    return results


def display_results_summary(results):
    """Display a summary of search results"""
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return

    info = results["search_info"]
    gyms = results["gyms"]

    print(f"\n🏋️  Found {info['total_results']} gyms near {info['zipcode']}")
    print(f"📊 Merge Statistics: {info['merged_count']} merged (avg confidence: {info['avg_confidence']})")
    print(f"📍 Sources: {info['yelp_results']} Yelp + {info['google_results']} Google Places")

    # Display top 10 results
    print(f"\n🔝 Top Results:")
    print("-" * 80)

    # Sort by confidence (merged first), then by rating
    sorted_gyms = sorted(gyms, key=lambda x: (x.get("match_confidence", 0), x.get("rating", 0)), reverse=True)

    for i, gym in enumerate(sorted_gyms[:10], 1):
        confidence = f"{gym.get('match_confidence', 0):.0%}" if gym.get("match_confidence", 0) > 0 else "N/A"
        rating = gym.get("rating", "N/A")
        review_count = gym.get("review_count", 0)

        print(f"{i:2d}. {gym['name'][:50]:<50} | {gym['source'][:20]:<20} | {confidence:>6} | {rating} ({review_count})")

    print("-" * 80)


def run_multiple_searches(zipcodes, radius=10, export_format=None):
    """Run searches for multiple ZIP codes"""
    all_results = {}

    for zipcode in zipcodes:
        print(f"\n{'='*60}")
        print(f"Searching ZIP code: {zipcode}")
        print(f"{'='*60}")

        results = run_gym_search(zipcode, radius=radius, export_format=export_format)
        all_results[zipcode] = results

        display_results_summary(results)

    return all_results


def main():
    """Main function for script execution"""

    # Example searches
    print("🏋️  GymIntel - Script Runner")
    print("=" * 50)

    # Single search example
    print("\n🎯 Single ZIP Code Search Example:")
    results = run_gym_search("10001", radius=2, export_format="json")
    display_results_summary(results)

    # Multiple searches example
    print("\n🎯 Multiple ZIP Code Search Example:")
    nyc_zipcodes = ["10001", "10003", "10011"]  # Chelsea, East Village, Greenwich Village
    multiple_results = run_multiple_searches(nyc_zipcodes, radius=1, export_format="csv")

    # Summary across all searches
    print(f"\n📈 Summary Across All ZIP Codes:")
    total_gyms = sum(len(results.get("gyms", [])) for results in multiple_results.values() if "gyms" in results)
    total_merged = sum(results.get("search_info", {}).get("merged_count", 0) for results in multiple_results.values())

    print(f"Total gyms found: {total_gyms}")
    print(f"Total merged: {total_merged}")
    print(f"Overall merge rate: {total_merged/max(total_gyms, 1):.1%}")

    return multiple_results


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        zipcode = sys.argv[1]
        radius = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        export_format = sys.argv[3] if len(sys.argv) > 3 else None

        print(f"🎯 Running search for ZIP code: {zipcode}")
        results = run_gym_search(zipcode, radius=radius, export_format=export_format)
        display_results_summary(results)
    else:
        # Run example searches
        main()
