# Mars-Sandbox Backend Tests

This directory contains unit tests for the mars-sandbox backend core modules.

## Test Coverage

Current test coverage focuses on core business logic modules:

| Module | Coverage | Description |
|--------|----------|-------------|
| `auth.py` | 100% | Authentication, session tokens, cookies |
| `schemas.py` | 100% | Pydantic request/response schemas |
| `models.py` | 100% | SQLAlchemy ORM models |
| `dependencies.py` | 100% | FastAPI dependency injections |
| `config.py` | 97% | Configuration settings |
| `scanner.py` | 40% | HTML directory scanner (metadata extraction, hash computation) |

**Overall Coverage: 29%** (core modules well-covered, routers and WS modules not yet tested)

## Test Files

- `test_auth.py` - Authentication module tests (12 tests)
- `test_config.py` - Configuration module tests (7 tests)
- `test_dependencies.py` - FastAPI dependencies tests (5 tests)
- `test_models.py` - SQLAlchemy ORM models tests (16 tests)
- `test_scanner.py` - Scanner utility tests (21 tests)
- `test_schemas.py` - Pydantic schemas tests (21 tests)

**Total: 82 tests**

## Running Tests

### Install Test Dependencies

```bash
cd mars-sandbox/backend
source venv/bin/activate
pip install pytest pytest-asyncio pytest-cov httpx
```

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run with Coverage Report

```bash
# Terminal report
python -m pytest tests/ --cov=app --cov-report=term-missing

# HTML report (opens in browser)
python -m pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

### Run Specific Test File

```bash
python -m pytest tests/test_auth.py -v
```

### Run Specific Test

```bash
python -m pytest tests/test_auth.py::TestCreateSessionToken::test_create_token_returns_string -v
```

## Test Architecture

### Database Testing

Tests use an in-memory SQLite database for isolation:
- Each test gets a fresh database session
- Tables are created before each test
- Tables are dropped after each test
- No interference between tests

### Fixtures

Defined in `conftest.py`:
- `test_engine` - Session-scoped SQLite engine
- `db_session` - Function-scoped database session
- `override_get_db` - Dependency override for FastAPI

### Async Testing

Async tests use `pytest-asyncio` with `asyncio_mode = auto`:
- Async test functions are automatically detected
- No need for `@pytest.mark.asyncio` decorator (but can be used explicitly)

## Test Categories

### 1. Unit Tests (Current)
- Pure function tests
- Model property tests
- Schema validation tests
- Configuration tests

### 2. Integration Tests (Future)
- API endpoint tests with HTTPX
- Database integration tests
- WebSocket connection tests

### 3. End-to-End Tests (Future)
- Full workflow tests
- Multi-step user scenarios

## Adding New Tests

1. Create `test_<module>.py` in the `tests/` directory
2. Use descriptive test class and method names
3. Add docstrings explaining test purpose
4. Use fixtures from `conftest.py` for database access
5. Run tests to verify: `python -m pytest tests/test_<module>.py -v`

### Example Test Structure

```python
class TestMyModule:
    """Test my_module functionality."""

    def test_specific_behavior(self, db_session):
        """Should do something specific."""
        # Arrange
        # Act
        # Assert
        assert True
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Naming**: Use descriptive names (`test_should_fail_when_invalid_input`)
3. **Coverage**: Test both success and error cases
4. **Fixtures**: Reuse fixtures for common setup
5. **Cleanup**: Ensure test data is cleaned up (handled by fixtures)

## TODO

- [ ] Add router endpoint tests (auth, pages, tags, nodes, commands, scan)
- [ ] Add WebSocket connection tests
- [ ] Add integration tests for scanner workflow
- [ ] Add tests for connection pool
- [ ] Increase overall coverage to 80%+
