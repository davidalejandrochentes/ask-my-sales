import pytest
from app.validator import validate_sql, InvalidSQLError


class TestValidSQL:
    @pytest.mark.parametrize("sql", [
        "SELECT * FROM orders",
        "SELECT order_date, customer, amount FROM orders WHERE status = 'completado'",
        "SELECT country, SUM(amount) FROM orders GROUP BY country",
        "SELECT strftime('%Y-%m', order_date) AS month, SUM(amount) FROM orders GROUP BY month",
        "SELECT customer, COUNT(*) AS orders, SUM(amount) AS total_spent FROM orders WHERE status = 'completado' GROUP BY customer ORDER BY total_spent DESC LIMIT 10",
        "WITH completed AS (SELECT * FROM orders WHERE status = 'completado') SELECT * FROM completed",
        "WITH cte1 AS (SELECT * FROM orders), cte2 AS (SELECT * FROM sales_by_month_country) SELECT * FROM cte1 JOIN cte2 ON cte1.country = cte2.country",
    ])
    def test_valid_select_statements(self, sql: str):
        result = validate_sql(sql)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("sql,expected_func", [
        ("SELECT SUM(amount) FROM orders", "SUM"),
        ("SELECT COUNT(*) FROM orders", "COUNT"),
        ("SELECT AVG(amount) FROM orders", "AVG"),
        ("SELECT MIN(amount) FROM orders", "MIN"),
        ("SELECT MAX(amount) FROM orders", "MAX"),
        ("SELECT ROUND(amount, 2) FROM orders", "ROUND"),
        ("SELECT strftime('%Y-%m', order_date) FROM orders", "STRFTIME"),
        ("SELECT substr(order_date, 1, 4) FROM orders", "SUBSTR"),
        ("SELECT lower(customer) FROM orders", "LOWER"),
        ("SELECT upper(country) FROM orders", "UPPER"),
        ("SELECT coalesce(amount, 0) FROM orders", "COALESCE"),
        ("SELECT date(order_date) FROM orders", "DATE"),
        ("SELECT abs(amount) FROM orders", "ABS"),
    ])
    def test_allowed_functions(self, sql: str, expected_func: str):
        result = validate_sql(sql)
        assert isinstance(result, str)

    def test_adds_limit_when_missing(self):
        sql = "SELECT * FROM orders"
        result = validate_sql(sql)
        assert "LIMIT 1000" in result.upper()

    def test_keeps_existing_limit(self):
        sql = "SELECT * FROM orders LIMIT 50"
        result = validate_sql(sql)
        assert "LIMIT 50" in result.upper()

    def test_allows_cte_aliases(self):
        sql = """
        WITH my_cte AS (SELECT * FROM orders WHERE status = 'completado')
        SELECT customer, SUM(amount) FROM my_cte GROUP BY customer
        """
        result = validate_sql(sql)
        assert isinstance(result, str)


class TestInvalidSQL:
    @pytest.mark.parametrize("sql", [
        "DROP TABLE orders",
        "DROP VIEW sales_by_month_country",
    ])
    def test_rejects_drop(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "UPDATE orders SET amount = 0",
        "UPDATE orders SET status = 'cancelado' WHERE amount < 10",
    ])
    def test_rejects_update(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "INSERT INTO orders VALUES (1, '2025-01-01', 'C1', 'ES', 'Prod', 100, 'completado')",
        "INSERT INTO orders (order_date, customer) VALUES ('2025-01-01', 'C1')",
    ])
    def test_rejects_insert(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "DELETE FROM orders",
        "DELETE FROM orders WHERE status = 'cancelado'",
    ])
    def test_rejects_delete(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "CREATE TABLE test (id INT)",
        "CREATE VIEW test_view AS SELECT * FROM orders",
    ])
    def test_rejects_create(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "ALTER TABLE orders ADD COLUMN test INT",
        "ALTER TABLE orders DROP COLUMN test",
    ])
    def test_rejects_alter(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "PRAGMA table_info(orders)",
        "PRAGMA foreign_keys = ON",
    ])
    def test_rejects_pragma(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "SELECT 1 UNION SELECT 2",
        "SELECT * FROM orders UNION SELECT * FROM orders",
    ])
    def test_rejects_union(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "SELECT * FROM orders; SELECT * FROM orders",
        "SELECT 1; SELECT 2",
    ])
    def test_rejects_multiple_statements(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "SELECT * FROM sqlite_master",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM non_existent_table",
    ])
    def test_rejects_disallowed_tables(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "SELECT * FROM orders -- comment",
        "SELECT * FROM orders /* comment */",
        "SELECT * FROM orders /* multi\nline */",
    ])
    def test_rejects_comments(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    @pytest.mark.parametrize("sql", [
        "SELECT unknown_func(amount) FROM orders",
        "SELECT my_custom_function(col) FROM orders",
        "SELECT random() FROM orders",
    ])
    def test_rejects_unknown_functions(self, sql: str):
        with pytest.raises(InvalidSQLError):
            validate_sql(sql)

    def test_rejects_empty_sql(self):
        with pytest.raises(InvalidSQLError):
            validate_sql("")

    def test_rejects_only_semicolon(self):
        with pytest.raises(InvalidSQLError):
            validate_sql(";")

    def test_rejects_select_star_from_disallowed(self):
        with pytest.raises(InvalidSQLError):
            validate_sql("SELECT * FROM sqlite_master")


class TestErrorMessages:
    def test_error_message_contains_reason(self):
        with pytest.raises(InvalidSQLError) as exc_info:
            validate_sql("DROP TABLE orders")
        assert "DROP" in str(exc_info.value) or "drop" in str(exc_info.value).lower()

    def test_error_message_for_comment(self):
        with pytest.raises(InvalidSQLError) as exc_info:
            validate_sql("SELECT * FROM orders -- comment")
        assert "comment" in str(exc_info.value).lower()

    def test_error_message_for_unknown_function(self):
        with pytest.raises(InvalidSQLError) as exc_info:
            validate_sql("SELECT unknown_func(col) FROM orders")
        assert "function" in str(exc_info.value).lower() or "unknown" in str(exc_info.value).lower()