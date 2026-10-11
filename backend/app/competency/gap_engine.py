from datetime import datetime

from app.competency.scoring import status_for


def rank_gaps(
    records: list[dict],
    threshold: float,
    thresholds: list[int],
) -> dict:
    """records: {competency_id, name, current_score|None, attempts, last_assessed_at}"""
    unassessed = []
    weak = []
    strong = []
    for r in records:
        score = r.get("current_score")
        item = {**r, "status": status_for(score, thresholds) if score is not None else "Unassessed"}
        if score is None:
            unassessed.append(item)
        elif score < threshold:
            weak.append(item)
        else:
            strong.append(item)

    def weak_key(x):
        last = x.get("last_assessed_at") or datetime.min
        return (x["current_score"], x.get("attempts") or 0, last)

    weak.sort(key=weak_key)
    strong.sort(key=lambda x: -(x["current_score"] or 0))
    return {"weak": weak, "strong": strong, "unassessed": unassessed}
