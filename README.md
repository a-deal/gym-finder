# GymIntel - Comprehensive Gym Discovery Platform

Find every gym in a metropolitan area with Instagram handles, membership fees, and contact information.

## Features

- 🏋️ Find gyms by zipcode
- 📍 Configurable search radius
- 📱 Instagram handle detection
- 💰 Membership fee discovery
- 📞 Contact information extraction
- 🌐 Multi-source data aggregation

## Installation

```bash
pip install -r requirements.txt
```

## Setup

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - Yelp API Key (get from https://www.yelp.com/developers)
   - Google Places API Key (optional, for enhanced coverage)

## Usage

Basic search:
```bash
python gym_finder.py --zipcode 90210
```

Custom radius:
```bash
python gym_finder.py --zipcode 90210 --radius 15
```

## Roadmap

- [ ] Google Places API integration
- [ ] OpenStreetMap data source
- [ ] Instagram handle verification
- [ ] Membership fee web scraping
- [ ] Social media metrics
- [ ] Equipment/amenity detection
- [ ] Class schedule extraction
- [ ] Review sentiment analysis

## Data Sources

**Current:**
- Yelp Fusion API

**Planned:**
- Google Places API
- OpenStreetMap Overpass API
- Facebook Places Graph API
- Instagram Basic Display API
- Mindbody API
- ClassPass API
- Strava API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request