from .core import Review


def apply_meta(review, meta_rating):
    """Create a new Review with an updated satisfaction rating.

    The user submits their raw score first, then rates how satisfied
    they are with that score (meta_rating). This returns a revised Review.

    Parameters
    ----------
    review     : Review — the original review
    meta_rating: float 0–1 — the user's satisfaction with their own score
    """
    return Review(
        user_id=review.user_id,
        raw_score=review.raw_score,
        satisfaction=meta_rating,
    )
