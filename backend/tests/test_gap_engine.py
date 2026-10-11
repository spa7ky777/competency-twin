from app.competency.gap_engine import rank_gaps


def test_gap_ranking():
    recs = [
        {"competency_id": 1, "name": "A", "current_score": 30, "attempts": 2, "last_assessed_at": None},
        {"competency_id": 2, "name": "B", "current_score": 50, "attempts": 1, "last_assessed_at": None},
        {"competency_id": 3, "name": "C", "current_score": 90, "attempts": 3, "last_assessed_at": None},
        {"competency_id": 4, "name": "D", "current_score": None, "attempts": 0, "last_assessed_at": None},
    ]
    g = rank_gaps(recs, 60, [39, 59, 74, 89])
    assert g["weak"][0]["name"] == "A"
    assert g["strong"][0]["name"] == "C"
    assert g["unassessed"][0]["name"] == "D"
