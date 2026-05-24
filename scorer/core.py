class Review:
    """A single review submitted by one user."""

    def __init__(self, user_id, raw_score, satisfaction):
        self.user_id = user_id        # str  — unique identifier for the reviewer
        self.raw_score = raw_score    # float 0–10 — how the user rates the target
        self.satisfaction = satisfaction  # float 0–1 — how confident the user is in their own score


def adjusted_score(review, group_mean):
    """Return a satisfaction-weighted score.

    High satisfaction  → score stays close to raw_score.
    Low satisfaction   → score is pulled toward the group mean.
    """
    weight = review.satisfaction
    return review.raw_score * weight + group_mean * (1 - weight)


def compute_mean(scores):
    """Return the arithmetic mean of a list of numbers."""
    if len(scores) == 0:
        return 0.0
    total = 0.0
    for score in scores:
        total = total + score
    return total / len(scores)


def aggregate(reviews, bot_ids=None):
    """Filter out bots, then return the satisfaction-adjusted mean score.

    Parameters
    ----------
    reviews : list[Review]
    bot_ids : set[str] | None  — user IDs identified as bots; skipped during aggregation
    """
    # Step 1: remove flagged bot accounts
    clean_reviews = []
    for review in reviews:
        if bot_ids is not None and review.user_id in bot_ids:
            continue  # skip this reviewer — they were flagged as a bot
        clean_reviews.append(review)

    if len(clean_reviews) == 0:
        return 0.0

    # Step 2: compute the group mean from clean reviews only
    raw_scores = []
    for review in clean_reviews:
        raw_scores.append(review.raw_score)
    group_mean = compute_mean(raw_scores)

    # Step 3: apply satisfaction adjustment to each clean review
    adjusted = []
    for review in clean_reviews:
        score = adjusted_score(review, group_mean)
        adjusted.append(score)

    return compute_mean(adjusted)
