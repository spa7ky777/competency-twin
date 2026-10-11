from app.competency.scoring import adaptive_difficulty, adaptive_mix


def targeted_plan(score: float | None, n: int) -> dict:
    return {"difficulty": adaptive_difficulty(score), "mix": adaptive_mix(score), "num_questions": n}
