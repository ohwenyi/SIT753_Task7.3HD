# FastAPI Backend Engineering Demo

A minimal yet production-ready FastAPI application demonstrating core backend engineering concepts including structured configuration, health checks, logging, and testing patterns.

## 🏗️ Architecture Overview

This project demonstrates a clean, scalable backend architecture with the following layers:

```
├── app/
│   ├── config.py          # Environment-based configuration
│   ├── main.py            # FastAPI application factory
│   ├── routers/           # API endpoint organization
│   │   ├── health.py      # Health check endpoints
│   │   └── echo.py        # Echo service endpoints
│   └── utils/
│       └── logging.py     # Structured logging setup
├── tests/                 # Integration tests
├── .env                   # Environment configuration
└── requirements.txt       # Python dependencies
```

### Key Design Principles

- **Separation of Concerns**: Each layer has a single responsibility
- **Configuration Management**: Environment-based config with validation
- **Observability**: Structured logging and comprehensive health checks
- **Testability**: Dependency injection and integration testing
- **Production Readiness**: Proper error handling and monitoring endpoints

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or poetry for dependency management

### Installation

1. **Clone and setup environment:**
```bash
git clone https://github.com/DanielPopoola/fastapi-microservice-health-check.git
cd fastapi-backend-demo
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application:**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Health Check Endpoints

| Endpoint | Purpose | Use Case |
|----------|---------|----------|
| `GET /health` | Comprehensive health check | Monitoring dashboards |
| `GET /health/live` | Liveness probe | Kubernetes liveness |
| `GET /health/ready` | Readiness probe | Kubernetes readiness |

#### Health Check Response Example

```json
{
  "status": "healthy",
  "timestamp": 1640995200.123,
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "duration_ms": 23.4
    },
    "redis": {
      "status": "healthy", 
      "duration_ms": 12.1
    }
  }
}
```

### Service Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /echo` | GET | Echo service with query parameter |
| `POST /echo` | POST | Echo service with request body |

#### Echo Examples

```bash
# Query parameter echo
curl "http://localhost:8000/echo?msg=hello"
# Response: {"echo": "hello"}

# Request body echo  
curl -X POST "http://localhost:8000/echo" \
  -H "Content-Type: application/json" \
  -d '{"message": "hello world"}'
# Response: {"echo": "hello world"}
```

## ⚙️ Configuration

Configuration is managed through environment variables with sensible defaults:

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | FastAPI Health Check Demo | Application name |
| `DEBUG` | false | Debug mode |
| `LOG_LEVEL` | INFO | Logging level |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8000 | Server port |

### Health Check Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `HEALTH_CHECK_TIMEOUT` | 5.0 | Health check timeout (seconds) |
| `DATABASE_URL` | None | PostgreSQL connection string |
| `REDIS_URL` | None | Redis connection string |

### Example Configuration

```bash
# Development
DEBUG=true
LOG_LEVEL=DEBUG

# Production
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
REDIS_URL=redis://localhost:6379/0
HEALTH_CHECK_TIMEOUT=3.0
```

## 📊 Logging

The application uses structured logging with different formats for development and production:

### Development Logging
- Colorized console output
- Human-readable format
- Detailed tracebacks

### Production Logging
- JSON format for log aggregation
- Structured fields for filtering
- Performance metrics

### Log Structure

```json
{
  "timestamp": "2024-01-01 12:00:00.000",
  "level": "INFO",
  "module": "app.routers.health", 
  "function": "health_check",
  "line": 123,
  "message": "Health check completed: healthy",
  "http_method": "GET",
  "http_path": "/health",
  "duration_ms": 45.2
}
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_endpoints.py

# Run with verbose output
pytest -v
```

### Test Structure

The project uses integration tests that verify the entire request/response cycle:

```python
# Example test
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

### Test Configuration

Tests use a separate configuration to avoid interfering with development:

```python
# Test settings override
def create_test_settings(**overrides):
    """Create test settings with optional overrides."""
    defaults = {
        "app_name": "FastAPI Test App",
        "debug": True,
        "log_level": "INFO",
        "database_url": None,
        "redis_url": None,
        "health_check_timeout": 1.0
    }
    defaults.update(overrides)
    return Settings(**defaults)
```

## 🔍 Monitoring & Observability

### Health Check Patterns

The application implements three types of health checks following industry best practices:

1. **Liveness Check** (`/health/live`)
   - Answers: "Is the process running?"
   - Use for: Kubernetes liveness probes
   - Action if failing: Restart the pod

2. **Readiness Check** (`/health/ready`) 
   - Answers: "Can the app serve requests?"
   - Use for: Kubernetes readiness probes
   - Action if failing: Remove from load balancer

3. **Comprehensive Check** (`/health`)
   - Answers: "Is everything working optimally?"
   - Use for: Monitoring dashboards
   - Action if failing: Alert operations team

### Metrics Collection

All health checks and requests are logged with structured data for metrics collection:

- Response times
- Error rates
- Dependency health trends
- Request patterns

## 🔧 Development

### Project Structure Explained

```
app/
├── config.py           # Centralized configuration management
├── main.py             # FastAPI application factory
├── routers/            # API endpoint organization
│   ├── __init__.py
│   ├── health.py       # Health check logic
│   └── echo.py         # Business logic endpoints
└── utils/              # Shared utilities
    ├── __init__.py
    └── logging.py      # Logging configuration
```

### Adding New Endpoints

1. Create a new router file in `app/routers/`
2. Define your endpoints using FastAPI decorators
3. Add the router to `main.py`
4. Write integration tests in `tests/`

### Code Quality

The project follows these conventions:
- Type hints for all function parameters and returns
- Pydantic models for request/response validation
- Structured logging for all operations
- Comprehensive error handling
- Dependency injection for testability

## 📚 Learning Resources

This project demonstrates several backend engineering concepts:

- **Configuration Management**: Pydantic BaseSettings
- **Dependency Injection**: FastAPI's dependency system
- **Structured Logging**: Loguru with JSON formatting
- **Health Checks**: Kubernetes-ready health endpoints
- **Testing**: Integration testing with httpx
- **Error Handling**: Proper HTTP status codes and error responses

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 What's Next?

This demo covers the fundamentals, but real-world applications often need:

- **Database Integration**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT tokens with role-based access
- **Rate Limiting**: Request throttling and API quotas  
- **Caching**: Redis integration for performance
- **Message Queues**: Background task processing
- **API Documentation**: Enhanced OpenAPI specs
- **Monitoring**: Prometheus metrics and Grafana dashboards

Each of these can be added incrementally while maintaining the clean architecture established here.
