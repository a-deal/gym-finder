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
    
    def find_gyms(self, zipcode, radius=10):
        """Main function to find gyms by zipcode"""
        click.echo(f"🏋️  Searching for gyms near {zipcode}...")
        
        # Convert zipcode to coordinates
        lat, lng = self.zipcode_to_coords(zipcode)
        if not lat or not lng:
            click.echo("❌ Could not find coordinates for zipcode")
            return
        
        click.echo(f"📍 Location: {lat:.4f}, {lng:.4f}")
        
        # Search Yelp for gyms
        gyms = self.search_yelp_gyms(lat, lng, radius)
        
        if not gyms:
            click.echo("❌ No gyms found")
            return
        
        # Enrich with Instagram handles
        click.echo("🔍 Detecting Instagram handles...")
        for gym in gyms:
            gym['instagram'] = self.detect_instagram_handle(gym['name'])
            gym['membership_fee'] = "TBD"  # Placeholder for future implementation
        
        # Display results
        self.display_results(gyms, zipcode)
    
    def export_to_csv(self, gyms, zipcode, filename=None):
        """Export gym results to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gyms_{zipcode}_{timestamp}.csv"
        
        headers = ["Name", "Address", "Phone", "Rating", "Review Count", "Instagram", "Membership Fee", "Source", "Yelp URL"]
        
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
                    gym['url']
                ]
                writer.writerow(row)
        
        return filename

    def display_results(self, gyms, zipcode):
        """Display gym results in a formatted table"""
        click.echo(f"\n🏋️  Found {len(gyms)} gyms near {zipcode}\n")
        
        # Prepare table data
        headers = ["Name", "Address", "Phone", "Rating", "Instagram", "Fee", "Source"]
        table_data = []
        
        for gym in gyms:
            row = [
                gym['name'][:30] + "..." if len(gym['name']) > 30 else gym['name'],
                gym['address'][:40] + "..." if len(gym['address']) > 40 else gym['address'],
                gym['phone'],
                f"{gym['rating']}" + (f" ({gym['review_count']})" if gym['review_count'] else ""),
                gym['instagram'],
                gym['membership_fee'],
                gym['source']
            ]
            table_data.append(row)
        
        click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))

@click.command()
@click.option('--zipcode', '-z', required=True, help='ZIP code to search around')
@click.option('--radius', '-r', default=10, help='Search radius in miles (default: 10)')
def main(zipcode, radius):
    """GymIntel - Find gyms, Instagram handles, and membership fees by zipcode"""
    finder = GymFinder()
    finder.find_gyms(zipcode, radius)

if __name__ == '__main__':
    main()