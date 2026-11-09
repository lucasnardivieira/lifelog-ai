"""Local speech-to-text with faster-whisper — audio never leaves the machine.

Optional dependency: `uv sync --extra voice`. The model is downloaded once on first use
(WHISPER_MODEL, default "small"; "base" is faster, "medium" more accurate).
"""

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel

    return WhisperModel(os.environ.get("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")


def available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def transcribe(path: Path) -> str:
    segments, _ = _model().transcribe(str(path), language="pt", vad_filter=True)
    return " ".join(s.text.strip() for s in segments).strip()
