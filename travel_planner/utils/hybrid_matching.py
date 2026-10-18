"""Evidence filters and explainable ranking, independent of embedding models."""


def supported(fact):
    return fact.get("status") == "supported" and bool(fact.get("source"))


def eligible(city, needs):
    profile = city.get("travel_profile", {})
    if profile.get("quality", {}).get("status") != "usable" or needs["conflicts"]:
        return False
    facts = profile.get("facts", {})
    required = set(needs["required"])
    if any(not supported(facts.get(key, {})) for key in required):
        return False
    if needs["either"] and not any(supported(facts.get(key, {})) for key in needs["either"]):
        return False
    # Declining an activity need not ban every city that offers it.
    if any(supported(facts.get(key, {})) for key in set(needs["excluded"]) & {"coast", "beach", "mountains"}):
        return False
    if needs["setting"] == "nonurban" and profile.get("setting", {}).get("value") not in {"rural", "small_town"}:
        return False
    if "quiet" in required:
        quiet = facts["quiet"]
        # A beach and a separate quiet inland park do not prove a quiet beach.
        for key in required & {"coast", "beach", "mountains", "hiking"}:
            if key not in quiet.get("compatible", []):
                return False
    return True


def semantic_text(city, needs=None):
    needs = needs or {"required": [], "preferred": [], "either": []}
    profile = city.get("travel_profile", {}).get("facts", {})
    keys = list(dict.fromkeys(needs["required"] + needs["preferred"] + needs["either"]))
    facts = [f"{key}: {profile[key].get('summary', '')} {profile[key].get('evidence_excerpt', '')}"
             for key in keys if supported(profile.get(key, {}))]
    # Unverified generic legacy labels are retained in the data, not scored.
    evidence = " ".join(". ".join(facts).split()[:110])
    description = " ".join(city.get("description", "").split()[:100])
    return f"{city['city']}, {city['country']}. {evidence}. {description}"


def rank_candidates(cities, needs, similarities):
    results = []
    for city, similarity in zip(cities, similarities):
        if not eligible(city, needs):
            continue
        facts = city["travel_profile"]["facts"]
        dimensions = needs["required"] + needs["preferred"]
        fit = sum(supported(facts.get(key, {})) for key in dimensions) / len(dimensions) if dimensions else .5
        quality = (sum((.7 if facts[key].get("method") == "source_text_rule" else 1)
                   for key in dimensions if supported(facts.get(key, {}))) / len(dimensions)) if dimensions else .7
        semantic = max(0, min(1, (float(similarity) + 1) / 2))
        score = .55 * semantic + .35 * fit + .10 * quality
        reasons, sources = [], []
        for key in needs["required"] + needs["preferred"] + needs["either"]:
            fact = facts.get(key, {})
            if supported(fact) and fact.get("summary") not in reasons:
                reasons.append(fact["summary"])
                sources.append({"label": key.capitalize(), "url": fact["source"]})
        focus = "quiet" if "quiet" in needs["required"] else "mountains"
        scope = facts.get(focus, {}).get("area", "") if focus in needs["required"] else ""
        limits = []
        if "quiet" in needs["required"]:
            limits.append("This is a specific-area recommendation, not a claim that the whole city is quiet. Crowd levels vary by date and time.")
        if needs["excluded"]:
            limits.append("Exclusions remove documented geographic matches; missing facts do not prove a feature is absent.")
        results.append({"name": city["city"], "country": city["country"],
            "lat": city["lat"], "lng": city["lng"], "score": score,
            "features": city["features"], "description": city.get("description", ""),
            "description_source": city.get("description_source", ""),
            "match_reasons": reasons, "match_sources": sources,
            "match_area": scope, "match_limits": limits,
            "score_components": {"semantic": round(semantic, 4), "preference_fit": round(fit, 4), "evidence": round(quality, 4)}})
    return sorted(results, key=lambda item: item["score"], reverse=True)
