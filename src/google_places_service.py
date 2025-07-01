#!/usr/bin/env python3
"""
Google Places API Service - Gym and Fitness Business Discovery
"""

import os

import click
import requests
from dotenv import load_dotenv

load_dotenv()


class GooglePlacesService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("GOOGLE_PLACES_API_KEY")

    def _validate_place_data(self, place):
        """Validate and sanitize place data from Google Places API.

        Ensures data integrity by validating required fields, sanitizing input,
        and providing safe defaults for missing or invalid data specific to
        Google Places API (New) response format.

        Args:
            place (dict): Raw place data from Google Places API response

        Returns:
            dict: Validated and sanitized place data, or None if invalid

        Example:
            >>> service = GooglePlacesService()
            >>> valid_gym = service._validate_place_data(raw_places_data)
            >>> if valid_gym:
            ...     print(f"Validated: {valid_gym['name']} at {valid_gym['address']}")
        """
        if not isinstance(place, dict):
            return None

        # Required fields validation
        display_name = place.get("displayName", {})
        if not isinstance(display_name, dict) or not display_name.get("text"):
            return None

        # Validate location data
        location = place.get("location", {})
        if not isinstance(location, dict):
            location = {}

        # Validate numeric fields
        rating = place.get("rating")
        if rating is not None and not isinstance(rating, (int, float)):
            rating = "N/A"

        user_rating_count = place.get("userRatingCount", 0)
        if not isinstance(user_rating_count, int) or user_rating_count < 0:
            user_rating_count = 0

        # Validate opening hours
        opening_hours = place.get("currentOpeningHours", place.get("regularOpeningHours", {}))
        if not isinstance(opening_hours, dict):
            opening_hours = {}

        return {
            "name": str(display_name.get("text", "Unknown")).strip(),
            "address": str(place.get("formattedAddress", "N/A")).strip(),
            "phone": str(place.get("nationalPhoneNumber", place.get("internationalPhoneNumber", "N/A"))).strip(),
            "rating": rating,
            "review_count": user_rating_count,
            "price": self.convert_price_level(place.get("priceLevel")),
            "url": str(place.get("websiteUri", f"https://maps.google.com/?place_id={place.get('id', '')}")).strip(),
            "source": "Google Places (New)",
            "place_id": str(place.get("id", "")).strip(),
            "location": {"lat": location.get("latitude"), "lng": location.get("longitude")},
            "types": place.get("types", []) if isinstance(place.get("types"), list) else [],
            "open_now": opening_hours.get("openNow"),
            "business_hours": opening_hours,
            "website": str(place.get("websiteUri", "")).strip(),
            "google_url": f"https://maps.google.com/?place_id={place.get('id', '')}",
            "price_level": self.map_price_level(place.get("priceLevel")),
        }

    def search_gyms(self, lat, lng, radius_miles=10):
        """Search for gyms using Google Places API (New) with enhanced details"""
        if not self.api_key:
            click.echo("Warning: GOOGLE_PLACES_API_KEY not found in .env file")
            return []

        # Convert miles to meters (Google Places uses meters)
        radius_meters = int(radius_miles * 1609.34)

        # New Google Places API endpoint
        search_url = "https://places.googleapis.com/v1/places:searchNearby"

        # New API uses POST with JSON body
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.internationalPhoneNumber,places.rating,places.userRatingCount,places.priceLevel,places.websiteUri,places.location,places.types,places.currentOpeningHours,places.regularOpeningHours",
        }

        payload = {
            "includedTypes": ["gym"],
            "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius_meters}},
            "maxResultCount": 20,  # New API allows up to 20 per request
        }

        try:
            gyms = []

            response = requests.post(search_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Validate API response structure
            if not isinstance(data, dict):
                click.echo("Warning: Invalid JSON response from Google Places API")
                return []

            places = data.get("places", [])
            if not isinstance(places, list):
                click.echo("Warning: Invalid places data from Google Places API")
                return []

            for place in places:
                validated_gym = self._validate_place_data(place)
                if validated_gym:
                    gyms.append(validated_gym)

            return gyms

        except requests.exceptions.Timeout:
            click.echo("Error: Google Places API request timed out")
            return []
        except requests.exceptions.ConnectionError:
            click.echo("Error: Unable to connect to Google Places API")
            return []
        except requests.exceptions.HTTPError as e:
            click.echo(f"Error: Google Places API HTTP error {e.response.status_code}: {e}")
            return []
        except requests.exceptions.RequestException as e:
            click.echo(f"Error: Google Places API request failed: {e}")
            return []
        except (ValueError, KeyError) as e:
            click.echo(f"Error: Invalid response format from Google Places API: {e}")
            return []

    def convert_price_level(self, price_level):
        """Convert Google Places (New) price level to readable format"""
        if not price_level:
            return "N/A"

        # New API uses string values
        price_map = {
            "PRICE_LEVEL_FREE": "Free",
            "PRICE_LEVEL_INEXPENSIVE": "$",
            "PRICE_LEVEL_MODERATE": "$$",
            "PRICE_LEVEL_EXPENSIVE": "$$$",
            "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
        }
        return price_map.get(price_level, "N/A")

    def map_price_level(self, price_level):
        """Map new API price level to numeric for comparison"""
        if not price_level:
            return None

        price_map = {
            "PRICE_LEVEL_FREE": 0,
            "PRICE_LEVEL_INEXPENSIVE": 1,
            "PRICE_LEVEL_MODERATE": 2,
            "PRICE_LEVEL_EXPENSIVE": 3,
            "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        }
        return price_map.get(price_level)

    def get_place_details(self, place_id):
        """Get detailed information for a specific Google Place using legacy API"""
        if not place_id or not self.api_key:
            return {}

        details_url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_address,formatted_phone_number,website,opening_hours,price_level",
            "key": self.api_key,
        }

        try:
            response = requests.get(details_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK":
                return data.get("result", {})
            else:
                return {}

        except requests.exceptions.RequestException:
            return {}

    def get_enhanced_place_details(self, place_id):
        """Phase 2: Enhanced Google Places Details API integration"""
        if not place_id or not self.api_key:
            return {}

        # Use new Google Places API for enhanced details
        details_url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "displayName,formattedAddress,nationalPhoneNumber,websiteUri,regularOpeningHours,priceLevel,rating,userRatingCount,editorialSummary,reviews,photos",
        }

        try:
            response = requests.get(details_url, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()

            # Extract rich details for enhanced matching
            enhanced_details = {
                "has_reviews": len(data.get("reviews", [])) > 0,
                "has_editorial_summary": bool(data.get("editorialSummary")),
                "has_photos": len(data.get("photos", [])) > 0,
                "has_hours": bool(data.get("regularOpeningHours")),
                "has_website": bool(data.get("websiteUri")),
                "review_sentiment": self.analyze_review_sentiment(data.get("reviews", [])),
                "business_completeness": self.calculate_business_profile_completeness(data),
            }

            return enhanced_details

        except requests.exceptions.RequestException:
            return {}

    def analyze_review_sentiment(self, reviews):
        """Phase 2: Basic review sentiment analysis for confidence scoring"""
        if not reviews:
            return 0.0

        # Simple sentiment keywords for fitness businesses
        positive_keywords = ["great", "excellent", "amazing", "love", "recommend", "clean", "friendly", "helpful"]
        negative_keywords = ["bad", "terrible", "dirty", "rude", "expensive", "crowded", "broken"]

        total_sentiment = 0.0
        review_count = 0

        for review in reviews[:5]:  # Analyze first 5 reviews
            review_text = review.get("text", {}).get("text", "").lower()
            if not review_text:
                continue

            positive_score = sum(1 for keyword in positive_keywords if keyword in review_text)
            negative_score = sum(1 for keyword in negative_keywords if keyword in review_text)

            # Normalize sentiment (-1 to 1)
            if positive_score + negative_score > 0:
                sentiment = (positive_score - negative_score) / (positive_score + negative_score)
                total_sentiment += sentiment
                review_count += 1

        return total_sentiment / max(review_count, 1) if review_count > 0 else 0.0

    def calculate_business_profile_completeness(self, place_data):
        """Phase 2: Calculate Google Places profile completeness score"""
        completeness_score = 0.0

        # Score based on available data fields
        if place_data.get("displayName"):
            completeness_score += 0.1
        if place_data.get("formattedAddress"):
            completeness_score += 0.1
        if place_data.get("nationalPhoneNumber"):
            completeness_score += 0.1
        if place_data.get("websiteUri"):
            completeness_score += 0.15
        if place_data.get("regularOpeningHours"):
            completeness_score += 0.1
        if place_data.get("photos"):
            completeness_score += 0.1
        if place_data.get("reviews"):
            completeness_score += 0.1
        if place_data.get("editorialSummary"):
            completeness_score += 0.05

        return min(completeness_score, 0.8)  # Cap at 80% completeness bonus


if __name__ == "__main__":
    # Test the Google Places service
    google = GooglePlacesService()
    gyms = google.search_gyms(40.7484, -73.9940, 2)

    print(f"Found {len(gyms)} gyms from Google Places:")
    for gym in gyms[:3]:  # Show first 3
        print(f"- {gym['name']}: {gym['address']}, Rating: {gym['rating']}")
