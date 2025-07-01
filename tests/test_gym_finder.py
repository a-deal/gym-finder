#!/usr/bin/env python3
"""
Test Suite for GymIntel - Comprehensive Gym Discovery Platform
"""

import unittest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.gym_finder import GymFinder
from src.yelp_service import YelpService
from src.google_places_service import GooglePlacesService


class TestYelpService(unittest.TestCase):
    """Test cases for Yelp API service"""
    
    def setUp(self):
        self.yelp_service = YelpService("test_api_key")
    
    def test_init_with_api_key(self):
        """Test YelpService initialization with API key"""
        service = YelpService("test_key")
        self.assertEqual(service.api_key, "test_key")
    
    def test_init_without_api_key(self):
        """Test YelpService initialization without API key"""
        with patch.dict(os.environ, {'YELP_API_KEY': 'env_key'}):
            service = YelpService()
            self.assertEqual(service.api_key, "env_key")
    
    @patch('src.yelp_service.requests.get')
    def test_search_gyms_success(self, mock_get):
        """Test successful gym search via Yelp API"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'businesses': [
                {
                    'name': 'Test Gym',
                    'location': {'display_address': ['123 Test St', 'New York, NY']},
                    'display_phone': '(555) 123-4567',
                    'rating': 4.5,
                    'review_count': 100,
                    'price': '$$',
                    'url': 'https://yelp.com/test-gym'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        gyms = self.yelp_service.search_gyms(40.7484, -73.9940, 2)
        
        self.assertEqual(len(gyms), 1)
        self.assertEqual(gyms[0]['name'], 'Test Gym')
        self.assertEqual(gyms[0]['source'], 'Yelp')
        self.assertEqual(gyms[0]['rating'], 4.5)
    
    @patch('src.yelp_service.requests.get')
    def test_search_gyms_api_error(self, mock_get):
        """Test gym search with API error"""
        mock_get.side_effect = Exception("API Error")
        
        gyms = self.yelp_service.search_gyms(40.7484, -73.9940, 2)
        
        self.assertEqual(gyms, [])
    
    @patch.dict(os.environ, {}, clear=True)
    def test_search_gyms_no_api_key(self):
        """Test gym search without API key"""
        service = YelpService(None)
        gyms = service.search_gyms(40.7484, -73.9940, 2)
        self.assertEqual(gyms, [])


class TestGooglePlacesService(unittest.TestCase):
    """Test cases for Google Places API service"""
    
    def setUp(self):
        self.google_service = GooglePlacesService("test_api_key")
    
    def test_convert_price_level(self):
        """Test price level conversion"""
        self.assertEqual(self.google_service.convert_price_level('PRICE_LEVEL_FREE'), 'Free')
        self.assertEqual(self.google_service.convert_price_level('PRICE_LEVEL_INEXPENSIVE'), '$')
        self.assertEqual(self.google_service.convert_price_level('PRICE_LEVEL_MODERATE'), '$$')
        self.assertEqual(self.google_service.convert_price_level(None), 'N/A')
    
    def test_map_price_level(self):
        """Test price level mapping to numeric"""
        self.assertEqual(self.google_service.map_price_level('PRICE_LEVEL_FREE'), 0)
        self.assertEqual(self.google_service.map_price_level('PRICE_LEVEL_EXPENSIVE'), 3)
        self.assertIsNone(self.google_service.map_price_level(None))
    
    @patch('src.google_places_service.requests.post')
    def test_search_gyms_success(self, mock_post):
        """Test successful gym search via Google Places API"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'places': [
                {
                    'id': 'test_place_id',
                    'displayName': {'text': 'Test Google Gym'},
                    'formattedAddress': '456 Google St, New York, NY',
                    'nationalPhoneNumber': '(555) 987-6543',
                    'rating': 4.2,
                    'userRatingCount': 75,
                    'location': {'latitude': 40.7484, 'longitude': -73.9940},
                    'types': ['gym', 'health'],
                    'websiteUri': 'https://testgooglegym.com'
                }
            ]
        }
        mock_post.return_value = mock_response
        
        gyms = self.google_service.search_gyms(40.7484, -73.9940, 2)
        
        self.assertEqual(len(gyms), 1)
        self.assertEqual(gyms[0]['name'], 'Test Google Gym')
        self.assertEqual(gyms[0]['source'], 'Google Places (New)')
        self.assertEqual(gyms[0]['place_id'], 'test_place_id')


