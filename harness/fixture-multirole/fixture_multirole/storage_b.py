"""Candidate backend B: sqlite3's key-value table. Stubbed, not wired into cli.py."""


def save(path, data):
    import json
    import sqlite3

    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT)")
    conn.execute("INSERT OR REPLACE INTO kv VALUES ('data', ?)", (json.dumps(data),))
    conn.commit()
    conn.close()


def load(path):
    import json
    import sqlite3

    conn = sqlite3.connect(path)
    row = conn.execute("SELECT v FROM kv WHERE k='data'").fetchone()
    conn.close()
    return json.loads(row[0]) if row else None
