#!/usr/bin/env python3
"""
GymIntel - Comprehensive Gym Discovery CLI Tool
"""

import os
import sys
import requests
import click
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from tabulate import tabulate
import time
import re
from urllib.parse import quote, urlparse
import ssl
import certifi
import csv
import json
from datetime import datetime
from difflib import SequenceMatcher
import math

# Import our service modules
from yelp_service import YelpService
from google_places_service import GooglePlacesService

load_dotenv()

class GymFinder:
    def __init__(self):
        self.yelp_api_key = os.getenv('YELP_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        
        # Initialize service modules
        self.yelp_service = YelpService(self.yelp_api_key)
        self.google_service = GooglePlacesService(self.google_api_key)
        
        # Create SSL context for certificate verification
        ctx = ssl.create_default_context(cafile=certifi.where())
        self.geolocator = Nominatim(user_agent="gym-intel-cli", ssl_context=ctx)
        
    def zipcode_to_coords(self, zipcode):
        """Convert zipcode to latitude/longitude coordinates"""
        try:
            location = self.geolocator.geocode(f"{zipcode}, USA")
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception as e:
            click.echo(f"Error converting zipcode: {e}")
            return None, None
    
    def search_yelp_gyms(self, lat, lng, radius_miles=10):
        """Search for gyms using Yelp API"""
        return self.yelp_service.search_gyms(lat, lng, radius_miles)
    
    def search_google_places_gyms(self, lat, lng, radius_miles=10):
        """Search for gyms using Google Places API with enhanced details"""
        return self.google_service.search_gyms(lat, lng, radius_miles)
    
    
    def compare_review_counts(self, yelp_count, google_count):
        """Intelligent review count correlation for business matching"""
        if not yelp_count or not google_count:
            return 0.0
        
        # Convert to numbers if they're strings
        try:
            yelp_num = int(yelp_count)
            google_num = int(google_count)
        except (ValueError, TypeError):
            return 0.0
        
        if yelp_num <= 0 or google_num <= 0:
            return 0.0
        
        # Calculate ratio (smaller/larger)
        larger = max(yelp_num, google_num)
        smaller = min(yelp_num, google_num)
        ratio = smaller / larger
        
        # Review count correlation scoring with fitness business context
        if ratio > 0.8:  # Very similar review counts (80%+ correlation)
            return 0.12  # Strong correlation
        elif ratio > 0.6:  # Good correlation
            return 0.08
        elif ratio > 0.4:  # Moderate correlation
            return 0.05
        elif ratio > 0.2:  # Weak but plausible correlation
            return 0.02
        
        # Special case: both have very few reviews (new businesses)
        if larger <= 10:
            return 0.03  # Small business bonus
        
        return 0.0
    
    def assess_website_quality(self, yelp_url, google_website):
        """Assess website quality and business legitimacy indicators"""
        confidence = 0.0
        
        # Google website analysis
        if google_website and google_website != 'N/A':
            # Real business website (not just Google Maps)
            if 'maps.google.com' not in google_website.lower():
                confidence += 0.04  # Has actual business website
                
                # Professional domain indicators
                business_domains = ['.com', '.net', '.org', '.biz']
                fitness_domains = ['.fitness', '.gym', '.health', '.wellness']
                
                if any(domain in google_website.lower() for domain in fitness_domains):
                    confidence += 0.03  # Fitness-specific domain
                elif any(domain in google_website.lower() for domain in business_domains):
                    confidence += 0.02  # Professional domain
                
                # HTTPS indicator (modern, professional websites)
                if google_website.lower().startswith('https://'):
                    confidence += 0.01  # Secure website
        
        # Yelp presence analysis
        if yelp_url and 'yelp.com/biz/' in yelp_url:
            confidence += 0.02  # Established Yelp presence
            
            # Check for rich Yelp profile indicators
            if len(yelp_url) > 50:  # Longer URLs often indicate more complete profiles
                confidence += 0.01  # Detailed Yelp profile
        
        return confidence
    
    def semantic_category_mapping(self, yelp_categories, google_types):
        """Phase 2: Advanced semantic category mapping for fitness businesses"""
        if not yelp_categories or not google_types:
            return 0.0
        
        # Enhanced fitness business taxonomy
        fitness_taxonomy = {
            'traditional_gym': {
                'yelp_terms': ['gym', 'fitness', 'health club', 'fitness center'],
                'google_types': ['gym', 'health', 'establishment', 'point_of_interest'],
                'weight': 1.0
            },
            'boutique_studio': {
                'yelp_terms': ['studio', 'boutique', 'pilates', 'yoga', 'barre'],
                'google_types': ['gym', 'health', 'spa', 'point_of_interest'],
                'weight': 0.9
            },
            'martial_arts': {
                'yelp_terms': ['martial arts', 'karate', 'kung fu', 'boxing', 'mma', 'jiu jitsu'],
                'google_types': ['gym', 'health', 'establishment'],
                'weight': 0.8
            },
            'dance_fitness': {
                'yelp_terms': ['dance', 'zumba', 'ballet', 'dance fitness'],
                'google_types': ['gym', 'health', 'establishment', 'school'],
                'weight': 0.7
            },
            'specialized_training': {
                'yelp_terms': ['training', 'personal training', 'crossfit', 'bootcamp'],
                'google_types': ['gym', 'health', 'establishment'],
                'weight': 0.8
            },
            'wellness_center': {
                'yelp_terms': ['wellness', 'rehabilitation', 'physical therapy', 'massage'],
                'google_types': ['health', 'physiotherapist', 'spa', 'doctor'],
                'weight': 0.6
            }
        }
        
        yelp_lower = yelp_categories.lower()
        google_lower = [t.lower() for t in google_types]
        
        best_match_score = 0.0
        
        for category, mapping in fitness_taxonomy.items():
            yelp_match = any(term in yelp_lower for term in mapping['yelp_terms'])
            google_match = any(gtype in google_lower for gtype in mapping['google_types'])
            
            if yelp_match and google_match:
                match_strength = len([term for term in mapping['yelp_terms'] if term in yelp_lower])
                google_strength = len([gtype for gtype in mapping['google_types'] if gtype in google_lower])
                
                # Combined semantic similarity score
                category_score = mapping['weight'] * (match_strength + google_strength) / 10
                best_match_score = max(best_match_score, category_score)
        
        return min(best_match_score, 0.15)  # Cap at 15% bonus
    
    
    def get_google_place_details(self, place_id):
        """Get detailed information for a specific Google Place"""
        if not place_id or not self.google_api_key:
            return {}
        
        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_address,formatted_phone_number,website,opening_hours,price_level",
            "key": self.google_api_key
        }
        
        try:
            response = requests.get(details_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('result', {})
            else:
                return {}
                
        except requests.exceptions.RequestException:
            return {}
    
    def geocode_address(self, address):
        """Geocode an address to get latitude/longitude coordinates"""
        if not address or address == 'N/A':
            return None, None
        
        try:
            location = self.geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            return None, None
        except Exception:
            return None, None
    
    def compare_business_hours(self, yelp_hours, google_hours):
        """Enhanced business hours comparison with intelligent parsing"""
        if not google_hours or not isinstance(google_hours, dict):
            return 0.0
        
        confidence = 0.0
        
        # Check for various Google hours data formats
        has_periods = google_hours.get('periods')
        has_descriptions = google_hours.get('weekdayDescriptions')
        has_open_now = 'openNow' in google_hours
        
        # Basic scoring for having hours data
        if has_periods or has_descriptions:
            confidence += 0.15  # Has structured hours
        
        # Real-time status bonus
        if has_open_now:
            confidence += 0.10  # Has real-time open/closed status
        
        # Enhanced parsing for common patterns
        if has_descriptions:
            descriptions = google_hours.get('weekdayDescriptions', [])
            
            # Look for 24/7 operations
            if any('24 hours' in desc.lower() or 'open 24' in desc.lower() for desc in descriptions):
                confidence += 0.05  # 24/7 operation signal
            
            # Look for consistent daily hours
            if len(descriptions) >= 7:  # Full week of hours
                confidence += 0.05  # Complete hours data
        
        return min(confidence, 0.3)  # Cap at 30% bonus
    
    def compare_categories(self, yelp_categories, google_types):
        """Compare categories/types between Yelp and Google Places"""
        if not yelp_categories or not google_types:
            return 0.0
        
        # Fitness-related keywords mapping
        fitness_keywords = {
            'gym': ['gym', 'fitness', 'health'],
            'fitness': ['gym', 'fitness', 'health', 'wellness'],
            'yoga': ['yoga', 'health', 'wellness'],
            'martial_arts': ['gym', 'health'],
            'pilates': ['health', 'wellness'],
            'boxing': ['gym', 'health'],
            'dance': ['health', 'wellness']
        }
        
        # Convert to lowercase for comparison
        google_types_lower = [t.lower() for t in google_types]
        
        # Check for fitness-related overlap
        for category in yelp_categories.split(','):
            category = category.strip().lower()
            if category in fitness_keywords:
                for keyword in fitness_keywords[category]:
                    if keyword in google_types_lower:
                        return 1.0  # Strong category match
        
        # Check for any gym/fitness/health overlap
        fitness_terms = ['gym', 'fitness', 'health', 'wellness']
        for term in fitness_terms:
            if term in google_types_lower:
                return 0.7  # Good category match
        
        return 0.0
    
    def compare_price_ranges(self, yelp_price, google_price_level):
        """Compare price ranges between Yelp and Google Places"""
        if not yelp_price or yelp_price == 'N/A' or google_price_level is None:
            return 0.0
        
        # Map Yelp price symbols to Google price levels
        yelp_to_google = {
            '$': 1,
            '$$': 2,
            '$$$': 3,
            '$$$$': 4
        }
        
        yelp_level = yelp_to_google.get(yelp_price)
        if yelp_level == google_price_level:
            return 1.0  # Exact price match
        elif yelp_level and abs(yelp_level - google_price_level) == 1:
            return 0.5  # Close price match
        
        return 0.0
    
    def token_based_name_similarity(self, name1, name2):
        """Phase 1: Enhanced token-based name similarity for gym matching"""
        if not name1 or not name2:
            return 0.0
        
        # Tokenize and clean names
        tokens1 = set(re.findall(r'\b\w+\b', name1.lower()))
        tokens2 = set(re.findall(r'\b\w+\b', name2.lower()))
        
        # Remove common gym words that don't add discriminative value
        common_words = {'gym', 'fitness', 'center', 'club', 'studio', 'training', 'academy', 'health', 'wellness'}
        tokens1 -= common_words
        tokens2 -= common_words
        
        # Calculate Jaccard similarity
        if not tokens1 and not tokens2:
            return 1.0  # Both empty after removing common words
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def semantic_name_similarity(self, name1, name2):
        """Phase 1: Semantic name similarity for fitness industry terms"""
        if not name1 or not name2:
            return 0.0
        
        # Fitness industry semantic mappings
        semantic_groups = {
            'crossfit': ['crossfit', 'cf', 'cross fit'],
            'yoga': ['yoga', 'yogi', 'namaste', 'zen'],
            'pilates': ['pilates', 'barre', 'reformer'],
            'boxing': ['boxing', 'box', 'fight', 'combat', 'mma', 'mixed martial arts'],
            'cycling': ['cycling', 'spin', 'cycle', 'bike', 'peloton'],
            'dance': ['dance', 'ballet', 'zumba', 'salsa'],
            'strength': ['strength', 'powerlifting', 'weights', 'iron', 'barbell'],
            'cardio': ['cardio', 'treadmill', 'running', 'marathon'],
            'martial_arts': ['karate', 'kung fu', 'taekwondo', 'judo', 'aikido', 'bjj', 'jiu jitsu']
        }
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Check for semantic matches
        for group, terms in semantic_groups.items():
            name1_has_term = any(term in name1_lower for term in terms)
            name2_has_term = any(term in name2_lower for term in terms)
            
            if name1_has_term and name2_has_term:
                return 0.8  # Strong semantic match
        
        return 0.0
    
    def estimate_coordinates_from_address(self, address):
        """Phase 1: Estimate coordinates from ZIP code + street for proximity scoring"""
        if not address:
            return None, None
        
        # Extract ZIP code
        zip_match = re.search(r'\b(\d{5})\b', address)
        if not zip_match:
            return None, None
        
        zipcode = zip_match.group(1)
        
        # NYC ZIP code coordinate mappings (major areas)
        nyc_zip_coords = {
            '10001': (40.7484, -73.9940),  # Midtown West
            '10002': (40.7156, -73.9898),  # Lower East Side
            '10003': (40.7310, -73.9898),  # East Village
            '10004': (40.7047, -74.0142),  # Financial District
            '10005': (40.7063, -74.0088),  # Financial District
            '10006': (40.7095, -74.0129),  # Financial District
            '10007': (40.7135, -74.0073),  # Financial District
            '10009': (40.7264, -73.9776),  # East Village
            '10010': (40.7390, -73.9826),  # Gramercy
            '10011': (40.7415, -74.0007),  # Chelsea
            '10012': (40.7259, -73.9997),  # SoHo
            '10013': (40.7195, -74.0055),  # Tribeca
            '10014': (40.7336, -74.0063),  # West Village
            '10016': (40.7452, -73.9764),  # Gramercy
            '10017': (40.7520, -73.9717),  # Midtown East
            '10018': (40.7549, -73.9934),  # Midtown West
            '10019': (40.7648, -73.9808),  # Midtown West
            '10020': (40.7589, -73.9774),  # Midtown
            '10021': (40.7685, -73.9540),  # Upper East Side
            '10022': (40.7574, -73.9718),  # Midtown East
            '10023': (40.7756, -73.9828),  # Upper West Side
            '10024': (40.7817, -73.9759),  # Upper West Side
            '10025': (40.7957, -73.9667),  # Upper West Side
            '10026': (40.7984, -73.9537),  # Harlem
            '10027': (40.8075, -73.9533),  # Harlem
            '10028': (40.7764, -73.9531),  # Upper East Side
            '10029': (40.7917, -73.9441),  # East Harlem
            '10030': (40.8180, -73.9425),  # Harlem
        }
        
        if zipcode in nyc_zip_coords:
            base_lat, base_lng = nyc_zip_coords[zipcode]
            
            # Add small random offset based on street number for more accuracy
            street_num_match = re.search(r'^(\d+)', address)
            if street_num_match:
                street_num = int(street_num_match.group(1))
                # Small offset based on street number (0.001 degree ≈ 100 meters)
                lat_offset = (street_num % 100) * 0.0001
                lng_offset = ((street_num // 100) % 100) * 0.0001
                return base_lat + lat_offset, base_lng + lng_offset
            
            return base_lat, base_lng
        
        return None, None
    
    def normalize_address(self, address):
        """Phase 1: Ultra-comprehensive address normalization"""
        if not address or address == 'N/A':
            return ''
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        
        # Comprehensive address abbreviations (40+ patterns)
        replacements = {
            # Street types
            ' street': ' st', ' st.': ' st',
            ' avenue': ' ave', ' ave.': ' ave', 
            ' boulevard': ' blvd', ' blvd.': ' blvd',
            ' road': ' rd', ' rd.': ' rd',
            ' drive': ' dr', ' dr.': ' dr',
            ' lane': ' ln', ' ln.': ' ln',
            ' place': ' pl', ' pl.': ' pl',
            ' court': ' ct', ' ct.': ' ct',
            ' circle': ' cir', ' cir.': ' cir',
            ' way': ' way', ' parkway': ' pkwy',
            ' highway': ' hwy', ' freeway': ' fwy',
            
            # Building types
            ' suite': ' ste', ' ste.': ' ste',
            ' apartment': ' apt', ' apt.': ' apt',
            ' floor': ' fl', ' fl.': ' fl',
            ' building': ' bldg', ' bldg.': ' bldg',
            ' room': ' rm', ' rm.': ' rm',
            ' unit': ' unit', ' #': ' unit ',
            
            # Ordinal numbers
            'first': '1st', 'second': '2nd', 'third': '3rd',
            'fourth': '4th', 'fifth': '5th', 'sixth': '6th',
            'seventh': '7th', 'eighth': '8th', 'ninth': '9th',
            'tenth': '10th', 'eleventh': '11th', 'twelfth': '12th',
            
            # Directions
            ' west ': ' w ', ' east ': ' e ', ' north ': ' n ', ' south ': ' s ',
            ' northwest ': ' nw ', ' northeast ': ' ne ',
            ' southwest ': ' sw ', ' southeast ': ' se ',
            
            # NYC specific
            'new york': 'ny', 'manhattan': 'ny',
            'brooklyn': 'ny', 'queens': 'ny', 'bronx': 'ny',
            'staten island': 'ny',
            
            # Common variations
            '&': 'and', 'avenue of the americas': '6th ave',
            'park avenue': 'park ave', 'madison avenue': 'madison ave',
            'broadway': 'broadway', 'wall street': 'wall st'
        }
        
        for full, abbrev in replacements.items():
            normalized = normalized.replace(full, abbrev)
        
        # Remove common punctuation and extra characters
        normalized = re.sub(r'[,\.](?!\d)', '', normalized)  # Remove commas/periods not followed by digits
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def normalize_phone(self, phone):
        """Enhanced phone number normalization with intelligence"""
        if not phone or phone == 'N/A' or phone == '':
            return ''
        
        # Extract only digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle US phone numbers (10 digits with optional country code)
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]
        elif len(digits) == 10:
            pass
        else:
            return digits  # Return as-is for international or unusual formats
            
        return digits
    
    def enhanced_phone_matching(self, yelp_phone, google_phone):
        """Enhanced phone number matching with partial matching intelligence"""
        if not yelp_phone or not google_phone or yelp_phone == 'N/A' or google_phone == 'N/A':
            return 0.0
        
        yelp_normalized = self.normalize_phone(yelp_phone)
        google_normalized = self.normalize_phone(google_phone)
        
        if not yelp_normalized or not google_normalized:
            return 0.0
        
        # Exact match - highest confidence
        if yelp_normalized == google_normalized:
            return 0.25  # Strong phone match bonus
        
        # Partial matching for different formats
        if len(yelp_normalized) >= 7 and len(google_normalized) >= 7:
            # Check last 7 digits (local number)
            yelp_local = yelp_normalized[-7:]
            google_local = google_normalized[-7:]
            
            if yelp_local == google_local:
                return 0.15  # Local number match
            
            # Check last 4 digits (exchange + number)
            if len(yelp_normalized) >= 4 and len(google_normalized) >= 4:
                yelp_suffix = yelp_normalized[-4:]
                google_suffix = google_normalized[-4:]
                
                if yelp_suffix == google_suffix:
                    return 0.08  # Partial phone match
        
        return 0.0
    
    def extract_domain(self, url):
        """Extract domain from URL for website matching"""
        if not url or url == 'N/A':
            return ''
        
        try:
            parsed = urlparse(url if url.startswith('http') else f'http://{url}')
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''
    
    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two coordinates in miles using Haversine formula"""
        if not all([lat1, lng1, lat2, lng2]):
            return float('inf')
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in miles
        r = 3959
        return c * r
    
    def fuzzy_match_gyms(self, yelp_gyms, google_gyms, confidence_threshold=0.35):
        """Advanced fuzzy matching with multiple confidence signals"""
        merged_gyms = []
        matched_google_indices = set()
        
        click.echo("🔗 Performing advanced gym matching...")
        
        for yelp_gym in yelp_gyms:
            best_match = None
            best_confidence = 0.0
            best_google_idx = -1
            
            # Normalize Yelp data for matching
            yelp_name_norm = yelp_gym['name'].lower().strip()
            yelp_address_norm = self.normalize_address(yelp_gym['address'])
            yelp_phone_norm = self.normalize_phone(yelp_gym['phone'])
            
            for idx, google_gym in enumerate(google_gyms):
                if idx in matched_google_indices:
                    continue
                
                # Normalize Google data for matching
                google_name_norm = google_gym['name'].lower().strip()
                google_address_norm = self.normalize_address(google_gym['address'])
                google_phone_norm = self.normalize_phone(google_gym['phone'])
                
                # Calculate confidence score using multiple signals
                confidence = 0.0
                
                # Enhanced name matching with chain detection
                yelp_name_clean = self.clean_gym_name(yelp_name_norm)
                google_name_clean = self.clean_gym_name(google_name_norm)
                
                # 1. Phase 1: Multi-level name similarity (30% weight - rebalanced)
                name_similarities = [
                    SequenceMatcher(None, yelp_name_norm, google_name_norm).ratio(),
                    SequenceMatcher(None, yelp_name_clean, google_name_clean).ratio(),
                    self.token_based_name_similarity(yelp_name_norm, google_name_norm),
                    self.semantic_name_similarity(yelp_name_clean, google_name_clean)
                ]
                name_similarity = max(name_similarities)
                confidence += name_similarity * 0.3
                
                # 2. Address similarity (25% weight - rebalanced) with enhanced matching
                address_bonus = 0
                if yelp_address_norm and google_address_norm:
                    # Full address similarity
                    address_similarity = SequenceMatcher(None, yelp_address_norm, google_address_norm).ratio()
                    address_bonus = address_similarity * 0.2
                    
                    # Street number exact match bonus
                    yelp_street_num = re.search(r'^\d+', yelp_address_norm)
                    google_street_num = re.search(r'^\d+', google_address_norm)
                    if yelp_street_num and google_street_num:
                        if yelp_street_num.group() == google_street_num.group():
                            address_bonus += 0.05  # Same street number bonus (reduced)
                    
                    # Street name partial matching
                    yelp_street = re.search(r'\d+\s+([^,]+)', yelp_address_norm)
                    google_street = re.search(r'\d+\s+([^,]+)', google_address_norm)
                    if yelp_street and google_street:
                        street_similarity = SequenceMatcher(None, yelp_street.group(1), google_street.group(1)).ratio()
                        if street_similarity > 0.8:
                            address_bonus += 0.03  # Similar street name bonus (reduced)
                
                confidence += address_bonus
                
                # 3. Phone number matching (15% weight - rebalanced) - now with complete Google phone data
                if yelp_phone_norm and google_phone_norm and len(yelp_phone_norm) >= 10 and len(google_phone_norm) >= 10:
                    if yelp_phone_norm == google_phone_norm:
                        confidence += 0.15  # Exact phone match (reduced)
                elif not google_phone_norm:  # Google missing phone is still common
                    pass  # No penalty for missing Google phone data
                
                # 4. Phase 1: Enhanced address intelligence with coordinate estimation (10% weight - rebalanced)
                address_intelligence_bonus = 0
                if yelp_address_norm and google_address_norm:
                    # ZIP code matching - strong location signal
                    yelp_zip = re.search(r'\b\d{5}\b', yelp_gym['address'])
                    google_zip = re.search(r'\b\d{5}\b', google_gym['address'])
                    if yelp_zip and google_zip and yelp_zip.group() == google_zip.group():
                        address_intelligence_bonus += 0.05  # Same ZIP code (reduced)
                    
                    # Floor/Suite similarity - same building indicator
                    yelp_suite = re.search(r'(ste|suite|fl|floor|apt|room|unit)\s*(\d+[a-z]?)', yelp_address_norm)
                    google_suite = re.search(r'(ste|suite|fl|floor|apt|room|unit)\s*(\d+[a-z]?)', google_address_norm)
                    if yelp_suite and google_suite and yelp_suite.group(2) == google_suite.group(2):
                        address_intelligence_bonus += 0.03  # Same suite/floor (reduced)
                    
                    # Coordinate-based proximity scoring (no geocoding API calls!)
                    yelp_coords = self.estimate_coordinates_from_address(yelp_gym['address'])
                    google_coords = google_gym.get('location', {})
                    if yelp_coords[0] and google_coords.get('lat'):
                        distance = self.calculate_distance(
                            yelp_coords[0], yelp_coords[1],
                            google_coords['lat'], google_coords['lng']
                        )
                        if distance < 0.1:  # Within 0.1 miles (160 meters)
                            address_intelligence_bonus += 0.05  # Very close proximity (reduced)
                        elif distance < 0.25:  # Within 0.25 miles (400 meters)
                            address_intelligence_bonus += 0.02  # Close proximity (reduced)
                
                confidence += address_intelligence_bonus
                
                # 5. Website domain matching (15% weight - rebalanced)
                website_bonus = 0
                yelp_domain = self.extract_domain(yelp_gym.get('url', ''))
                google_website = google_gym.get('website', '')
                if google_website and 'yelp.com' not in yelp_domain:
                    google_domain = self.extract_domain(google_website)
                    if yelp_domain and google_domain and yelp_domain == google_domain:
                        website_bonus = 0.15  # Same website domain (reduced)
                
                confidence += website_bonus
                
                # 6. Enhanced business hours comparison (5% weight - rebalanced)
                hours_bonus = 0
                if 'business_hours' in google_gym:
                    hours_similarity = self.compare_business_hours(
                        yelp_gym.get('hours'), google_gym['business_hours']
                    )
                    hours_bonus = hours_similarity * 0.33  # Reduced impact
                
                confidence += hours_bonus
                
                # 7. Phase 2: Semantic category mapping intelligence (10% weight)
                category_bonus = 0
                if 'types' in google_gym:
                    # Use enhanced semantic category mapping
                    semantic_similarity = self.semantic_category_mapping(
                        "gyms,fitness", google_gym['types']
                    )
                    category_bonus = semantic_similarity
                
                confidence += category_bonus
                
                # 8. Price range correlation (10% weight)
                price_bonus = 0
                if 'price' in yelp_gym and 'price' in google_gym:
                    price_similarity = self.compare_price_ranges(
                        yelp_gym['price'], google_gym.get('price_level')
                    )
                    price_bonus = price_similarity * 0.1
                
                confidence += price_bonus
                
                # Enhanced confidence boosters (reduced)
                if name_similarity > 0.9:  # Excellent name match
                    confidence += 0.05  # Reduced from 0.15
                elif name_similarity > 0.8:  # Very good name match  
                    confidence += 0.03  # Reduced from 0.1
                elif name_similarity > 0.7:  # Good name match
                    confidence += 0.02  # Reduced from 0.05
                
                # Chain/franchise detection bonus (reduced)
                chain_bonus = self.detect_chain_match(yelp_name_norm, google_name_norm)
                confidence += chain_bonus * 0.5  # Reduced impact
                
                # Review count correlation (reduced)
                review_bonus = self.compare_review_counts(
                    yelp_gym.get('review_count', 0), 
                    google_gym.get('review_count', 0)
                )
                confidence += review_bonus * 0.5  # Reduced impact
                
                # Website quality assessment (reduced)
                website_quality_bonus = self.assess_website_quality(
                    yelp_gym.get('url', ''),
                    google_gym.get('website', '')
                )
                confidence += website_quality_bonus * 0.5  # Reduced impact
                
                # Enhanced phone number intelligence (reduced)
                phone_intelligence_bonus = self.enhanced_phone_matching(
                    yelp_gym.get('phone', ''),
                    google_gym.get('phone', '')
                )
                confidence += phone_intelligence_bonus * 0.5  # Reduced impact
                
                # Phase 2: Enhanced Google Places Details integration (reduced)
                google_details_bonus = 0
                if google_gym.get('place_id'):
                    enhanced_details = self.google_service.get_enhanced_place_details(google_gym['place_id'])
                    if enhanced_details:
                        # Business completeness bonus (reduced)
                        google_details_bonus += enhanced_details.get('business_completeness', 0.0) * 0.25
                        
                        # Review sentiment bonus (reduced)
                        sentiment = enhanced_details.get('review_sentiment', 0.0)
                        if sentiment > 0.3:  # Positive sentiment
                            google_details_bonus += 0.01  # Reduced from 0.03
                        elif sentiment > 0.1:  # Neutral-positive sentiment
                            google_details_bonus += 0.005  # Reduced from 0.01
                        
                        # Rich profile indicators (reduced)
                        if enhanced_details.get('has_photos'):
                            google_details_bonus += 0.01  # Reduced from 0.02
                        if enhanced_details.get('has_editorial_summary'):
                            google_details_bonus += 0.01  # Reduced from 0.02
                
                confidence += google_details_bonus
                
                # Track best match for this Yelp gym
                if confidence > best_confidence and confidence >= confidence_threshold:
                    best_confidence = confidence
                    best_match = google_gym
                    best_google_idx = idx
            
            # Create merged gym entry
            if best_match and best_confidence >= confidence_threshold:
                # Merge data from both sources
                merged_gym = {
                    'name': yelp_gym['name'],  # Prefer Yelp name (usually more accurate)
                    'address': yelp_gym['address'],  # Prefer Yelp address (more detailed)
                    'phone': yelp_gym['phone'] if yelp_gym['phone'] != 'N/A' else best_match['phone'],
                    'rating': yelp_gym['rating'],  # Prefer Yelp rating
                    'review_count': yelp_gym['review_count'],
                    'price': yelp_gym['price'] if yelp_gym['price'] != 'N/A' else best_match['price'],
                    'url': yelp_gym['url'],  # Keep Yelp URL as primary
                    'source': 'Merged (Yelp + Google)',
                    'sources': ['Yelp', 'Google Places'],
                    'match_confidence': best_confidence,
                    # Add Google-specific data
                    'place_id': best_match.get('place_id'),
                    'location': best_match.get('location'),
                    'types': best_match.get('types'),
                    'open_now': best_match.get('open_now')
                }
                
                merged_gyms.append(merged_gym)
                matched_google_indices.add(best_google_idx)
                
            else:
                # No good match found, keep Yelp gym as-is
                yelp_only = yelp_gym.copy()
                yelp_only['sources'] = ['Yelp']
                yelp_only['match_confidence'] = 0.0
                merged_gyms.append(yelp_only)
        
        # Add unmatched Google gyms
        for idx, google_gym in enumerate(google_gyms):
            if idx not in matched_google_indices:
                google_only = google_gym.copy()
                google_only['sources'] = ['Google Places']
                google_only['match_confidence'] = 0.0
                merged_gyms.append(google_only)
        
        # Calculate merge statistics
        merged_count = sum(1 for gym in merged_gyms if gym.get('match_confidence', 0) > 0)
        total_unique = len(merged_gyms)
        
        avg_confidence = sum(gym.get('match_confidence', 0) for gym in merged_gyms if gym.get('match_confidence', 0) > 0) / max(merged_count, 1)
        click.echo(f"🔗 Merged {merged_count} gyms (avg confidence: {avg_confidence:.1%}), {total_unique} total unique gyms")
        
        return merged_gyms
    
    def clean_gym_name(self, name):
        """Clean gym name for better matching by removing common suffixes and prefixes"""
        if not name:
            return ''
        
        # Remove common business suffixes
        suffixes_to_remove = [
            r'\s+llc$', r'\s+inc$', r'\s+corp$', r'\s+ltd$',
            r'\s+gym$', r'\s+fitness$', r'\s+center$', r'\s+club$',
            r'\s+studio$', r'\s+training$', r'\s+academy$'
        ]
        
        cleaned = name.lower().strip()
        for suffix in suffixes_to_remove:
            cleaned = re.sub(suffix, '', cleaned)
        
        # Remove location suffixes like "- chelsea", "nyc", "manhattan"
        cleaned = re.sub(r'\s*-\s*[a-z\s]+$', '', cleaned)
        cleaned = re.sub(r'\s+(nyc|ny|manhattan|brooklyn|queens)$', '', cleaned)
        
        return cleaned.strip()
    
    def detect_chain_match(self, name1, name2):
        """Detect if two names represent the same chain/franchise"""
        # Common gym chains
        chains = [
            ['equinox'], ['planet fitness'], ['crunch'], ['ymca', 'y.m.c.a'],
            ['soulcycle'], ['crossfit'], ['blink'], ['la fitness'], ['24 hour fitness'],
            ['gold\'s gym', 'golds gym'], ['anytime fitness'], ['orange theory', 'orangetheory']
        ]
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        for chain_variants in chains:
            name1_has_chain = any(variant in name1_lower for variant in chain_variants)
            name2_has_chain = any(variant in name2_lower for variant in chain_variants)
            
            if name1_has_chain and name2_has_chain:
                return 0.2  # Strong chain match bonus
        
        return 0.0
    
    def detect_instagram_handle(self, gym_name, gym_url=""):
        """Basic Instagram handle detection"""
        # Simple heuristic - convert gym name to likely Instagram format
        handle_base = re.sub(r'[^a-zA-Z0-9]', '', gym_name.lower())
        possible_handles = [
            f"@{handle_base}",
            f"@{handle_base}gym",
            f"@{handle_base}fitness",
            f"@{gym_name.lower().replace(' ', '')}"
        ]
        
        # For MVP, return first possible handle
        # In full version, we'd verify these exist
        return possible_handles[0] if possible_handles else "N/A"
    
    def find_gyms(self, zipcode, radius=10, export_format=None, use_google=True, use_google_details=True):
        """Main function to find gyms by zipcode using multiple data sources"""
        click.echo(f"🏋️  Searching for gyms near {zipcode}...")
        
        # Convert zipcode to coordinates
        lat, lng = self.zipcode_to_coords(zipcode)
        if not lat or not lng:
            click.echo("❌ Could not find coordinates for zipcode")
            return
        
        click.echo(f"📍 Location: {lat:.4f}, {lng:.4f}")
        
        # Search multiple data sources
        all_gyms = []
        
        # Search Yelp
        click.echo("🔍 Searching Yelp...")
        yelp_gyms = self.search_yelp_gyms(lat, lng, radius)
        
        # Search Google Places if enabled and API key available
        google_gyms = []
        if use_google and self.google_api_key and self.google_api_key != "your_google_places_api_key_here":
            click.echo("🔍 Searching Google Places...")
            google_gyms = self.search_google_places_gyms(lat, lng, radius)
        
        # Perform advanced data merging if we have both sources
        if yelp_gyms and google_gyms:
            click.echo("🔗 Merging data from multiple sources...")
            all_gyms = self.fuzzy_match_gyms(yelp_gyms, google_gyms)
        else:
            # Fallback to simple combination if only one source
            all_gyms = yelp_gyms + google_gyms
            for gym in all_gyms:
                if 'sources' not in gym:
                    gym['sources'] = [gym['source']]
                gym['match_confidence'] = 0.0
        
        if not all_gyms:
            click.echo("❌ No gyms found from any source")
            return
        
        click.echo(f"✅ Found {len(yelp_gyms)} Yelp + {len(google_gyms)} Google Places = {len(all_gyms)} total gyms")
        
        # Enrich with Instagram handles
        click.echo("📱 Detecting Instagram handles...")
        for gym in all_gyms:
            if 'instagram' not in gym or gym['instagram'] == 'N/A':
                gym['instagram'] = self.detect_instagram_handle(gym['name'])
            if 'membership_fee' not in gym:
                gym['membership_fee'] = "TBD"  # Placeholder for future implementation
        
        # Display results
        self.display_results(all_gyms, zipcode, export_format)
    
    def export_to_csv(self, gyms, zipcode, filename=None):
        """Export gym results to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gyms_{zipcode}_{timestamp}.csv"
        
        headers = ["Name", "Address", "Phone", "Rating", "Review Count", "Instagram", "Membership Fee", "Source", "Confidence", "URL"]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for gym in gyms:
                row = [
                    gym['name'],
                    gym['address'],
                    gym['phone'],
                    gym['rating'],
                    gym['review_count'],
                    gym['instagram'],
                    gym['membership_fee'],
                    gym['source'],
                    gym.get('match_confidence', 0.0),
                    gym['url']
                ]
                writer.writerow(row)
        
        return filename

    def export_to_json(self, gyms, zipcode, filename=None):
        """Export gym results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gyms_{zipcode}_{timestamp}.json"
        
        export_data = {
            "search_info": {
                "zipcode": zipcode,
                "timestamp": datetime.now().isoformat(),
                "total_results": len(gyms)
            },
            "gyms": gyms
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        return filename

    def display_results(self, gyms, zipcode, export_format=None):
        """Display gym results in a formatted table and optionally export"""
        click.echo(f"\n🏋️  Found {len(gyms)} gyms near {zipcode}\n")
        
        # Prepare table data
        headers = ["Name", "Address", "Phone", "Rating", "Instagram", "Fee", "Source", "Confidence"]
        table_data = []
        
        for gym in gyms:
            confidence = gym.get('match_confidence', 0.0)
            confidence_display = f"{confidence:.0%}" if confidence > 0 else "N/A"
            
            row = [
                gym['name'][:30] + "..." if len(gym['name']) > 30 else gym['name'],
                gym['address'][:40] + "..." if len(gym['address']) > 40 else gym['address'],
                gym['phone'],
                f"{gym['rating']}" + (f" ({gym['review_count']})" if gym['review_count'] else ""),
                gym['instagram'],
                gym['membership_fee'],
                gym['source'],
                confidence_display
            ]
            table_data.append(row)
        
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Export if requested
        if export_format:
            if export_format.lower() == 'csv':
                filename = self.export_to_csv(gyms, zipcode)
                click.echo(f"\n📁 Results exported to: {filename}")
            elif export_format.lower() == 'json':
                filename = self.export_to_json(gyms, zipcode)
                click.echo(f"\n📁 Results exported to: {filename}")
            elif export_format.lower() == 'both':
                csv_file = self.export_to_csv(gyms, zipcode)
                json_file = self.export_to_json(gyms, zipcode)
                click.echo(f"\n📁 Results exported to:")
                click.echo(f"   CSV: {csv_file}")
                click.echo(f"   JSON: {json_file}")

@click.command()
@click.option('--zipcode', '-z', required=True, help='ZIP code to search around')
@click.option('--radius', '-r', default=10, help='Search radius in miles (default: 10)')
@click.option('--export', '-e', type=click.Choice(['csv', 'json', 'both'], case_sensitive=False), help='Export results to file (csv, json, or both)')
@click.option('--no-google', is_flag=True, help='Disable Google Places API (use only Yelp)')
def main(zipcode, radius, export, no_google):
    """GymIntel - Find gyms, Instagram handles, and membership fees by zipcode"""
    finder = GymFinder()
    finder.find_gyms(zipcode, radius, export, use_google=not no_google)

if __name__ == '__main__':
    main()