"""Crisis-language safety net. Runs on every free-text/voice message, before anything else.

Claude's extraction also returns a `risk` level; this keyword pass is the fallback so a failed or
refused API call can never silence a crisis message. The reply is warm and practical, not a lecture,
and never diagnostic (docs/research/psychology-foundations.md §9).
"""

import re
import unicodedata

CRISIS_PATTERNS = [
    r"\bsuicid",
    r"\bme mat(ar|o)\b",
    r"\bquero morrer\b",
    r"\bnao quero (mais )?viver\b",
    r"\bacabar com (a minha vida|tudo)\b",
    r"\bsumir (de vez|pra sempre|para sempre)\b",
    r"\bme (machucar|cortar|ferir)\b",
    r"\bautoles",
    r"\bnao aguento mais viver\b",
    r"\bseria melhor (se eu|sem mim)\b",
]

# Telegram HTML parse mode
SUPPORT_MESSAGE = (
    "💬 Obrigado por me contar isso. Você não precisa passar por isso sem apoio.\n\n"
    "Se puder, fale agora com alguém:\n"
    "• <b>CVV — 188</b> (ligação gratuita, 24h) ou o chat em https://cvv.org.br/chat/\n"
    "• <b>SAMU — 192</b> em emergência\n"
    "• Ou uma pessoa de confiança perto de você.\n\n"
    "Eu sou só um diário e não substituo esse cuidado. Estou aqui quando quiser registrar algo."
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def keyword_risk(text: str) -> bool:
    t = _normalize(text)
    return any(re.search(p, t) for p in CRISIS_PATTERNS)
