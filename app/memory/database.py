import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "conversations.db"


def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id) REFERENCES conversations(id)
    )
    """)

    conn.commit()
    conn.close()


def create_conversation(title="New Chat"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO conversations(title) VALUES(?)",
        (title,)
    )

    conversation_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return conversation_id


def save_message(conversation_id, role, content):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO messages(conversation_id, role, content)
    VALUES(?,?,?)
    """, (conversation_id, role, content))

    conn.commit()
    conn.close()


def load_history(conversation_id, limit=20):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, content
    FROM messages
    WHERE conversation_id=?
    ORDER BY id ASC
    LIMIT ?
    """, (conversation_id, limit))

    rows = cursor.fetchall()

    conn.close()

    return rows