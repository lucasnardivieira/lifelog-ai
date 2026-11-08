from lifelog.export import habit_series


def test_habit_strength_forgives_a_missed_day() -> None:
    rows = [
        {"habit": "meditar", "day": f"2026-01-{d:02d}", "done": True, "if_then": "Se… então…"}
        for d in range(1, 31)
    ]
    rows[20]["done"] = False
    (habit,) = habit_series(rows)
    strengths = [p["strength"] for p in habit["points"]]
    assert strengths[20] < strengths[19]  # dented
    assert strengths[20] > strengths[10]  # not reset
    assert strengths[-1] > strengths[19]  # recovers
    assert habit["if_then"] == "Se… então…"
