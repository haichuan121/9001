from scorer.core import Review, adjusted_score, aggregate, compute_mean


def test_adjusted_score_full_satisfaction():
    review = Review("u1", raw_score=8.0, satisfaction=1.0)
    result = adjusted_score(review, group_mean=5.0)
    assert result == 8.0


def test_adjusted_score_zero_satisfaction():
    review = Review("u1", raw_score=8.0, satisfaction=0.0)
    result = adjusted_score(review, group_mean=5.0)
    assert result == 5.0


def test_adjusted_score_half_satisfaction():
    review = Review("u1", raw_score=8.0, satisfaction=0.5)
    result = adjusted_score(review, group_mean=4.0)
    assert result == 6.0  # 8*0.5 + 4*0.5


def test_compute_mean_basic():
    assert compute_mean([2.0, 4.0, 6.0]) == 4.0


def test_compute_mean_empty():
    assert compute_mean([]) == 0.0


def test_aggregate_filters_bots():
    reviews = [
        Review("bot", raw_score=10.0, satisfaction=1.0),
        Review("bot", raw_score=10.0, satisfaction=1.0),
        Review("bot", raw_score=10.0, satisfaction=1.0),
        Review("real", raw_score=6.0, satisfaction=0.8),
    ]
    result = aggregate(reviews, bot_ids={"bot"})
    assert result < 10.0


def test_aggregate_no_bots_returns_adjusted_mean():
    reviews = [
        Review("a", raw_score=6.0, satisfaction=1.0),
        Review("b", raw_score=8.0, satisfaction=1.0),
    ]
    result = aggregate(reviews)
    assert result == 7.0


def test_aggregate_empty_after_filter_returns_zero():
    reviews = [Review("bot", 9.0, 1.0)]
    result = aggregate(reviews, bot_ids={"bot"})
    assert result == 0.0
