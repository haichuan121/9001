================================================================
COMP9001 Final Project — Smart Review Scoring System
Student: Qiyuan Dong
================================================================

OVERVIEW
--------
A smart rating tool that goes beyond simple star scores.
Users rate an item, then rate how confident they are in their
own score. The system uses that confidence to adjust the final
result, and automatically reduces the influence of users who
show suspicious rating patterns (always max, always min, or
monotonous scores).


FILES SUBMITTED
---------------
app_gui.py      — GUI desktop application  (MAIN program)
app.py          — Terminal version         (runs in Ed)
scorer/core.py      — Core scoring logic
scorer/meta_score.py — Satisfaction-weight helper
scorer/bot_detect.py — Six-signal bot detection engine


HOW TO RUN
----------

Option A — Terminal (works in Ed, no extra libraries needed):
    python app.py

Option B — Desktop GUI (requires a display):
    python app_gui.py

    The GUI uses tkinter, which is part of Python's standard
    library and does not require pip install. However, it needs
    a graphical display to open the window, so it cannot run
    inside Ed's browser terminal.

    A pre-built Windows .exe is available at:
    https://github.com/haichuan121/9001


LIBRARIES USED
--------------
tkinter     — Python built-in (standard library)
              Used in: app_gui.py only
              Creates the desktop window and UI widgets.

No third-party packages (pip install) are required to run
app.py or app_gui.py.

PyInstaller was used separately to build the .exe file,
but is NOT needed to run the Python source code.


PYTHON CONCEPTS DEMONSTRATED
-----------------------------
- for loops       (score accumulation, leaderboard sort,
                   user history iteration)
- while loop      (menu loop, input validation retry loop)
- if / elif /else (weight rules, menu dispatch)
- functions       (each feature is an isolated function)
- dictionaries    (items and users storage)
- lists           (review history, ranked list)
- classes         (Review, BotSignal in scorer/ modules)
- math            (mean, variance, standard deviation)


FEATURES (GUI tabs / terminal menu)
------------------------------------
1. Add Item         — add a new rateable item
2. Rate Item        — two-round input:
                        Round 1: score (0-10)
                        Round 2: confidence in that score (0-1)
3. Leaderboard      — all items ranked by weighted final score
4. User Weights     — per-user influence weight based on their
                      rating history; suspicious users highlighted


SCORING FORMULA
---------------
final_score = SUM(raw x confidence x user_weight)
              / SUM(confidence x user_weight)

USER WEIGHT RULES
-----------------
Average score >= 8.5  ->  weight 0.4  (always high)
Average score <= 1.5  ->  weight 0.4  (always low)
Score variance < 1.0  ->  weight 0.7  (low variety)
Otherwise             ->  weight 1.0  (normal)

GitHub: https://github.com/haichuan121/9001
================================================================
