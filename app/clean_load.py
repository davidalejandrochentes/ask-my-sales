import csv
import os
from pathlib import Path

from app.cleaning import clean_rows
from app.db import connect_rw


def main() -> None:
    db_path = os.getenv("DB_PATH", "data/orders.db")
    csv_path = Path("data/raw/orders_dirty.csv")
    rejected_path = Path("data/rejected.csv")

    # Read CSV
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_rows = list(reader)

    # Clean rows
    result = clean_rows(raw_rows)

    # Recreate orders table and insert
    conn = connect_rw(db_path)
    try:
        conn.execute("DROP TABLE IF EXISTS orders")
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

        for row in result.valid:
            conn.execute(
                "INSERT INTO orders (order_date, customer, country, product, amount, status) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    row["fecha"],
                    row["cliente"],
                    row["pais"],
                    row["producto"],
                    row["importe"],
                    row["estado"],
                ),
            )

        # Apply views
        views_sql = Path("sql/views.sql").read_text(encoding="utf-8")
        for statement in views_sql.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(stmt)

        conn.commit()
    finally:
        conn.close()

    # Write rejected rows
    rejected_path.parent.mkdir(parents=True, exist_ok=True)
    with rejected_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["fecha", "cliente", "pais", "producto", "importe", "estado", "reason"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row, reason in result.rejected:
            out_row = dict(row)
            out_row["reason"] = reason
            writer.writerow(out_row)

    # Print summary
    print(  # noqa: T201
        f"rows_in={len(raw_rows)}, loaded={len(result.valid)}, "
        f"duplicates_removed={result.duplicates_removed}, "
        f"rejected_invalid_date={result.rejected_invalid_date}, "
        f"rejected_empty_amount={result.rejected_empty_amount}, "
        f"dates_normalized={result.dates_normalized}"
    )


if __name__ == "__main__":
    main()
