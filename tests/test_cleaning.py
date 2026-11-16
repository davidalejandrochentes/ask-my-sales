from app.cleaning import clean_rows, parse_amount, parse_date


class TestParseDate:
    def test_iso_format(self):
        assert parse_date("2025-01-15") == "2025-01-15"
        assert parse_date("2025-12-31") == "2025-12-31"
        assert parse_date("2025-06-01") == "2025-06-01"

    def test_dd_mm_yyyy(self):
        assert parse_date("15/01/2025") == "2025-01-15"
        assert parse_date("31/12/2025") == "2025-12-31"
        assert parse_date("01/06/2025") == "2025-06-01"

    def test_dd_mm_yyyy_dash(self):
        assert parse_date("15-01-2025") == "2025-01-15"
        assert parse_date("31-12-2025") == "2025-12-31"
        assert parse_date("01-06-2025") == "2025-06-01"

    def test_d_mmm_yyyy_spanish(self):
        assert parse_date("15 ene 2025") == "2025-01-15"
        assert parse_date("31 dic 2025") == "2025-12-31"
        assert parse_date("1 mar 2025") == "2025-03-01"
        assert parse_date("15 MAY 2025") == "2025-05-15"
        assert parse_date("15 May 2025") == "2025-05-15"

    def test_invalid_dates(self):
        assert parse_date("2025-13-45") is None
        assert parse_date("31/02/2025") is None
        assert parse_date("ayer") is None
        assert parse_date("2025/3/") is None
        assert parse_date("no-fecha") is None
        assert parse_date("") is None
        assert parse_date("2025-00-00") is None
        assert parse_date("32/01/2025") is None
        assert parse_date("15/13/2025") is None
        assert parse_date("2025-2-30") is None
        assert parse_date("30 feb 2025") is None


class TestParseAmount:
    def test_valid_amounts(self):
        assert parse_amount("100.50") == 100.50
        assert parse_amount("5.00") == 5.00
        assert parse_amount("500.00") == 500.00
        assert parse_amount("  123.45  ") == 123.45
        assert parse_amount("0.01") == 0.01

    def test_invalid_amounts(self):
        assert parse_amount("") is None
        assert parse_amount("  ") is None
        assert parse_amount("abc") is None
        assert parse_amount("no-numero") is None


class TestCleanRows:
    def test_basic_cleaning(self):
        rows = [
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
            {
                "fecha": "15/02/2025",
                "cliente": "Cliente_002",
                "pais": "México",
                "producto": "Ratón",
                "importe": "50.00",
                "estado": "pendiente",
            },
            {
                "fecha": "15 mar 2025",
                "cliente": "Cliente_003",
                "pais": "Argentina",
                "producto": "Monitor",
                "importe": "200.00",
                "estado": "completado",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 3
        assert len(result.rejected) == 0
        assert result.dates_normalized == 2
        assert result.duplicates_removed == 0
        assert result.rejected_invalid_date == 0
        assert result.rejected_empty_amount == 0

    def test_invalid_date_rejected(self):
        rows = [
            {
                "fecha": "ayer",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_002",
                "pais": "México",
                "producto": "Ratón",
                "importe": "50.00",
                "estado": "pendiente",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 1
        assert len(result.rejected) == 1
        assert result.rejected[0][1] == "invalid_date"
        assert result.rejected_invalid_date == 1
        assert result.rejected_empty_amount == 0

    def test_empty_amount_rejected(self):
        rows = [
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "",
                "estado": "completado",
            },
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_002",
                "pais": "México",
                "producto": "Ratón",
                "importe": "50.00",
                "estado": "pendiente",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 1
        assert len(result.rejected) == 1
        assert result.rejected[0][1] == "empty_amount"
        assert result.rejected_empty_amount == 1
        assert result.rejected_invalid_date == 0

    def test_date_priority_over_amount(self):
        rows = [
            {
                "fecha": "ayer",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "",
                "estado": "completado",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 0
        assert len(result.rejected) == 1
        assert result.rejected[0][1] == "invalid_date"
        assert result.rejected_invalid_date == 1
        assert result.rejected_empty_amount == 0

    def test_whitespace_stripped(self):
        rows = [
            {
                "fecha": " 2025-01-15 ",
                "cliente": " Cliente_001 ",
                "pais": " España ",
                "producto": " Teclado ",
                "importe": " 100.50 ",
                "estado": " completado ",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 1
        v = result.valid[0]
        assert v["fecha"] == "2025-01-15"
        assert v["cliente"] == "Cliente_001"
        assert v["pais"] == "España"
        assert v["producto"] == "Teclado"
        assert v["importe"] == 100.50
        assert v["estado"] == "completado"

    def test_duplicates_removed(self):
        rows = [
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 1
        assert result.duplicates_removed == 2

    def test_duplicate_after_normalization(self):
        rows = [
            {
                "fecha": "2025-01-15",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
            {
                "fecha": "15/01/2025",
                "cliente": "Cliente_001",
                "pais": "España",
                "producto": "Teclado",
                "importe": "100.50",
                "estado": "completado",
            },
        ]
        result = clean_rows(rows)
        assert len(result.valid) == 1
        assert result.duplicates_removed == 1
        assert result.dates_normalized == 1


class TestCleanRowsIntegration:
    def test_real_csv_summary(self):
        import csv

        with open("data/raw/orders_dirty.csv", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        result = clean_rows(rows)

        assert result.duplicates_removed == 50
        assert result.rejected_invalid_date == 15
        assert result.rejected_empty_amount == 30
        assert result.dates_normalized == 40
        assert len(result.valid) == 955
        assert len(rows) == 1050
