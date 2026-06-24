# ============================================================
# COMP9001 Final Project  —  Smart Review Scoring System
# Student: Qiyuan Dong
#
# HOW TO RUN (terminal / Ed):
#   python app.py
#
# This is the TERMINAL version — works in any Python environment
# including Ed, with no external libraries required.
#
# For the full GUI desktop version, see app_gui.py
# ============================================================

# ============================================================
# Data storage  (plain dictionaries)
# ============================================================

items = {}   # { item_name -> { "reviews": [...], "score": float } }
users = {}   # { username  -> { "weight": float, "history": [float], "note": str } }


# ============================================================
# Core logic
# ============================================================

def compute_user_weight(history):
    """Return (weight, note) based on the user's scoring history."""
    if len(history) < 2:
        return 1.0, "Not enough history"

    total = 0.0
    for score in history:
        total = total + score
    average = total / len(history)

    variance_sum = 0.0
    for score in history:
        variance_sum = variance_sum + (score - average) ** 2
    variance = variance_sum / len(history)

    if average >= 8.5:
        return 0.4, "Always high scores - influence reduced"
    elif average <= 1.5:
        return 0.4, "Always low scores - influence reduced"
    elif variance < 1.0:
        return 0.7, "Low score variety - influence slightly reduced"
    else:
        return 1.0, "Normal"


def _mean(values):
    if len(values) == 0:
        return 0.0
    total = 0.0
    for v in values:
        total = total + v
    return total / len(values)


def _stddev(values):
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = 0.0
    for v in values:
        variance = variance + (v - m) ** 2
    return (variance / len(values)) ** 0.5


def filter_malicious(review_list):
    """Remove malicious reviews using three standards."""
    flagged = []
    keep    = []

    # Standard 1: formula gaming
    for review in review_list:
        if (review["raw"] >= 9.5 or review["raw"] <= 0.5) and review["satisfaction"] == 0.0:
            flagged.append(review)
        else:
            keep.append(review)

    # Standard 3: coordinated identical
    combo_users = {}
    for review in review_list:
        key = (review["raw"], review["satisfaction"])
        if key not in combo_users:
            combo_users[key] = set()
        combo_users[key].add(review["user"])

    still_keep = []
    for review in keep:
        key = (review["raw"], review["satisfaction"])
        if len(combo_users[key]) >= 3:
            flagged.append(review)
        else:
            still_keep.append(review)
    keep = still_keep

    # Standard 2: statistical outlier
    if len(keep) >= 5:
        raws   = [r["raw"] for r in keep]
        mean   = _mean(raws)
        stddev = _stddev(raws)
        if stddev > 0:
            final_keep = []
            for review in keep:
                if abs(review["raw"] - mean) > 3 * stddev:
                    flagged.append(review)
                else:
                    final_keep.append(review)
            keep = final_keep

    return keep, flagged


def compute_item_score(review_list):
    """New scoring logic:
    1. Remove malicious reviews.
    2. group_mean = mean of clean raw scores.
    3. adjusted = raw*(1-sat) + group_mean*sat
       sat=1 → agree with current score; sat=0 → fully use own raw score.
    4. Final = weighted mean of adjusted, weighted by user_weight.
    """
    if len(review_list) == 0:
        return 0.0

    clean, _ = filter_malicious(review_list)
    if len(clean) == 0:
        return 0.0

    raws       = [r["raw"] for r in clean]
    group_mean = _mean(raws)

    weighted_sum = 0.0
    weight_total = 0.0

    for review in clean:
        username    = review["user"]
        user_weight = users[username]["weight"] if username in users else 1.0
        adjusted    = review["raw"] * (1 - review["satisfaction"]) \
                    + group_mean    *      review["satisfaction"]
        weighted_sum = weighted_sum + adjusted    * user_weight
        weight_total = weight_total + user_weight

    if weight_total == 0.0:
        return 0.0
    return weighted_sum / weight_total


def refresh_scores():
    for name in items:
        items[name]["score"] = compute_item_score(items[name]["reviews"])


# ============================================================
# Input helpers
# ============================================================

def get_float(prompt, lo, hi):
    while True:
        try:
            value = float(input(prompt).strip())
            if lo <= value <= hi:
                return value
            print(f"  Please enter a number between {lo} and {hi}.")
        except ValueError:
            print("  Invalid input.")


