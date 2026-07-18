"""History Engine — stores draw history and computes rolling window statistics.

Each "draw" is a single outcome of the underlying random process.
For roulette: the number that came up (0-36).
For poker: the hand ranking achieved.

A single draw can trigger multiple bet wins (e.g., roulette "17" wins
num_17, red, odd, low, dozen_2, col_2).
"""

import sqlite3
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np

from core.game import Game


# Standard rolling window sizes
DEFAULT_WINDOWS = [50, 100, 250, 500, 1000, 5000]


@dataclass
class DrawRecord:
    """A single recorded draw."""

    draw_id: int
    game_name: str
    timestamp: str  # ISO 8601
    raw_outcome: str  # e.g. "17" for roulette, "two_pair" for poker
    won_bet_ids: list[str] = field(default_factory=list)


@dataclass
class WindowStats:
    """Statistics for a single bet over a rolling window."""

    bet_id: str
    window_size: int
    n_draws: int  # number of draws in this window
    hits: int  # actual wins
    expected: float  # E = n * p
    std: float  # σ = sqrt(n * p * (1-p))
    z_score: float  # Z = (hits - expected) / std


class HistoryEngine:
    """Stores draw history in SQLite and computes rolling window statistics."""

    def __init__(self, db_path: str = "data/history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS draws (
                    draw_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    raw_outcome TEXT NOT NULL,
                    won_bet_ids TEXT NOT NULL  -- JSON array
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_draws_game
                ON draws(game_name, draw_id)
            """)

    def record_draw(
        self,
        game: Game,
        raw_outcome: str,
        won_bet_ids: list[str],
        timestamp: Optional[str] = None,
    ) -> int:
        """Record a draw and return its draw_id.

        Args:
            game: The game this draw belongs to
            raw_outcome: The raw result (e.g. "17", "flush")
            won_bet_ids: Which bets won on this draw
            timestamp: ISO 8601 timestamp (default: now)
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO draws (game_name, timestamp, raw_outcome, won_bet_ids) "
                "VALUES (?, ?, ?, ?)",
                (game.name, timestamp, raw_outcome, json.dumps(won_bet_ids)),
            )
            return cursor.lastrowid

    def get_draws(
        self, game_name: str, limit: Optional[int] = None
    ) -> list[DrawRecord]:
        """Retrieve draws for a game, most recent first."""
        query = (
            "SELECT draw_id, game_name, timestamp, raw_outcome, won_bet_ids "
            "FROM draws WHERE game_name = ? ORDER BY draw_id DESC"
        )
        if limit is not None:
            query += f" LIMIT {limit}"

        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(query, (game_name,)).fetchall()

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

    def count_draws(self, game_name: str) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM draws WHERE game_name = ?", (game_name,)
            ).fetchone()
            return row[0]

    def compute_window_stats(
        self,
        game: Game,
        bet_id: str,
        window_size: int,
    ) -> WindowStats:
        """Compute statistics for a single bet over the most recent N draws."""
        bet = game.get_bet(bet_id)
        draws = self.get_draws(game.name, limit=window_size)
        n = len(draws)

        if n == 0:
            return WindowStats(
                bet_id=bet_id,
                window_size=window_size,
                n_draws=0,
                hits=0,
                expected=0.0,
                std=0.0,
                z_score=0.0,
            )

        hits = sum(1 for d in draws if bet_id in d.won_bet_ids)
        p = bet.probability
        expected = n * p
        std = np.sqrt(n * p * (1 - p))

        if std < 1e-10:
            z_score = 0.0
        else:
            z_score = (hits - expected) / std

        return WindowStats(
            bet_id=bet_id,
            window_size=window_size,
            n_draws=n,
            hits=hits,
            expected=expected,
            std=std,
            z_score=z_score,
        )

    def compute_all_windows(
        self,
        game: Game,
        bet_id: str,
        windows: Optional[list[int]] = None,
    ) -> list[WindowStats]:
        """Compute statistics for all standard window sizes."""
        if windows is None:
            windows = DEFAULT_WINDOWS
        return [self.compute_window_stats(game, bet_id, w) for w in windows]

    def clear_history(self, game_name: str) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("DELETE FROM draws WHERE game_name = ?", (game_name,))
