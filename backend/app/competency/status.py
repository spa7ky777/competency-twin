from app.competency.scoring import LABELS, status_for


def status_payload(thresholds: list[int]) -> dict:
    bands = [
        {"label": LABELS[0], "min": 0, "max": thresholds[0]},
        {"label": LABELS[1], "min": thresholds[0] + 1, "max": thresholds[1]},
        {"label": LABELS[2], "min": thresholds[1] + 1, "max": thresholds[2]},
        {"label": LABELS[3], "min": thresholds[2] + 1, "max": thresholds[3]},
        {"label": LABELS[4], "min": thresholds[3] + 1, "max": 100},
    ]
    return {"thresholds": thresholds, "labels": LABELS, "bands": bands, "status_for_example": status_for(55, thresholds)}
