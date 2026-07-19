"""Tests for the SessionManager — multi-table session support."""

import pytest
import tempfile
from pathlib import Path

from core.session import SessionManager, Session


class TestSessionManagerCreate:
    """Creating and listing sessions."""

    def test_create_session_returns_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s = mgr.create("Table 1", "roulette")
            assert s.name == "Table 1"
            assert s.game_type == "roulette"
            assert s.session_id > 0

    def test_create_session_auto_generates_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s1 = mgr.create("A", "roulette")
            s2 = mgr.create("B", "poker")
            assert s2.session_id == s1.session_id + 1

    def test_create_session_sets_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s = mgr.create("T", "roulette")
            assert s.created_at is not None
            assert "T" in s.created_at or s.created_at != ""

    def test_list_sessions_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            assert mgr.list_all() == []

    def test_list_sessions_returns_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            mgr.create("A", "roulette")
            mgr.create("B", "poker")
            mgr.create("C", "roulette")
            sessions = mgr.list_all()
            assert len(sessions) == 3
            names = [s.name for s in sessions]
            assert "A" in names
            assert "B" in names
            assert "C" in names

    def test_list_sessions_filtered_by_game_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            mgr.create("R1", "roulette")
            mgr.create("P1", "poker")
            mgr.create("R2", "roulette")
            roulette = mgr.list_all(game_type="roulette")
            assert len(roulette) == 2
            poker = mgr.list_all(game_type="poker")
            assert len(poker) == 1


class TestSessionManagerGet:
    """Retrieving sessions by ID."""

    def test_get_existing_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            created = mgr.create("My Table", "roulette")
            fetched = mgr.get(created.session_id)
            assert fetched is not None
            assert fetched.name == "My Table"
            assert fetched.game_type == "roulette"

    def test_get_nonexistent_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            assert mgr.get(999) is None

    def test_get_active_defaults_to_most_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            mgr.create("Old", "roulette")
            mgr.create("New", "poker")
            active = mgr.get_active()
            assert active is not None
            assert active.name == "New"

    def test_get_active_returns_none_when_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            assert mgr.get_active() is None


class TestSessionManagerDelete:
    """Deleting sessions."""

    def test_delete_removes_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s = mgr.create("To Delete", "roulette")
            assert mgr.delete(s.session_id) is True
            assert mgr.get(s.session_id) is None

    def test_delete_nonexistent_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            assert mgr.delete(999) is False

    def test_delete_shifts_active_to_previous(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s1 = mgr.create("First", "roulette")
            s2 = mgr.create("Second", "roulette")
            mgr.delete(s2.session_id)
            active = mgr.get_active()
            assert active is not None
            assert active.session_id == s1.session_id


class TestSessionManagerRename:
    """Renaming sessions."""

    def test_rename_updates_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s = mgr.create("Old Name", "roulette")
            assert mgr.rename(s.session_id, "New Name") is True
            fetched = mgr.get(s.session_id)
            assert fetched.name == "New Name"

    def test_rename_nonexistent_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            assert mgr.rename(999, "X") is False


class TestSessionManagerDrawCount:
    """Counting draws per session."""

    def test_draw_count_zero_for_new_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s = mgr.create("Empty", "roulette")
            assert mgr.draw_count(s.session_id) == 0

    def test_draw_count_after_recording(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SessionManager(Path(tmp) / "sessions.db")
            s = mgr.create("With Draws", "roulette")
            # Record a draw via the session's history
            from core.game import Game, Bet
            game = Game("Test", [Bet(id="num_0", name="0", probability=1/37, odds=36.0)])
            mgr.record_draw(s.session_id, game, "0", ["num_0"])
            assert mgr.draw_count(s.session_id) == 1
