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
from urllib.parse import quote
import ssl
import certifi
import csv
import json
from datetime import datetime

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
        """Search for gyms using Google Places API"""
        if not self.google_api_key:
            click.echo("Warning: GOOGLE_PLACES_API_KEY not found in .env file")
            return []
        
        # Convert miles to meters (Google Places uses meters)
        radius_meters = int(radius_miles * 1609.34)
        
        # First, search for nearby gyms
        search_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        
        params = {
            "location": f"{lat},{lng}",
            "radius": radius_meters,
            "type": "gym",
            "key": self.google_api_key
        }
        
        try:
            gyms = []
            
            # Google Places returns up to 60 results across 3 pages
            next_page_token = None
            pages_fetched = 0
            max_pages = 3
            
            while pages_fetched < max_pages:
                if next_page_token:
                    params["pagetoken"] = next_page_token
                elif pages_fetched > 0:
                    break
                    
                response = requests.get(search_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') != 'OK' and data.get('status') != 'ZERO_RESULTS':
                    click.echo(f"Google Places API error: {data.get('status')}")
                    break
                
                for place in data.get('results', []):
                    gym = {
                        'name': place.get('name'),
                        'address': place.get('vicinity'),
                        'phone': 'N/A',  # Basic version without place details
                        'rating': place.get('rating', 'N/A'),
                        'review_count': place.get('user_ratings_total', 0),
                        'price': self._convert_google_price_level(place.get('price_level')),
                        'url': f"https://maps.google.com/?place_id={place.get('place_id')}",
                        'source': 'Google Places',
                        'place_id': place.get('place_id'),
                        'location': place.get('geometry', {}).get('location', {}),
                        'types': place.get('types', []),
                        'open_now': place.get('opening_hours', {}).get('open_now') if place.get('opening_hours') else None
                    }
                    gyms.append(gym)
                
                # Check for next page
                next_page_token = data.get('next_page_token')
                pages_fetched += 1
                
                # Google requires a delay between paginated requests
                if next_page_token and pages_fetched < max_pages:
                    time.sleep(2)
            
            return gyms
            
        except requests.exceptions.RequestException as e:
            click.echo(f"Error searching Google Places: {e}")
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
    
    def find_gyms(self, zipcode, radius=10, export_format=None, use_google=True):
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
        
        # Combine results (simple concatenation for now)
        all_gyms = yelp_gyms + google_gyms
        
        if not all_gyms:
            click.echo("❌ No gyms found from any source")
            return
        
        # Add source metadata
        for gym in all_gyms:
            if 'sources' not in gym:
                gym['sources'] = [gym['source']]
            gym['match_confidence'] = 0.0  # No merging in this version
        
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