class TestGymFinder(unittest.TestCase):
    """Test cases for main GymFinder application"""
    
    def setUp(self):
        with patch.dict(os.environ, {'YELP_API_KEY': 'test_yelp', 'GOOGLE_PLACES_API_KEY': 'test_google'}):
            self.gym_finder = GymFinder()
    
    def test_init(self):
        """Test GymFinder initialization"""
        self.assertEqual(self.gym_finder.yelp_api_key, 'test_yelp')
        self.assertEqual(self.gym_finder.google_api_key, 'test_google')
        self.assertIsNotNone(self.gym_finder.yelp_service)
        self.assertIsNotNone(self.gym_finder.google_service)
    
    @patch('src.gym_finder.Nominatim')
    def test_zipcode_to_coords(self, mock_nominatim):
        """Test zipcode to coordinates conversion"""
        mock_geolocator = Mock()
        mock_location = Mock()
        mock_location.latitude = 40.7484
        mock_location.longitude = -73.9940
        mock_geolocator.geocode.return_value = mock_location
        mock_nominatim.return_value = mock_geolocator
        
        # Create new instance to use mocked geolocator
        with patch.dict(os.environ, {'YELP_API_KEY': 'test', 'GOOGLE_PLACES_API_KEY': 'test'}):
            finder = GymFinder()
            lat, lng = finder.zipcode_to_coords("10001")
        
        self.assertEqual(lat, 40.7484)
        self.assertEqual(lng, -73.9940)
    
    def test_normalize_address(self):
        """Test address normalization"""
        test_cases = [
            ("123 Main Street", "123 main st"),
            ("456 First Avenue, Suite 5", "456 1st ave ste 5"),
            ("789 West 42nd St., New York", "789 w 42nd st ny"),
        ]
        
        for input_addr, expected in test_cases:
            result = self.gym_finder.normalize_address(input_addr)
            self.assertEqual(result, expected)
    
    def test_normalize_phone(self):
        """Test phone number normalization"""
        test_cases = [
            ("(555) 123-4567", "5551234567"),
            ("555-123-4567", "5551234567"),
            ("1-555-123-4567", "5551234567"),
            ("+1 555 123 4567", "5551234567"),
        ]
        
        for input_phone, expected in test_cases:
            result = self.gym_finder.normalize_phone(input_phone)
            self.assertEqual(result, expected)
    
    def test_clean_gym_name(self):
        """Test gym name cleaning"""
        test_cases = [
            ("Planet Fitness Gym", "planet"),
            ("CrossFit Studio NYC", "crossfit studio nyc"),
            ("Equinox Fitness Center LLC", "equinox fitness"),
        ]
        
        for input_name, expected in test_cases:
            result = self.gym_finder.clean_gym_name(input_name)
            self.assertEqual(result, expected)
    
    def test_token_based_name_similarity(self):
        """Test token-based name similarity"""
        # Exact match after tokenization
        similarity = self.gym_finder.token_based_name_similarity("Planet Fitness", "Planet Fitness Gym")
        self.assertGreater(similarity, 0.5)
        
        # No similarity
        similarity = self.gym_finder.token_based_name_similarity("Planet Fitness", "Equinox")
        self.assertEqual(similarity, 0.0)
    
    def test_semantic_name_similarity(self):
        """Test semantic name similarity"""
        # Martial arts similarity
        similarity = self.gym_finder.semantic_name_similarity("Karate Dojo", "Kung Fu Academy")
        self.assertGreater(similarity, 0.0)
        
        # No semantic similarity
        similarity = self.gym_finder.semantic_name_similarity("Yoga Studio", "Car Repair")
        self.assertEqual(similarity, 0.0)
    
    def test_estimate_coordinates_from_address(self):
        """Test coordinate estimation from address"""
        # Test NYC ZIP code
        lat, lng = self.gym_finder.estimate_coordinates_from_address("123 Main St, New York, NY 10001")
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lng)
        self.assertAlmostEqual(lat, 40.7484, places=1)
        
        # Test no ZIP code
        lat, lng = self.gym_finder.estimate_coordinates_from_address("123 Main St")
        self.assertIsNone(lat)
        self.assertIsNone(lng)
    
    def test_calculate_distance(self):
        """Test distance calculation between coordinates"""
        # Distance between two close points in NYC
        distance = self.gym_finder.calculate_distance(40.7484, -73.9940, 40.7484, -73.9940)
        self.assertEqual(distance, 0.0)
        
        # Distance with invalid coordinates
        distance = self.gym_finder.calculate_distance(None, None, 40.7484, -73.9940)
        self.assertEqual(distance, float('inf'))
    
    def test_detect_chain_match(self):
        """Test chain/franchise detection"""
        # Same chain
        bonus = self.gym_finder.detect_chain_match("Equinox Tribeca", "Equinox Upper East Side")
        self.assertGreater(bonus, 0.0)
        
        # Different chains
        bonus = self.gym_finder.detect_chain_match("Planet Fitness", "Gold's Gym")
        self.assertEqual(bonus, 0.0)
    
    def test_compare_review_counts(self):
        """Test review count correlation"""
        # Similar review counts
        correlation = self.gym_finder.compare_review_counts(100, 90)
        self.assertGreater(correlation, 0.0)
        
        # Very different review counts
        correlation = self.gym_finder.compare_review_counts(10, 1000)
        self.assertEqual(correlation, 0.0)
        
        # Invalid input
        correlation = self.gym_finder.compare_review_counts(None, 100)
        self.assertEqual(correlation, 0.0)


