#!/usr/bin/env python3
"""
Performance Benchmarking for Metropolitan Area Batch Processing
"""

import os
import sys
import time
from datetime import datetime
from statistics import mean, stdev

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from run_gym_search import run_batch_search, run_metro_search


def benchmark_batch_processing():
    """Benchmark batch processing performance at different scales"""

    print("🏋️  GymIntel Performance Benchmarking")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Test configurations
    test_configs = [
        {"name": "Small Batch", "zip_codes": ["10001", "10003"], "workers": 2},
        {"name": "Medium Batch", "zip_codes": ["10001", "10003", "10011", "10014", "10016"], "workers": 4},
        {
            "name": "Large Batch",
            "zip_codes": ["10001", "10003", "10011", "10014", "10016", "10018", "10019", "10022", "10023", "10024"],
            "workers": 4,
        },
        {
            "name": "Extra Large Batch",
            "zip_codes": [
                "10001",
                "10003",
                "10011",
                "10014",
                "10016",
                "10018",
                "10019",
                "10022",
                "10023",
                "10024",
                "10025",
                "10026",
                "10027",
                "10028",
                "10029",
            ],
            "workers": 6,
        },
    ]

    results = []

    for config in test_configs:
        print(f"\n📊 Testing: {config['name']}")
        print(f"   ZIP Codes: {len(config['zip_codes'])}")
        print(f"   Workers: {config['workers']}")

        # Run multiple iterations for accuracy
        iterations = 3
        times = []

        for i in range(iterations):
            print(f"   Iteration {i+1}/{iterations}...", end="", flush=True)

            start = time.time()
            batch_results = run_batch_search(
                zip_codes=config["zip_codes"],
                radius=1,  # Small radius for faster testing
                use_google=True,
                max_workers=config["workers"],
                quiet=True,
            )
            elapsed = time.time() - start

            times.append(elapsed)

            # Count successful results
            successful = len([r for r in batch_results.values() if "error" not in r])
            print(f" {elapsed:.1f}s ({successful}/{len(config['zip_codes'])} successful)")

        # Calculate statistics
        avg_time = mean(times)
        std_time = stdev(times) if len(times) > 1 else 0
        throughput = len(config["zip_codes"]) / avg_time

        result = {
            "name": config["name"],
            "zip_codes": len(config["zip_codes"]),
            "workers": config["workers"],
            "avg_time": avg_time,
            "std_dev": std_time,
            "throughput": throughput,
        }
        results.append(result)

        print(f"   Average: {avg_time:.2f}s ± {std_time:.2f}s")
        print(f"   Throughput: {throughput:.2f} ZIP codes/second")

    # Summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"{'Configuration':<20} {'ZIPs':<6} {'Workers':<8} {'Avg Time':<10} {'Throughput':<15}")
    print("-" * 60)

    for r in results:
        print(
            f"{r['name']:<20} {r['zip_codes']:<6} {r['workers']:<8} "
            f"{r['avg_time']:.2f}s ± {r['std_dev']:.2f} {r['throughput']:.2f} ZIPs/sec"
        )

    # Scaling analysis
    print("\n📈 SCALING ANALYSIS")
    print("-" * 60)

    base_throughput = results[0]["throughput"]
    for r in results[1:]:
        scaling_factor = r["throughput"] / base_throughput
        print(f"{r['name']}: {scaling_factor:.2f}x throughput vs {results[0]['name']}")

    # Worker efficiency
    print("\n👷 WORKER EFFICIENCY")
    print("-" * 60)

    for r in results:
        efficiency = (r["throughput"] / r["workers"]) * 100
        print(f"{r['name']}: {efficiency:.1f}% efficiency per worker")


def benchmark_metro_areas():
    """Benchmark metropolitan area performance"""

    print("\n\n🏙️  METROPOLITAN AREA BENCHMARKING")
    print("=" * 60)

    metro_tests = [
        {"code": "miami", "sample": 5, "name": "Miami (Small)"},
        {"code": "boston", "sample": 10, "name": "Boston (Medium)"},
        {"code": "nyc", "sample": 20, "name": "NYC (Large)"},
    ]

    for test in metro_tests:
        print(f"\n📊 Testing: {test['name']} - {test['sample']} ZIP codes")

        start = time.time()
        results = run_metro_search(metro_code=test["code"], radius=1, sample_size=test["sample"], max_workers=4)
        elapsed = time.time() - start

        if "error" not in results:
            stats = results["metro_info"]["statistics"]
            print(f"   Time: {elapsed:.1f}s")
            print(f"   Successful: {stats['zip_codes_successful']}/{stats['zip_codes_processed']}")
            print(f"   Total Gyms: {stats['total_gyms_found']}")
            print(f"   Deduplication: {stats.get('duplication_rate', 0):.1f}%")
            print(f"   Throughput: {stats['zip_codes_processed']/elapsed:.2f} ZIPs/sec")
        else:
            print(f"   Error: {results['error']}")


def main():
    """Run all benchmarks"""

    # Check API keys
    if not os.getenv("YELP_API_KEY") or not os.getenv("GOOGLE_PLACES_API_KEY"):
        print("❌ Error: API keys not configured")
        print("Please set YELP_API_KEY and GOOGLE_PLACES_API_KEY environment variables")
        return

    try:
        benchmark_batch_processing()
        benchmark_metro_areas()

        print("\n\n✅ Benchmarking Complete!")
        print(f"Timestamp: {datetime.now().isoformat()}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmarking interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during benchmarking: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
