# migrate_db.py - Run this ONCE before starting the updated app
import sqlite3
from auth import get_password_hash

DB_PATH = "pneumoai.db"

con = sqlite3.connect(DB_PATH)

# Add user_id column to scans if not exists
try:
    con.execute("ALTER TABLE scans ADD COLUMN user_id INTEGER REFERENCES users(id)")
    print("✅ Added user_id column to scans table")
except sqlite3.OperationalError:
    print("ℹ️ user_id column already exists")

# Create users table if not exists
con.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT
    )
""")
print("✅ Users table ready")

# Create a default admin user (username: admin, password: admin123)
admin_pw = get_password_hash("admin123")
try:
    con.execute("INSERT INTO users (username, email, hashed_password, created_at) VALUES (?, ?, ?, ?)",
                ("admin", "admin@example.com", admin_pw, "2025-01-01T00:00:00"))
    print("✅ Created admin user: admin / admin123")
except sqlite3.IntegrityError:
    print("ℹ️ Admin user already exists")

con.commit()
con.close()
print("Migration complete!")