class TestConfidenceScoring(unittest.TestCase):
    """Test cases for confidence scoring system"""
    
    def setUp(self):
        with patch.dict(os.environ, {'YELP_API_KEY': 'test_yelp', 'GOOGLE_PLACES_API_KEY': 'test_google'}):
            self.gym_finder = GymFinder()
    
    def test_fuzzy_match_confidence_calculation(self):
        """Test that confidence scoring produces reasonable results"""
        # Mock gym data
        yelp_gyms = [
            {
                'name': 'Planet Fitness',
                'address': '123 Main St, New York, NY 10001',
                'phone': '(555) 123-4567',
                'rating': 4.0,
                'review_count': 100,
                'price': '$$',
                'url': 'https://yelp.com/planet-fitness'
            }
        ]
        
        google_gyms = [
            {
                'name': 'Planet Fitness Gym',
                'address': '123 Main Street, New York, NY 10001',
                'phone': '(555) 123-4567',
                'rating': 4.1,
                'review_count': 95,
                'source': 'Google Places',
                'place_id': 'test_place_id',
                'location': {'lat': 40.7484, 'lng': -73.9940},
                'types': ['gym', 'health'],
                'website': 'https://planetfitness.com'
            }
        ]
        
        # Test fuzzy matching
        merged_gyms = self.gym_finder.fuzzy_match_gyms(yelp_gyms, google_gyms, confidence_threshold=0.35)
        
        # Should have one merged gym with high confidence
        self.assertEqual(len(merged_gyms), 1)
        merged_gym = merged_gyms[0]
        self.assertEqual(merged_gym['source'], 'Merged (Yelp + Google)')
        self.assertGreater(merged_gym['match_confidence'], 0.35)
        self.assertIn('Yelp', merged_gym['sources'])
        self.assertIn('Google Places', merged_gym['sources'])


class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflow"""
    
    def setUp(self):
        with patch.dict(os.environ, {'YELP_API_KEY': 'test_yelp', 'GOOGLE_PLACES_API_KEY': 'test_google'}):
            self.gym_finder = GymFinder()
    
    @patch.object(GymFinder, 'search_yelp_gyms')
    @patch.object(GymFinder, 'search_google_places_gyms')
    @patch.object(GymFinder, 'zipcode_to_coords')
    def test_find_gyms_integration(self, mock_coords, mock_google, mock_yelp):
        """Test complete gym finding workflow"""
        # Mock coordinate conversion
        mock_coords.return_value = (40.7484, -73.9940)
        
        # Mock Yelp results
        mock_yelp.return_value = [
            {
                'name': 'Test Gym Yelp',
                'address': '123 Test St, New York, NY 10001',
                'phone': '(555) 123-4567',
                'rating': 4.0,
                'review_count': 100,
                'price': '$$',
                'url': 'https://yelp.com/test-gym',
                'source': 'Yelp'
            }
        ]
        
        # Mock Google results
        mock_google.return_value = [
            {
                'name': 'Test Gym Google',
                'address': '456 Google St, New York, NY 10001',
                'phone': '(555) 987-6543',
                'rating': 4.2,
                'review_count': 75,
                'source': 'Google Places',
                'place_id': 'test_place',
                'location': {'lat': 40.7484, 'lng': -73.9940},
                'types': ['gym'],
                'website': 'https://testgym.com'
            }
        ]
        
        # Mock the display_results method to avoid CLI output
        with patch.object(self.gym_finder, 'display_results'):
            self.gym_finder.find_gyms("10001", radius=2)
        
        # Verify methods were called
        mock_coords.assert_called_once_with("10001")
        mock_yelp.assert_called_once()
        mock_google.assert_called_once()


if __name__ == '__main__':
    # Set up test environment
    os.environ['YELP_API_KEY'] = 'test_yelp_key'
    os.environ['GOOGLE_PLACES_API_KEY'] = 'test_google_key'
    
    # Run tests
    unittest.main(verbosity=2)