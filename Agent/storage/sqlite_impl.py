import aiosqlite
from datetime import datetime, timezone

_sqlite_conn = None


class SqliteAuditStorage:
    def __init__(self, conn: aiosqlite.Connection):
        self._conn = conn

    async def log_message(self, user_id: str, role: str, content: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        await self._conn.execute(
            "INSERT INTO audit_log (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, role, content, timestamp),
        )
        await self._conn.commit()


async def build_sqlite_storage(config: dict) -> SqliteAuditStorage:
    global _sqlite_conn
    db_path = config.get("sqlite_path", "./data/db/audit_log.db")
    print(f"[*] 初始化審計日誌模組: 連線至 SQLite ({db_path})")
    conn = await aiosqlite.connect(db_path)
    await conn.execute(
        """CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )"""
    )
    await conn.commit()
    _sqlite_conn = conn
    return SqliteAuditStorage(conn)


async def close_sqlite_storage():
    global _sqlite_conn
    if _sqlite_conn is not None:
        await _sqlite_conn.close()
        _sqlite_conn = None
