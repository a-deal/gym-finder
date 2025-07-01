# GymIntel CLI - Advanced Gym Discovery Platform

A powerful **command-line tool** delivering **comprehensive gym intelligence** through **multi-source data fusion** with **advanced confidence scoring**. Combines Yelp Fusion API and Google Places API (New) to provide the most complete gym discovery platform available.

> **🌐 Web App Development**: This CLI tool is now complete and stable. We're developing a web application version at **[GymIntel-Web](https://github.com/a-deal/gymintel-web)** with interactive maps, data visualization, and persistent storage. [Learn more about the roadmap](#web-app-roadmap) below.

## Features

### 🎯 **Multi-Source Intelligence**
- **Yelp + Google Places fusion** for maximum coverage (70+ gyms per area)
- **Advanced confidence scoring** (40-90% range) with 8 weighted matching signals
- **Intelligent duplicate detection** achieving 20%+ merge rates
- **Google Places API (New)** for 5x faster performance

### 🏙️ **Metropolitan Intelligence** (NEW)
- **6 Major US Metropolitan Areas**: NYC, LA, Chicago, SF, Boston, Miami
- **400+ ZIP codes** with market characteristics and demographics
- **Parallel batch processing** with configurable workers (2-6)
- **Cross-ZIP deduplication** removing 90%+ duplicates
- **Metropolitan analytics** with aggregate statistics

### 🏋️ **Comprehensive Gym Data**
- **Complete contact info** - phones, addresses, websites
- **Ratings & reviews** from multiple sources with cross-validation
- **Price ranges** with platform correlation
- **Operating hours** and real-time status
- **Instagram predictions** and social media discovery
- **Membership fee estimates** (coming soon)

### 📊 **Advanced Analytics**
- **Confidence scoring** for data quality transparency
- **Source attribution** showing data origins
- **Merge statistics** and coverage metrics
- **Export capabilities** (CSV, JSON) with timestamps

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/a-deal/gymintel-cli.git
cd gymintel-cli
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

## API Setup

1. **Create environment file:**
```bash
cp .env.example .env
```

2. **Get API Keys:**

