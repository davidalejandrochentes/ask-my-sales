import sqlite3
from pathlib import Path

import pytest

INSERT_ORDER = (
    "INSERT INTO orders (order_date, customer, country, product, amount, status) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)


@pytest.fixture
def temp_db(tmp_path: Path) -> str:
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
    conn.commit()
    yield str(db_path)
    conn.close()


def apply_views(conn: sqlite3.Connection) -> None:
    views_sql = Path("sql/views.sql").read_text(encoding="utf-8")
    for statement in views_sql.split(";"):
        stmt = statement.strip()
        if stmt:
            conn.execute(stmt)
    conn.commit()


class TestSalesByMonthCountry:
    def test_columns_and_order(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        # Insert test data: completed orders across months and countries
        conn.executemany(
            INSERT_ORDER,
            [
                ("2025-01-15", "C1", "España", "Teclado", 100.0, "completado"),
                ("2025-01-20", "C2", "México", "Ratón", 50.0, "completado"),
                ("2025-02-10", "C3", "España", "Monitor", 200.0, "completado"),
                ("2025-02-15", "C4", "Argentina", "Portátil", 300.0, "completado"),
                ("2025-01-25", "C5", "España", "Auriculares", 75.0, "pendiente"),  # not completed
            ],
        )
        conn.commit()

        apply_views(conn)

        cursor = conn.execute("SELECT * FROM sales_by_month_country")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        assert columns == ["month", "country", "orders", "total_sales"]
        assert len(rows) == 4  # 4 completed orders across 2 months, 3 countries

        # Check order: by month, then country
        assert rows[0][0] == "2025-01"  # month
        assert rows[0][1] == "España"  # country
        assert rows[1][0] == "2025-01"
        assert rows[1][1] == "México"
        assert rows[2][0] == "2025-02"
        assert rows[2][1] == "Argentina"
        assert rows[3][0] == "2025-02"
        assert rows[3][1] == "España"

        conn.close()

    def test_only_completed_orders(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        conn.executemany(
            INSERT_ORDER,
            [
                ("2025-01-15", "C1", "España", "Teclado", 100.0, "completado"),
                ("2025-01-20", "C2", "México", "Ratón", 50.0, "pendiente"),
                ("2025-01-25", "C3", "Argentina", "Monitor", 200.0, "cancelado"),
            ],
        )
        conn.commit()

        apply_views(conn)

        cursor = conn.execute("SELECT * FROM sales_by_month_country")
        rows = cursor.fetchall()

        # Only 1 completed order should appear
        assert len(rows) == 1
        assert rows[0][1] == "España"
        assert rows[0][2] == 1  # orders count
        assert rows[0][3] == 100.0  # total_sales

        conn.close()

    def test_total_sales_rounded_to_two_decimals(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        conn.executemany(
            INSERT_ORDER,
            [
                ("2025-01-15", "C1", "España", "Teclado", 100.123, "completado"),
                ("2025-01-20", "C2", "España", "Ratón", 50.456, "completado"),
            ],
        )
        conn.commit()

        apply_views(conn)

        cursor = conn.execute("SELECT total_sales FROM sales_by_month_country")
        row = cursor.fetchone()
        # 100.123 + 50.456 = 150.579 -> rounded to 150.58
        assert row[0] == 150.58

        conn.close()


class TestTopCustomers:
    def test_columns_and_limit_10(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        # Insert 12 completed orders from different customers
        data = [
            (f"2025-01-{i:02d}", f"Customer_{i}", "España", "Prod", float(i * 100), "completado")
            for i in range(1, 13)
        ]
        conn.executemany(INSERT_ORDER, data)
        conn.commit()

        apply_views(conn)

        cursor = conn.execute("SELECT * FROM top_customers")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        assert columns == ["customer", "orders", "total_spent"]
        assert len(rows) == 10  # LIMIT 10

        conn.close()

    def test_order_by_total_spent_desc_customer_asc(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        # Customer_A: 2 orders, total 300
        # Customer_B: 1 order, total 500 (should be first)
        # Customer_C: 3 orders, total 300 (tie with A, but C > A alphabetically)
        conn.executemany(
            INSERT_ORDER,
            [
                ("2025-01-15", "Customer_A", "España", "Teclado", 100.0, "completado"),
                ("2025-01-20", "Customer_A", "España", "Ratón", 200.0, "completado"),
                ("2025-01-10", "Customer_B", "México", "Monitor", 500.0, "completado"),
                ("2025-01-25", "Customer_C", "Argentina", "Portátil", 100.0, "completado"),
                ("2025-01-28", "Customer_C", "Argentina", "Auriculares", 100.0, "completado"),
                ("2025-01-30", "Customer_C", "Argentina", "Webcam", 100.0, "completado"),
            ],
        )
        conn.commit()

        apply_views(conn)

        cursor = conn.execute("SELECT customer, total_spent FROM top_customers")
        rows = cursor.fetchall()

        # Order: B (500), A (300), C (300) - but C comes after A alphabetically in tie
        assert rows[0][0] == "Customer_B"
        assert rows[0][1] == 500.0
        assert rows[1][0] == "Customer_A"
        assert rows[1][1] == 300.0
        assert rows[2][0] == "Customer_C"
        assert rows[2][1] == 300.0

        conn.close()

    def test_only_completed_orders(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        conn.executemany(
            INSERT_ORDER,
            [
                ("2025-01-15", "C1", "España", "Teclado", 100.0, "completado"),
                ("2025-01-20", "C2", "México", "Ratón", 500.0, "pendiente"),
                ("2025-01-25", "C3", "Argentina", "Monitor", 200.0, "cancelado"),
            ],
        )
        conn.commit()

        apply_views(conn)

        cursor = conn.execute("SELECT * FROM top_customers")
        rows = cursor.fetchall()

        assert len(rows) == 1
        assert rows[0][0] == "C1"
        assert rows[0][2] == 100.0

        conn.close()


class TestViewTotalsMatch:
    def test_sales_by_month_country_sum_matches_orders(self, temp_db: str):
        conn = sqlite3.connect(temp_db)
        conn.executemany(
            INSERT_ORDER,
            [
                ("2025-01-15", "C1", "España", "Teclado", 100.12, "completado"),
                ("2025-01-20", "C2", "México", "Ratón", 50.34, "completado"),
                ("2025-02-10", "C3", "España", "Monitor", 200.56, "completado"),
                ("2025-02-15", "C4", "Argentina", "Portátil", 300.78, "completado"),
                ("2025-01-25", "C5", "España", "Auriculares", 75.90, "pendiente"),
                ("2025-01-28", "C6", "México", "Webcam", 150.00, "cancelado"),
            ],
        )
        conn.commit()

        apply_views(conn)

        # Sum from view
        cursor = conn.execute("SELECT SUM(total_sales) FROM sales_by_month_country")
        view_sum = cursor.fetchone()[0]

        # Sum from orders table (only completado)
        cursor = conn.execute("SELECT SUM(amount) FROM orders WHERE status = 'completado'")
        orders_sum = cursor.fetchone()[0]

        assert view_sum == round(orders_sum, 2)

        conn.close()
