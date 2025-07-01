# GymIntel - Refactored Architecture

## 📁 File Structure

```
gymintel-cli/
├── main.py                  # Entry point
├── src/
│   ├── gym_finder.py        # Main CLI application with confidence scoring
│   ├── yelp_service.py      # Yelp API service module
│   ├── google_places_service.py # Google Places API service module
│   ├── run_gym_search.py    # Programmatic search & batch processing
│   └── metro_areas.py       # Metropolitan area definitions
├── tests/
│   ├── test_gym_finder.py   # Unit tests for core functionality
│   ├── test_batch_processing.py # Tests for metro & batch features
│   └── run_tests.py         # Test runner script
├── scripts/
│   ├── benchmark.py         # Performance benchmarking
│   ├── benchmark_metro.py   # Metropolitan area benchmarks
│   └── examples.py          # Usage examples
├── docs/
│   ├── ARCHITECTURE.md      # This file
│   ├── TESTING.md          # Testing guide
│   ├── CI_CD_SETUP.md      # CI/CD documentation
│   └── CONTRIBUTING.md     # Contribution guide
├── .github/
│   └── workflows/           # GitHub Actions CI/CD
├── BENCHMARK_RESULTS.md     # Performance test results
├── README.md               # Project documentation
├── .env                    # API keys
└── requirements.txt        # Dependencies
```

## 🏗️ Architecture Overview

### **Separation of Concerns**

#### **1. Main Application (`gym_finder.py`)**
- **Core Logic**: Confidence scoring, data merging, fuzzy matching
- **Orchestration**: Coordinates between service modules
- **Business Intelligence**: Multi-level name similarity, semantic matching
- **Output**: CLI interface, export functionality, results display

#### **2. Yelp Service (`yelp_service.py`)**
- **API Integration**: Yelp Fusion API for gym search
- **Data Formatting**: Standardized gym data structure
- **Business Details**: Additional business information retrieval
- **Independence**: Can be used standalone for Yelp-only searches

#### **3. Google Places Service (`google_places_service.py`)**
- **API Integration**: Google Places API (New) for gym search
- **Enhanced Details**: Rich business profile data extraction
- **Sentiment Analysis**: Review sentiment scoring
- **Business Completeness**: Profile quality assessment

#### **4. Metropolitan Intelligence (`metro_areas.py` & `run_gym_search.py`)**
- **Metro Definitions**: 6 major US metropolitan areas with 400+ ZIP codes
- **Market Characteristics**: Demographics and fitness market traits
- **Batch Processing**: Parallel execution with configurable workers
- **Cross-ZIP Deduplication**: Intelligent duplicate detection across regions

#### **5. Batch Processing Engine (`run_gym_search.py`)**
- **Parallel Execution**: ThreadPoolExecutor for concurrent searches
- **Progress Tracking**: Real-time status updates for batch operations
- **Statistical Aggregation**: Metropolitan-level analytics
- **Export Management**: Batch and metro-level data exports

## 🔧 Service Module Benefits

### **Modularity**
- Each API service is self-contained
- Easy to test individual components
- Clear separation of API-specific logic

### **Maintainability**
- API changes only affect respective service modules
- Easier to debug API-specific issues
- Clean, focused code organization

### **Reusability**
- Services can be imported independently
- Useful for other projects requiring Yelp/Google data
- Supports microservice architecture patterns

### **Testability**
- Individual services can be unit tested
- Mock services for integration testing
- Isolated API dependency testing

## 🎯 Ultimate Confidence Scoring System

### **Phase 1: Enhanced Foundation**
- **Token-based name similarity**: Advanced tokenization
- **Semantic name matching**: Fitness industry semantic groups
- **Address normalization**: 40+ pattern replacements
- **Coordinate estimation**: ZIP code proximity scoring

### **Phase 2: API Intelligence**
- **Google Places Details**: Business profile completeness
- **Semantic category mapping**: Fitness business taxonomy
- **Review sentiment analysis**: Positive/negative detection
- **Rich profile indicators**: Photos, summaries, quality metrics

