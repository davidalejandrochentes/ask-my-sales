import csv
import random
from datetime import date, timedelta
from pathlib import Path

COUNTRIES = [
    "España",
    "México",
    "Argentina",
    "Colombia",
    "Chile",
    "Perú",
    "Ecuador",
    "Estados Unidos",
]

PRODUCTS = [
    "Teclado",
    "Ratón",
    "Monitor",
    "Portátil",
    "Auriculares",
    "Webcam",
    "Altavoz",
    "Disco SSD",
    "Cable USB-C",
    "Mochila",
]

STATUS_WEIGHTS = [
    ("completado", 70),
    ("pendiente", 15),
    ("cancelado", 15),
]

SPANISH_MONTHS = [
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
]

INVALID_DATES = [
    "ayer",
    "manana",
    "no-fecha",
    "fecha-invalida",
    "invalid",
    "2025/3/",
    "2025/13/01",
    "2025.01.01",
    "2025-01",
    "01-01",
    "31-13-2025",
    "32-01-2025",
    "2025-00-00",
    "2025-13-45",
    "30-feb-2025",
]


def random_date(rng: random.Random) -> date:
    start = date(2025, 1, 1)
    end = date(2025, 12, 31)
    delta = end - start
    random_days = rng.randint(0, delta.days)
    return start + timedelta(days=random_days)


def format_date_iso(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def format_date_dd_mm_yyyy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def format_date_dd_mm_yyyy_dash(d: date) -> str:
    return d.strftime("%d-%m-%Y")


def format_date_d_mmm_yyyy(d: date) -> str:
    return f"{d.day} {SPANISH_MONTHS[d.month - 1]} {d.year}"


def random_amount(rng: random.Random) -> str:
    value = rng.uniform(5.0, 500.0)
    return f"{value:.2f}"


def random_customer(rng: random.Random, num_customers: int = 150) -> str:
    return f"Cliente_{rng.randint(1, num_customers):03d}"


def random_country(rng: random.Random) -> str:
    return rng.choice(COUNTRIES)


def random_product(rng: random.Random) -> str:
    return rng.choice(PRODUCTS)


def random_status(rng: random.Random) -> str:
    choices = []
    for status, weight in STATUS_WEIGHTS:
        choices.extend([status] * weight)
    return rng.choice(choices)


def generate_clean_row(rng: random.Random, existing_keys: set) -> dict:
    while True:
        d = random_date(rng)
        fecha = format_date_iso(d)
        cliente = random_customer(rng)
        pais = random_country(rng)
        producto = random_product(rng)
        importe = random_amount(rng)
        estado = random_status(rng)

        key = (fecha, cliente, pais, producto, importe, estado)
        if key not in existing_keys:
            existing_keys.add(key)
            return {
                "fecha": fecha,
                "cliente": cliente,
                "pais": pais,
                "producto": producto,
                "importe": importe,
                "estado": estado,
            }


def generate_rows(seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    existing_keys: set = set()

    base_rows = []
    for _ in range(1000):
        row = generate_clean_row(rng, existing_keys)
        base_rows.append(row)

    rows = base_rows.copy()

    all_indices = list(range(1000))
    rng.shuffle(all_indices)

    dup_indices = all_indices[:50]
    for idx in dup_indices:
        rows.append(rows[idx].copy())

    date_alt_indices = all_indices[50:90]
    date_formats = [
        format_date_dd_mm_yyyy,
        format_date_dd_mm_yyyy_dash,
        format_date_d_mmm_yyyy,
    ]
    for i, idx in enumerate(date_alt_indices):
        d = date.fromisoformat(rows[idx]["fecha"])
        rows[idx]["fecha"] = date_formats[i % 3](d)

    invalid_indices = all_indices[90:105]
    for i, idx in enumerate(invalid_indices):
        rows[idx]["fecha"] = INVALID_DATES[i % len(INVALID_DATES)]

    empty_amount_indices = all_indices[105:135]
    for idx in empty_amount_indices:
        rows[idx]["importe"] = ""

    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["fecha", "cliente", "pais", "producto", "importe", "estado"]
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = generate_rows(42)
    write_csv(rows, Path("data/raw/orders_dirty.csv"))
    print(f"Generated {len(rows)} rows in data/raw/orders_dirty.csv")  # noqa: T201


if __name__ == "__main__":
    main()
