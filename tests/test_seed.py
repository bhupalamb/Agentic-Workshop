import sqlite3
from pathlib import Path

from load_seed import load


def test_tables_created(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"tickets", "customers"} == tables


def test_tickets_columns(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(tickets)")]
    assert cols == ["ticket_id", "customer_id", "created_at", "text"]


def test_customers_columns(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(customers)")]
    assert cols == ["customer_id", "name", "plan", "open_tickets"]


def test_tickets_populated(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    assert count > 0


def test_customers_populated(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    assert count > 0


def test_idempotent(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        first = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        second = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    assert first == second


def test_known_ticket(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT customer_id FROM tickets WHERE ticket_id = ?", ("T-1042",)
        ).fetchone()
    assert row is not None
    assert row[0] == "C-77"


def test_known_customer(tmp_path):
    db = tmp_path / "test.db"
    load(db_path=db)
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT plan, open_tickets FROM customers WHERE customer_id = ?", ("C-05",)
        ).fetchone()
    assert row is not None
    assert row[0] == "Enterprise"
    assert row[1] == 4  # open_tickets is stored as INTEGER