### **Phase 3: Advanced Intelligence**
- **Business hours parsing**: Real-time status recognition
- **Review correlation**: Cross-platform review intelligence
- **Website quality assessment**: Domain legitimacy analysis
- **Social media prediction**: Instagram handle generation

## 📊 Performance Metrics

### **Confidence Scoring Results**
- **Average confidence**: 72-86% (perfectly calibrated)
- **Range**: 40-90% (ideal target range)
- **Merge rate**: 40% (20/50 gyms successfully merged)
- **Execution time**: Sub-3 seconds for single ZIP code

### **Data Coverage**
- **Yelp results**: 50 gyms per search
- **Google Places**: 20 gyms per search
- **Total unique**: ~50 gyms after intelligent merging
- **Geographic accuracy**: ZIP + street coordinate estimation

### **Metropolitan Processing Performance**
- **Batch processing**: ~36 seconds for 2 ZIP codes
- **Parallel efficiency**: Linear scaling with workers
- **Deduplication rate**: 91-99% across metros
- **Metropolitan coverage**: 400+ ZIP codes across 6 cities

## 🏙️ Metropolitan Intelligence Architecture

### **Metropolitan Area Data Structure**
```python
@dataclass
class MetropolitanArea:
    name: str                      # e.g., "New York City"
    code: str                      # e.g., "nyc"
    zip_codes: List[str]           # 50-150 ZIP codes per metro
    state: str                     # Primary state
    population: Optional[int]      # Metro population
    density_category: str          # low/medium/high/very_high
    market_characteristics: List[str]  # e.g., ["premium_market", "high_competition"]
```

### **Batch Processing Architecture**
- **Parallel Workers**: 2-6 concurrent threads (configurable)
- **Queue Management**: ThreadPoolExecutor with futures
- **Error Resilience**: Individual ZIP failures don't stop batch
- **Memory Efficiency**: Streaming results, no full dataset in memory

### **Cross-ZIP Deduplication Algorithm**
1. **Signature Generation**: Normalized name + address fragments
2. **Similarity Detection**: Set intersection for character matching
3. **Threshold Tuning**: >3 name chars + >5 address chars = duplicate
4. **Performance**: O(n) with hash-based lookups

## 🚀 Usage Examples

### **Using Individual Services**

```python
# Yelp-only search
from yelp_service import YelpService
yelp = YelpService()
gyms = yelp.search_gyms(40.7484, -73.9940, radius_miles=2)

# Google Places-only search
from google_places_service import GooglePlacesService
google = GooglePlacesService()
gyms = google.search_gyms(40.7484, -73.9940, radius_miles=2)
```

### **Full Application**
```bash
# Single ZIP code search
python main.py --zipcode 10001 --radius 2

# Metropolitan area search
python main.py --metro nyc --radius 2

# Batch processing
python main.py --zipcodes "10001,10003,10011" --workers 4
```

### **Programmatic Usage**
```python
from run_gym_search import run_metro_search, run_batch_search

# Search entire metropolitan area
results = run_metro_search("nyc", radius=2, sample_size=10)

# Batch process multiple ZIPs
results = run_batch_search(["10001", "10003"], radius=2, max_workers=4)
```

## 🔮 Future Enhancements

### **Additional Service Modules**
- **Foursquare Service**: Additional venue data
- **Facebook Places Service**: Social media integration
- **Yelp Reviews Service**: Detailed review analysis
- **Instagram Service**: Handle verification and metrics

### **Enhanced Intelligence**
- **Machine Learning**: Confidence score optimization
- **Geospatial Analysis**: Advanced proximity algorithms
- **Business Validation**: Real-time status verification
- **Competitive Analysis**: Market gap identification

This refactored architecture provides a solid foundation for scalable, maintainable gym discovery intelligence with enterprise-level confidence scoring.
