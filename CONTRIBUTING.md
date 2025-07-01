# Contributing to GymIntel

Thank you for your interest in contributing to GymIntel! This guide will help you get started with contributing to our gym discovery platform.

## 🚀 Quick Start

### 1. Set Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-username/gym-finder.git
cd gym-finder

# Install dependencies
pip install -r requirements.txt
pip install pre-commit pytest pytest-cov black flake8 isort

# Set up pre-commit hooks
pre-commit install

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

## 🤖 For Repository Maintainers: Claude Review Setup

**Important**: To enable automated Claude code reviews on pull requests, repository maintainers need to configure the Anthropic API key:

### Setting up Claude Review

1. **Get an Anthropic API Key**:
   - Visit [https://console.anthropic.com/](https://console.anthropic.com/)
   - Create an account or sign in
   - Navigate to API Keys section
   - Create a new API key

2. **Add to Repository Secrets**:
   ```bash
   # Go to your repository settings
   https://github.com/your-username/gym-finder/settings/secrets/actions

   # Add new repository secret:
   # Name: ANTHROPIC_API_KEY
   # Value: [your-anthropic-api-key]
   ```

3. **How Claude Review Works**:
   - 🔍 Automatically reviews all pull requests
   - 📝 Provides feedback on code quality, security, and best practices
   - ✅ Runs alongside other CI/CD checks
   - 💬 Posts review comments directly in the PR

4. **Triggering Manual Reviews**:
   ```bash
   # Comment on any PR to trigger a manual review
   @claude
   ```

**Note**: Without the API key configured, the `claude-review` check will fail. All other CI/CD checks will continue to work normally.

### 2. Run Tests

```bash
# Run the full test suite
python3 run_tests.py

# Run specific test categories
python3 -m pytest test_gym_finder.py        # Unit tests
python3 examples.py                         # Feature examples
python3 benchmark.py                        # Performance tests
```

### 3. Make Changes

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Test your changes
python3 run_tests.py

# Commit (pre-commit hooks will run automatically)
git add .
git commit -m "feat: add amazing new feature"
git push origin feature/your-feature-name
```

## 📋 Types of Contributions

### 🐛 Bug Fixes
- Fix issues in confidence scoring algorithms
- Resolve API integration problems
- Address performance bottlenecks
- Improve error handling

### ✨ New Features
- Additional API integrations (Foursquare, Facebook Places)
- Enhanced confidence scoring methods
- New export formats
- Performance optimizations

### 📚 Documentation
- Improve README and guides
- Add code examples
- Update API documentation
- Create tutorials

### 🧪 Testing
- Add unit tests for new features
- Improve test coverage
- Create integration tests
- Performance benchmarks

## 🏗️ Architecture Guidelines

### Code Organization
```
gym-finder/
├── gym_finder.py          # Main application & confidence scoring
├── yelp_service.py         # Yelp API integration
├── google_places_service.py # Google Places API integration
├── test_gym_finder.py      # Unit tests
├── run_gym_search.py       # Script-based execution
├── examples.py             # Feature demonstrations
└── benchmark.py            # Performance testing
```

### Design Principles
1. **Separation of Concerns**: Keep API logic separate from business logic
2. **Modularity**: Each service should be self-contained
3. **Testability**: Write code that's easy to test
4. **Performance**: Maintain sub-3 second execution times
5. **Reliability**: Handle API failures gracefully

## 🎯 Confidence Scoring Guidelines

### Current System
Our confidence scoring uses 8+ weighted signals:
- Name similarity (30% weight)
- Address matching (25% weight)
- Phone matching (15% weight)
- Address intelligence (10% weight)
- Website domain (15% weight)
- Business hours (5% weight)
- Category alignment (10% weight)
- Price correlation (10% weight)

### Adding New Signals
When adding confidence signals:

1. **Weight carefully**: Total weights should ≈ 100%
2. **Test extensively**: Run benchmarks to ensure no regressions
3. **Document impact**: Show before/after confidence distributions
4. **Validate accuracy**: Higher confidence should mean better matches

```python
# Example: Adding a new confidence signal
def new_confidence_signal(self, yelp_data, google_data):
    """Calculate confidence based on new data point"""
    confidence = 0.0

    # Your scoring logic here
    if some_condition:
        confidence += 0.05  # 5% weight

    return min(confidence, 0.10)  # Cap at 10%
```

## 🧪 Testing Requirements

### Test Coverage Standards
- **Smoke Tests**: Must pass for all PRs
- **Unit Tests**: Aim for >80% coverage on new code
- **Integration Tests**: Test complete workflows
- **Performance Tests**: No >10% regressions

### Writing Tests
```python
# Example unit test
def test_new_feature(self):
    """Test new feature functionality"""
    gym_finder = GymFinder()
    result = gym_finder.new_feature("test_input")

    self.assertIsNotNone(result)
    self.assertGreater(len(result), 0)
    # More assertions...
```

### Running Specific Tests
```bash
# Test specific functionality
python3 -c "
from gym_finder import GymFinder
gf = GymFinder()
# Test your feature
print('✅ Feature test passed')
"

# Performance test
python3 -c "
import time
start = time.time()
# Your code here
elapsed = time.time() - start
assert elapsed < 1.0, f'Too slow: {elapsed}s'
print(f'✅ Performance OK: {elapsed:.3f}s')
"
```

## 📊 Performance Guidelines

### Performance Targets
- **Search execution**: < 3 seconds
- **Address normalization**: < 1ms per address
- **Name similarity**: < 50ms per comparison
- **Memory usage**: < 100MB for typical searches

### Optimization Tips
1. **Minimize API calls**: Batch requests when possible
2. **Cache results**: Store expensive computations
3. **Optimize algorithms**: Use efficient string matching
4. **Profile code**: Use benchmarks to identify bottlenecks

```python
# Example: Efficient implementation
def optimize_example(self, data_list):
    """Optimized version with caching"""
    if not hasattr(self, '_cache'):
        self._cache = {}

    results = []
    for item in data_list:
        key = hash(item)
        if key not in self._cache:
            self._cache[key] = expensive_operation(item)
        results.append(self._cache[key])

    return results
```

## 🔧 API Integration Guidelines

### Adding New APIs
1. **Create separate service module**: Follow `yelp_service.py` pattern
2. **Implement standard interface**: `search_gyms(lat, lng, radius)`
3. **Handle errors gracefully**: Return empty list on failures
4. **Respect rate limits**: Add appropriate delays
5. **Add to confidence scoring**: Integrate with main algorithm

```python
# Example: New API service template
class NewAPIService:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('NEW_API_KEY')

    def search_gyms(self, lat, lng, radius_miles=10):
        """Standard search interface"""
        if not self.api_key:
            return []

        try:
            # API call implementation
            return formatted_results
        except Exception as e:
            click.echo(f"Error searching NewAPI: {e}")
            return []
```

## 📝 Code Style

### Formatting
We use automated formatting tools:
- **Black**: Line length 127 characters
- **isort**: Import sorting
- **flake8**: Linting

```bash
# Format code automatically
black --line-length=127 *.py
isort --line-length=127 *.py
flake8 --max-line-length=127 *.py
```

### Naming Conventions
- **Functions**: `snake_case` (e.g., `normalize_address`)
- **Classes**: `PascalCase` (e.g., `GymFinder`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_COUNT`)
- **Private methods**: `_snake_case` (e.g., `_internal_method`)

