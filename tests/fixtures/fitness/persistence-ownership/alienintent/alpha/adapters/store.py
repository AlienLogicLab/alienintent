"""The declared owner of the ledger table."""
import sqlite3

SCHEMA = "CREATE TABLE ledger (id INTEGER NOT NULL)"


def open_store(path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute(SCHEMA)
    return connection
