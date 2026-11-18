"""SQLite connection and schema management."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path):
        self.path = Path(path)

    def _connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @contextmanager
    def read(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self):
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self.transaction() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL CHECK (length(trim(name)) BETWEEN 1 AND 100),
                    description TEXT NOT NULL DEFAULT '' CHECK (length(description) <= 500),
                    total_stock INTEGER NOT NULL CHECK (total_stock >= 0),
                    available_stock INTEGER NOT NULL CHECK (
                        available_stock >= 0 AND available_stock <= total_stock
                    ),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS loan_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipment_id INTEGER NOT NULL,
                    borrower_name TEXT NOT NULL CHECK (
                        length(trim(borrower_name)) BETWEEN 1 AND 100
                    ),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    loaned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    due_date TEXT NOT NULL,
                    returned_at TEXT,
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'returned')),
                    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE RESTRICT
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_loan_records_status ON loan_records(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_loan_records_equipment ON loan_records(equipment_id)"
            )
