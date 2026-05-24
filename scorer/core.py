from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence


@dataclass
class Review:
    user_id: str
    raw_score: float       # 0–10，用户对目标的原始评分
    satisfaction: float    # 0–1，用户对自己这次打分的满意度


def adjusted_score(review: Review, global_mean: float) -> float:
    """满意度加权修正：满意度低则向全局均值收缩。"""
    w = review.satisfaction
    return review.raw_score * w + global_mean * (1 - w)


def aggregate(reviews: Sequence[Review], bot_ids: set[str] | None = None) -> float:
    """过滤水军后，返回修正均值。"""
    clean = [r for r in reviews if not (bot_ids and r.user_id in bot_ids)]
    if not clean:
        return 0.0
    global_mean = sum(r.raw_score for r in clean) / len(clean)
    scores = [adjusted_score(r, global_mean) for r in clean]
    return sum(scores) / len(scores)
