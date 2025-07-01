#!/usr/bin/env python3
"""
Yelp API Service - Gym and Fitness Business Discovery
"""

import os

import click
import requests
from dotenv import load_dotenv

load_dotenv()


class YelpService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("YELP_API_KEY")

    def _validate_business_data(self, business):
        """Validate and sanitize business data from Yelp API.

        Ensures data integrity by validating required fields, sanitizing input,
        and providing safe defaults for missing or invalid data.

        Args:
            business (dict): Raw business data from Yelp API response

        Returns:
            dict: Validated and sanitized business data, or None if invalid

        Example:
            >>> service = YelpService()
            >>> valid_gym = service._validate_business_data(raw_yelp_data)
            >>> if valid_gym:
            ...     print(f"Validated: {valid_gym['name']}")
        """
        if not isinstance(business, dict):
            return None

        # Required fields validation
        if not business.get("name"):
            return None

        # Sanitize location data
        location = business.get("location", {})
        if not isinstance(location, dict):
            location = {}

        display_address = location.get("display_address", [])
        if not isinstance(display_address, list):
            display_address = []

        # Validate numeric fields
        rating = business.get("rating")
        if rating is not None and not isinstance(rating, (int, float)):
            rating = "N/A"

        review_count = business.get("review_count", 0)
        if not isinstance(review_count, int) or review_count < 0:
            review_count = 0

        return {
            "name": str(business.get("name", "")).strip(),
            "address": ", ".join(str(addr) for addr in display_address),
            "phone": str(business.get("display_phone", "N/A")).strip(),
            "rating": rating,
            "review_count": review_count,
            "price": str(business.get("price", "N/A")).strip(),
            "url": str(business.get("url", "")).strip(),
            "source": "Yelp",
        }

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
            "sort_by": "distance",
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Validate API response structure
            if not isinstance(data, dict):
                click.echo("Warning: Invalid JSON response from Yelp API")
                return []

            businesses = data.get("businesses", [])
            if not isinstance(businesses, list):
                click.echo("Warning: Invalid businesses data from Yelp API")
                return []

            gyms = []
            for business in businesses:
                validated_gym = self._validate_business_data(business)
                if validated_gym:
                    gyms.append(validated_gym)

            return gyms

        except requests.exceptions.Timeout:
            click.echo("Error: Yelp API request timed out")
            return []
        except requests.exceptions.ConnectionError:
            click.echo("Error: Unable to connect to Yelp API")
            return []
        except requests.exceptions.HTTPError as e:
            click.echo(f"Error: Yelp API HTTP error {e.response.status_code}: {e}")
            return []
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: Yelp API request failed: {e}")
            return []
        except (ValueError, KeyError) as e:
            click.echo(f"Error: Invalid response format from Yelp API: {e}")
            return []

    def get_business_details(self, business_id):
        """Get detailed information for a specific Yelp business"""
        if not self.api_key:
            return {}

        url = f"https://api.yelp.com/v3/businesses/{business_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            return {
                "hours": data.get("hours", []),
                "photos": data.get("photos", []),
                "categories": data.get("categories", []),
                "location": data.get("location", {}),
                "transactions": data.get("transactions", []),
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
