import math


class BotSignal:
    """Records one suspicious signal detected for a user."""

    def __init__(self, user_id, reason, confidence):
        self.user_id = user_id      # str   — the flagged account
        self.reason = reason        # str   — name of the detection signal
        self.confidence = confidence  # float 0–1 — how certain we are


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _group_scores_by_user(reviews, field):
    """Return a dict mapping each user_id to a list of their values for `field`."""
    groups = {}
    for review in reviews:
        uid = review.user_id
        value = getattr(review, field)
        if uid not in groups:
            groups[uid] = []
        groups[uid].append(value)
    return groups


def _mean(values):
    """Return the arithmetic mean of a list of floats."""
    if len(values) == 0:
        return 0.0
    total = 0.0
    for v in values:
        total = total + v
    return total / len(values)


def _variance(values):
    """Return the variance of a list of floats (returns 0.0 for fewer than 2 values)."""
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    squared_diffs = 0.0
    for v in values:
        squared_diffs = squared_diffs + (v - m) ** 2
    return squared_diffs / len(values)


def _stddev(values):
    """Return the standard deviation of a list of floats."""
    return math.sqrt(_variance(values))


# ---------------------------------------------------------------------------
# Six detection signals
# ---------------------------------------------------------------------------

def check_duplicate_submissions(reviews, threshold=3):
    """Signal 1: same user posted too many reviews (volume spamming)."""
    # Count how many times each user appears
    counts = {}
    for review in reviews:
        uid = review.user_id
        if uid in counts:
            counts[uid] = counts[uid] + 1
        else:
            counts[uid] = 1

    # Flag anyone above the threshold
    signals = []
    for uid, count in counts.items():
        if count >= threshold:
            confidence = min(1.0, count / (threshold * 2))
            signals.append(BotSignal(uid, "duplicate_submissions", confidence))
    return signals


def check_score_monotony(reviews):
    """Signal 2: user always gives the exact same score (zero variance)."""
    groups = _group_scores_by_user(reviews, "raw_score")
    signals = []
    for uid, scores in groups.items():
        if len(scores) >= 2 and _variance(scores) == 0.0:
            signals.append(BotSignal(uid, "score_monotony", 0.85))
    return signals


def check_extreme_bias(reviews, extreme_lo=1.0, extreme_hi=9.0):
    """Signal 3: every score from this user is at the extreme high or low end."""
    groups = _group_scores_by_user(reviews, "raw_score")
    signals = []
    for uid, scores in groups.items():
        if len(scores) < 2:
            continue
        # Count how many scores fall in the extreme zone
        extreme_count = 0
        for score in scores:
            if score <= extreme_lo or score >= extreme_hi:
                extreme_count = extreme_count + 1
        # Flag only if every single score is extreme
        if extreme_count == len(scores):
            signals.append(BotSignal(uid, "extreme_bias", 0.70))
    return signals


def check_satisfaction_anomaly(reviews):
    """Signal 4: user always gives a perfect satisfaction of 1.0 — suspiciously consistent."""
    groups = _group_scores_by_user(reviews, "satisfaction")
    signals = []
    for uid, sats in groups.items():
        if len(sats) < 2:
            continue
        all_perfect = True
        for s in sats:
            if s != 1.0:
                all_perfect = False
                break
        if all_perfect:
            signals.append(BotSignal(uid, "satisfaction_anomaly", 0.65))
    return signals


def check_statistical_outlier(reviews, z_threshold=2.5):
    """Signal 5: user's average score is a statistical outlier from the crowd."""
    # Collect all scores for global statistics
    all_scores = []
    for review in reviews:
        all_scores.append(review.raw_score)

    # Need enough data for statistics to be meaningful
    if len(all_scores) < 5:
        return []

    global_mean = _mean(all_scores)
    global_std = _stddev(all_scores)

    if global_std == 0:
        return []

    groups = _group_scores_by_user(reviews, "raw_score")
    signals = []
    for uid, scores in groups.items():
        user_mean = _mean(scores)
        z_score = abs(user_mean - global_mean) / global_std
        if z_score >= z_threshold:
            confidence = min(1.0, z_score / (z_threshold * 2))
            signals.append(BotSignal(uid, "statistical_outlier", confidence))
    return signals


def check_coordinated_attack(reviews, min_group=3):
    """Signal 6: multiple different users submit the exact same (score, satisfaction) pair."""
    # Group users by their (score, satisfaction) combination
    combo_groups = {}
    for review in reviews:
        key = (review.raw_score, review.satisfaction)
        if key not in combo_groups:
            combo_groups[key] = []
        combo_groups[key].append(review.user_id)

    signals = []
    for key, user_ids in combo_groups.items():
        # Use a set to count unique users with this combo
        unique_users = set(user_ids)
        if len(unique_users) >= min_group:
            for uid in unique_users:
                signals.append(BotSignal(uid, "coordinated_attack", 0.90))
    return signals


# ---------------------------------------------------------------------------
# Main interface
# ---------------------------------------------------------------------------

def detect_bots(reviews, confidence_threshold=0.6, duplicate_threshold=3,
                z_threshold=2.5, coordinated_min_group=3):
    """Run all six signals and return the set of flagged user IDs.

    Any user whose highest-confidence signal meets the threshold is flagged.
    Lower confidence_threshold → catches more bots but more false positives.
    Higher confidence_threshold → fewer false positives but may miss some bots.
    """
    all_signals = explain(reviews,
                          duplicate_threshold=duplicate_threshold,
                          z_threshold=z_threshold,
                          coordinated_min_group=coordinated_min_group)
    flagged = set()
    for signal in all_signals:
        if signal.confidence >= confidence_threshold:
            flagged.add(signal.user_id)
    return flagged


def explain(reviews, duplicate_threshold=3, z_threshold=2.5, coordinated_min_group=3):
    """Return every raw BotSignal across all six checks — useful for auditing."""
    all_signals = []
    all_signals += check_duplicate_submissions(reviews, duplicate_threshold)
    all_signals += check_score_monotony(reviews)
    all_signals += check_extreme_bias(reviews)
    all_signals += check_satisfaction_anomaly(reviews)
    all_signals += check_statistical_outlier(reviews, z_threshold)
    all_signals += check_coordinated_attack(reviews, coordinated_min_group)
    return all_signals
