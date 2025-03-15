
import sqlite3
import os
from flask import g

DATABASE = 'issues.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            ward TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            image TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            department TEXT,
            assigned_to TEXT,
            assigned_to_name TEXT,
            assigned_time TEXT,
            resolved_image TEXT,
            resolved_photo_timestamp TEXT,
            resolved_by TEXT,
            resolved_by_name TEXT,
            status_updated TEXT,
            status_updated_by TEXT,
            status_note TEXT
        )
        ''')
        conn.commit()
