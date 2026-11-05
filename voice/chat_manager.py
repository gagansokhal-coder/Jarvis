"""
Gagan AI Persistent Chat & Memory Management Engine.
Stores conversation sessions and messages like ChatGPT/Gemini in a lightweight SQLite database.
Supports session management, memory pruning/optimization, and instant search/retrieval.
"""

import os
import sqlite3
import datetime
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "chat_history.db")

os.makedirs(DATA_DIR, exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables for chat sessions and message logs."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_updated ON sessions(updated_at DESC)")
    conn.commit()
    conn.close()

init_db()

class ChatManager:
    @staticmethod
    def create_session(title: str = None) -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not title:
            title = f"Tactical Session {now[5:16]}"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now)
        )
        conn.commit()
        conn.close()
        return session_id

    @staticmethod
    def get_active_session() -> str:
        """Get the most recent session or create one if none exists."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sessions ORDER BY updated_at DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            return row["id"]
        return ChatManager.create_session("New Strategic Chat")

    @staticmethod
    def add_message(session_id: str, role: str, content: str, source: str = "voice"):
        """Save a message to the specified session."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        cursor = conn.cursor()

        # Update session title from first user query if still generic
        cursor.execute("SELECT title, (SELECT COUNT(*) FROM messages WHERE session_id = ?) as count FROM sessions WHERE id = ?", (session_id, session_id))
        s_row = cursor.fetchone()
        if s_row and s_row["count"] == 0 and role == "user":
            snippet = content.strip().split("\n")[0][:36]
            clean_title = snippet.capitalize() if snippet else "Tactical Query"
            cursor.execute("UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?", (clean_title, now, session_id))
        else:
            cursor.execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (now, session_id))

        cursor.execute(
            "INSERT INTO messages (session_id, role, content, source, timestamp) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, source, now)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_sessions() -> list:
        """Retrieve all sessions with message counts and previews."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.title, s.created_at, s.updated_at, COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
        """)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_messages(session_id: str) -> list:
        """Retrieve all messages for a given session."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, content, source, timestamp FROM messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a specific session and all its messages."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.execute("VACUUM")
        conn.close()
        return deleted

    @staticmethod
    def clear_all_sessions() -> bool:
        """Delete all chat history to optimize and free memory."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM sessions")
        conn.commit()
        cursor.execute("VACUUM")
        conn.close()
        return True

    @staticmethod
    def optimize_memory(session_id: str = None, keep_recent: int = 12) -> int:
        """
        Prunes older messages in a session to keep context compact and fast.
        Keeps the latest `keep_recent` messages and vacuums database.
        """
        conn = get_connection()
        cursor = conn.cursor()

        if session_id:
            target_sessions = [session_id]
        else:
            cursor.execute("SELECT id FROM sessions")
            target_sessions = [r["id"] for r in cursor.fetchall()]

        pruned_count = 0
        for sid in target_sessions:
            cursor.execute("""
                DELETE FROM messages
                WHERE session_id = ? AND id NOT IN (
                    SELECT id FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?
                )
            """, (sid, sid, keep_recent))
            pruned_count += cursor.rowcount

        # Remove abandoned sessions that have 0 messages
        cursor.execute("""
            DELETE FROM sessions
            WHERE id NOT IN (SELECT DISTINCT session_id FROM messages)
        """)

        conn.commit()
        cursor.execute("VACUUM")
        conn.close()
        return pruned_count

    @staticmethod
    def get_recent_history_context(session_id: str = None, limit: int = 6) -> list:
        """Return clean context list formatted for Ollama / LLM prompt injection."""
        if not session_id:
            session_id = ChatManager.get_active_session()
        msgs = ChatManager.get_messages(session_id)
        if not msgs:
            return []
        recent = msgs[-limit:]
        return [{"role": m["role"], "content": m["content"]} for m in recent]
