from __future__ import annotations
from collections import Counter
from .core import Review


def detect_bots(reviews: list[Review], duplicate_threshold: int = 3) -> set[str]:
    """简单水军识别：同一用户重复评分超过阈值即标记。"""
    counts = Counter(r.user_id for r in reviews)
    return {uid for uid, n in counts.items() if n >= duplicate_threshold}
