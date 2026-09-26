"""Load seed CSV files into app.db."""

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = ROOT / "seed"

# Columns that should be stored as integers rather than text.
_INT_COLUMNS = {"open_tickets"}


def load(db_path: Path | None = None) -> None:
    """Read seed CSVs and write them into the SQLite database (idempotent).

    CSV data is loaded into memory before the database is opened so that all
    DDL runs first (no pending DML → no implicit commits from legacy transaction
    control), followed by a single DML transaction covering both tables.
    """
    if db_path is None:
        db_path = ROOT / "app.db"

    tables = ("tickets", "customers")
    loaded = {table: _read_csv(table) for table in tables}

    with sqlite3.connect(db_path) as conn:
        # DDL phase: drop and recreate tables with no pending DML.
        for table, (columns, _) in loaded.items():
            cols_sql = ", ".join(
                f'"{c}" {"INTEGER" if c in _INT_COLUMNS else "TEXT"}'
                for c in columns
            )
            conn.execute(f'DROP TABLE IF EXISTS "{table}"')
            conn.execute(f'CREATE TABLE "{table}" ({cols_sql})')
        # DML phase: one transaction for both tables.
        for table, (columns, rows) in loaded.items():
            placeholders = ", ".join("?" for _ in columns)
            col_names = ", ".join(f'"{c}"' for c in columns)
            for row_values in rows:
                conn.execute(
                    f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders})',
                    row_values,
                )
        conn.commit()


def _read_csv(table: str) -> tuple[list[str], list[list]]:
    path = SEED / f"{table}.csv"
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames)
        rows = [[row[c] for c in columns] for row in reader]
    return columns, rows


if __name__ == "__main__":
    load()
    print(f"Loaded seed data into {ROOT / 'app.db'}")
