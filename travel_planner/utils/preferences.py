"""Explicit destination requirements that semantic similarity must not override."""
import re

_COAST = r"(?:oceans?|beach(?:es)?|seaside|coast(?:al|line)?|sea|surfing|snorkel(?:ing|ling)?)"


def wants_coast(text):
    text = text.lower()
    if re.search(r"\b(?:avoid|without|no|not|don't want|do not want|don't like)\s+(?:the\s+)?" + _COAST + r"\b", text):
        return False
    return bool(re.search(r"\b" + _COAST + r"\b", text))
