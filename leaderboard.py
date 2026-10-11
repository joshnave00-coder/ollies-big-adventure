import json
import os
import sys

APP_DIR_NAME = "OlliesBigAdventure"
MAX_SCORES = 5


def _user_data_dir():
    """Per-user folder for saved data (always writable, outside the code folder)."""
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    return os.path.join(base, APP_DIR_NAME)


# Scores are saved per user.  Up to 0.8.1 they lived in highscores.json next to
# the code; that file is now only read (never written) as the starting board
# until the first new score is saved, so nobody's old scores are lost.
_SCORES_FILE = os.path.join(_user_data_dir(), "highscores.json")
_LEGACY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")


def load_scores():
    """Return list of (score, initials) sorted descending, at most MAX_SCORES entries.

    Never raises: a missing, unreadable or damaged file yields an empty board, and
    individual damaged entries are skipped so the rest of the board survives."""
    path = _SCORES_FILE if os.path.exists(_SCORES_FILE) else _LEGACY_FILE
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):   # ValueError covers bad JSON and bad encoding
        return []
    if not isinstance(data, list):
        return []
    scores = []
    for e in data:
        try:
            scores.append((int(e["score"]), str(e["initials"]).upper()[:3]))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
    scores.sort(key=lambda x: x[0], reverse=True)
    return scores[:MAX_SCORES]


def save_score(score, initials):
    """Add entry, keep top MAX_SCORES. Returns updated sorted list.

    The file is written to a temp file and swapped in, so a crash or power cut
    mid-save can't leave a half-written leaderboard.  If the folder isn't
    writable the game carries on with the in-memory list instead of crashing."""
    scores = load_scores()
    scores.append((score, initials.upper()[:3]))
    scores.sort(key=lambda x: x[0], reverse=True)
    scores = scores[:MAX_SCORES]
    tmp = _SCORES_FILE + ".tmp"
    try:
        os.makedirs(os.path.dirname(_SCORES_FILE), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump([{"score": s, "initials": i} for s, i in scores], f)
        os.replace(tmp, _SCORES_FILE)
    except OSError as err:
        print(f"Could not save high scores to {_SCORES_FILE}: {err}", file=sys.stderr)
    return scores


def is_high_score(score):
    """True if score would appear on the top-5 leaderboard."""
    if score <= 0:
        return False
    scores = load_scores()
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1][0]
