
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('issues.db')
    c = conn.cursor()
    
    # Create issues table
    c.execute('''
        CREATE TABLE IF NOT EXISTS issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            user_name TEXT,
            title TEXT,
            category TEXT,
            description TEXT,
            location TEXT,
            ward TEXT,
            latitude REAL,
            longitude REAL,
            image TEXT,
            status TEXT DEFAULT 'not_resolved',
            timestamp TEXT,
            department TEXT,
            assigned_to TEXT,
            assigned_to_name TEXT,
            assigned_time TEXT,
            assigned_by TEXT,
            resolved_image TEXT,
            resolved_photo_timestamp TEXT,
            resolved_by TEXT,
            resolved_by_name TEXT,
            status_note TEXT,
            status_updated TEXT,
            status_updated_by TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_db():
    conn = sqlite3.connect('issues.db')
    conn.row_factory = dict_factory
    return conn
