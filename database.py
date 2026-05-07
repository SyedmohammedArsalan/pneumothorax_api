import sqlite3, os
from datetime import datetime

DB_PATH = "pneumoai.db"

def init_db():
    os.makedirs("uploads", exist_ok=True)
    con = sqlite3.connect(DB_PATH)
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
    con.commit(); con.close()

def save_scan(filename, filepath, result, confidence, has_ptx):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT INTO scans (filename,filepath,result,confidence,has_ptx,created_at)
        VALUES (?,?,?,?,?,?)
    """, (filename, filepath, result, confidence,
          int(has_ptx), datetime.now().isoformat()))
    con.commit(); con.close()

def get_history(limit=20):
    con = sqlite3.connect(DB_PATH)
    rows = con.execute("""
        SELECT id,filename,result,confidence,has_ptx,created_at
        FROM scans ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    con.close()
    return [{"id":r[0],"filename":r[1],"result":r[2],
             "confidence":r[3],"has_ptx":bool(r[4]),
             "created_at":r[5]} for r in rows]

def get_stats():
    con = sqlite3.connect(DB_PATH)
    total   = con.execute("SELECT COUNT(*) FROM scans").fetchone()[0]
    pos     = con.execute("SELECT COUNT(*) FROM scans WHERE has_ptx=1").fetchone()[0]
    avg_conf= con.execute("SELECT AVG(confidence) FROM scans").fetchone()[0]
    con.close()
    return {"total": total, "positive": pos,
            "negative": total - pos,
            "avg_confidence": round(avg_conf or 0, 4)}