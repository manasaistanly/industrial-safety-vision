import sqlite3
import threading
import time


class EventLogger:
    """Anonymous safety event logger using SQLite.

    Stores only: timestamp, zone_id, missing_ppe (comma list), action_taken
    No images, no identities.
    """

    def __init__(self, db_path="ppe_safety_events.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    zone_id TEXT NOT NULL,
                    missing_ppe TEXT,
                    action_taken TEXT NOT NULL
                )
                """
            )
            conn.commit()
            conn.close()

    def log_event(self, zone_id: str, missing_ppe: list, action_taken: str):
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=5)
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO events (ts, zone_id, missing_ppe, action_taken) VALUES (?, ?, ?, ?)",
                (int(time.time()), zone_id, ",".join(sorted(missing_ppe or [])), action_taken),
            )
            conn.commit()
            conn.close()
