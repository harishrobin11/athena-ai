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
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id INTEGER,
        role TEXT,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()


def create_conversation(title, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO conversations(title, user_id)
        VALUES (?, ?)
        """,
        (title, user_id),
    )

    conn.commit()

    conversation_id = cursor.lastrowid

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

def list_conversations(user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, created_at
    FROM conversations
    WHERE user_id = ?
    ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows

def get_messages(conversation_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, content
    FROM messages
    WHERE conversation_id=?
    ORDER BY id ASC
    """, (conversation_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows

def update_conversation_title(
    conversation_id,
    title,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE conversations
        SET title=?
        WHERE id=?
        """,
        (
            title,
            conversation_id,
        ),
    )

    conn.commit()
    conn.close()
def search_conversations(
    query,
    user_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, created_at
    FROM conversations
    WHERE user_id = ?
    AND title LIKE ?
    ORDER BY id DESC
    """, (
        user_id,
        f"%{query}%"
    ))

    rows = cursor.fetchall()

    conn.close()

    return rows

def delete_conversation(
    conversation_id,
    user_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM conversations
    WHERE id = ?
    AND user_id = ?
    """, (
        conversation_id,
        user_id
    ))

    conn.commit()
    conn.close()
def get_stats():
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM documents"
    )
    documents = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM conversations"
    )
    conversations = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM messages"
    )
    messages = cursor.fetchone()[0]

    conn.close()

    return {
        "documents": documents,
        "conversations": conversations,
        "messages": messages,
    }
def create_user(
    username: str,
    email: str,
    password_hash: str
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (username, email, password_hash)
        VALUES (?, ?, ?)
    """, (
        username,
        email,
        password_hash
    ))

    conn.commit()
    conn.close()
def get_user_by_username(username: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()

    conn.close()

    return user
def get_conversation_owner(
    conversation_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT user_id
    FROM conversations
    WHERE id = ?
    """, (conversation_id,))

    row = cursor.fetchone()

    conn.close()

    return row

def create_document(
    user_id,
    filename
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO documents(
        user_id,
        filename
    )
    VALUES (?, ?)
    """, (
        user_id,
        filename
    ))

    conn.commit()
    conn.close()
def list_documents_by_user(
    user_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT filename
    FROM documents
    WHERE user_id = ?
    ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()

    conn.close()

    return rows

def delete_document_by_user(
    filename,
    user_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    DELETE FROM documents
    WHERE filename = ?
    AND user_id = ?
    """, (
        filename,
        user_id
    ))

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted > 0

def owns_document(
    filename,
    user_id
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM documents
    WHERE filename = ?
    AND user_id = ?
    """, (
        filename,
        user_id
    ))

    row = cursor.fetchone()

    conn.close()

    return row is not None