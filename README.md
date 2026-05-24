# Smart Review Scoring System

**USYD COMP9001 — Final Project**

A Python tool that goes beyond traditional star ratings. Users rate a target *and* rate how confident they feel about their own score. The system uses that confidence to adjust the final result, then filters out fake reviewers (bots/shills) before computing the aggregate.

## Core Ideas

| Problem | Our Solution |
|---------|-------------|
| Ratings don't reflect true confidence | A *satisfaction weight* pulls uncertain scores toward the group average |
| Bots and shills skew results | Six detection signals flag suspicious accounts before aggregation |

### Correction Formula

```
adjusted = raw_score × satisfaction + group_mean × (1 − satisfaction)
```

A satisfaction of 1.0 keeps the score as-is. A satisfaction of 0.0 replaces it with the group mean — the user is saying "I'm not sure, go with the crowd."

## Project Structure

```
9001/
├── main.py               # Demo — run this for the presentation
├── scorer/
│   ├── core.py           # Review class, score adjustment, aggregation
│   ├── meta_score.py     # Apply a satisfaction rating to a review
│   └── bot_detect.py     # Six-signal bot detection engine
└── tests/
    ├── test_core.py
    └── test_bot_detect.py
```

## Python Concepts Demonstrated

- **for loops** — iterating over review lists and dictionaries
- **if / elif / else** — conditional logic in every detection signal
- **functions** — each detection check is an isolated, testable function
- **lists and dictionaries** — core data structures throughout
- **classes** — `Review` and `BotSignal` model real-world entities
- **math** — mean, variance, standard deviation for outlier detection

## Quick Start

```bash
python main.py
```

## Running Tests

```bash
python -m pytest tests/ -v
```