### Documentation
```python
def example_function(param1, param2):
    """Brief description of what the function does.

    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2

    Returns:
        dict: Description of return value

    Example:
        >>> result = example_function("test", 123)
        >>> print(result['key'])
    """
    # Implementation here
    return {"key": "value"}
```

## 🚀 Pull Request Process

### Before Submitting
1. **Run full test suite**: `python3 run_tests.py`
2. **Check performance**: `python3 benchmark.py`
3. **Update documentation**: Add/update relevant docs
4. **Test examples**: `python3 examples.py`

### PR Requirements
- [ ] ✅ All CI checks pass
- [ ] 📝 Clear description of changes
- [ ] 🧪 Tests added for new features
- [ ] 📚 Documentation updated
- [ ] 🎯 No performance regressions

### Review Process
1. **Automated checks**: CI pipeline validates code
   - ✅ Unit tests across Python 3.8-3.11
   - 🔒 Security scanning (Bandit + Safety)
   - 🎨 Code formatting (Black + isort + flake8)
   - ⚡ Performance tests
   - 📚 Documentation checks
   - 🤖 **Claude AI review** (code quality & best practices)
2. **Manual review**: Maintainer reviews for quality
3. **Testing**: Reviewer may test functionality
4. **Approval**: PR approved and merged

**Note**: If the `claude-review` check fails, ensure the repository has the `ANTHROPIC_API_KEY` configured (see setup section above).

## 🐛 Reporting Issues

### Bug Reports
Use the bug report template and include:
- Clear reproduction steps
- Expected vs actual behavior
- Environment details
- Test results

### Feature Requests
Use the feature request template and include:
- Clear motivation
- Proposed solution
- Impact assessment
- Implementation ideas

## 🎯 Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Pull Request Comments**: Code-specific discussions

### Quick Questions
For quick questions, check:
1. **TESTING.md**: Testing procedures
2. **ARCHITECTURE.md**: System design
3. **README.md**: Basic usage
4. **Examples**: `python3 examples.py`

### Mentorship
New contributors welcome! Look for:
- **Good first issue** label
- **Help wanted** label
- **Documentation** improvements

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🎉 Recognition

Contributors are recognized in:
- GitHub contributor graphs
- Release notes for significant contributions
- CONTRIBUTORS.md file (coming soon)

Thank you for helping make GymIntel better! 🏋️‍♂️✨
