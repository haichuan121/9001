"""
Smart Review Scoring System - Interactive App
USYD COMP9001 Final Project
"""

# ============================================================
# Data storage  (plain dictionaries, no external libraries)
# ============================================================

# items  : { item_name -> { "reviews": [...], "score": float } }
# Each review: { "user": str, "raw": float, "satisfaction": float }
items = {}

# users  : { username -> { "weight": float, "history": [scores], "note": str } }
users = {}


# ============================================================
# Score computation
# ============================================================

def compute_user_weight(history):
    """Return a weight (0.0-1.0) based on the user's scoring history.

    Uses a loop to inspect every past score, then applies rules:
      - Always high (average >= 8.5)  -> weight 0.4
      - Always low  (average <= 1.5)  -> weight 0.4
      - Low variety (variance < 1.0)  -> weight 0.7
      - Normal                        -> weight 1.0
    """
    if len(history) < 2:
        return 1.0, "Not enough history"

    # --- calculate average using a for loop ---
    total = 0.0
    for score in history:
        total = total + score
    average = total / len(history)

    # --- calculate variance using a for loop ---
    variance_sum = 0.0
    for score in history:
        variance_sum = variance_sum + (score - average) ** 2
    variance = variance_sum / len(history)

    # --- apply weight rules ---
    if average >= 8.5:
        return 0.4, "Always high scores - influence reduced"
    elif average <= 1.5:
        return 0.4, "Always low scores - influence reduced"
    elif variance < 1.0:
        return 0.7, "Low score variety - influence slightly reduced"
    else:
        return 1.0, "Normal"


def compute_item_score(review_list):
    """Compute the weighted final score for one item.

    Formula:
        final = sum(raw * satisfaction * user_weight)
                / sum(satisfaction * user_weight)

    Low satisfaction or low user_weight both reduce a review's influence.
    """
    if len(review_list) == 0:
        return 0.0

    weighted_sum = 0.0
    weight_total = 0.0

    for review in review_list:
        username = review["user"]
        user_weight = users[username]["weight"] if username in users else 1.0
        effective = review["satisfaction"] * user_weight
        weighted_sum = weighted_sum + review["raw"] * effective
        weight_total = weight_total + effective

    if weight_total == 0.0:
        return 0.0
    return weighted_sum / weight_total


def refresh_scores():
    """Recompute the final score for every item after any change."""
    for name in items:
        items[name]["score"] = compute_item_score(items[name]["reviews"])


# ============================================================
# Feature 1 - Add item
# ============================================================

def add_item():
    print("\n-- Add New Item --")
    name = input("  Item name: ").strip()

    if name == "":
        print("  Name cannot be empty.")
        return

    if name in items:
        print(f"  '{name}' already exists.")
        return

    items[name] = {"reviews": [], "score": 0.0}
    print(f"  Added: '{name}'")


# ============================================================
# Feature 2 - Rate an item (two rounds)
# ============================================================

def get_float(prompt, lo, hi):
    """Keep asking until the user enters a valid float in [lo, hi]."""
    while True:
        raw_input = input(prompt).strip()
        try:
            value = float(raw_input)
            if lo <= value <= hi:
                return value
            else:
                print(f"  Please enter a number between {lo} and {hi}.")
        except ValueError:
            print("  Invalid input - please enter a number.")


def rate_item():
    print("\n-- Rate an Item --")

    if len(items) == 0:
        print("  No items yet. Add one first (option 1).")
        return

    # Show available items
    print("  Available items:")
    index = 1
    for name in items:
        print(f"    {index}. {name}  (current score: {items[name]['score']:.2f})")
        index = index + 1

    name = input("  Item to rate: ").strip()
    if name not in items:
        print(f"  '{name}' not found.")
        return

    username = input("  Your username: ").strip()
    if username == "":
        print("  Username cannot be empty.")
        return

    # --- Round 1: raw score ---
    print("\n  Round 1 - How do you rate this item?")
    raw = get_float("  Score (0-10): ", 0, 10)

    # --- Round 2: satisfaction (meta-rating) ---
    print("\n  Round 2 - How confident are you in the score you just gave?")
    print("  (1.0 = very sure,  0.0 = not sure at all)")
    satisfaction = get_float("  Confidence (0-1): ", 0, 1)

    # Store the review
    review = {"user": username, "raw": raw, "satisfaction": satisfaction}
    items[name]["reviews"].append(review)

    # Create user if new
    if username not in users:
        users[username] = {"weight": 1.0, "history": [], "note": "New user"}

    # Update user history and recompute weight
    users[username]["history"].append(raw)
    new_weight, new_note = compute_user_weight(users[username]["history"])
    users[username]["weight"] = new_weight
    users[username]["note"] = new_note

    # Refresh all item scores
    refresh_scores()

    print(f"\n  Review saved.")
    print(f"  '{name}' updated score: {items[name]['score']:.2f}")

    # Warn if user weight was reduced
    if new_weight < 1.0:
        print(f"  Note: your influence weight is {new_weight:.1f} ({new_note})")


# ============================================================
# Feature 3 - Leaderboard
# ============================================================

def show_leaderboard():
    print("\n-- Leaderboard --")

    if len(items) == 0:
        print("  No items yet.")
        return

    # Build a list of (name, data) and sort by score descending
    ranked = []
    for name in items:
        ranked.append((name, items[name]))

    # Bubble sort so the loop structure is visible (course-friendly)
    for i in range(len(ranked)):
        for j in range(len(ranked) - 1 - i):
            if ranked[j][1]["score"] < ranked[j + 1][1]["score"]:
                ranked[j], ranked[j + 1] = ranked[j + 1], ranked[j]

    print(f"\n  {'Rank':<6} {'Item':<22} {'Score':<8} {'Reviews'}")
    print("  " + "-" * 46)

    rank = 1
    for name, data in ranked:
        review_count = len(data["reviews"])
        print(f"  {rank:<6} {name:<22} {data['score']:<8.2f} {review_count}")
        rank = rank + 1


# ============================================================
# Feature 4 - User weight report
# ============================================================

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

        # Calculate average score for display
        if len(history) > 0:
            avg = sum(history) / len(history)
        else:
            avg = 0.0

        print(
            f"  {username:<16} {data['weight']:<8.2f} "
            f"{len(history):<9} {avg:<11.2f} {data['note']}"
        )


# ============================================================
# Main menu
# ============================================================

def print_menu():
    print("\n" + "=" * 40)
    print("  1. Add a new item")
    print("  2. Rate an item")
    print("  3. Leaderboard")
    print("  4. User influence weights")
    print("  5. Quit")
    print("=" * 40)


def main():
    print("=" * 40)
    print("  Smart Review Scoring System")
    print("  USYD COMP9001 - Final Project")
    print("=" * 40)

    while True:
        print_menu()
        choice = input("  Choose (1-5): ").strip()

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
