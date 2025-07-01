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
from .yelp_service import YelpService
from .google_places_service import GooglePlacesService

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
    
    def geocode_address(self, address):
        """Geocode an address to get coordinates"""
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
        
        yelp_lower = yelp_categories.lower()
        google_lower = [t.lower() for t in google_types]
        
        for category, keywords in fitness_keywords.items():
            if category in yelp_lower:
                if any(keyword in google_lower for keyword in keywords):
                    return 0.8  # High confidence match
        
        return 0.0

    def compare_price_ranges(self, yelp_price, google_price_level):
        """Compare price ranges between Yelp and Google Places"""
        if not yelp_price or google_price_level is None:
            return 0.0
        
        # Map Yelp price symbols to Google's 0-4 scale
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

    def extract_domain(self, url):
        """Extract domain from URL for website matching"""
        if not url or url == 'N/A':
            return ''
        
        try:
            parsed = urlparse(url if url.startswith('http') else f'http://{url}')
            domain = parsed.netloc.lower()
            # Remove www prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''

    def clean_gym_name(self, name):
        """Clean gym name for better matching"""
        if not name:
            return ''
        
        # Remove common gym suffixes and business designators
        cleaned = name.lower()
        
        # Remove business entity types
        entity_types = [
            r'\s+llc$', r'\s+inc$', r'\s+corp$', r'\s+ltd$', r'\s+co$',
            r'\s+company$', r'\s+enterprises$', r'\s+group$'
        ]
        
        for pattern in entity_types:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Remove location indicators
        location_patterns = [
            r'\s+\w+\s+location$', r'\s+\w+\s+branch$', r'\s+downtown$',
            r'\s+uptown$', r'\s+midtown$', r'\s+east\s+side$', r'\s+west\s+side$'
        ]
        
        for pattern in location_patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        return cleaned.strip()

    def calculate_distance(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two coordinates in miles"""
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

    def detect_chain_match(self, name1, name2):
        """Detect common gym chain/franchise matches"""
        if not name1 or not name2:
            return 0.0
        
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Common gym chains with variations
        chains = [
            ['planet fitness', 'planet'],
            ['la fitness', 'la fit'],
            ['24 hour fitness', '24hr fitness', '24 fitness'],
            ['anytime fitness', 'anytime'],
            ['gold\'s gym', 'golds gym', 'gold gym'],
            ['crunch fitness', 'crunch'],
            ['equinox', 'equinox fitness'],
            ['lifetime fitness', 'life time'],
            ['snap fitness', 'snap'],
            ['curves', 'curves fitness'],
            ['orange theory', 'orangetheory'],
            ['f45', 'f45 training'],
            ['crossfit', 'cf', 'cross fit'],
            ['soulcycle', 'soul cycle'],
            ['barry\'s bootcamp', 'barrys', 'barry'],
            ['pure barre', 'purebarre'],
            ['flywheel', 'flywheel sports']
        ]
        
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

    def fuzzy_match_gyms(self, yelp_gyms, google_gyms, confidence_threshold=0.35):
        """Advanced fuzzy matching with multiple confidence signals"""
        merged_gyms = []
        matched_google_indices = set()
        
        click.echo("🔗 Performing advanced gym matching...")
        
        for yelp_gym in yelp_gyms:
            best_match = None
            best_confidence = 0.0
            best_google_idx = -1
            
            # Normalize Yelp gym data
            yelp_name_norm = yelp_gym['name'].lower()
            yelp_address_norm = self.normalize_address(yelp_gym['address'])
            yelp_phone_norm = self.normalize_phone(yelp_gym.get('phone', ''))
            
            for idx, google_gym in enumerate(google_gyms):
                if idx in matched_google_indices:
                    continue
                
                # Normalize Google gym data
                google_name_norm = google_gym['name'].lower()
                google_address_norm = self.normalize_address(google_gym['address'])
                google_phone_norm = self.normalize_phone(google_gym.get('phone', ''))
                
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
                
                # 4. Enhanced confidence boosters (reduced)
                if name_similarity > 0.9:  # Excellent name match
                    confidence += 0.05  # Reduced from 0.15
                elif name_similarity > 0.8:  # Very good name match  
                    confidence += 0.03  # Reduced from 0.1
                elif name_similarity > 0.7:  # Good name match
                    confidence += 0.02  # Reduced from 0.05
                
                # Chain/franchise detection bonus (reduced)
                chain_bonus = self.detect_chain_match(yelp_name_norm, google_name_norm)
                confidence += chain_bonus * 0.5  # Reduced impact
                
                # Track best match for this Yelp gym
                if confidence > best_confidence and confidence >= confidence_threshold:
                    best_confidence = confidence
                    best_match = google_gym
                    best_google_idx = idx
            
            # Create merged gym entry
            if best_match and best_confidence >= confidence_threshold:
                merged_gym = self._merge_gym_records(yelp_gym, best_match, best_confidence)
                merged_gyms.append(merged_gym)
                matched_google_indices.add(best_google_idx)
                
                click.echo(f"✅ Matched: {yelp_gym['name'][:40]}... ↔ {best_match['name'][:40]}... (confidence: {best_confidence:.2f})")
            else:
                # No match found, add Yelp-only gym
                yelp_gym['match_confidence'] = 0.0
                yelp_gym['sources'] = ['Yelp']
                merged_gyms.append(yelp_gym)
                click.echo(f"➕ Yelp-only: {yelp_gym['name'][:50]}...")
        
        # Add remaining Google-only gyms
        for idx, google_gym in enumerate(google_gyms):
            if idx not in matched_google_indices:
                google_gym['match_confidence'] = 0.0
                google_gym['sources'] = ['Google Places']
                merged_gyms.append(google_gym)
                click.echo(f"➕ Google-only: {google_gym['name'][:50]}...")
        
        click.echo(f"🎯 Merging complete: {len(yelp_gyms)} Yelp + {len(google_gyms)} Google → {len(merged_gyms)} unique gyms")
        
        return merged_gyms

    def _merge_gym_records(self, yelp_gym, google_gym, confidence):
        """Merge individual gym records from different sources"""
        
        # Data source priority rules
        merged = {
            'name': yelp_gym['name'],  # Prefer Yelp names (usually more business-focused)
            'address': google_gym['address'] if len(google_gym['address']) > len(yelp_gym['address']) else yelp_gym['address'],
            'phone': yelp_gym['phone'] if yelp_gym['phone'] != 'N/A' else google_gym['phone'],
            'rating': google_gym['rating'] if google_gym['rating'] != 'N/A' else yelp_gym['rating'],
            'review_count': max(yelp_gym.get('review_count', 0), google_gym.get('review_count', 0)),
            'price': yelp_gym['price'] if yelp_gym['price'] != 'N/A' else google_gym['price'],
            'url': yelp_gym['url'],  # Prefer Yelp URLs for business pages
            'source': 'Merged (Yelp + Google)',
            'sources': ['Yelp', 'Google Places'],
            'match_confidence': round(confidence, 2),
            'instagram': yelp_gym.get('instagram', 'N/A'),
            'membership_fee': yelp_gym.get('membership_fee', 'TBD'),
            
            # Google-specific data
            'place_id': google_gym.get('place_id'),
            'location': google_gym.get('location', {}),
            'types': google_gym.get('types', []),
            'open_now': google_gym.get('open_now')
        }
        
        return merged

    def find_gyms(self, zipcode, radius=10, export_format=None, use_google=True, use_google_details=True):
        """Main function to find gyms by zipcode using multiple data sources"""
        click.echo(f"🏋️  Searching for gyms near {zipcode}...")
        
        # Convert zipcode to coordinates
        lat, lng = self.zipcode_to_coords(zipcode)
        if not lat or not lng:
            click.echo("❌ Could not find coordinates for zipcode")
            return
        
        click.echo(f"📍 Coordinates: {lat:.4f}, {lng:.4f}")
        
        # Search both Yelp and Google Places
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
                gym['instagram'] = self.detect_instagram_handle(gym['name'], gym.get('url', ''))
        
        # Sort by confidence score (for merged gyms) and rating
        all_gyms.sort(key=lambda x: (x.get('match_confidence', 0), 
                                   x['rating'] if x['rating'] != 'N/A' else 0), reverse=True)
        
        # Display results
        self.display_results(all_gyms)
        
        # Export if requested
        if export_format:
            self.export_results(all_gyms, zipcode, export_format)

    def display_results(self, gyms):
        """Display gym results in a formatted table"""
        if not gyms:
            click.echo("No gyms found.")
            return
        
        # Prepare data for tabulate
        headers = ['Name', 'Address', 'Phone', 'Rating', 'Reviews', 'Price', 'Source', 'Confidence', 'Instagram']
        rows = []
        
        for gym in gyms:
            # Truncate long names and addresses for display
            name = gym['name'][:30] + "..." if len(gym['name']) > 30 else gym['name']
            address = gym['address'][:40] + "..." if len(gym['address']) > 40 else gym['address']
            phone = gym.get('phone', 'N/A')
            rating = gym.get('rating', 'N/A')
            reviews = gym.get('review_count', 'N/A')
            price = gym.get('price', 'N/A')
            sources = ', '.join(gym.get('sources', [gym.get('source', 'Unknown')]))
            confidence = f"{gym.get('match_confidence', 0.0):.2f}" if gym.get('match_confidence', 0) > 0 else "-"
            instagram = gym.get('instagram', 'N/A')
            
            rows.append([name, address, phone, rating, reviews, price, sources, confidence, instagram])
        
        # Display table
        click.echo("\n" + "="*120)
        click.echo("🏋️  GYM SEARCH RESULTS")
        click.echo("="*120)
        click.echo(tabulate(rows, headers=headers, tablefmt="grid"))
        click.echo(f"\nTotal gyms found: {len(gyms)}")

    def export_results(self, gyms, zipcode, format='csv'):
        """Export results to CSV or JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == 'csv':
            filename = f"gyms_{zipcode}_{timestamp}.csv"
            self.export_to_csv(gyms, filename)
        elif format.lower() == 'json':
            filename = f"gyms_{zipcode}_{timestamp}.json"
            self.export_to_json(gyms, filename)
        else:
            click.echo(f"❌ Unsupported export format: {format}")
            return
        
        click.echo(f"✅ Results exported to {filename}")

    def export_to_csv(self, gyms, filename):
        """Export gym data to CSV file"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'address', 'phone', 'rating', 'review_count', 'price', 'url', 'sources', 'match_confidence', 'instagram', 'membership_fee']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for gym in gyms:
                # Prepare row data
                row = {
                    'name': gym.get('name', ''),
                    'address': gym.get('address', ''),
                    'phone': gym.get('phone', ''),
                    'rating': gym.get('rating', ''),
                    'review_count': gym.get('review_count', ''),
                    'price': gym.get('price', ''),
                    'url': gym.get('url', ''),
                    'sources': ', '.join(gym.get('sources', [])),
                    'match_confidence': gym.get('match_confidence', ''),
                    'instagram': gym.get('instagram', ''),
                    'membership_fee': gym.get('membership_fee', '')
                }
                writer.writerow(row)

    def export_to_json(self, gyms, filename):
        """Export gym data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(gyms, jsonfile, indent=2, ensure_ascii=False)


# CLI Interface
@click.command()
@click.option('--zipcode', '-z', required=True, help='ZIP code to search around')
@click.option('--radius', '-r', default=10, help='Search radius in miles (default: 10)')
@click.option('--export', '-e', help='Export format: csv or json')
@click.option('--no-google', is_flag=True, help='Skip Google Places search')
def main(zipcode, radius, export, no_google):
    """GymIntel - Find and compare gyms in your area"""
    
    gym_finder = GymFinder()
    
    # Check API keys
    if not gym_finder.yelp_api_key:
        click.echo("⚠️  Warning: YELP_API_KEY not found in .env file")
    
    if not no_google and not gym_finder.google_api_key:
        click.echo("⚠️  Warning: GOOGLE_PLACES_API_KEY not found in .env file")
    
    # Find gyms
    gym_finder.find_gyms(
        zipcode=zipcode,
        radius=radius,
        export_format=export,
        use_google=not no_google
    )


if __name__ == "__main__":
    main()