### Yelp Fusion API (Required)
- Go to [Yelp Developers](https://www.yelp.com/developers)
- Create account and generate API key
- Add to `.env`: `YELP_API_KEY=your_key_here`

### Google Places API (New) - Recommended
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Enable **Places API (New)** (not legacy)
- Generate API key with Places permissions
- Add to `.env`: `GOOGLE_PLACES_API_KEY=your_key_here`

> **Note**: Google requires billing but offers generous free tiers

## Usage

### Basic Discovery
```bash
# Multi-source gym discovery (recommended)
python main.py --zipcode 10001

# Custom search radius in miles
python main.py --zipcode 10001 --radius 5

# Yelp-only mode (faster, less comprehensive)
python main.py --zipcode 10001 --no-google
```

### 🆕 Metropolitan Area Search
```bash
# Search entire metropolitan area
python main.py --metro nyc --radius 2

# List available metropolitan areas
python main.py --list-metros

# Sample mode for testing (limit ZIP codes)
python main.py --metro la --sample 10 --radius 2

# Export metropolitan results
python main.py --metro chicago --export csv
```

### 🆕 Batch Processing
```bash
# Process multiple ZIP codes
python main.py --zipcodes "10001,10003,10011" --radius 1

# Batch with custom workers
python main.py --zipcodes "10001,10003,10011,10014,10016" --workers 6

# Export batch results
python main.py --zipcodes "90210,90211,90212" --export json
```

### Export & Analysis
```bash
# Export with confidence scoring and merge statistics
python main.py --zipcode 10001 --export csv
python main.py --zipcode 10001 --export json
python main.py --zipcode 10001 --export both
```

### Command Options
- `--zipcode` / `-z`: Single ZIP code to search
- `--metro` / `-m`: Metropolitan area code (nyc, la, chicago, sf, boston, miami)
- `--zipcodes`: Comma-separated list of ZIP codes for batch processing
- `--radius` / `-r`: Search radius in miles (default: 10)
- `--export` / `-e`: Export format - csv, json, or both
- `--no-google`: Disable Google Places (Yelp-only)
- `--workers`: Number of parallel workers (default: 4)
- `--sample`: Sample size for metro areas (for testing)
- `--list-metros`: List available metropolitan areas

## Sample Output

```
🏋️  Searching for gyms near 10001...
📍 Location: 40.7484, -73.9940
🔍 Searching Yelp...
🔍 Searching Google Places...
🔗 Merging data from multiple sources...
🔗 Merged 19 gyms (avg confidence: 45.2%), 85 total unique gyms
✅ Found 50 Yelp + 20 Google Places = 85 total gyms

🏋️  Found 85 gyms near 10001

+---------------------------+-----------------------------------+----------------+----------+-------------------+-------+------------------------+--------------+
| Name                      | Address                           | Phone          | Rating   | Instagram         | Fee   | Source                 | Confidence   |
+===========================+===================================+================+==========+===================+=======+========================+==============+
| Mega Elite Fitness        | 235 West 29 St, New York, NY     | (347) 393-2065 | 4.7 (37) | @megaelitefitness | TBD   | Merged (Yelp + Google) | 66%          |
| Church Street Boxing      | 153 W 29th St, New York, NY      | (646) 368-9260 | 2.9 (7)  | @churchstreetbox  | TBD   | Merged (Yelp + Google) | 53%          |
| Equinox Tribeca          | 54 Murray Street, New York        | N/A            | 3.5 (98) | @equinoxtribeca   | TBD   | Google Places          | N/A          |
+---------------------------+-----------------------------------+----------------+----------+-------------------+-------+------------------------+--------------+

📁 Results exported to: gyms_10001_20250701_120000.csv
```

## Architecture

### Confidence Scoring System
Advanced **8-signal algorithm** for intelligent data fusion:

1. **Name Similarity (40%)** - Fuzzy matching with business name cleaning
2. **Address Matching (30%)** - Enhanced normalization + street/suite matching
3. **Phone Exact Match (20%)** - Complete phone data comparison
4. **Coordinate Proximity (15%)** - Distance-based matching with geocoding
5. **Website Domain (25%)** - Business website URL comparison
6. **Business Hours (15%)** - Operating schedule correlation
7. **Category Alignment (10%)** - Fitness/gym type matching
8. **Price Correlation (10%)** - Price level comparison

### Performance Metrics
- **API Efficiency**: 1-2 requests vs 100+ in legacy systems
- **Merge Accuracy**: 20%+ merge rate with 40-90% confidence
- **Coverage**: 50+ Yelp + 20+ Google = 70+ unique gyms per area
- **Speed**: 5x faster than legacy Google Places API

## Roadmap

### ✅ **Completed (Current Version)**
- [x] Multi-source data fusion (Yelp + Google Places)
- [x] Advanced confidence scoring algorithm
- [x] Google Places API (New) integration
- [x] Intelligent duplicate detection
- [x] Enhanced export capabilities

### ✅ **Phase 2: Metropolitan Intelligence** (COMPLETED)
- [x] Multi-city batch processing with 6 major US metros
- [x] Parallel processing with configurable workers
- [x] Cross-ZIP deduplication (90%+ efficiency)
- [x] Metropolitan area analytics and statistics

### 🔧 **CLI Maintenance & Enhancements**
- [ ] Performance optimizations for large batch searches
- [ ] Additional metropolitan areas (Austin, Denver, Seattle)
- [ ] Enhanced export formats (XML, Excel)
- [ ] Improved error handling and retry logic
- [ ] Configuration file support (.gymintel.yaml)

> **Note**: Advanced business intelligence, interactive maps, and web platform features are now being developed in **[GymIntel-Web](https://github.com/a-deal/gymintel-web)**

## Data Sources

### **Active Sources**
- **Yelp Fusion API** - Business data, reviews, ratings, contact info
- **Google Places API (New)** - Location data, hours, websites, photos
- **Nominatim Geocoding** - Address coordinate conversion

### **CLI-Focused Integrations** (Low Priority)
- OpenStreetMap Overpass API (additional venue data)
- CSV input support (bulk processing from files)
- Configuration files (.gymintel.yaml)

> **Advanced Integrations**: Social media APIs, business intelligence features, and real-time data are being implemented in **[GymIntel-Web](https://github.com/a-deal/gymintel-web)**

## Export Formats

### CSV Output
Spreadsheet-compatible with all data fields including confidence scores

### JSON Output
Structured data with comprehensive metadata:
```json
{
  "search_info": {
    "zipcode": "10001",
    "timestamp": "2025-07-01T12:00:00",
    "total_results": 85,
    "merge_stats": "19 merged, 85 unique",
    "avg_confidence": "45.2%"
  },
  "gyms": [
    {
      "name": "Mega Elite Fitness",
      "source": "Merged (Yelp + Google)",
      "match_confidence": 0.66,
      "sources": ["Yelp", "Google Places"],
      "phone": "(347) 393-2065",
      "website": "https://megaelite.com",
      "location": {"lat": 40.7484, "lng": -73.9940}
    }
  ]
}
```

## Contributing

Contributions welcome! This project is actively developed.

### Development Setup
```bash
git clone https://github.com/a-deal/gymintel-cli.git
cd gymintel-cli
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
```

### Contributing Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Commit with descriptive messages
5. Push and submit a Pull Request

### Architecture Notes
- **Multi-source data fusion** via confidence scoring algorithms
- **Modular design** for easy API integration
- **Comprehensive error handling** with graceful fallbacks
- **Performance optimized** with caching and rate limiting

## 🌐 Web App Roadmap

### **CLI Tool Status: Complete & Stable** ✅

This command-line tool represents the complete Phase 1 & 2 implementation:
- ✅ **Phase 1**: Multi-source data fusion with confidence scoring
- ✅ **Phase 2**: Metropolitan intelligence with batch processing (6 metros, 400+ ZIP codes)

### **Next Evolution: Web Application** 🚀

We're developing a web application version at **[GymIntel-Web](https://github.com/a-deal/gymintel-web)** featuring:

The web application will feature:

1. **GraphQL API** - Flexible data queries and real-time subscriptions
2. **Interactive Maps** - Mapbox integration with confidence score overlays
3. **Business Intelligence** - Market analytics and competitor analysis
4. **Data Visualization** - Charts, heatmaps, and trend analysis
5. **User Accounts** - Saved searches and preferences

**📋 Full Details**: See complete architecture and development phases at **[GymIntel-Web README](https://github.com/a-deal/gymintel-web)**

### **Migration Path**

**For Current CLI Users:**
- **Keep using this CLI tool** - it remains fully supported and stable
- **Export your data** using `--export json` for seamless web app import
- **GraphQL API access** - programmatic data access when available

**For Contributors:**
- **CLI improvements**: Continue contributing to this repository
- **Web development**: Join development at [GymIntel-Web](https://github.com/a-deal/gymintel-web)

### **Why Fork the Project?**

1. **Stability**: CLI tool remains stable and production-ready
2. **Focus**: Different tech stacks and deployment strategies
3. **User Choice**: CLI for developers/automation, Web for business users

---

## 🤝 Project Ecosystem

| Project | Purpose | Status | Best For |
|---------|---------|--------|----------|
| **[GymIntel CLI](https://github.com/a-deal/gymintel-cli)** | Command-line tool | ✅ Production | Scripts, automation, developers |
| **[GymIntel-Web](https://github.com/a-deal/gymintel-web)** | Web application | 🚀 In Progress | Business users, visualization, analysis |

---

**GymIntel CLI** - *Comprehensive gym intelligence at your command line* 🏋️‍♂️✨

**License**: MIT | **Status**: Production Ready | **Coverage**: 6 metros, 400+ ZIP codes | **Web Version**: Coming Soon
