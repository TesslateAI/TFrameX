# TFrameX Enterprise Testing Suite

This directory contains comprehensive tests and validation scripts for TFrameX Enterprise features.

## Test Environment Setup

### 1. Environment Variables

Copy the provided `.env.test` file to configure the test environment:

```bash
# Copy test environment configuration
cp .env.test.example .env.test

# Edit with your LLM credentials if needed
nano .env.test
```

The test environment uses these key variables:
- `OPENAI_API_KEY`: LLM API key for testing
- `OPENAI_API_BASE`: LLM API base URL
- `OPENAI_MODEL_NAME`: LLM model name
- `TFRAMEX_ENTERPRISE_*`: Enterprise feature configuration

### 2. Install Test Dependencies

```bash
# Install test-specific requirements
pip install -r requirements-test.txt

# Or install with optional dependencies
pip install -e ".[test]"
```

## Running Tests

### Quick Validation

Run the simple validation script to check if all enterprise features are working:

```bash
python tests/run_tests.py
```

This script tests:
- ✅ Basic enterprise setup and configuration
- ✅ Storage backend functionality
- ✅ Metrics collection
- ✅ Security features (authentication, RBAC)
- ✅ LLM integration with real API

### Comprehensive Test Suite

Run the full test suite with detailed validation:

```bash
python tests/test_enterprise.py
```

This includes:
- Storage backend tests (SQLite, Memory, PostgreSQL, S3)
- Metrics collection tests (Prometheus, StatsD, OpenTelemetry, Custom)
- Authentication tests (API Key, JWT, OAuth2, Basic Auth)
- Authorization tests (RBAC, permissions, roles)
- Session management tests
- Audit logging tests
- Full enterprise integration tests

### Using Pytest

Run tests with pytest for better reporting:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/ -m "enterprise"
pytest tests/ -m "security"
pytest tests/ -m "storage"

# Run with coverage
pytest tests/ --cov=tframex.enterprise

# Run verbose with logging
pytest tests/ -v --log-cli-level=INFO
```

### Performance Benchmarks

Run performance benchmarks to validate enterprise feature performance:

```bash
python tests/benchmark_enterprise.py
```

This benchmarks:
- Storage operation performance (insert/select ops/sec)
- Metrics collection performance
- Authentication performance
- Enterprise app startup time

Expected performance benchmarks:
- **Storage**: >1,000 insert ops/sec, >5,000 select ops/sec
- **Metrics**: >5,000 counter ops/sec
- **Authentication**: >500 auth ops/sec
- **Startup**: <5 seconds for full enterprise initialization

## Test Categories

### Unit Tests
- Individual component functionality
- Isolated feature testing
- Mock dependencies

### Integration Tests
- Component interaction testing
- End-to-end workflows
- Real dependency testing

### Performance Tests
- Throughput benchmarks
- Latency measurements
- Resource usage validation

### Security Tests
- Authentication validation
- Authorization enforcement
- Audit logging verification

## Test Data

Test data is stored in temporary directories and cleaned up automatically. The test environment uses:

- **Storage**: SQLite database in `test_data/` directory
- **Metrics**: In-memory collection with custom logging backend
- **Sessions**: Memory-based session store
- **Audit Logs**: In-memory storage with short retention

## Enterprise Feature Test Coverage

### ✅ Storage Layer
- [x] In-memory storage backend
- [x] SQLite storage backend
- [x] PostgreSQL storage backend (if dependencies available)
- [x] S3 storage backend (if dependencies available)
- [x] Storage factory and registry
- [x] Data migration between backends
- [x] Storage health checks

### ✅ Metrics Collection
- [x] Metrics manager coordination
- [x] Prometheus metrics collector
- [x] StatsD metrics collector
- [x] OpenTelemetry metrics collector
- [x] Custom metrics backends
- [x] Metric types (counter, gauge, histogram, timer)
- [x] Metric buffering and batching
- [x] Background metric collection

### ✅ Security Framework
- [x] API Key authentication
- [x] Basic HTTP authentication
- [x] JWT authentication
- [x] OAuth2 authentication
- [x] RBAC engine with roles and permissions
- [x] Permission inheritance
- [x] Policy-based authorization
- [x] Security middleware integration

### ✅ Session Management
- [x] Session creation and validation
- [x] Session expiration and cleanup
- [x] Session rotation for security
- [x] Multiple session stores (database, memory)
- [x] Session limit enforcement
- [x] Background session cleanup

### ✅ Audit Logging
- [x] Comprehensive event logging
- [x] Event filtering and categorization
- [x] Audit event search and retrieval
- [x] Compliance reporting
- [x] Event buffering and batching
- [x] Configurable retention policies

### ✅ Enterprise Integration
- [x] TFrameX core integration
- [x] Configuration management
- [x] Health monitoring
- [x] Graceful startup and shutdown
- [x] Error handling and recovery
- [x] Performance optimization

## Test Configuration

### Pytest Configuration

The `pytest.ini` file configures:
- Test discovery patterns
- Asyncio test support
- Logging configuration
- Test markers for categorization
- Coverage settings

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only security tests
pytest -m security

# Run tests that require LLM access
pytest -m requires_llm

# Skip slow tests
pytest -m "not slow"
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure TFrameX is in Python path
   export PYTHONPATH="$(pwd):$PYTHONPATH"
   ```

2. **Missing Dependencies**
   ```bash
   # Install all optional dependencies
   pip install -r requirements-test.txt
   ```

3. **Database Connection Issues**
   ```bash
   # Check if test database directory exists
   mkdir -p test_data
   ```

4. **LLM API Issues**
   ```bash
   # Verify API credentials in .env.test
   echo $OPENAI_API_KEY
   ```

### Debug Mode

Enable debug logging for detailed test information:

```bash
# Set debug level
export TFRAMEX_LOG_LEVEL=DEBUG

# Run tests with debug output
python tests/run_tests.py
```

### Test Data Cleanup

Test data is automatically cleaned up, but you can manually clean:

```bash
# Remove test data directory
rm -rf test_data/

# Clean pytest cache
rm -rf .pytest_cache/
```

## Contributing

When adding new enterprise features:

1. **Add unit tests** for individual components
2. **Add integration tests** for feature interaction
3. **Update benchmark tests** for performance validation
4. **Add security tests** for security-related features
5. **Update this documentation** with new test coverage

### Test Naming Conventions

- `test_*.py`: Test files
- `Test*`: Test classes
- `test_*`: Test methods
- Use descriptive names that explain what is being tested

### Test Structure

```python
class TestNewFeature(TestEnterpriseBase):
    """Test new enterprise feature."""
    
    async def test_basic_functionality(self):
        """Test basic feature functionality."""
        # Setup
        # Test
        # Assert
        # Cleanup
    
    async def test_error_handling(self):
        """Test feature error handling."""
        # Test error conditions
        # Verify proper error responses
    
    async def test_integration(self):
        """Test feature integration with other components."""
        # Test feature interaction
        # Verify end-to-end workflows
```

## Test Results

Test results are logged with clear pass/fail indicators:
- ✅ Test passed
- ❌ Test failed
- ⚠️ Test warning or performance issue
- 🎉 All tests completed successfully

For detailed test results, check the log output or use pytest's reporting features.