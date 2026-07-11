import json
import os

_SCORES_FILE = os.path.join(os.path.dirname(__file__), "highscores.json")
MAX_SCORES = 5


def load_scores():
    """Return list of (score, initials) sorted descending, at most MAX_SCORES entries."""
    try:
        with open(_SCORES_FILE, "r") as f:
            data = json.load(f)
        return [(int(e["score"]), str(e["initials"])) for e in data]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []


def save_score(score, initials):
    """Add entry, keep top MAX_SCORES. Returns updated sorted list."""
    scores = load_scores()
    scores.append((score, initials.upper()[:3]))
    scores.sort(key=lambda x: x[0], reverse=True)
    scores = scores[:MAX_SCORES]
    with open(_SCORES_FILE, "w") as f:
        json.dump([{"score": s, "initials": i} for s, i in scores], f)
    return scores


def is_high_score(score):
    """True if score would appear on the top-5 leaderboard."""
    if score <= 0:
        return False
    scores = load_scores()
    if len(scores) < MAX_SCORES:
        return True
    return score > scores[-1][0]
