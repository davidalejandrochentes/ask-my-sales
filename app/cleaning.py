from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

SPANISH_MONTHS = {
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


@dataclass
class CleanResult:
    valid: list[dict]
    rejected: list[tuple[dict, str]]
    duplicates_removed: int
    dates_normalized: int
    rejected_invalid_date: int
    rejected_empty_amount: int


def parse_date(raw: str) -> str | None:
    s = raw.strip()
    if not s:
        return None

    # YYYY-MM-DD
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        try:
            y, m, d = int(s[:4]), int(s[5:7]), int(s[8:10])
            date(y, m, d)
            return s
        except ValueError:
            return None

    # DD/MM/YYYY
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
                return f"{y:04d}-{m:02d}-{d:02d}"
            except ValueError:
                return None

    # DD-MM-YYYY (but not YYYY-MM-DD which we already checked)
    if "-" in s and not (len(s) == 10 and s[4] == "-" and s[7] == "-"):
        parts = s.split("-")
        if len(parts) == 3:
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                date(y, m, d)
                return f"{y:04d}-{m:02d}-{d:02d}"
            except ValueError:
                return None

    # D mmm YYYY (Spanish month abbreviations)
    parts = s.split()
    if len(parts) == 3:
        try:
            d = int(parts[0])
            m_str = parts[1].lower()
            y = int(parts[2])
            if m_str in SPANISH_MONTHS:
                m = SPANISH_MONTHS[m_str]
                date(y, m, d)
                return f"{y:04d}-{m:02d}-{d:02d}"
        except (ValueError, IndexError):
            return None

    return None


def parse_amount(raw: str) -> float | None:
    s = raw.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def clean_rows(raw_rows: Iterable[dict]) -> CleanResult:
    normalized_rows: list[dict] = []
    rejected: list[tuple[dict, str]] = []
    dates_normalized = 0
    rejected_invalid_date = 0
    rejected_empty_amount = 0

    for row in raw_rows:
        stripped = {k: v.strip() for k, v in row.items()}

        # Parse date first (priority)
        iso_date = parse_date(stripped["fecha"])
        if iso_date is None:
            rejected.append((row, "invalid_date"))
            rejected_invalid_date += 1
            continue

        # Check if date was normalized (wasn't already YYYY-MM-DD)
        if stripped["fecha"] != iso_date:
            dates_normalized += 1

        # Parse amount
        amount = parse_amount(stripped["importe"])
        if amount is None:
            rejected.append((row, "empty_amount"))
            rejected_empty_amount += 1
            continue

        # Build normalized row
        norm_row = {
            "fecha": iso_date,
            "cliente": stripped["cliente"],
            "pais": stripped["pais"],
            "producto": stripped["producto"],
            "importe": amount,
            "estado": stripped["estado"],
        }

        normalized_rows.append(norm_row)

    # Deduplicate: keep first occurrence
    seen_keys: set = set()
    valid_rows: list[dict] = []
    for row in normalized_rows:
        key = (
            row["fecha"],
            row["cliente"],
            row["pais"],
            row["producto"],
            row["importe"],
            row["estado"],
        )
        if key not in seen_keys:
            seen_keys.add(key)
            valid_rows.append(row)

    duplicates_removed = len(normalized_rows) - len(valid_rows)

    return CleanResult(
        valid=valid_rows,
        rejected=rejected,
        duplicates_removed=duplicates_removed,
        dates_normalized=dates_normalized,
        rejected_invalid_date=rejected_invalid_date,
        rejected_empty_amount=rejected_empty_amount,
    )
