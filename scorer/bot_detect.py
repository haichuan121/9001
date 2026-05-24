from __future__ import annotations
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Sequence

from .core import Review


@dataclass
class BotSignal:
    user_id: str
    reason: str
    confidence: float  # 0.0–1.0，越高越可疑


# ── 工具函数 ────────────────────────────────────────────────────────────────

def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / len(values)


def _stddev(values: list[float]) -> float:
    return math.sqrt(_variance(values))


def _by_user(reviews: list[Review], field: str) -> dict[str, list[float]]:
    result: dict[str, list[float]] = defaultdict(list)
    for r in reviews:
        result[r.user_id].append(getattr(r, field))
    return result


# ── 单维信号检测 ─────────────────────────────────────────────────────────────

def check_duplicate_submissions(
    reviews: list[Review], threshold: int = 3
) -> list[BotSignal]:
    """同一用户重复提交次数超过阈值 — 刷量水军。"""
    counts = Counter(r.user_id for r in reviews)
    return [
        BotSignal(uid, "duplicate_submissions", min(1.0, n / (threshold * 2)))
        for uid, n in counts.items()
        if n >= threshold
    ]


def check_score_monotony(reviews: list[Review]) -> list[BotSignal]:
    """用户多次评分完全一致（零方差）— 机器人批量提交特征。"""
    signals = []
    for uid, scores in _by_user(reviews, "raw_score").items():
        if len(scores) >= 2 and _variance(scores) == 0.0:
            signals.append(BotSignal(uid, "score_monotony", 0.85))
    return signals


def check_extreme_bias(
    reviews: list[Review],
    extreme_lo: float = 1.0,
    extreme_hi: float = 9.0,
) -> list[BotSignal]:
    """用户所有评分均为极端值（只给满分或只给差评）— 刷分水军。"""
    signals = []
    for uid, scores in _by_user(reviews, "raw_score").items():
        if len(scores) >= 2:
            extreme_count = sum(1 for s in scores if s <= extreme_lo or s >= extreme_hi)
            ratio = extreme_count / len(scores)
            if ratio == 1.0:
                signals.append(BotSignal(uid, "extreme_bias", 0.7))
    return signals


def check_satisfaction_anomaly(reviews: list[Review]) -> list[BotSignal]:
    """用户每次满意度都恰好是 1.0 — 过于整齐，真实用户极少如此。"""
    signals = []
    for uid, sats in _by_user(reviews, "satisfaction").items():
        if len(sats) >= 2 and all(s == 1.0 for s in sats):
            signals.append(BotSignal(uid, "satisfaction_anomaly", 0.65))
    return signals


def check_statistical_outlier(
    reviews: list[Review], z_threshold: float = 2.5
) -> list[BotSignal]:
    """用户均分与群体均分偏差超过 z 阈值 — 统计意义上的离群账号。"""
    all_scores = [r.raw_score for r in reviews]
    if len(all_scores) < 5:
        return []
    global_mean = _mean(all_scores)
    global_std = _stddev(all_scores)
    if global_std == 0:
        return []

    signals = []
    for uid, scores in _by_user(reviews, "raw_score").items():
        z = abs(_mean(scores) - global_mean) / global_std
        if z >= z_threshold:
            signals.append(BotSignal(uid, "statistical_outlier", min(1.0, z / (z_threshold * 2))))
    return signals


def check_coordinated_attack(
    reviews: list[Review], min_group: int = 3
) -> list[BotSignal]:
    """多个不同账号给出完全相同的 (分数, 满意度) 组合 — 协同刷分。"""
    combo_users: dict[tuple[float, float], set[str]] = defaultdict(set)
    for r in reviews:
        combo_users[(r.raw_score, r.satisfaction)].add(r.user_id)

    signals = []
    for uids in combo_users.values():
        if len(uids) >= min_group:
            for uid in uids:
                signals.append(BotSignal(uid, "coordinated_attack", 0.9))
    return signals


# ── 主入口 ───────────────────────────────────────────────────────────────────

def detect_bots(
    reviews: list[Review],
    confidence_threshold: float = 0.6,
    duplicate_threshold: int = 3,
    z_threshold: float = 2.5,
    coordinated_min_group: int = 3,
) -> set[str]:
    """综合六维信号识别水军，返回被标记用户 ID 集合。

    任意一个信号的置信度 >= confidence_threshold 即判定为水军。
    调低 confidence_threshold 可提高召回率，调高则提高精确率。
    """
    signals = explain(
        reviews,
        duplicate_threshold=duplicate_threshold,
        z_threshold=z_threshold,
        coordinated_min_group=coordinated_min_group,
    )
    return {s.user_id for s in signals if s.confidence >= confidence_threshold}


def explain(
    reviews: list[Review],
    duplicate_threshold: int = 3,
    z_threshold: float = 2.5,
    coordinated_min_group: int = 3,
) -> list[BotSignal]:
    """返回所有原始信号（含原因和置信度），用于调试与人工审核。"""
    all_signals: list[BotSignal] = []
    all_signals += check_duplicate_submissions(reviews, duplicate_threshold)
    all_signals += check_score_monotony(reviews)
    all_signals += check_extreme_bias(reviews)
    all_signals += check_satisfaction_anomaly(reviews)
    all_signals += check_statistical_outlier(reviews, z_threshold)
    all_signals += check_coordinated_attack(reviews, coordinated_min_group)
    return all_signals
