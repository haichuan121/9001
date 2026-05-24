"""Tests for app.py — score computation and user weight logic."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app


def setup_function():
    """Reset global state before each test."""
    app.items.clear()
    app.users.clear()


# ── compute_user_weight ──────────────────────────────────────────────

def test_weight_new_user_single_score():
    weight, note = app.compute_user_weight([9.0])
    assert weight == 1.0   # not enough history to penalise


def test_weight_always_high():
    history = [10.0, 9.5, 10.0, 9.0, 10.0]
    weight, note = app.compute_user_weight(history)
    assert weight == 0.4
    assert "high" in note.lower()


def test_weight_always_low():
    history = [0.0, 1.0, 0.5, 0.0, 1.5]
    weight, note = app.compute_user_weight(history)
    assert weight == 0.4
    assert "low" in note.lower()


def test_weight_low_variety():
    history = [5.0, 5.2, 4.9, 5.1, 5.0]
    weight, note = app.compute_user_weight(history)
    assert weight == 0.7
    assert "variety" in note.lower()


def test_weight_normal():
    history = [3.0, 6.0, 9.0, 2.0, 7.5]
    weight, note = app.compute_user_weight(history)
    assert weight == 1.0
    assert note == "Normal"


# ── compute_item_score ───────────────────────────────────────────────

def test_item_score_single_review():
    app.users["alice"] = {"weight": 1.0, "history": [], "note": "Normal"}
    reviews = [{"user": "alice", "raw": 8.0, "satisfaction": 1.0}]
    assert app.compute_item_score(reviews) == 8.0


def test_item_score_low_satisfaction_pulls_to_zero():
    app.users["alice"] = {"weight": 1.0, "history": [], "note": "Normal"}
    reviews = [{"user": "alice", "raw": 10.0, "satisfaction": 0.0}]
    assert app.compute_item_score(reviews) == 0.0


def test_item_score_reduced_weight_lowers_influence():
    app.users["normal"] = {"weight": 1.0, "history": [], "note": "Normal"}
    app.users["shill"]  = {"weight": 0.4, "history": [], "note": "Always high"}

    reviews = [
        {"user": "normal", "raw": 5.0, "satisfaction": 1.0},
        {"user": "shill",  "raw": 10.0, "satisfaction": 1.0},
    ]
    score = app.compute_item_score(reviews)
    # Shill's 10.0 has less pull — result should be closer to 5.0 than to 10.0
    assert score < 7.5


def test_item_score_empty_reviews():
    assert app.compute_item_score([]) == 0.0


# ── refresh_scores ───────────────────────────────────────────────────

def test_refresh_updates_all_items():
    app.users["u"] = {"weight": 1.0, "history": [], "note": "Normal"}
    app.items["Alpha"] = {"reviews": [{"user": "u", "raw": 7.0, "satisfaction": 1.0}], "score": 0.0}
    app.items["Beta"]  = {"reviews": [{"user": "u", "raw": 4.0, "satisfaction": 1.0}], "score": 0.0}
    app.refresh_scores()
    assert abs(app.items["Alpha"]["score"] - 7.0) < 0.01
    assert abs(app.items["Beta"]["score"]  - 4.0) < 0.01
