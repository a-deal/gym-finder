#!/usr/bin/env python3
"""
New Google Places API implementation for testing
"""

import click
import requests


def search_google_places_gyms_new(api_key, lat, lng, radius_miles=10):
    """Search for gyms using Google Places API (New) with enhanced details"""
    if not api_key:
        click.echo("Warning: GOOGLE_PLACES_API_KEY not found")
        return []

    # Convert miles to meters (Google Places uses meters)
    radius_meters = int(radius_miles * 1609.34)

    # New Google Places API endpoint
    search_url = "https://places.googleapis.com/v1/places:searchNearby"

    # New API uses POST with JSON body
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.internationalPhoneNumber,places.rating,places.userRatingCount,places.priceLevel,places.websiteUri,places.location,places.types,places.currentOpeningHours,places.regularOpeningHours",
    }

    payload = {
        "includedTypes": ["gym"],
        "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius_meters}},
        "maxResultCount": 20,  # New API allows up to 20 per request
    }

    try:
        gyms = []

        response = requests.post(search_url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()

        for place in data.get("places", []):
            # Extract data from new API format
            display_name = place.get("displayName", {})
            location = place.get("location", {})
            opening_hours = place.get("currentOpeningHours", place.get("regularOpeningHours", {}))

            gym = {
                "name": display_name.get("text", "Unknown"),
                "address": place.get("formattedAddress", "N/A"),
                "phone": place.get("nationalPhoneNumber", place.get("internationalPhoneNumber", "N/A")),
                "rating": place.get("rating", "N/A"),
                "review_count": place.get("userRatingCount", 0),
                "price": convert_google_price_level_new(place.get("priceLevel")),
                "url": place.get("websiteUri", f"https://maps.google.com/?place_id={place.get('id')}"),
                "source": "Google Places (New)",
                "place_id": place.get("id"),
                "location": {"lat": location.get("latitude"), "lng": location.get("longitude")},
                "types": place.get("types", []),
                "open_now": opening_hours.get("openNow"),
                "business_hours": opening_hours,
                "website": place.get("websiteUri", ""),
                "google_url": f"https://maps.google.com/?place_id={place.get('id')}",
                "price_level": map_price_level_new(place.get("priceLevel")),
            }
            gyms.append(gym)

        return gyms

    except requests.exceptions.RequestException as e:
        click.echo(f"Error searching Google Places (New API): {e}")
        return []


def convert_google_price_level_new(price_level):
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


def map_price_level_new(price_level):
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


if __name__ == "__main__":
    # Test the new API
    import os

    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    gyms = search_google_places_gyms_new(api_key, 40.7484, -73.9940, 2)

    print(f"Found {len(gyms)} gyms with New API:")
    for gym in gyms[:3]:  # Show first 3
        print(f"- {gym['name']}: {gym['address']}, Phone: {gym['phone']}, Website: {gym['website']}")
