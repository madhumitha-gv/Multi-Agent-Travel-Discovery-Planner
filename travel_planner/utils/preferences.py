"""Extract explicit requirements before semantic ranking; no generation calls."""
import re

TERMS = {
    "coast": r"oceans?|beach(?:es)?|seaside|coast(?:al|line)?|sea|surfing|snorkel(?:ing|ling)?",
    "beach": r"beach(?:es)?|surfing|snorkel(?:ing|ling)?",
    "mountains": r"mountains?|mountainous|alpine",
    "quiet": r"calm|quiet|peaceful|tranquil(?:ity)?|serene|uncrowded|secluded",
    "hiking": r"hik(?:e|es|ing)|trekk?ing",
    "skiing": r"ski(?:ing)?|snowboard(?:ing)?",
}
SOFT = {"food": r"food|cuisine|culinary", "history": r"history|historic(?:al)?|heritage",
        "culture": r"culture|cultural|museums?|architecture", "relaxation": r"relax\w*|restful"}
NEGATIVE = r"\b(?:no|not|without|avoid(?:ing)?|don't|do not|rather than|never)\s+(?:\w+\s+){0,4}$"


def _mentions(text, terms):
    positive, negative = False, False
    for clause in re.split(r"[.;!?]|\b(?:but|however|instead)\b", text):
        for match in re.finditer(r"\b(?:" + terms + r")\b", clause):
            before = clause[max(0, match.start()-80):match.start()]
            if re.search(NEGATIVE, before):
                negative = True
            else:
                positive = True
    return positive, negative


def extract_requirements(text):
    text = text.lower().replace("’", "'")
    required, excluded = set(), set()
    for key, terms in TERMS.items():
        yes, no = _mentions(text, terms)
        if yes:
            required.add(key)
        if no:
            excluded.add(key)
    if re.search(r"\b(?:avoid|without|no|away from)\s+(?:the\s+)?(?:crowds|crowded places|noise|hustle|city crowds)\b", text):
        required.add("quiet")
    preferred = [key for key, terms in SOFT.items() if _mentions(text, terms)[0]]
    setting = "nonurban" if re.search(r"\b(?:no|without|avoid(?:ing)?|not)\s+(?:a\s+|any\s+|big\s+|busy\s+)?(?:cities|city|urban stays)\b", text) else None
    either = []
    if {"mountains", "coast"} <= required and re.search(r"\b(?:mountains?\s+or\s+(?:beaches?|oceans?)|(?:beaches?|oceans?)\s+or\s+mountains?)\b", text):
        either = ["mountains", "coast"]
        required -= {"mountains", "coast", "beach"}
    conflicts = sorted(required & excluded)
    if "beach" in required and "coast" in excluded:
        conflicts.append("beach/coast")
    return {"required": sorted(required), "excluded": sorted(excluded),
            "preferred": preferred, "setting": setting, "either": either,
            "conflicts": conflicts}


def wants_coast(text):
    needs = extract_requirements(text)
    return "coast" in needs["required"] or "coast" in needs["either"]
