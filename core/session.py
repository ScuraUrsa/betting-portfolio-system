"""Session Manager — multi-table support for independent betting sessions.

Each session represents a separate "table" with its own:
- Name (e.g. "Table 1", "Casino Warsaw — Roulette")
- Game type (roulette or poker)
- Independent draw history
- Independent recommendations and signals

Sessions are stored in a SQLite database alongside draw history.
"""

from __future__ import annotations

import sqlite3
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from core.game import Game


@dataclass
class Session:
    """A named betting session (table)."""

    session_id: int
    name: str
    game_type: str  # "roulette" or "poker"
    created_at: str  # ISO 8601


class SessionManager:
    """Manages multiple independent betting sessions.

    Each session has its own draw history. The manager stores sessions
    in a SQLite database and provides CRUD operations.

    Usage:
        mgr = SessionManager("data/sessions.db")
        s = mgr.create("Table 1", "roulette")
        mgr.record_draw(s.session_id, game, "17", ["num_17", "red", ...])
        draws = mgr.get_draws(s.session_id, game.name)
    """

    def __init__(self, db_path: str | Path = "data/sessions.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    game_type TEXT NOT NULL CHECK(game_type IN ('roulette', 'poker')),
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_draws (
                    draw_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    game_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    raw_outcome TEXT NOT NULL,
                    won_bet_ids TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_draws_session
                ON session_draws(session_id, draw_id)
            """)
            conn.execute("PRAGMA foreign_keys = ON")

    # ── Session CRUD ──────────────────────────────────────────────────

    def create(self, name: str, game_type: str) -> Session:
        """Create a new session and return it."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO sessions (name, game_type, created_at) VALUES (?, ?, ?)",
                (name, game_type, now),
            )
            return Session(
                session_id=cursor.lastrowid,
                name=name,
                game_type=game_type,
                created_at=now,
            )

    def get(self, session_id: int) -> Optional[Session]:
        """Get a session by ID, or None if not found."""
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT session_id, name, game_type, created_at "
                "FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return Session(session_id=row[0], name=row[1], game_type=row[2], created_at=row[3])

    def list_all(self, game_type: Optional[str] = None) -> list[Session]:
        """List all sessions, optionally filtered by game type."""
        with sqlite3.connect(str(self.db_path)) as conn:
            if game_type:
                rows = conn.execute(
                    "SELECT session_id, name, game_type, created_at "
                    "FROM sessions WHERE game_type = ? ORDER BY session_id DESC",
                    (game_type,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT session_id, name, game_type, created_at "
                    "FROM sessions ORDER BY session_id DESC"
                ).fetchall()
        return [
            Session(session_id=r[0], name=r[1], game_type=r[2], created_at=r[3])
            for r in rows
        ]

    def get_active(self) -> Optional[Session]:
        """Return the most recently created session, or None."""
        sessions = self.list_all()
        return sessions[0] if sessions else None

    def delete(self, session_id: int) -> bool:
        """Delete a session and all its draws. Returns True if deleted."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            return cursor.rowcount > 0

    def rename(self, session_id: int, new_name: str) -> bool:
        """Rename a session. Returns True if updated."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "UPDATE sessions SET name = ? WHERE session_id = ?",
                (new_name, session_id),
            )
            return cursor.rowcount > 0

    # ── Draw history (per session) ────────────────────────────────────

    def record_draw(
        self,
        session_id: int,
        game: Game,
        raw_outcome: str,
        won_bet_ids: list[str],
        timestamp: Optional[str] = None,
    ) -> int:
        """Record a draw for a specific session. Returns draw_id."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute(
                "INSERT INTO session_draws (session_id, game_name, timestamp, raw_outcome, won_bet_ids) "
                "VALUES (?, ?, ?, ?, ?)",
                (session_id, game.name, timestamp, raw_outcome, json.dumps(won_bet_ids)),
            )
            return cursor.lastrowid

    def get_draws(
        self,
        session_id: int,
        game_name: str,
        limit: Optional[int] = None,
    ) -> list:
        """Retrieve draws for a session, most recent first."""
        from core.history import DrawRecord

        query = (
            "SELECT draw_id, game_name, timestamp, raw_outcome, won_bet_ids "
            "FROM session_draws WHERE session_id = ? AND game_name = ? "
            "ORDER BY draw_id DESC"
        )
        params: list = [session_id, game_name]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            DrawRecord(
                draw_id=r[0],
                game_name=r[1],
                timestamp=r[2],
                raw_outcome=r[3],
                won_bet_ids=json.loads(r[4]),
            )
            for r in rows
        ]

    def draw_count(self, session_id: int, game_name: Optional[str] = None) -> int:
        """Count draws for a session, optionally filtered by game name."""
        with sqlite3.connect(str(self.db_path)) as conn:
            if game_name:
                row = conn.execute(
                    "SELECT COUNT(*) FROM session_draws WHERE session_id = ? AND game_name = ?",
                    (session_id, game_name),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT COUNT(*) FROM session_draws WHERE session_id = ?",
                    (session_id,),
                ).fetchone()
            return row[0]

    def clear_draws(self, session_id: int, game_name: Optional[str] = None) -> None:
        """Clear draw history for a session."""
        with sqlite3.connect(str(self.db_path)) as conn:
            if game_name:
                conn.execute(
                    "DELETE FROM session_draws WHERE session_id = ? AND game_name = ?",
                    (session_id, game_name),
                )
            else:
                conn.execute(
                    "DELETE FROM session_draws WHERE session_id = ?",
                    (session_id,),
                )
