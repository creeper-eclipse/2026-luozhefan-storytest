import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        input_text TEXT NOT NULL,
        output_data TEXT NOT NULL,
        created_at TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def add_record(type: str, input_text: str, output_data: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO history (type, input_text, output_data, created_at) VALUES (?,?,?,?)",
              (type, input_text, json.dumps(output_data, ensure_ascii=False), datetime.now().isoformat()))
    conn.commit()
    record_id = c.lastrowid
    conn.close()
    return record_id

def get_records(type_filter: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: int = 50) -> list:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = "SELECT id, type, input_text, output_data, created_at FROM history WHERE 1=1"
    params = []
    if type_filter:
        query += " AND type=?"
        params.append(type_filter)
    if start_date:
        query += " AND date(created_at) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(created_at) <= date(?)"
        params.append(end_date)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [{"id": row[0], "type": row[1], "input_text": row[2], "output_data": json.loads(row[3]), "created_at": row[4]} for row in rows]

def delete_record(record_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM history WHERE id=?", (record_id,))
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0

def update_record(record_id: int, input_text: Optional[str] = None, output_data: Optional[dict] = None) -> bool:
    """更新记录的 input_text 和/或 output_data"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updates = []
    params = []
    if input_text is not None:
        updates.append("input_text=?")
        params.append(input_text)
    if output_data is not None:
        updates.append("output_data=?")
        params.append(json.dumps(output_data, ensure_ascii=False))
    if not updates:
        conn.close()
        return False
    params.append(record_id)
    query = f"UPDATE history SET {', '.join(updates)} WHERE id=?"
    c.execute(query, params)
    conn.commit()
    affected = c.rowcount
    conn.close()
    return affected > 0