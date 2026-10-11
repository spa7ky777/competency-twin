from __future__ import annotations

# Status: 0-39 Critical Gap | 40-59 Needs Improvement | 60-74 Developing | 75-89 Proficient | 90-100 Strong
# Thresholds from env are the upper bounds of the first four bands: default 39,59,74,89

DEFAULT_THRESHOLDS = [39, 59, 74, 89]
LABELS = ["Critical Gap", "Needs Improvement", "Developing", "Proficient", "Strong"]


def status_for(score: float, thresholds: list[int] | None = None) -> str:
    t = thresholds or DEFAULT_THRESHOLDS
    if score <= t[0]:
        return LABELS[0]
    if score <= t[1]:
        return LABELS[1]
    if score <= t[2]:
        return LABELS[2]
    if score <= t[3]:
        return LABELS[3]
    return LABELS[4]


def ema_weight(n_questions: int, ema_base: float = 0.6, cap: float = 0.5) -> float:
    """Weight grows with n; small quizzes move the score less.

    new = (1-w)*old + w*quiz_percent
    Example: old=42, 8/10=80, n=10, ema_base=0.6 -> w=0.6*10/13≈0.4615 -> ~59.5
    """
    if n_questions <= 0:
        return 0.0
    return min(ema_base * (n_questions / (n_questions + 3)), cap)


def update_score(
    old_score: float | None,
    quiz_percent: float,
    n_questions: int,
    ema_base: float = 0.6,
) -> tuple[float, float]:
    """Returns (new_score, weight_used). First assessment copies quiz percent."""
    if old_score is None:
        return quiz_percent, 1.0
    w = ema_weight(n_questions, ema_base)
    return (1 - w) * old_score + w * quiz_percent, w


def adaptive_difficulty(score: float | None) -> str:
    if score is None or score < 40:
        return "easy"
    if score < 60:
        return "easy-medium"
    if score < 75:
        return "medium"
    return "medium-hard"


def adaptive_mix(score: float | None) -> list[str]:
    band = adaptive_difficulty(score)
    if band == "easy":
        return ["easy", "easy", "easy", "medium"]
    if band == "easy-medium":
        return ["easy", "easy", "medium", "medium"]
    if band == "medium":
        return ["medium", "medium", "medium", "hard"]
    return ["medium", "hard", "hard", "hard"]
