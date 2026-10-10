import json
import os
import sys

_SCORES_FILE = os.path.join(os.path.dirname(__file__), "highscores.json")
MAX_SCORES = 5


def load_scores():
    """Return list of (score, initials) sorted descending, at most MAX_SCORES entries.

    Never raises: a missing, unreadable or damaged file yields an empty board, and
    individual damaged entries are skipped so the rest of the board survives."""
    try:
        with open(_SCORES_FILE, "r", encoding="utf-8") as f:
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
