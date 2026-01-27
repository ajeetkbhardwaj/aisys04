import sqlite3
import os

DB_PATH = "claims.db"

def setup_db():
    """Initializes a dummy database with orders."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS orders")
    cursor.execute("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            amount REAL,
            customer_tier TEXT
        )
    """)
    
    # Seed Data
    # ORD-123: High value (Trigger Human Review)
    # ORD-456: Low value (Auto Approve)
    data = [
        ("ORD-123", 1500.00, "VIP"),
        ("ORD-456", 50.00, "REGULAR")
    ]
    cursor.executemany("INSERT INTO orders VALUES (?,?,?)", data)
    conn.commit()
    conn.close()
    print("✅ Database initialized with dummy orders.")

def get_order_details(order_id: str):
    """Fetches order details from SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT amount, customer_tier FROM orders WHERE order_id=?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"amount": row[0], "tier": row[1]}
    return None

if __name__ == "__main__":
    setup_db()