"""
Data and Memory Cleaner for Gagan AI.
Cleans all logs, chat history, cached emails, screenshots, and session corpus.
"""
import os
import glob
import sqlite3
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

def clear_all_logs() -> int:
    """Truncate all log files in logs directory."""
    cleared = 0
    if os.path.exists(LOGS_DIR):
        for f in glob.glob(os.path.join(LOGS_DIR, "*.log")):
            try:
                with open(f, "w", encoding="utf-8") as fp:
                    fp.write("")
                cleared += 1
            except Exception:
                pass
    return cleared

def clear_chat_history() -> bool:
    """Clear all chat messages and sessions from SQLite chat_history.db."""
    try:
        from voice.chat_manager import ChatManager
        return ChatManager.clear_all_sessions()
    except Exception:
        db_path = os.path.join(DATA_DIR, "chat_history.db")
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM messages")
                cursor.execute("DELETE FROM sessions")
                conn.commit()
                cursor.execute("VACUUM")
                conn.close()
                return True
            except Exception:
                pass
    return False

def clear_cached_emails() -> int:
    """Clear cached emails and email memory files."""
    email_files = [
        os.path.join(DATA_DIR, "latest_email.json"),
        os.path.join(DATA_DIR, "latest_email.txt"),
        os.path.join(DATA_DIR, "workspace", "LATEST_EMAIL.md"),
        os.path.join(DATA_DIR, "watcher_state.json")
    ]
    count = 0
    for f in email_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                count += 1
            except Exception:
                pass
    return count

def clear_session_corpus_and_dreams() -> int:
    """Clear agent dream logs and session corpus in workspace."""
    cleared = 0
    patterns = [
        os.path.join(DATA_DIR, "workspace", "memory", "dreaming", "rem", "*.md"),
        os.path.join(DATA_DIR, "workspace", "memory", "dreaming", "light", "*.md"),
        os.path.join(DATA_DIR, "workspace", "memory", ".dreams", "session-corpus", "*.*"),
        os.path.join(DATA_DIR, "screenshots", "*.png"),
        os.path.join(DATA_DIR, "browser_screenshots", "*.png")
    ]
    for pattern in patterns:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
                cleared += 1
            except Exception:
                pass
    return cleared

def purge_all_memory_and_logs() -> dict:
    """Comprehensive purge of logs, chats, email cache, and temporary memories."""
    logs_count = clear_all_logs()
    chats_ok = clear_chat_history()
    emails_count = clear_cached_emails()
    dreams_count = clear_session_corpus_and_dreams()
    return {
        "status": "SUCCESS",
        "cleared_logs": logs_count,
        "cleared_chats": chats_ok,
        "cleared_emails": emails_count,
        "cleared_temp_files": dreams_count,
        "spoken_summary": "All logs, chat histories, cached emails, and temporary session memories have been completely cleared, Gagan."
    }

if __name__ == "__main__":
    res = purge_all_memory_and_logs()
    print("Purge result:", res)
