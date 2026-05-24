from __future__ import annotations
from .core import Review


def apply_meta(review: Review, meta_rating: float) -> Review:
    """用二次评分（满意度）更新 Review，返回新实例。"""
    return Review(
        user_id=review.user_id,
        raw_score=review.raw_score,
        satisfaction=meta_rating,
    )
