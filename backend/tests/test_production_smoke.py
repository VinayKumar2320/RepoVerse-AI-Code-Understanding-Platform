import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.config import normalize_database_url
from backend.app.core.database import init_db

def test_database_url_normalization():
    assert normalize_database_url("postgres://user:pass@host:5432/db") == "postgresql+psycopg://user:pass@host:5432/db"
    assert normalize_database_url("postgresql://user:pass@host:5432/db") == "postgresql+psycopg://user:pass@host:5432/db"
    assert normalize_database_url("postgresql+psycopg://user:pass@host:5432/db") == "postgresql+psycopg://user:pass@host:5432/db"
    assert normalize_database_url("sqlite+aiosqlite:///./test.db") == "sqlite+aiosqlite:///./test.db"

@pytest.mark.asyncio
async def test_production_cors_and_headers():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test options CORS preflight
        headers = {
            "Origin": "https://repoverse.vercel.app",
            "Access-Control-Request-Method": "GET",
        }
        resp = await client.options("/api/v1/health", headers=headers)
        assert resp.status_code == 200

        # Test health check payload
        health_resp = await client.get("/api/v1/health")
        assert health_resp.status_code == 200
        data = health_resp.json()
        assert data["status"] == "healthy"
        assert "parsing_support" in data

@pytest.mark.asyncio
async def test_invalid_repo_analysis_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid host should be blocked with 400
        resp = await client.post("/api/v1/repositories/analyze", json={"url": "https://attacker.com/evil/repo"})
        assert resp.status_code == 400
        assert "not allowed" in resp.json()["detail"].lower()
