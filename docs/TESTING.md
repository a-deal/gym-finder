# GymIntel Testing Guide

## 🧪 Test Files Overview

### **Core Test Files**

| File | Purpose | Usage |
|------|---------|-------|
| `tests/test_gym_finder.py` | Core unit tests | `python3 -m unittest tests.test_gym_finder` |
| `tests/test_batch_processing.py` | Metropolitan & batch tests | `python3 tests/test_batch_processing.py` |
| `tests/run_tests.py` | Test runner with detailed output | `python3 tests/run_tests.py` |
| `scripts/examples.py` | Feature demonstrations | `python3 scripts/examples.py` |
| `scripts/benchmark.py` | Performance testing | `python3 scripts/benchmark.py` |
| `scripts/benchmark_metro.py` | Metropolitan benchmarks | `python3 scripts/benchmark_metro.py` |

## 🚀 Quick Start Testing

### **1. Run All Tests**
```bash
# Core functionality tests
python3 tests/run_tests.py

# Metropolitan and batch processing tests
python3 tests/test_batch_processing.py
```
This runs smoke tests, unit tests, and integration tests with detailed output.

### **2. Metropolitan Area Testing**
```bash
# Test single metropolitan area
python main.py --metro nyc --sample 5 --radius 2

# Test batch processing
python main.py --zipcodes "10001,10003,10011" --radius 1

# List available metros
python main.py --list-metros
```

### **3. Performance Benchmarking**
```bash
# Full metropolitan benchmarks
python3 scripts/benchmark_metro.py

# Basic performance tests
python3 scripts/benchmark.py
```

### **4. Feature Examples**
```bash
python3 scripts/examples.py
```
Demonstrates all major features including confidence scoring, semantic matching, and API services.

## 📋 Test Categories

### **Smoke Tests** 💨
- Basic import checks
- Instance creation
- Method execution
- API key configuration

### **Unit Tests** 🧪
- **YelpService**: API integration, error handling
- **GooglePlacesService**: API integration, price conversion
- **GymFinder**: Core logic, confidence scoring
- **Address/Phone Normalization**: Data cleaning
- **Semantic Matching**: Name similarity algorithms

### **Integration Tests** 🔧
- Complete workflow testing
- Service module coordination
- Multi-source data merging
- Export functionality

### **Metropolitan Tests** 🏙️
- **Metro Area Definitions**: Validate 6 major US metros
- **Batch Processing**: Parallel execution testing
- **Cross-ZIP Deduplication**: Algorithm validation
- **Statistics Generation**: Metropolitan analytics
- **Performance Scaling**: Multi-worker efficiency

## 🎯 Script-Based Usage Examples

### **Programmatic Search**
```python
from run_gym_search import run_gym_search, run_batch_search, run_metro_search

# Single search
results = run_gym_search("10001", radius=2, export_format="json")

# Batch processing
results = run_batch_search(["10001", "10003", "10011"], radius=2, max_workers=4)

# Metropolitan area search
results = run_metro_search("nyc", radius=2, sample_size=10)

# Access statistics
stats = results["metro_info"]["statistics"]
print(f"Total gyms: {stats['total_gyms_found']}")
print(f"Deduplication rate: {stats['duplication_rate']:.1f}%")
```

### **Service Module Usage**
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

### **Direct GymFinder Usage**
```python
from gym_finder import GymFinder

gym_finder = GymFinder()

# Test specific features
similarity = gym_finder.token_based_name_similarity("Planet Fitness", "Planet Fitness Gym")
normalized = gym_finder.normalize_address("123 Main Street")
coords = gym_finder.estimate_coordinates_from_address("123 Main St, NYC 10001")
```

## 📊 Expected Test Results

### **Smoke Tests**: ✅ 4/4 PASSED
- All imports successful
- Instance creation working
- Basic methods functional
- API keys configured

### **Unit Tests**: Target 18+ tests
- Most tests should pass
- Some may fail due to API rate limits or changes
- Integration tests compensate for unit test limitations

### **Integration Tests**: ✅ 4/4 PASSED
- Basic search functionality
- Service module imports
- Confidence scoring
- Address normalization

### **Metropolitan Tests**: ✅ 11/11 PASSED
- Metro area definitions validated
- Batch processing with 2-6 workers
- Cross-ZIP deduplication 90%+ efficiency
- Statistics generation accurate
- All 6 metros (NYC, LA, Chicago, SF, Boston, Miami) tested

## 🔧 Troubleshooting

### **Common Issues**

**1. API Key Errors**
```bash
# Check .env file exists and has keys
cat .env
```

**2. Import Errors**
```bash
# Ensure all files are in same directory
ls -la *.py
```

**3. Test Failures**
- Some unit tests may fail due to real API calls
- Integration tests are more reliable for overall functionality
- Check benchmark.py for comprehensive testing

### **Performance Expectations**

- **Search time**: < 3 seconds per ZIP code
- **Confidence range**: 58-86% for merged gyms
- **Merge rate**: ~40% (20/50 gyms typically merged)
- **Coverage**: 50+ Yelp + 20+ Google = 70+ total unique gyms

## 🎮 Interactive Testing

### **CLI vs Script Comparison**
```bash
# CLI method (original)
python3 gym_finder.py --zipcode 10001 --radius 2

# Script method (new)
python3 run_gym_search.py 10001 2
```

Both methods produce identical results but script method offers:
- ✅ Programmatic access
- ✅ Return values for further processing
- ✅ Quiet mode for automation
- ✅ Better integration with other tools

### **Batch Processing**
```python
# Process multiple ZIP codes automatically
zipcodes = ["10001", "10003", "10011", "10014", "10016"]
all_results = run_multiple_searches(zipcodes, radius=1)
```

## 📈 Continuous Testing

### **Automated Testing Setup**
```bash
# Run tests in background
nohup python3 benchmark.py > benchmark_results.log 2>&1 &

# Quick validation
python3 run_gym_search.py 10001 1 > /dev/null && echo "✅ System OK"
```

### **Performance Monitoring**
The benchmark.py script provides comprehensive metrics:
- Execution time statistics
- Confidence score distribution
- API response consistency
- Multi-ZIP code scalability

This testing suite ensures GymIntel maintains high performance and accuracy across all supported features.
