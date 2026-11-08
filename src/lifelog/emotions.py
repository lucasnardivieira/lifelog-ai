"""PT-BR emotion vocabulary placed on Russell's circumplex (valence × arousal, each −2…+2).

Used to (1) offer precise words at check-in time (emotional granularity), (2) let Claude map
free text to words, and (3) colour words by quadrant in the dashboard.
Positions are approximate and only used for display/defaults; the user's own valence/arousal
rating is the measurement.
"""

from typing import Literal

Quadrant = Literal["yellow", "red", "blue", "green"]

QUADRANTS: dict[Quadrant, dict[str, str]] = {
    "yellow": {"label": "Agradável + energia alta", "hint": "animado, motivado"},
    "red": {"label": "Desagradável + energia alta", "hint": "ansioso, irritado"},
    "blue": {"label": "Desagradável + energia baixa", "hint": "triste, cansado"},
    "green": {"label": "Agradável + energia baixa", "hint": "calmo, satisfeito"},
}

# word: (valence, arousal)
EMOTIONS: dict[str, tuple[int, int]] = {
    # yellow — pleasant, high energy
    "animado": (2, 2),
    "empolgado": (2, 2),
    "alegre": (2, 1),
    "motivado": (1, 2),
    "inspirado": (2, 1),
    "orgulhoso": (2, 1),
    "confiante": (1, 1),
    "curioso": (1, 1),
    "focado": (1, 1),
    "grato": (2, 0),
    # red — unpleasant, high energy
    "ansioso": (-1, 2),
    "estressado": (-2, 2),
    "irritado": (-2, 1),
    "frustrado": (-2, 1),
    "sobrecarregado": (-2, 2),
    "preocupado": (-1, 1),
    "impaciente": (-1, 1),
    "inseguro": (-1, 1),
    "com raiva": (-2, 2),
    "tenso": (-1, 2),
    # blue — unpleasant, low energy
    "triste": (-2, -1),
    "cansado": (-1, -2),
    "desanimado": (-2, -1),
    "entediado": (-1, -1),
    "sozinho": (-2, -1),
    "decepcionado": (-2, -1),
    "esgotado": (-2, -2),
    "melancólico": (-1, -1),
    "apático": (-1, -2),
    "culpado": (-2, -1),
    # green — pleasant, low energy
    "calmo": (1, -1),
    "tranquilo": (1, -2),
    "satisfeito": (2, -1),
    "relaxado": (2, -2),
    "em paz": (2, -2),
    "aliviado": (1, -1),
    "acolhido": (2, -1),
    "sereno": (1, -2),
    "contente": (1, -1),
    "descansado": (1, -1),
}


def quadrant(valence: float, arousal: float) -> Quadrant:
    """Neutral valence counts as pleasant, neutral arousal as low (ties are rare in averages)."""
    if valence >= 0:
        return "yellow" if arousal > 0 else "green"
    return "red" if arousal > 0 else "blue"


def words_in(q: Quadrant) -> list[str]:
    return [w for w, (v, a) in EMOTIONS.items() if quadrant(v, a) == q]
