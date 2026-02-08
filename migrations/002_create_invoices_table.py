""" 
Migration: Create products, clients, invoices and invoice_items tables
Version: 002
Description: Adds products and clients seed data and invoice schema
"""

import sqlite3
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import DATABASE_PATH


def upgrade():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Create migrations tracking table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check if this migration has already been applied
    cursor.execute("SELECT 1 FROM _migrations WHERE name = ?", ("002_create_invoices_table",))
    if cursor.fetchone():
        print("Migration 002_create_invoices_table already applied. Skipping.")
        conn.close()
        return

    # Create products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Create clients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            registration_no TEXT
        )
    """)

    # Create invoices table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_no TEXT NOT NULL,
            issue_date TEXT,
            due_date TEXT,
            client_id INTEGER,
            address TEXT,
            tax REAL DEFAULT 0.0,
            total REAL DEFAULT 0.0,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    # Create invoice_items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)

    # Seed sample products
    sample_products = [
        ("Widget A", 10.0),
        ("Widget B", 15.5),
        ("Service C", 50.0),
    ]
    cursor.executemany("INSERT INTO products (name, price) VALUES (?, ?)", sample_products)

    # Seed sample clients
    sample_clients = [
        ("Alice", "123 Main St", "REG-001"),
        ("Bob Inc", "456 Oak Ave", "REG-002"),
    ]
    cursor.executemany("INSERT INTO clients (name, address, registration_no) VALUES (?, ?, ?)", sample_clients)

    # Record this migration
    cursor.execute("INSERT INTO _migrations (name) VALUES (?)", ("002_create_invoices_table",))

    conn.commit()
    conn.close()
    print("Migration 002_create_invoices_table applied successfully.")


def downgrade():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS invoice_items")
    cursor.execute("DROP TABLE IF EXISTS invoices")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS clients")

    cursor.execute("DELETE FROM _migrations WHERE name = ?", ("002_create_invoices_table",))

    conn.commit()
    conn.close()
    print("Migration 002_create_invoices_table reverted successfully.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run database migration")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade"],
        help="Migration action to perform"
    )

    args = parser.parse_args()

    if args.action == "upgrade":
        upgrade()
    elif args.action == "downgrade":
        downgrade()
