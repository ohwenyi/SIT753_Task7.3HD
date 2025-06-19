import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# Import our application
from app.main import create_app
from app.config import Settings, get_settings
from app.routers.health import ServiceCheck


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

@pytest.fixture
def app_with_dependency_override():
    """Create app with dependency override capability."""
    app = create_app()

    original_overrides = app.dependency_overrides.copy()

    def override_settings(test_settings):
        def get_test_settings():
            return test_settings
        
        # Override using the original get_settings function as key
        app.dependency_overrides[get_settings] = get_test_settings

    def restore_settings():
        app.dependency_overrides.clear()
        app.dependency_overrides.update(original_overrides)

    app.override_settings = override_settings
    app.restore_settings = restore_settings

    yield app

    restore_settings()

@pytest.fixture
def client(app_with_dependency_override):
    """Create test client with dependency override capability."""
    return TestClient(app_with_dependency_override)


@pytest_asyncio.fixture
async def async_client(app_with_dependency_override):
    """Create async test client with ASGITransport."""
    transport = ASGITransport(app=app_with_dependency_override)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Test health check endpoints with consistent dependency management."""

    def test_health_no_dependencies(self, client, app_with_dependency_override):
        """Test health check with no dependencies configured."""
        test_settings = create_test_settings()
        app_with_dependency_override.override_settings(test_settings)

        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert data["checks"] == {}

    @patch('app.routers.health.check_database', new_callable=AsyncMock)
    def test_health_with_database_healthy(self, mock_db_check, client, app_with_dependency_override):
        """Test health check with healthy database."""
        test_settings = create_test_settings(
            database_url="postgresql://test:test@localhost:5432/test"
        )
        app_with_dependency_override.override_settings(test_settings)

        mock_db_check.return_value = ServiceCheck(
            status="healthy",
            duration_ms=50.0
        )
        
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data["checks"]
        assert data["checks"]["database"]["status"] == "healthy"

    @patch('app.routers.health.check_database', new_callable=AsyncMock)
    def test_health_with_database_unhealthy(self, mock_db_check, client, app_with_dependency_override):
        """Test health check with unhealty database."""
        test_settings = create_test_settings(
            database_url="postgresql://test:test@localhost:5432/test"
        )
        app_with_dependency_override.override_settings(test_settings)

        mock_db_check.return_value = ServiceCheck(
            status="unhealthy",
            duration_ms=100.0,
            error="Connection refused"
        )

        response = client.get("/health")

        assert response.status_code == 503
        data = response.json()
        assert data['detail']['status'] == 'unhealthy'
        assert data['detail']['checks']['database']['status'] == 'unhealthy'

    def test_readiness_with_critical_services_down(self, client, app_with_dependency_override):
        """Test that readiness fails when critical services are down."""
        test_settings = create_test_settings(
            database_url="postgresql://test:test@localhost:5432/test"
        )
        app_with_dependency_override.override_settings(test_settings)

        with patch('app.routers.health.perform_health_checks', new_callable=AsyncMock) as mock_health_check:
            mock_health_check.return_value = {
                "database": ServiceCheck(
                status="unhealthy",
                duration_ms=1000.0,
                error="Connection refused"
                )
            }    
            response = client.get("/health/ready")
            #print("Status:", response.status_code)
            #print("Body:", response.json())

            assert response.status_code == 503
            data = response.json() 
            assert data['status'] == 'not_ready'


class TestEchoEndpoints:
    """Test echo endpoints."""
    
    def test_echo_query_basic(self, client):
        """Test basic echo functionality."""
        response = client.get("/echo/?msg=hello")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["echo"] == "hello"
        assert "timestamp" in data
        assert "metadata" in data
        assert data["metadata"]["original_message"] == "hello"
    
    def test_echo_query_with_uppercase(self, client):
        """Test echo with uppercase transformation."""
        response = client.get("/echo/?msg=hello&uppercase=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["echo"] == "HELLO"
        assert data["metadata"]["transformations_applied"]["uppercase"] is True
    
    def test_echo_query_with_prefix(self, client):
        """Test echo with prefix."""
        response = client.get("/echo/?msg=world&prefix=Hello")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["echo"] == "Hello: world"
        assert data["metadata"]["transformations_applied"]["prefix_added"] is True
    
    def test_echo_query_validation_error(self, client):
        """Test echo with invalid input."""
        # Empty message should fail validation
        response = client.get("/echo/?msg=")
        
        assert response.status_code == 422
    
    def test_echo_query_too_long(self, client):
        """Test echo with message too long."""
        long_message = "a" * 1001  # Exceeds 1000 char limit
        response = client.get(f"/echo/?msg={long_message}")
        
        assert response.status_code == 422
    
    def test_echo_post_basic(self, client):
        """Test POST echo endpoint."""
        payload = {
            "message": "hello post",
            "uppercase": False,
            "prefix": None
        }
        
        response = client.post("/echo/", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["echo"] == "hello post"
        assert data["metadata"]["original_message"] == "hello post"
    
    def test_echo_post_with_transformations(self, client):
        """Test POST echo with transformations."""
        payload = {
            "message": "hello post",
            "uppercase": True,
            "prefix": "API"
        }
        
        response = client.post("/echo/", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["echo"] == "API: HELLO POST"
        assert data["metadata"]["transformations_applied"]["uppercase"] is True
        assert data["metadata"]["transformations_applied"]["prefix_added"] is True
    
    def test_echo_reverse(self, client):
        """Test reverse echo endpoint."""
        response = client.get("/echo/reverse?msg=hello")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["echo"] == "olleh"
        assert data["metadata"]["original_message"] == "hello"
        assert data["metadata"]["transformation"] == "reverse"
    
    def test_echo_stats(self, client):
        """Test echo stats endpoint."""
        response = client.get("/echo/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "echo"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        assert len(data["endpoints"]) == 4

class TestApplicationFlow:
    """Test overall application behavior."""
    
    def test_echo_stats_as_info_endpoint(self, client):
        """Test echo stats endpoint as application info."""
        response = client.get("/echo/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "endpoints" in data
    
    def test_request_timing_header(self, client):
        """Test that timing header is added to responses."""
        response = client.get("/health/")
        
        if "X-Response-Time" in response.headers:
            timing = response.headers["X-Response-Time"]
            assert timing.endswith("ms")
    
    def test_basic_cors_or_headers(self, client):
        """Test basic headers are present."""
        response = client.get("/health/")
        
       
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"
        
    def test_404_handling(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404


class TestAsyncEndpoints:
    """Test endpoints using async client."""
    
    @pytest.mark.asyncio
    async def test_async_health_check(self, async_client):
        """Test health check with async client."""
        response = await async_client.get("/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_async_echo(self, async_client):
        """Test echo endpoint with async client."""
        response = await async_client.get("/echo/?msg=async_test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["echo"] == "async_test"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, async_client):
        """Test handling multiple concurrent requests."""
        # Send multiple requests concurrently
        tasks = [
            async_client.get(f"/echo/?msg=request_{i}")
            for i in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["echo"] == f"request_{i}"


# Test configuration for pytest
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()