import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm import LLMClient, LLMError
from app.main import app, get_validated_settings


class FakeLLM(LLMClient):
    def __init__(self, sql_to_return: str | None = None, error: Exception | None = None):
        self._sql_to_return = sql_to_return
        self._error = error

    def generate_sql(self, question: str, schema_context: str) -> str:
        if self._error:
            raise self._error
        if self._sql_to_return is None:
            return "SELECT 1"
        return self._sql_to_return


def create_test_db(tmp_path) -> str:
    """Create a temporary SQLite database with test data and views."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))

    conn.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TEXT NOT NULL,
            customer TEXT NOT NULL,
            country TEXT NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    test_data = [
        ("2025-01-15", "Cliente_001", "España", "Teclado", 100.0, "completado"),
        ("2025-01-20", "Cliente_002", "México", "Ratón", 50.0, "completado"),
        ("2025-02-10", "Cliente_003", "España", "Monitor", 200.0, "completado"),
        ("2025-02-15", "Cliente_004", "Argentina", "Portátil", 300.0, "pendiente"),
        ("2025-03-01", "Cliente_005", "Chile", "Auriculares", 150.0, "cancelado"),
    ]
    INSERT_ORDER = (
        "INSERT INTO orders (order_date, customer, country, product, amount, status) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    conn.executemany(INSERT_ORDER, test_data)
    conn.commit()

    views_sql = """
    DROP VIEW IF EXISTS sales_by_month_country;
    DROP VIEW IF EXISTS top_customers;

    CREATE VIEW sales_by_month_country AS
    SELECT
        strftime('%Y-%m', order_date) AS month,
        country,
        COUNT(*) AS orders,
        ROUND(SUM(amount), 2) AS total_sales
    FROM orders
    WHERE status = 'completado'
    GROUP BY strftime('%Y-%m', order_date), country
    ORDER BY month, country;

    CREATE VIEW top_customers AS
    SELECT
        customer,
        COUNT(*) AS orders,
        ROUND(SUM(amount), 2) AS total_spent
    FROM orders
    WHERE status = 'completado'
    GROUP BY customer
    ORDER BY total_spent DESC, customer ASC
    LIMIT 10;
    """
    for stmt in views_sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()

    conn.close()
    return str(db_path)


@pytest.fixture
def temp_db(tmp_path):
    return create_test_db(tmp_path)


@pytest.fixture
def fake_settings(temp_db):
    return Settings(
        nvidia_api_key="test-key",
        nvidia_base_url="https://test.example.com",
        nvidia_model="test-model",
        db_path=temp_db,
    )


def make_client(settings: Settings | None = None) -> TestClient:
    """Create a TestClient with optional dependency overrides."""
    app.dependency_overrides.clear()

    if settings is not None:
        app.dependency_overrides[get_validated_settings] = lambda: settings

    client = TestClient(app)
    return client


class TestAskEndpoint:
    def test_ask_success(self, temp_db, fake_settings, monkeypatch):
        """Test successful request with valid SQL from fake LLM."""
        fake_llm = FakeLLM(
            sql_to_return=(
                "SELECT country, SUM(amount) FROM orders "
                "WHERE status = 'completado' GROUP BY country LIMIT 10"
            )
        )

        # Monkeypatch get_llm_client to return our fake LLM
        import app.main

        monkeypatch.setattr(app.main, "get_llm_client", lambda s: fake_llm)

        client = make_client(settings=fake_settings)

        response = client.post("/ask", json={"question": "cuanto vendimos por pais"})

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "cuanto vendimos por pais"
        assert "sql" in data
        assert "columns" in data
        assert "rows" in data
        assert "row_count" in data
        assert isinstance(data["columns"], list)
        assert isinstance(data["rows"], list)
        assert isinstance(data["row_count"], int)
        assert data["row_count"] == len(data["rows"])

    def test_ask_llm_error_returns_502(self, temp_db, fake_settings, monkeypatch):
        """Test LLM error returns 502 LLM_UNAVAILABLE."""
        fake_llm = FakeLLM(error=LLMError("LLM unavailable"))

        import app.main

        monkeypatch.setattr(app.main, "get_llm_client", lambda s: fake_llm)

        client = make_client(settings=fake_settings)

        response = client.post("/ask", json={"question": "cuanto vendimos"})

        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"]["code"] == "LLM_UNAVAILABLE"
        assert "LLM unavailable" in data["detail"]["error"]["message"]

    def test_ask_invalid_sql_returns_422(self, temp_db, fake_settings, monkeypatch):
        """Test dangerous SQL from LLM returns 422 INVALID_SQL."""
        fake_llm = FakeLLM(sql_to_return="DROP TABLE orders")

        import app.main

        monkeypatch.setattr(app.main, "get_llm_client", lambda s: fake_llm)

        client = make_client(settings=fake_settings)

        response = client.post("/ask", json={"question": "borra todos los pedidos"})

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_SQL"

    def test_ask_without_api_key_returns_503(self, temp_db, monkeypatch):
        """Test missing API key returns 503 LLM_NOT_CONFIGURED."""
        test_settings = Settings(
            nvidia_api_key=None,
            nvidia_base_url="https://test.example.com",
            nvidia_model=None,
            db_path=temp_db,
        )

        # Monkeypatch get_settings where it's used (app.main)
        import app.main

        monkeypatch.setattr(app.main, "get_settings", lambda: test_settings)

        client = make_client()
        response = client.post("/ask", json={"question": "cuanto vendimos"})

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["error"]["code"] == "LLM_NOT_CONFIGURED"

    def test_health_endpoint(self, temp_db, fake_settings):
        """Test health endpoint returns ok."""
        client = make_client(settings=fake_settings)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_ask_invalid_question_too_long(self, temp_db, fake_settings):
        """Test question exceeding 500 chars returns 422."""
        client = make_client(settings=fake_settings)

        long_question = "a" * 501
        response = client.post("/ask", json={"question": long_question})
        assert response.status_code == 422

    def test_ask_empty_question(self, temp_db, fake_settings):
        """Test empty question returns 422."""
        client = make_client(settings=fake_settings)

        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 422
