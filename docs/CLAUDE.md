# CLAUDE.md - Project Context for AI Assistants

This file provides context for AI assistants (like Claude) to understand the GymIntel project structure and provide better assistance.

## Project Overview

GymIntel is an advanced gym discovery platform that combines multiple data sources (Yelp, Google Places) with intelligent confidence scoring to provide comprehensive gym intelligence. The project recently completed Phase 2, adding metropolitan-scale batch processing capabilities.

## Key Features

1. **Multi-Source Data Fusion**: Combines Yelp and Google Places APIs
2. **Confidence Scoring**: 8-signal algorithm (40-90% confidence range)
3. **Metropolitan Intelligence**: 6 major US metros with 400+ ZIP codes
4. **Batch Processing**: Parallel execution with 2-6 workers
5. **Cross-ZIP Deduplication**: 90%+ efficiency in removing duplicates

## Project Structure

```
gymintel-cli/
   main.py                  # Entry point
   src/
      gym_finder.py        # CLI and core logic
      yelp_service.py      # Yelp API integration
      google_places_service.py # Google Places API
      run_gym_search.py    # Batch processing engine
      metro_areas.py       # Metropolitan definitions
   tests/
      test_gym_finder.py   # Core unit tests
      test_batch_processing.py # Metro tests
   scripts/
       benchmark.py         # Performance testing
       benchmark_metro.py   # Metro benchmarks
```

## Current Status

-  Phase 1: Multi-source fusion (completed)
-  Phase 2: Metropolitan intelligence (completed)
- ✅ CLI Tool: Complete and stable for production use

**Note**: Advanced business intelligence and web platform features are now being developed in **[GymIntel-Web](https://github.com/a-deal/gymintel-web)** with GraphQL API, interactive maps, and PostgreSQL.

## Key Commands

```bash
# Single ZIP search
python main.py --zipcode 10001 --radius 2

# Metropolitan search
python main.py --metro nyc --radius 2

# Batch processing
python main.py --zipcodes "10001,10003,10011"

# Run tests
python3 tests/test_batch_processing.py
```

## Performance Metrics

- Single ZIP: ~3 seconds
- Batch (2 ZIPs): ~36 seconds
- Deduplication: 91-99% efficiency
- Merge rate: 40% average
- Confidence: 72-86% range

## When Assisting Users

1. **Code Changes**: Follow existing patterns in the codebase
2. **Testing**: Always run `tests/test_batch_processing.py` for metro features
3. **Documentation**: Update README.md for user-facing changes
4. **Performance**: Maintain <3 second single ZIP performance
5. **Metropolitan Areas**: 6 available (NYC, LA, Chicago, SF, Boston, Miami)

## Common Tasks

- **Add new metro**: Edit `src/metro_areas.py`
- **Improve confidence**: Modify `gym_finder.py` scoring algorithm
- **Add API**: Create new service module following `yelp_service.py` pattern
- **Performance test**: Run `scripts/benchmark_metro.py`

## API Keys Required

```bash
YELP_API_KEY=your_key_here
GOOGLE_PLACES_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here  # For Claude reviews
```

## Recent Changes (Phase 2)

- Added 6 metropolitan area definitions
- Implemented parallel batch processing
- Created cross-ZIP deduplication algorithm
- Added comprehensive test suite (11 tests)
- Updated CLI with new options: --metro, --zipcodes, --list-metros

This context helps AI assistants understand the project's architecture, conventions, and current state to provide more accurate assistance.
