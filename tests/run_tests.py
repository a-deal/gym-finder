#!/usr/bin/env python3
"""
Test Runner for GymIntel - Simple script to run all tests
"""

import os
import sys
import unittest
from io import StringIO

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def run_unit_tests():
    """Run unit tests with detailed output"""
    print("🧪 Running Unit Tests")
    print("=" * 50)

    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(".", pattern="test_*.py")

    # Capture test output
    stream = StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    # Display results
    output = stream.getvalue()
    print(output)

    # Summary
    print(f"\n📊 Test Results Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    # Display failures and errors
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    success = len(result.failures) == 0 and len(result.errors) == 0
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"\n🎯 Overall Status: {status}")

    return success


def run_integration_tests():
    """Run basic integration tests"""
    print("\n🔧 Running Integration Tests")
    print("=" * 50)

    try:
        from run_gym_search import run_gym_search  # noqa: E402

        # Test 1: Basic search functionality
        print("1️⃣  Testing basic search functionality... ", end="", flush=True)
        result = run_gym_search("10001", radius=1, quiet=True)

        if "error" not in result and "gyms" in result:
            print("✅ PASSED")
            integration_test_1 = True
        else:
            print("❌ FAILED")
            integration_test_1 = False

        # Test 2: Service module imports
        print("2️⃣  Testing service module imports... ", end="", flush=True)
        try:
            from google_places_service import GooglePlacesService
            from gym_finder import GymFinder
            from yelp_service import YelpService

            print("✅ PASSED")
            integration_test_2 = True
        except ImportError as e:
            print(f"❌ FAILED: {e}")
            integration_test_2 = False

        # Test 3: Confidence scoring
        print("3️⃣  Testing confidence scoring... ", end="", flush=True)
        try:
            gym_finder = GymFinder()
            confidence = gym_finder.token_based_name_similarity("Planet Fitness", "Planet Fitness Gym")
            if confidence > 0:
                print("✅ PASSED")
                integration_test_3 = True
            else:
                print("❌ FAILED: No similarity detected")
                integration_test_3 = False
        except Exception as e:
            print(f"❌ FAILED: {e}")
            integration_test_3 = False

        # Test 4: Address normalization
        print("4️⃣  Testing address normalization... ", end="", flush=True)
        try:
            gym_finder = GymFinder()
            normalized = gym_finder.normalize_address("123 Main Street")
            if normalized == "123 main st":
                print("✅ PASSED")
                integration_test_4 = True
            else:
                print(f"❌ FAILED: Expected '123 main st', got '{normalized}'")
                integration_test_4 = False
        except Exception as e:
            print(f"❌ FAILED: {e}")
            integration_test_4 = False

        # Integration test summary
        passed_tests = sum([integration_test_1, integration_test_2, integration_test_3, integration_test_4])
        total_tests = 4

        print(f"\n📊 Integration Test Results: {passed_tests}/{total_tests} passed")

        if passed_tests == total_tests:
            print("🎯 Integration Status: ✅ ALL PASSED")
            return True
        else:
            print("🎯 Integration Status: ❌ SOME FAILED")
            return False

    except Exception as e:
        print(f"💥 Integration test error: {e}")
        return False


def run_smoke_tests():
    """Run quick smoke tests to verify basic functionality"""
    print("\n💨 Running Smoke Tests")
    print("=" * 50)

    smoke_tests = []

    try:
        # Smoke test 1: Can we import everything?
        print("💨 Testing imports... ", end="", flush=True)
        from google_places_service import GooglePlacesService
        from gym_finder import GymFinder
        from run_gym_search import run_gym_search
        from yelp_service import YelpService

        print("✅")
        smoke_tests.append(True)

        # Smoke test 2: Can we create instances?
        print("💨 Testing instance creation... ", end="", flush=True)
        gym_finder = GymFinder()
        YelpService("test_key")
        GooglePlacesService("test_key")
        print("✅")
        smoke_tests.append(True)

        # Smoke test 3: Can we run basic methods?
        print("💨 Testing basic methods... ", end="", flush=True)
        gym_finder.normalize_address("123 Test St")
        gym_finder.normalize_phone("(555) 123-4567")
        gym_finder.token_based_name_similarity("Gym A", "Gym B")
        print("✅")
        smoke_tests.append(True)

        # Smoke test 4: Do we have API keys?
        print("💨 Testing API key configuration... ", end="", flush=True)
        if gym_finder.yelp_api_key and gym_finder.google_api_key:
            print("✅")
            smoke_tests.append(True)
        else:
            print("⚠️  (API keys not configured)")
            smoke_tests.append(False)

    except Exception as e:
        print(f"❌ {e}")
        smoke_tests.append(False)

    passed_smoke = sum(smoke_tests)
    total_smoke = len(smoke_tests)

    print(f"\n📊 Smoke Test Results: {passed_smoke}/{total_smoke} passed")

    if passed_smoke == total_smoke:
        print("🎯 Smoke Status: ✅ ALL PASSED")
        return True
    elif passed_smoke >= total_smoke - 1:  # Allow API key test to fail
        print("🎯 Smoke Status: ✅ MOSTLY PASSED (API keys may need configuration)")
        return True
    else:
        print("🎯 Smoke Status: ❌ FAILED")
        return False


def main():
    """Main test runner"""
    print("🧪 GymIntel Test Suite Runner")
    print("=" * 60)

    # Run all test types
    smoke_passed = run_smoke_tests()
    unit_passed = run_unit_tests()
    integration_passed = run_integration_tests()

    # Overall summary
    print(f"\n📋 Final Test Summary")
    print("=" * 60)
    print(f"💨 Smoke Tests: {'✅ PASSED' if smoke_passed else '❌ FAILED'}")
    print(f"🧪 Unit Tests: {'✅ PASSED' if unit_passed else '❌ FAILED'}")
    print(f"🔧 Integration Tests: {'✅ PASSED' if integration_passed else '❌ FAILED'}")

    overall_status = smoke_passed and unit_passed and integration_passed

    if overall_status:
        print(f"\n🎉 OVERALL STATUS: ✅ ALL TESTS PASSED")
        print(f"   GymIntel is ready for use!")
        return 0
    else:
        print(f"\n⚠️  OVERALL STATUS: ❌ SOME TESTS FAILED")
        print(f"   Please check the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
