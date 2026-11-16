from app.llm import _postprocess_response


class TestPostprocessResponse:
    def test_plain_sql(self):
        sql = "SELECT * FROM orders"
        result = _postprocess_response(sql)
        assert result == "SELECT * FROM orders"

    def test_sql_with_fences(self):
        raw = "```sql\nSELECT * FROM orders\n```"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_sql_with_fences_no_language(self):
        raw = "```\nSELECT * FROM orders\n```"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_sql_with_whitespace_around_fences(self):
        raw = "  ```sql\nSELECT * FROM orders\n```  "
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_think_block_removed(self):
        raw = "```question\nSome reasoning\n```\nSELECT * FROM orders"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_think_block_with_answer(self):
        raw = "```question\nThinking...\n```\n```sql\nSELECT * FROM orders\n```"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_multiple_think_blocks(self):
        raw = "```question\nFirst\n```\n```question\nSecond\n```\nSELECT * FROM orders"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_think_block_multiline(self):
        raw = "```question\nLine 1\nLine 2\nLine 3\n```\nSELECT * FROM orders"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_whitespace_stripped(self):
        raw = "  \n  SELECT * FROM orders  \n  "
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"

    def test_empty_string(self):
        result = _postprocess_response("")
        assert result == ""

    def test_only_whitespace(self):
        result = _postprocess_response("   \n\t  ")
        assert result == ""

    def test_only_think_block(self):
        raw = "```question\nJust thinking\n```"
        result = _postprocess_response(raw)
        assert result == ""

    def test_only_fences(self):
        raw = "```sql\n```"
        result = _postprocess_response(raw)
        assert result == ""

    def test_complex_realistic(self):
        raw = (
            "```question\nThe user wants to know sales in Spain.\n"
            "I need to filter by country and status.\n```\n"
            "```sql\n"
            "SELECT SUM(amount) FROM orders "
            "WHERE country = 'España' AND status = 'completado'\n"
            "```"
        )
        result = _postprocess_response(raw)
        expected = (
            "SELECT SUM(amount) FROM orders " "WHERE country = 'España' AND status = 'completado'"
        )
        assert result == expected

    def test_fences_with_newlines(self):
        raw = "```sql\nSELECT 1\n```\n"
        result = _postprocess_response(raw)
        assert result == "SELECT 1"

    def test_no_fences_but_whitespace(self):
        raw = "\n\nSELECT * FROM orders\n\n"
        result = _postprocess_response(raw)
        assert result == "SELECT * FROM orders"
