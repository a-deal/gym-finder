#!/usr/bin/env python3
"""
Test Suite for Multi-City Batch Processing
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from metro_areas import MetropolitanArea, get_metro_area, get_metro_zip_codes  # noqa: E402
from run_gym_search import generate_metro_statistics, run_batch_search, run_metro_search  # noqa: E402


class TestMetroAreas(unittest.TestCase):
    """Test cases for metropolitan area definitions"""

    def test_get_metro_area_valid(self):
        """Test getting a valid metropolitan area"""
        nyc = get_metro_area("nyc")
        self.assertIsNotNone(nyc)
        self.assertEqual(nyc.name, "New York City")
        self.assertEqual(nyc.code, "nyc")
        self.assertTrue(len(nyc.zip_codes) > 50)  # NYC should have many ZIP codes

    def test_get_metro_area_invalid(self):
        """Test getting an invalid metropolitan area"""
        invalid = get_metro_area("invalid_code")
        self.assertIsNone(invalid)

    def test_get_metro_zip_codes(self):
        """Test getting ZIP codes for a metropolitan area"""
        nyc_zips = get_metro_zip_codes("nyc")
        self.assertTrue(len(nyc_zips) > 50)
        self.assertIn("10001", nyc_zips)  # Manhattan ZIP should be included

        # Test invalid metro
        invalid_zips = get_metro_zip_codes("invalid")
        self.assertEqual(invalid_zips, [])

    def test_metro_area_structure(self):
        """Test metropolitan area data structure"""
        la = get_metro_area("la")
        self.assertIsNotNone(la)
        self.assertIsInstance(la.zip_codes, list)
        self.assertIsInstance(la.market_characteristics, list)
        self.assertIn(la.density_category, ["low", "medium", "high", "very_high"])


class TestBatchProcessing(unittest.TestCase):
    """Test cases for batch processing functionality"""

    def setUp(self):
        """Set up test environment"""
        with patch.dict(os.environ, {"YELP_API_KEY": "test_yelp", "GOOGLE_PLACES_API_KEY": "test_google"}):
            pass

    @patch("run_gym_search.run_gym_search")
    def test_run_batch_search_success(self, mock_run_gym_search):
        """Test successful batch search execution"""
        # Mock individual search results
        mock_run_gym_search.side_effect = [
            {"search_info": {"zipcode": "10001", "merged_count": 5}, "gyms": [{"name": "Gym 1", "source": "Yelp"}] * 10},
            {"search_info": {"zipcode": "10003", "merged_count": 3}, "gyms": [{"name": "Gym 2", "source": "Google"}] * 8},
        ]

        zip_codes = ["10001", "10003"]
        results = run_batch_search(zip_codes, radius=5, max_workers=2, quiet=True)

        self.assertEqual(len(results), 2)
        self.assertIn("10001", results)
        self.assertIn("10003", results)
        self.assertEqual(len(results["10001"]["gyms"]), 10)
        self.assertEqual(len(results["10003"]["gyms"]), 8)

        # Verify run_gym_search was called correctly
        self.assertEqual(mock_run_gym_search.call_count, 2)

    @patch("run_gym_search.run_gym_search")
    def test_run_batch_search_with_errors(self, mock_run_gym_search):
        """Test batch search with some failures"""

        # Mock one success, one failure
        def side_effect(zipcode, **kwargs):
            if zipcode == "10001":
                return {"search_info": {"zipcode": "10001"}, "gyms": []}
            else:
                raise Exception("API Error")

        mock_run_gym_search.side_effect = side_effect

        zip_codes = ["10001", "invalid"]
        results = run_batch_search(zip_codes, quiet=True)

        self.assertEqual(len(results), 2)
        self.assertIn("10001", results)
        self.assertIn("invalid", results)
        self.assertNotIn("error", results["10001"])
        self.assertIn("error", results["invalid"])

    def test_generate_metro_statistics(self):
        """Test metropolitan area statistics generation"""
        # Create mock metro area
        metro_area = MetropolitanArea(
            name="Test Metro",
            code="test",
            description="Test area",
            zip_codes=["10001", "10002"],
            state="NY",
            market_characteristics=["test_market"],
        )

        # Create mock batch results
        batch_results = {
            "10001": {
                "gyms": [
                    {"name": "Gym 1", "source": "Yelp", "match_confidence": 0.8},
                    {"name": "Gym 2", "source": "Merged", "match_confidence": 0.9},
                ],
                "search_info": {"merged_count": 1},
            },
            "10002": {
                "gyms": [{"name": "Gym 3", "source": "Google Places", "match_confidence": 0.0}],
                "search_info": {"merged_count": 0},
            },
            "10003": {"error": "Failed search"},
        }

        stats = generate_metro_statistics(metro_area, batch_results)

        self.assertEqual(stats["metro_area_name"], "Test Metro")
        self.assertEqual(stats["zip_codes_processed"], 3)
        self.assertEqual(stats["zip_codes_successful"], 2)
        self.assertEqual(stats["zip_codes_failed"], 1)
        self.assertEqual(stats["total_gyms_found"], 3)
        self.assertEqual(stats["total_merged_gyms"], 1)
        self.assertAlmostEqual(stats["overall_merge_rate"], 33.33333333333333, places=5)  # 1/3 * 100
        self.assertAlmostEqual(stats["average_confidence"], 0.85)  # (0.8 + 0.9) / 2


class TestMetroSearch(unittest.TestCase):
    """Test cases for metropolitan area search functionality"""

    @patch("run_gym_search.run_batch_search")
    @patch("run_gym_search.deduplicate_metro_gyms")
    def test_run_metro_search_success(self, mock_deduplicate, mock_batch_search):
        """Test successful metropolitan area search"""
        # Mock batch search results
        mock_batch_results = {
            "10001": {"gyms": [{"name": "Gym 1", "address": "123 Main St"}], "search_info": {"merged_count": 1}}
        }
        mock_batch_search.return_value = mock_batch_results

        # Mock deduplication
        mock_deduplicate.return_value = [{"name": "Gym 1", "address": "123 Main St"}]

        # Run metro search for NYC (should exist)
        results = run_metro_search("nyc", radius=2, sample_size=1)

        self.assertNotIn("error", results)
        self.assertIn("metro_info", results)
        self.assertIn("zip_results", results)
        self.assertIn("all_gyms", results)

        # Verify structure
        metro_info = results["metro_info"]
        self.assertIn("area", metro_info)
        self.assertIn("search_params", metro_info)
        self.assertIn("statistics", metro_info)

        # Verify mock calls
        mock_batch_search.assert_called_once()
        mock_deduplicate.assert_called_once()

    def test_run_metro_search_invalid_metro(self):
        """Test metropolitan area search with invalid metro code"""
        results = run_metro_search("invalid_metro_code")

        self.assertIn("error", results)
        self.assertIn("Unknown metropolitan area", results["error"])


class TestIntegration(unittest.TestCase):
    """Integration tests for batch processing workflow"""

    @patch("run_gym_search.run_gym_search")
    def test_small_batch_integration(self, mock_run_gym_search):
        """Test small batch processing integration"""
        # Mock realistic search results
        mock_run_gym_search.side_effect = [
            {
                "search_info": {"zipcode": "10001", "merged_count": 2, "timestamp": "2024-01-01T12:00:00"},
                "gyms": [
                    {
                        "name": "Test Gym 1",
                        "address": "123 Main St, New York, NY 10001",
                        "source": "Merged",
                        "match_confidence": 0.85,
                        "rating": 4.5,
                    },
                    {
                        "name": "Test Gym 2",
                        "address": "456 Broadway, New York, NY 10001",
                        "source": "Yelp",
                        "match_confidence": 0.0,
                        "rating": 4.2,
                    },
                ],
            }
        ]

        # Test batch processing
        results = run_batch_search(["10001"], radius=2, quiet=True)

        self.assertEqual(len(results), 1)
        self.assertIn("10001", results)
        result = results["10001"]
        self.assertEqual(len(result["gyms"]), 2)
        self.assertEqual(result["search_info"]["merged_count"], 2)

    def test_metro_area_list_completeness(self):
        """Test that all defined metro areas have required fields"""
        from metro_areas import METROPOLITAN_AREAS

        for code, metro in METROPOLITAN_AREAS.items():
            with self.subTest(metro_code=code):
                self.assertIsInstance(metro.name, str)
                self.assertIsInstance(metro.code, str)
                self.assertIsInstance(metro.zip_codes, list)
                self.assertTrue(len(metro.zip_codes) > 0)
                self.assertIsInstance(metro.market_characteristics, list)
                self.assertIn(metro.density_category, ["low", "medium", "high", "very_high"])


if __name__ == "__main__":
    # Set up test environment
    os.environ["YELP_API_KEY"] = "test_yelp_key"
    os.environ["GOOGLE_PLACES_API_KEY"] = "test_google_key"

    # Run tests
    unittest.main(verbosity=2)
