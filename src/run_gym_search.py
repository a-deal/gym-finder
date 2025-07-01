#!/usr/bin/env python3
"""
Script Runner for GymIntel - Execute gym searches programmatically
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

from gym_finder import GymFinder
from metro_areas import MetropolitanArea, get_metro_area


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


def run_batch_search(
    zip_codes: List[str],
    radius: int = 10,
    export_format: Optional[str] = None,
    use_google: bool = True,
    max_workers: int = 4,
    quiet: bool = False,
) -> Dict[str, dict]:
    """
    Run gym searches for multiple ZIP codes in parallel

    Args:
        zip_codes: List of ZIP codes to search
        radius: Search radius in miles
        export_format: Export format ('csv', 'json', 'both', or None)
        use_google: Whether to use Google Places API
        max_workers: Maximum number of parallel workers
        quiet: Whether to suppress individual search output

    Returns:
        Dict mapping ZIP codes to their search results
    """
    if not quiet:
        print(f"🚀 Starting batch search for {len(zip_codes)} ZIP codes")
        print(f"⚙️  Using {max_workers} parallel workers")
        print(f"📍 Search radius: {radius} miles")
        print("=" * 60)

    batch_results = {}
    completed_count = 0
    start_time = time.time()

    def search_single_zip(zipcode: str) -> tuple:
        """Search a single ZIP code and return results"""
        try:
            result = run_gym_search(
                zipcode=zipcode,
                radius=radius,
                export_format=None,  # Handle export at batch level
                use_google=use_google,
                quiet=True,  # Always quiet for individual searches
            )
            return zipcode, result, None
        except Exception as e:
            return zipcode, None, str(e)

    # Execute searches in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_zipcode = {executor.submit(search_single_zip, zipcode): zipcode for zipcode in zip_codes}

        # Process completed jobs
        for future in as_completed(future_to_zipcode):
            zipcode, result, error = future.result()
            completed_count += 1

            if error:
                if not quiet:
                    print(f"❌ {zipcode}: {error}")
                batch_results[zipcode] = {"error": error, "results": []}
            else:
                if not quiet:
                    gyms_count = len(result.get("gyms", []))
                    merged_count = result.get("search_info", {}).get("merged_count", 0)
                    print(f"✅ {zipcode}: {gyms_count} gyms ({merged_count} merged) - " f"[{completed_count}/{len(zip_codes)}]")
                batch_results[zipcode] = result

    elapsed_time = time.time() - start_time

    if not quiet:
        print("=" * 60)
        print(f"🎉 Batch search completed in {elapsed_time:.1f} seconds")
        print(f"✅ Successful: {len([r for r in batch_results.values() if 'error' not in r])}")
        print(f"❌ Failed: {len([r for r in batch_results.values() if 'error' in r])}")

    return batch_results


def run_metro_search(
    metro_code: str,
    radius: int = 10,
    export_format: Optional[str] = None,
    use_google: bool = True,
    max_workers: int = 4,
    sample_size: Optional[int] = None,
) -> Dict[str, any]:
    """
    Run gym search for an entire metropolitan area

    Args:
        metro_code: Metropolitan area code (e.g., 'nyc', 'la', 'chicago')
        radius: Search radius in miles
        export_format: Export format ('csv', 'json', 'both', or None)
        use_google: Whether to use Google Places API
        max_workers: Maximum number of parallel workers
        sample_size: Limit to N ZIP codes for testing (None = all)

    Returns:
        Dict with metro area results and aggregated statistics
    """

    # Get metropolitan area definition
    metro_area = get_metro_area(metro_code)
    if not metro_area:
        return {"error": f"Unknown metropolitan area: {metro_code}"}

    zip_codes = metro_area.zip_codes
    if sample_size:
        zip_codes = zip_codes[:sample_size]
        print(f"🧪 Sample mode: Processing {sample_size} of {len(metro_area.zip_codes)} ZIP codes")

    print(f"🏙️  {metro_area.name} Metropolitan Area Analysis")
    print(f"📊 Population: {metro_area.population:,}" if metro_area.population else "")
    print(f"📊 Market: {', '.join(metro_area.market_characteristics[:3])}")
    print(f"📊 Processing {len(zip_codes)} ZIP codes")

    # Run batch search
    batch_results = run_batch_search(
        zip_codes=zip_codes,
        radius=radius,
        export_format=None,  # Handle at metro level
        use_google=use_google,
        max_workers=max_workers,
        quiet=False,
    )

    # Generate metropolitan area aggregated statistics
    metro_stats = generate_metro_statistics(metro_area, batch_results)

    # Combine all gym data for cross-metro duplicate detection
    all_gyms = []
    for zipcode, result in batch_results.items():
        if "gyms" in result:
            for gym in result["gyms"]:
                gym["source_zipcode"] = zipcode  # Track origin
                all_gyms.append(gym)

    # Deduplicate across the entire metropolitan area
    if len(all_gyms) > 0:
        print(f"\n🔗 Performing metropolitan-wide deduplication...")
        deduplicated_gyms = deduplicate_metro_gyms(all_gyms)
        metro_stats["deduplicated_gym_count"] = len(deduplicated_gyms)
        metro_stats["duplication_rate"] = (len(all_gyms) - len(deduplicated_gyms)) / len(all_gyms) * 100
        print(f"🔗 Removed {len(all_gyms) - len(deduplicated_gyms)} duplicates across metro area")
        print(f"🔗 Metro duplication rate: {metro_stats['duplication_rate']:.1f}%")
    else:
        deduplicated_gyms = []
        metro_stats["deduplicated_gym_count"] = 0
        metro_stats["duplication_rate"] = 0

    # Prepare final results
    metro_results = {
        "metro_info": {
            "area": metro_area,
            "search_params": {
                "radius": radius,
                "use_google": use_google,
                "zip_codes_processed": len(zip_codes),
                "timestamp": datetime.now().isoformat(),
            },
            "statistics": metro_stats,
        },
        "zip_results": batch_results,
        "all_gyms": deduplicated_gyms,
    }

    # Export if requested
    if export_format:
        export_metro_results(metro_results, metro_code, export_format)

    return metro_results


def generate_metro_statistics(metro_area: MetropolitanArea, batch_results: Dict[str, dict]) -> Dict[str, any]:
    """Generate aggregated statistics for metropolitan area"""

    successful_searches = [r for r in batch_results.values() if "gyms" in r]
    failed_searches = [r for r in batch_results.values() if "error" in r]

    if not successful_searches:
        return {"error": "No successful searches to analyze"}

    # Aggregate gym counts
    total_gyms = sum(len(result["gyms"]) for result in successful_searches)
    total_merged = sum(result.get("search_info", {}).get("merged_count", 0) for result in successful_searches)

    # Calculate confidence distribution
    all_confidences = []
    for result in successful_searches:
        for gym in result["gyms"]:
            if gym.get("match_confidence", 0) > 0:
                all_confidences.append(gym["match_confidence"])

    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

    # Source distribution
    source_counts = {"Yelp": 0, "Google Places": 0, "Merged": 0}
    for result in successful_searches:
        for gym in result["gyms"]:
            if "Merged" in gym.get("source", ""):
                source_counts["Merged"] += 1
            elif "Yelp" in gym.get("source", ""):
                source_counts["Yelp"] += 1
            elif "Google" in gym.get("source", ""):
                source_counts["Google Places"] += 1

    # ZIP code density analysis
    gyms_per_zip = [len(result["gyms"]) for result in successful_searches]
    avg_gyms_per_zip = sum(gyms_per_zip) / len(gyms_per_zip) if gyms_per_zip else 0
    max_gyms_zip = max(gyms_per_zip) if gyms_per_zip else 0
    min_gyms_zip = min(gyms_per_zip) if gyms_per_zip else 0

    return {
        "metro_area_name": metro_area.name,
        "zip_codes_total": len(metro_area.zip_codes),
        "zip_codes_processed": len(batch_results),
        "zip_codes_successful": len(successful_searches),
        "zip_codes_failed": len(failed_searches),
        "total_gyms_found": total_gyms,
        "total_merged_gyms": total_merged,
        "overall_merge_rate": (total_merged / total_gyms * 100) if total_gyms > 0 else 0,
        "average_confidence": avg_confidence,
        "source_distribution": source_counts,
        "gyms_per_zip": {"average": avg_gyms_per_zip, "maximum": max_gyms_zip, "minimum": min_gyms_zip},
        "market_characteristics": metro_area.market_characteristics,
        "density_category": metro_area.density_category,
    }


def deduplicate_metro_gyms(all_gyms: List[dict]) -> List[dict]:
    """
    Remove duplicates across the entire metropolitan area
    Uses name and address similarity to detect cross-ZIP duplicates
    """
    if not all_gyms:
        return []

    # Import here to avoid circular imports
    gym_finder = GymFinder()

    deduplicated = []
    processed_names = set()

    for gym in all_gyms:
        # Create a normalized signature for duplicate detection
        normalized_name = gym_finder.normalize_address(gym.get("name", "")).lower()
        normalized_address = gym_finder.normalize_address(gym.get("address", "")).lower()

        # Create a signature combining name and address fragments
        signature = f"{normalized_name[:20]}_{normalized_address[:30]}"

        # Check if we've seen a very similar gym
        is_duplicate = False
        for existing_sig in processed_names:
            # Simple similarity check - in production, could use more sophisticated matching
            if (
                len(set(signature.split("_")[0]) & set(existing_sig.split("_")[0])) > 3
                and len(set(signature.split("_")[1]) & set(existing_sig.split("_")[1])) > 5
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            processed_names.add(signature)
            deduplicated.append(gym)

    return deduplicated


def export_metro_results(metro_results: Dict[str, any], metro_code: str, export_format: str):
    """Export metropolitan area results to file(s)"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if export_format in ["json", "both"]:
        filename = f"metro_{metro_code}_{timestamp}.json"

        # Prepare JSON-serializable data
        export_data = {
            "metro_info": {
                "area_name": metro_results["metro_info"]["area"].name,
                "area_code": metro_code,
                "population": metro_results["metro_info"]["area"].population,
                "market_characteristics": metro_results["metro_info"]["area"].market_characteristics,
                "search_params": metro_results["metro_info"]["search_params"],
                "statistics": metro_results["metro_info"]["statistics"],
            },
            "gyms": metro_results["all_gyms"],
            "zip_results_summary": {
                zipcode: {
                    "gym_count": len(result.get("gyms", [])),
                    "merged_count": result.get("search_info", {}).get("merged_count", 0),
                    "error": result.get("error"),
                }
                for zipcode, result in metro_results["zip_results"].items()
            },
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"📁 Metro JSON exported to: {filename}")

    if export_format in ["csv", "both"]:
        filename = f"metro_{metro_code}_{timestamp}.csv"

        # Use existing CSV export but with metro data
        gym_finder = GymFinder()
        csv_filename = gym_finder.export_to_csv(metro_results["all_gyms"], f"metro_{metro_code}")
        print(f"📁 Metro CSV exported to: {csv_filename}")


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
