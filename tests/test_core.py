from scorer.core import Review, aggregate, adjusted_score
from scorer.bot_detect import detect_bots


def test_adjusted_score_full_satisfaction():
    r = Review("u1", raw_score=8.0, satisfaction=1.0)
    assert adjusted_score(r, global_mean=5.0) == 8.0


def test_adjusted_score_zero_satisfaction():
    r = Review("u1", raw_score=8.0, satisfaction=0.0)
    assert adjusted_score(r, global_mean=5.0) == 5.0


def test_aggregate_filters_bots():
    reviews = [
        Review("bot", raw_score=10.0, satisfaction=1.0),
        Review("bot", raw_score=10.0, satisfaction=1.0),
        Review("bot", raw_score=10.0, satisfaction=1.0),
        Review("real", raw_score=6.0, satisfaction=0.8),
    ]
    bots = detect_bots(reviews)
    result = aggregate(reviews, bot_ids=bots)
    assert result < 10.0


def test_detect_bots():
    reviews = [Review("spammer", 9.0, 1.0)] * 5 + [Review("normal", 5.0, 0.9)]
    bots = detect_bots(reviews)
    assert "spammer" in bots
    assert "normal" not in bots
