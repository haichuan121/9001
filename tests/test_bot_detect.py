from scorer.core import Review
from scorer.bot_detect import (
    detect_bots, explain,
    check_duplicate_submissions, check_score_monotony,
    check_extreme_bias, check_satisfaction_anomaly,
    check_statistical_outlier, check_coordinated_attack,
)


def make_review(uid, score, sat=0.8):
    return Review(uid, score, sat)


# --- check_duplicate_submissions ---

def test_duplicate_flags_repeat_user():
    reviews = [make_review("bot", 9.0)] * 4 + [make_review("real", 6.0)]
    signals = check_duplicate_submissions(reviews, threshold=3)
    flagged = [s.user_id for s in signals]
    assert "bot" in flagged
    assert "real" not in flagged


def test_duplicate_below_threshold_is_clean():
    reviews = [make_review("u", 7.0), make_review("u", 8.0)]
    assert check_duplicate_submissions(reviews, threshold=3) == []


# --- check_score_monotony ---

def test_monotony_flags_identical_scores():
    reviews = [make_review("bot", 10.0)] * 3
    signals = check_score_monotony(reviews)
    assert any(s.user_id == "bot" for s in signals)


def test_monotony_ignores_varied_scores():
    reviews = [make_review("u", 7.0), make_review("u", 8.0), make_review("u", 6.0)]
    assert check_score_monotony(reviews) == []


def test_monotony_single_review_is_clean():
    assert check_score_monotony([make_review("u", 9.0)]) == []


# --- check_extreme_bias ---

def test_extreme_bias_all_high():
    reviews = [make_review("s", 10.0), make_review("s", 9.5), make_review("s", 10.0)]
    signals = check_extreme_bias(reviews)
    assert any(s.user_id == "s" for s in signals)


def test_extreme_bias_all_low():
    reviews = [make_review("h", 0.0), make_review("h", 0.5), make_review("h", 1.0)]
    signals = check_extreme_bias(reviews)
    assert any(s.user_id == "h" for s in signals)


def test_extreme_bias_mixed_is_clean():
    reviews = [make_review("u", 10.0), make_review("u", 5.0), make_review("u", 1.0)]
    assert check_extreme_bias(reviews) == []


# --- check_satisfaction_anomaly ---

def test_satisfaction_anomaly_all_perfect():
    reviews = [Review("bot", 9.0, 1.0), Review("bot", 8.0, 1.0), Review("bot", 7.0, 1.0)]
    signals = check_satisfaction_anomaly(reviews)
    assert any(s.user_id == "bot" for s in signals)


def test_satisfaction_anomaly_varied_is_clean():
    reviews = [Review("u", 7.0, 0.6), Review("u", 8.0, 0.9)]
    assert check_satisfaction_anomaly(reviews) == []


# --- check_statistical_outlier ---

def test_statistical_outlier_detected():
    normal = [make_review(f"u{i}", 5.0 + i * 0.1) for i in range(10)]
    outlier = [make_review("extreme", 10.0), make_review("extreme", 10.0)]
    signals = check_statistical_outlier(normal + outlier, z_threshold=2.0)
    assert any(s.user_id == "extreme" for s in signals)


def test_statistical_outlier_needs_min_reviews():
    reviews = [make_review("u", 10.0), make_review("v", 1.0)]
    assert check_statistical_outlier(reviews) == []


# --- check_coordinated_attack ---

def test_coordinated_attack_same_combo():
    reviews = [
        Review("a", 10.0, 1.0), Review("b", 10.0, 1.0), Review("c", 10.0, 1.0),
        Review("legit", 6.0, 0.7),
    ]
    signals = check_coordinated_attack(reviews, min_group=3)
    flagged = {s.user_id for s in signals}
    assert {"a", "b", "c"} <= flagged
    assert "legit" not in flagged


def test_coordinated_attack_below_min_group():
    reviews = [Review("a", 10.0, 1.0), Review("b", 10.0, 1.0)]
    assert check_coordinated_attack(reviews, min_group=3) == []


# --- detect_bots (main interface) ---

def test_detect_bots_flags_spammer():
    reviews = [make_review("bot", 10.0)] * 5 + [make_review("real", 6.0)]
    bots = detect_bots(reviews)
    assert "bot" in bots
    assert "real" not in bots


def test_explain_returns_multiple_reasons():
    reviews = [Review("bot", 10.0, 1.0)] * 3
    signals = explain(reviews)
    reasons = {s.reason for s in signals if s.user_id == "bot"}
    assert "duplicate_submissions" in reasons
    assert "score_monotony" in reasons
