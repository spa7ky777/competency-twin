from app.competency.scoring import adaptive_difficulty, ema_weight, status_for, update_score


def test_status_bands():
    t = [39, 59, 74, 89]
    assert status_for(0, t) == "Critical Gap"
    assert status_for(39, t) == "Critical Gap"
    assert status_for(40, t) == "Needs Improvement"
    assert status_for(59, t) == "Needs Improvement"
    assert status_for(60, t) == "Developing"
    assert status_for(90, t) == "Strong"


def test_ema_example_42_then_8_of_10():
    new, w = update_score(42.0, 80.0, 10, 0.6)
    assert 55 <= new <= 62
    assert abs(w - 0.6 * 10 / 13) < 1e-6


def test_first_assessment_copies_quiz():
    new, w = update_score(None, 70.0, 5)
    assert new == 70.0
    assert w == 1.0


def test_small_attempt_moves_less():
    w10 = ema_weight(10)
    w2 = ema_weight(2)
    assert w2 < w10


def test_adaptive_difficulty():
    assert adaptive_difficulty(20) == "easy"
    assert adaptive_difficulty(50) == "easy-medium"
    assert adaptive_difficulty(70) == "medium"
    assert adaptive_difficulty(80) == "medium-hard"
