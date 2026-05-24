"""
Smart Review Scoring System - Demo
USYD COMP9001 Final Project
"""

from scorer.core import Review, aggregate
from scorer.meta_score import apply_meta
from scorer.bot_detect import detect_bots, explain


def print_separator():
    print("-" * 50)


def main():
    print("=" * 50)
    print("  Smart Review Scoring System")
    print("  USYD COMP9001 - Final Project Demo")
    print("=" * 50)

    # ------------------------------------------------------------------
    # Step 1: Collect reviews
    # Each reviewer gives a raw score (0-10) and a satisfaction (0-1).
    # Satisfaction is the meta-rating: "how confident am I in my score?"
    # ------------------------------------------------------------------
    print("\n[Step 1] Raw reviews submitted by users")
    print_separator()

    reviews = [
        Review("alice",   raw_score=8.0, satisfaction=0.9),
        Review("bob",     raw_score=6.0, satisfaction=0.5),
        Review("carol",   raw_score=7.0, satisfaction=0.8),
        Review("bot1",    raw_score=10.0, satisfaction=1.0),
        Review("bot1",    raw_score=10.0, satisfaction=1.0),
        Review("bot1",    raw_score=10.0, satisfaction=1.0),
        Review("bot1",    raw_score=10.0, satisfaction=1.0),
        Review("shill_a", raw_score=10.0, satisfaction=1.0),
        Review("shill_b", raw_score=10.0, satisfaction=1.0),
        Review("shill_c", raw_score=10.0, satisfaction=1.0),
    ]

    for r in reviews:
        print(f"  {r.user_id:<12} score={r.raw_score:.1f}  satisfaction={r.satisfaction:.1f}")

    # ------------------------------------------------------------------
    # Step 2: Apply meta-scores (update satisfaction after reflection)
    # ------------------------------------------------------------------
    print("\n[Step 2] Bob reconsiders - updates his satisfaction to 0.3")
    print_separator()

    updated_reviews = []
    for r in reviews:
        if r.user_id == "bob":
            r = apply_meta(r, meta_rating=0.3)
            print(f"  bob's satisfaction updated -> {r.satisfaction:.1f}")
        updated_reviews.append(r)

    # ------------------------------------------------------------------
    # Step 3: Detect bots
    # ------------------------------------------------------------------
    print("\n[Step 3] Running bot detection across six signals")
    print_separator()

    signals = explain(updated_reviews)
    seen = set()
    for signal in signals:
        key = (signal.user_id, signal.reason)
        if key not in seen:
            seen.add(key)
            print(f"  [!] {signal.user_id:<12} | {signal.reason:<25} | confidence={signal.confidence:.2f}")

    bot_ids = detect_bots(updated_reviews)
    print(f"\n  Flagged as bots: {sorted(bot_ids)}")

    # ------------------------------------------------------------------
    # Step 4: Compare scores with and without bot filtering
    # ------------------------------------------------------------------
    print("\n[Step 4] Score comparison")
    print_separator()

    raw_mean = sum(r.raw_score for r in updated_reviews) / len(updated_reviews)
    score_without_filter = aggregate(updated_reviews, bot_ids=None)
    score_with_filter    = aggregate(updated_reviews, bot_ids=bot_ids)

    print(f"  Simple mean (no adjustment, no filter): {raw_mean:.2f}")
    print(f"  Adjusted score (no bot filter):         {score_without_filter:.2f}")
    print(f"  Adjusted score (bots removed):          {score_with_filter:.2f}")

    print("\n  Bots inflated the score by "
          f"{score_without_filter - score_with_filter:.2f} points.")
    print("\n[Done]")


if __name__ == "__main__":
    main()