# ============================================================
# Features
# ============================================================

def add_item():
    print("\n-- Add New Item --")
    name = input("  Item name: ").strip()
    if not name:
        print("  Name cannot be empty.")
        return
    if name in items:
        print(f"  '{name}' already exists.")
        return
    items[name] = {"reviews": [], "score": 0.0}
    print(f"  Added: '{name}'")


def rate_item():
    print("\n-- Rate an Item --")
    if len(items) == 0:
        print("  No items yet. Add one first (option 1).")
        return

    print("  Available items:")
    index = 1
    for name in items:
        print(f"    {index}. {name}  (score: {items[name]['score']:.2f})")
        index = index + 1

    name = input("  Item to rate: ").strip()
    if name not in items:
        print(f"  '{name}' not found.")
        return

    username = input("  Your username: ").strip()
    if not username:
        print("  Username cannot be empty.")
        return

    print("\n  Round 1 - How do you rate this item?")
    raw = get_float("  Score (0-10): ", 0, 10)

    current_score = items[name]["score"]
    review_count  = len(items[name]["reviews"])
    if review_count == 0:
        print("\n  Round 2 - No overall score yet (you are the first reviewer).")
    else:
        print(f"\n  Round 2 - Current overall score: {current_score:.2f} / 10  ({review_count} reviews)")
    print("  How satisfied are you with the current overall score?")
    print("  (1.0 = fully agree  |  0.0 = strongly disagree)")
    satisfaction = get_float("  Satisfaction (0-1): ", 0, 1)

    items[name]["reviews"].append({"user": username, "raw": raw, "satisfaction": satisfaction})

    if username not in users:
        users[username] = {"weight": 1.0, "history": [], "note": "New user"}
    users[username]["history"].append(raw)

    new_weight, new_note = compute_user_weight(users[username]["history"])
    users[username]["weight"] = new_weight
    users[username]["note"] = new_note

    refresh_scores()
    print(f"\n  Review saved. '{name}' updated score: {items[name]['score']:.2f}")
    if new_weight < 1.0:
        print(f"  Note: your influence weight is {new_weight:.1f} ({new_note})")


def show_leaderboard():
    print("\n-- Leaderboard --")
    if len(items) == 0:
        print("  No items yet.")
        return

    ranked = []
    for name in items:
        ranked.append((name, items[name]))

    for i in range(len(ranked)):
        for j in range(len(ranked) - 1 - i):
            if ranked[j][1]["score"] < ranked[j + 1][1]["score"]:
                ranked[j], ranked[j + 1] = ranked[j + 1], ranked[j]

    print(f"\n  {'Rank':<6} {'Item':<22} {'Score':<8} {'Reviews'}")
    print("  " + "-" * 46)
    rank = 1
    for name, data in ranked:
        print(f"  {rank:<6} {name:<22} {data['score']:<8.2f} {len(data['reviews'])}")
        rank = rank + 1


def show_user_weights():
    print("\n-- User Influence Weights --")
    if len(users) == 0:
        print("  No users yet.")
        return

    print(f"\n  {'User':<16} {'Weight':<8} {'Reviews':<9} {'Avg Score':<11} {'Note'}")
    print("  " + "-" * 65)

    for username in users:
        data = users[username]
        history = data["history"]
        avg = sum(history) / len(history) if history else 0.0
        print(f"  {username:<16} {data['weight']:<8.2f} {len(history):<9} {avg:<11.2f} {data['note']}")


# ============================================================
# Main menu
# ============================================================

def main():
    print("=" * 42)
    print("  Smart Review Scoring System")
    print("  USYD COMP9001 - Final Project")
    print("=" * 42)

    while True:
        print("\n  1. Add a new item")
        print("  2. Rate an item")
        print("  3. Leaderboard")
        print("  4. User influence weights")
        print("  5. Quit")

        choice = input("\n  Choose (1-5): ").strip()

        if choice == "1":
            add_item()
        elif choice == "2":
            rate_item()
        elif choice == "3":
            show_leaderboard()
        elif choice == "4":
            show_user_weights()
        elif choice == "5":
            print("\n  Goodbye!")
            break
        else:
            print("  Invalid choice. Please enter 1 to 5.")


if __name__ == "__main__":
    main()
