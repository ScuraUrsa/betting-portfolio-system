"""Session-aware history adapter — bridges SessionManager to HistoryEngine interface.

This adapter wraps a SessionManager + session_id and exposes the same
API as HistoryEngine. This allows ExtremumEngine, ValueEngine, and all
other pipeline components to work with per-session data without any changes.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from core.game import Game
from core.history import DrawRecord, WindowStats, DEFAULT_WINDOWS
from core.session import SessionManager


class SessionHistoryAdapter:
    """Wraps SessionManager to look like HistoryEngine for a specific session.

    Usage:
        mgr = SessionManager("data/sessions.db")
        session = mgr.create("Table 1", "roulette")
        history = SessionHistoryAdapter(mgr, session.session_id)
        # Now use history exactly like HistoryEngine:
        history.record_draw(game, "17", ["num_17", "red"])
        draws = history.get_draws(game.name)
    """

    def __init__(self, session_manager: SessionManager, session_id: int) -> None:
        self._mgr = session_manager
        self._session_id = session_id

    @property
    def session_id(self) -> int:
        return self._session_id

    def record_draw(
        self,
        game: Game,
        raw_outcome: str,
        won_bet_ids: list[str],
        timestamp: Optional[str] = None,
    ) -> int:
        return self._mgr.record_draw(
            self._session_id, game, raw_outcome, won_bet_ids, timestamp
        )

    def get_draws(
        self, game_name: str, limit: Optional[int] = None
    ) -> list[DrawRecord]:
        return self._mgr.get_draws(self._session_id, game_name, limit)

    def count_draws(self, game_name: str) -> int:
        return self._mgr.draw_count(self._session_id, game_name)

    def compute_window_stats(
        self,
        game: Game,
        bet_id: str,
        window_size: int,
    ) -> WindowStats:
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
        if windows is None:
            windows = DEFAULT_WINDOWS
        return [self.compute_window_stats(game, bet_id, w) for w in windows]

    def clear_history(self, game_name: str) -> None:
        self._mgr.clear_draws(self._session_id, game_name)
