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

load_dotenv()

class GymFinder:
    def __init__(self):
        self.yelp_api_key = os.getenv('YELP_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_PLACES_API_KEY')
        
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
        if not self.yelp_api_key:
            click.echo("Warning: YELP_API_KEY not found in .env file")
            return []
        
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {self.yelp_api_key}"}
        
        params = {
            "latitude": lat,
            "longitude": lng,
            "categories": "gyms,fitness",
            "radius": int(radius_miles * 1609.34),  # Convert miles to meters
            "limit": 50,
            "sort_by": "distance"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            gyms = []
            for business in data.get('businesses', []):
                gym = {
                    'name': business.get('name'),
                    'address': ', '.join(business.get('location', {}).get('display_address', [])),
                    'phone': business.get('display_phone', 'N/A'),
                    'rating': business.get('rating', 'N/A'),
                    'review_count': business.get('review_count', 0),
                    'price': business.get('price', 'N/A'),
                    'url': business.get('url', ''),
                    'source': 'Yelp'
                }
                gyms.append(gym)
            
            return gyms
            
        except requests.exceptions.RequestException as e:
            click.echo(f"Error searching Yelp: {e}")
            return []
    
    def search_google_places_gyms(self, lat, lng, radius_miles=10):
        """Search for gyms using Google Places API with enhanced details"""
        if not self.google_api_key:
            click.echo("Warning: GOOGLE_PLACES_API_KEY not found in .env file")
            return []
        
        # Convert miles to meters (Google Places uses meters)
        radius_meters = int(radius_miles * 1609.34)
        
        # New Google Places API endpoint
        search_url = "https://places.googleapis.com/v1/places:searchNearby"
        
        # New API uses POST with JSON body
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.google_api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.internationalPhoneNumber,places.rating,places.userRatingCount,places.priceLevel,places.websiteUri,places.location,places.types,places.currentOpeningHours,places.regularOpeningHours"
        }
        
        payload = {
            "includedTypes": ["gym"],
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng
                    },
                    "radius": radius_meters
                }
            },
            "maxResultCount": 20  # New API allows up to 20 per request
        }
        
        try:
            gyms = []
            
            response = requests.post(search_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for place in data.get('places', []):
                # Extract data from new API format
                display_name = place.get('displayName', {})
                location = place.get('location', {})
                opening_hours = place.get('currentOpeningHours', place.get('regularOpeningHours', {}))
                
                gym = {
                    'name': display_name.get('text', 'Unknown'),
                    'address': place.get('formattedAddress', 'N/A'),
                    'phone': place.get('nationalPhoneNumber', place.get('internationalPhoneNumber', 'N/A')),
                    'rating': place.get('rating', 'N/A'),
                    'review_count': place.get('userRatingCount', 0),
                    'price': self._convert_google_price_level_new(place.get('priceLevel')),
                    'url': place.get('websiteUri', f"https://maps.google.com/?place_id={place.get('id')}"),
                    'source': 'Google Places',
                    'place_id': place.get('id'),
                    'location': {
                        'lat': location.get('latitude'),
                        'lng': location.get('longitude')
                    },
                    'types': place.get('types', []),
                    'open_now': opening_hours.get('openNow'),
                    'business_hours': opening_hours,
                    'website': place.get('websiteUri', ''),
                    'google_url': f"https://maps.google.com/?place_id={place.get('id')}",
                    'price_level': self._map_price_level_new(place.get('priceLevel'))
                }
                gyms.append(gym)
            
            return gyms
            
        except requests.exceptions.RequestException as e:
            click.echo(f"Error searching Google Places (New API): {e}")
            return []
    
    def _convert_google_price_level(self, price_level):
        """Convert Google Places price level to readable format"""
        if price_level is None:
            return 'N/A'
        
        price_map = {
            0: 'Free',
            1: '$',
            2: '$$', 
            3: '$$$',
            4: '$$$$'
        }
        return price_map.get(price_level, 'N/A')
    
    def _convert_google_price_level_new(self, price_level):
        """Convert Google Places (New) price level to readable format"""
        if not price_level:
            return 'N/A'
        
        # New API uses string values
        price_map = {
            'PRICE_LEVEL_FREE': 'Free',
            'PRICE_LEVEL_INEXPENSIVE': '$',
            'PRICE_LEVEL_MODERATE': '$$', 
            'PRICE_LEVEL_EXPENSIVE': '$$$',
            'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$'
        }
        return price_map.get(price_level, 'N/A')
    
    def _map_price_level_new(self, price_level):
        """Map new API price level to numeric for comparison"""
        if not price_level:
            return None
        
        price_map = {
            'PRICE_LEVEL_FREE': 0,
            'PRICE_LEVEL_INEXPENSIVE': 1,
            'PRICE_LEVEL_MODERATE': 2,
            'PRICE_LEVEL_EXPENSIVE': 3,
            'PRICE_LEVEL_VERY_EXPENSIVE': 4
        }
        return price_map.get(price_level)
    
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
        """Compare business hours between Yelp and Google Places"""
        if not yelp_hours or not google_hours:
            return 0.0
        
        # This is a simplified comparison - in practice, you'd parse actual hours
        # For now, we'll check if both have hours data as a basic signal
        if isinstance(google_hours, dict) and google_hours.get('periods'):
            return 0.5  # Basic match - both have hours data
        
        return 0.0
    
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
    
    def normalize_address(self, address):
        """Normalize address for better matching"""
        if not address or address == 'N/A':
            return ''
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        
        # Common address abbreviations - more comprehensive
        replacements = {
            ' street': ' st', ' st.': ' st',
            ' avenue': ' ave', ' ave.': ' ave', 
            ' boulevard': ' blvd', ' blvd.': ' blvd',
            ' road': ' rd', ' rd.': ' rd',
            ' drive': ' dr', ' dr.': ' dr',
            ' lane': ' ln', ' ln.': ' ln',
            ' place': ' pl', ' pl.': ' pl',
            ' suite': ' ste', ' ste.': ' ste',
            ' apartment': ' apt', ' apt.': ' apt',
            ' floor': ' fl', ' fl.': ' fl',
            'first': '1st', 'second': '2nd', 'third': '3rd',
            'fourth': '4th', 'fifth': '5th', 'sixth': '6th',
            'seventh': '7th', 'eighth': '8th', 'ninth': '9th',
            ' west ': ' w ', ' east ': ' e ', ' north ': ' n ', ' south ': ' s ',
            'new york': 'ny', 'manhattan': 'ny'
        }
        
        for full, abbrev in replacements.items():
            normalized = normalized.replace(full, abbrev)
        
        # Remove common punctuation and extra characters
        normalized = re.sub(r'[,\.](?!\d)', '', normalized)  # Remove commas/periods not followed by digits
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def normalize_phone(self, phone):
        """Normalize phone number for exact matching"""
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
    
    def fuzzy_match_gyms(self, yelp_gyms, google_gyms, confidence_threshold=0.4):
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
                
                # 1. Name similarity (40% weight) - try both original and cleaned names
                name_similarity = max(
                    SequenceMatcher(None, yelp_name_norm, google_name_norm).ratio(),
                    SequenceMatcher(None, yelp_name_clean, google_name_clean).ratio()
                )
                confidence += name_similarity * 0.4
                
                # 2. Address similarity (30% weight) with enhanced matching
                address_bonus = 0
                if yelp_address_norm and google_address_norm:
                    # Full address similarity
                    address_similarity = SequenceMatcher(None, yelp_address_norm, google_address_norm).ratio()
                    address_bonus = address_similarity * 0.3
                    
                    # Street number exact match bonus
                    yelp_street_num = re.search(r'^\d+', yelp_address_norm)
                    google_street_num = re.search(r'^\d+', google_address_norm)
                    if yelp_street_num and google_street_num:
                        if yelp_street_num.group() == google_street_num.group():
                            address_bonus += 0.15  # Same street number bonus
                    
                    # Street name partial matching
                    yelp_street = re.search(r'\d+\s+([^,]+)', yelp_address_norm)
                    google_street = re.search(r'\d+\s+([^,]+)', google_address_norm)
                    if yelp_street and google_street:
                        street_similarity = SequenceMatcher(None, yelp_street.group(1), google_street.group(1)).ratio()
                        if street_similarity > 0.8:
                            address_bonus += 0.1  # Similar street name bonus
                
                confidence += address_bonus
                
                # 3. Phone number matching (20% weight) - now with complete Google phone data
                if yelp_phone_norm and google_phone_norm and len(yelp_phone_norm) >= 10 and len(google_phone_norm) >= 10:
                    if yelp_phone_norm == google_phone_norm:
                        confidence += 0.2  # Exact phone match
                elif not google_phone_norm:  # Google missing phone is still common
                    pass  # No penalty for missing Google phone data
                
                # 4. Coordinate proximity (15% weight) - enhanced with geocoding
                coordinate_bonus = 0
                if 'location' in google_gym and google_gym['location'] and 'lat' in google_gym['location']:
                    google_lat = google_gym['location']['lat']
                    google_lng = google_gym['location']['lng']
                    
                    # Geocode Yelp address for comparison
                    yelp_lat, yelp_lng = self.geocode_address(yelp_gym['address'])
                    if yelp_lat and yelp_lng:
                        distance = self.calculate_distance(yelp_lat, yelp_lng, google_lat, google_lng)
                        if distance < 0.05:  # Within 0.05 miles (about 250 feet)
                            coordinate_bonus = 0.15
                        elif distance < 0.1:  # Within 0.1 miles
                            coordinate_bonus = 0.1
                        elif distance < 0.2:  # Within 0.2 miles
                            coordinate_bonus = 0.05
                
                confidence += coordinate_bonus
                
                # 5. Website domain matching (25% weight)
                website_bonus = 0
                yelp_domain = self.extract_domain(yelp_gym.get('url', ''))
                google_website = google_gym.get('website', '')
                if google_website and 'yelp.com' not in yelp_domain:
                    google_domain = self.extract_domain(google_website)
                    if yelp_domain and google_domain and yelp_domain == google_domain:
                        website_bonus = 0.25  # Same website domain
                
                confidence += website_bonus
                
                # 6. Business hours comparison (15% weight)
                hours_bonus = 0
                if 'business_hours' in google_gym:
                    hours_similarity = self.compare_business_hours(
                        yelp_gym.get('hours'), google_gym['business_hours']
                    )
                    hours_bonus = hours_similarity * 0.15
                
                confidence += hours_bonus
                
                # 7. Category/type alignment (10% weight)
                category_bonus = 0
                if 'types' in google_gym:
                    category_similarity = self.compare_categories(
                        "gyms,fitness", google_gym['types']
                    )
                    category_bonus = category_similarity * 0.1
                
                confidence += category_bonus
                
                # 8. Price range correlation (10% weight)
                price_bonus = 0
                if 'price' in yelp_gym and 'price' in google_gym:
                    price_similarity = self.compare_price_ranges(
                        yelp_gym['price'], google_gym.get('price_level')
                    )
                    price_bonus = price_similarity * 0.1
                
                confidence += price_bonus
                
                # Enhanced confidence boosters
                if name_similarity > 0.9:  # Excellent name match
                    confidence += 0.15
                elif name_similarity > 0.8:  # Very good name match  
                    confidence += 0.1
                elif name_similarity > 0.7:  # Good name match
                    confidence += 0.05
                
                # Chain/franchise detection bonus
                chain_bonus = self.detect_chain_match(yelp_name_norm, google_name_norm)
                confidence += chain_bonus
                
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