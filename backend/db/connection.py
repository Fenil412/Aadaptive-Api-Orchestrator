"""SQLite fallback DB connection using aiosqlite."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parents[1] / "api_orchestrator.db"


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Async context manager yielding an aiosqlite connection."""
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    try:
        yield conn
        await conn.commit()
    except Exception:
        await conn.rollback()
        raise
    finally:
        await conn.close()


async def insert_api_log(
    conn: aiosqlite.Connection,
    api_name: str,
    latency: float,
    cost: float,
    success: bool,
    system_load: float = 1.0,
    action_taken: str | None = None,
) -> int:
    cursor = await conn.execute(
        "INSERT INTO api_logs (api_name, latency, cost, success, system_load, action_taken) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (api_name, latency, cost, int(success), system_load, action_taken),
    )
    return cursor.lastrowid


async def get_api_logs(
    conn: aiosqlite.Connection, limit: int = 100, api_name: str | None = None
) -> list[dict[str, Any]]:
    if api_name:
        cursor = await conn.execute(
            "SELECT * FROM api_logs WHERE api_name = ? ORDER BY timestamp DESC LIMIT ?",
            (api_name, limit),
        )
    else:
        cursor = await conn.execute(
            "SELECT * FROM api_logs ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def insert_rl_decision(
    conn: aiosqlite.Connection,
    state: list[float],
    action: int,
    reward: float,
    api_name: str,
) -> int:
    import json
    cursor = await conn.execute(
        "INSERT INTO rl_decisions (state, action, reward, api_name) VALUES (?, ?, ?, ?)",
        (json.dumps(state), action, reward, api_name),
    )
    return cursor.lastrowid


async def get_rl_decisions(conn: aiosqlite.Connection, limit: int = 50) -> list[dict[str, Any]]:
    cursor = await conn.execute(
        "SELECT * FROM rl_decisions ORDER BY timestamp DESC LIMIT ?", (limit,)
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
