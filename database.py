import sqlite3, os
from datetime import datetime

DB_PATH = "pneumoai.db"

def init_db():
    os.makedirs("uploads", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    
    # Original scans table
    con.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT,
            filepath    TEXT,
            result      TEXT,
            confidence  REAL,
            has_ptx     INTEGER,
            created_at  TEXT
        )
    """)
    
    # NEW: Users table
    con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT UNIQUE NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT
        )
    """)
    
    # Add user_id column to scans (if not exists)
    try:
        con.execute("ALTER TABLE scans ADD COLUMN user_id INTEGER REFERENCES users(id)")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    con.commit()
    con.close()

def save_scan(filename, filepath, result, confidence, has_ptx, user_id=None):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT INTO scans (filename, filepath, result, confidence, has_ptx, created_at, user_id)
        VALUES (?,?,?,?,?,?,?)
    """, (filename, filepath, result, confidence,
          int(has_ptx), datetime.now().isoformat(), user_id))
    con.commit()
    con.close()

def get_history(limit=20, user_id=None):
    con = sqlite3.connect(DB_PATH)
    if user_id is not None:
        rows = con.execute("""
            SELECT id, filename, result, confidence, has_ptx, created_at
            FROM scans WHERE user_id = ? ORDER BY id DESC LIMIT ?
        """, (user_id, limit)).fetchall()
    else:
        rows = con.execute("""
            SELECT id, filename, result, confidence, has_ptx, created_at
            FROM scans ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    con.close()
    return [{"id":r[0],"filename":r[1],"result":r[2],
             "confidence":r[3],"has_ptx":bool(r[4]),
             "created_at":r[5]} for r in rows]

def get_stats(user_id=None):
    con = sqlite3.connect(DB_PATH)
    if user_id is not None:
        total   = con.execute("SELECT COUNT(*) FROM scans WHERE user_id=?", (user_id,)).fetchone()[0]
        pos     = con.execute("SELECT COUNT(*) FROM scans WHERE has_ptx=1 AND user_id=?", (user_id,)).fetchone()[0]
        avg_conf= con.execute("SELECT AVG(confidence) FROM scans WHERE user_id=?", (user_id,)).fetchone()[0]
    else:
        total   = con.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
        pos     = con.execute("SELECT COUNT(*) FROM scans WHERE has_ptx=1").fetchone()[0]
        avg_conf= con.execute("SELECT AVG(confidence) FROM scans").fetchone()[0]
    con.close()
    return {"total": total, "positive": pos,
            "negative": total - pos,
            "avg_confidence": round(avg_conf or 0, 4)}