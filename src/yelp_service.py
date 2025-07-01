#!/usr/bin/env python3
"""
Yelp API Service - Gym and Fitness Business Discovery
"""

import os
import requests
import click
from dotenv import load_dotenv

load_dotenv()


class YelpService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('YELP_API_KEY')
        
    def search_gyms(self, lat, lng, radius_miles=10):
        """Search for gyms using Yelp API"""
        if not self.api_key:
            click.echo("Warning: YELP_API_KEY not found in .env file")
            return []
        
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
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
    
    def get_business_details(self, business_id):
        """Get detailed information for a specific Yelp business"""
        if not self.api_key:
            return {}
        
        url = f"https://api.yelp.com/v3/businesses/{business_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            return {
                'hours': data.get('hours', []),
                'photos': data.get('photos', []),
                'categories': data.get('categories', []),
                'location': data.get('location', {}),
                'transactions': data.get('transactions', [])
            }
            
        except requests.exceptions.RequestException:
            return {}


if __name__ == "__main__":
    # Test the Yelp service
    yelp = YelpService()
    gyms = yelp.search_gyms(40.7484, -73.9940, 2)
    
    print(f"Found {len(gyms)} gyms from Yelp:")
    for gym in gyms[:3]:  # Show first 3
        print(f"- {gym['name']}: {gym['address']}, Rating: {gym['rating']}")