"""Build structured evidence in the existing catalogue; no runtime web calls.

Source-supported common fields are filled in. Missing experience evidence is
explicitly distinguished from absence. Reviewed experience facts describe a
specific area or excursion, never an entire city's permanent crowd level.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
CHECKED = "2026-10-18"


def fact(summary, source, **details):
    return {"status": "supported", "summary": summary, "source": source,
            "checked_at": CHECKED, **details}


MOUNTAINS = {
    "Guilin": fact("Karst peaks and hills across the Guilin region provide mountain scenery.", "https://visitguilin.org/things-to-do/mountains", access="in_area", area="Guilin karst landscape"),
    "Santiago": fact("Santiago is a city base for Andes and Cajón del Maipo excursions; it is not a quiet mountain village.", "https://visitsantiago.travel/en/montana-y-naturaleza/", access="excursion", area="Cajón del Maipo"),
    "Quito": fact("Quito offers access to the Andean slopes of Rucu Pichincha; the city remains an urban base.", "https://visitquito.ec/es/rucu-pichincha-la-montana-guardiana-de-quito/", access="in_area", area="Rucu Pichincha"),
    "Denver": fact("Denver is a city base for Rocky Mountain excursions rather than a mountain retreat itself.", "https://visitdenver.com/head-to-the-mountains/", access="excursion", area="Rocky Mountain foothills"),
    "Vancouver": fact("Vancouver is an urban base for the North Shore mountains, outside the city center.", "https://www.destinationvancouver.com/vancouver/greater-vancouver-area", access="excursion", area="North Shore mountains"),
    "Sapporo": fact("Jozankei is a nature and hot-spring valley in the mountains of the Sapporo area.", "https://www.sapporo.travel/en/spot/facility/jozankei_onsen/", access="excursion", area="Jozankei"),
    "Cape Town": fact("Table Mountain forms a mountain landscape within the Cape Town area.", "https://www.sanbi.org/gardens/kirstenbosch/", access="in_area", area="Table Mountain"),
}
QUIET = {
    "Guilin": fact("For quieter surroundings, focus on accommodation in the Yangshuo countryside, away from West Street nightlife.", "https://visitguilin.org/where-to-stay/yangshuo/", area="Yangshuo countryside", scope="specific_area", compatible=["mountains", "hiking"], crowd_level="unknown"),
    "Santiago": fact("Las Melosas in Cajón del Maipo offers a slower-paced mountain excursion outside central Santiago.", "https://visitsantiago.travel/en/montana-y-naturaleza/", area="Las Melosas, Cajón del Maipo", scope="specific_area", compatible=["mountains"], crowd_level="unknown"),
    "Sapporo": fact("Focus on Jozankei's nature walks and hot springs rather than central Sapporo; this popular resort can still be busy.", "https://www.sapporo.travel/en/spot/facility/jozankei_onsen/", area="Jozankei", scope="specific_area", compatible=["mountains"], crowd_level="unknown"),
    "Sydney": fact("Heathcote National Park is a quieter bushland excursion alternative to crowded Royal National Park near Sydney.", "https://www.nationalparks.nsw.gov.au/get-inspired/stories/skip-royal-head-to-stunning-heathcote-national-park", area="Heathcote National Park", scope="specific_area", compatible=["hiking"], crowd_level="unknown"),
    "Stockholm": fact("For a calmer seaside setting, focus on Ingarö Havscamping in the archipelago rather than central Stockholm.", "https://www.visitstockholm.com/guides/campsites-in-stockholm-and-the-archipelago/", area="Ingarö Havscamping, Stockholm archipelago", scope="specific_area", compatible=["coast", "beach"], crowd_level="unknown"),
}


def topic_context(context, topic, fallback):
    patterns = {"food": r"cuisine|food|gastronom|culture|tourism",
                "history": r"history|historical", "culture": r"culture|architecture|arts|museums|heritage"}
    # Also accept headings from earlier plain-text cache versions.
    blocks = re.split(r"(?m)^(?:## )?([A-Z][A-Za-z0-9 ,/&()–—'-]{1,69})\n", context)
    selected = []
    for heading, body in zip(blocks[1::2], blocks[2::2]):
        if re.search(patterns[topic], heading, re.I):
            selected.append(heading + " " + body)
    # If no dedicated section exists, examine only the introduction, not
    # unrelated business, reference or transport sections containing keywords.
    return "\n".join(selected) or (blocks[0] if context else fallback)


def build_profile(city, context=""):
    description = city.get("description", "")
    source = city.get("description_source", "")
    kind = city.get("place_type_description", "")
    text = (kind + " " + description).lower()
    issues = []
    if city.get("duplicate_of"):
        issues.append("duplicate_alias")
    if city.get("catalogue_status") == "needs_review":
        issues.append("unverified_identity")
    if city["city"] == "Boankra":
        issues.append("sparse_travel_evidence")
    if len((context or description).split()) < 25:
        issues.append("sparse_description")
    if not source or not city.get("description_coordinates"):
        issues.append("missing_source_location")
    if re.search(r"\bvillage\b", kind.lower()) or re.search(r"\bis a village\b", description.lower()):
        place_type, setting = "village", "rural"
    elif re.search(r"\bis a town\b", description.lower()):
        place_type, setting = "town", "small_town"
    elif re.search(r"\bdistrict\b", kind.lower()) and "city" not in kind.lower():
        place_type, setting = "district", "mixed"
    elif "borough" in kind.lower():
        place_type, setting = "borough", "urban"
    elif re.search(r"\bcity\b|\bcapital\b", text):
        place_type, setting = "city", "urban"
    else:
        place_type, setting = "settlement", "unknown"
    facts = {key: {"status": "unknown", "reason": "No reviewed evidence for this attribute yet."}
             for key in ("coast", "beach", "mountains", "quiet", "hiking", "skiing", "food", "history", "culture", "relaxation")}
    geography = context or description
    facts["geography"] = fact(f"{city['city']} is recorded as a {place_type} in {city['country']}.", source,
        scope="city_context", country=city['country'], coordinates={"lat": city['lat'], "lng": city['lng']}, place_type=place_type)
    if city.get("coastal") is True:
        facts["coast"] = fact("Coastal access is documented; this does not by itself establish a beach or swimming destination.", city.get("coastal_source", source), scope="city_or_coastal_area")
        if re.search(r"\bbeach(?:es)?\b", description + " " + city.get("features", ""), re.I):
            facts["beach"] = fact("Beach access is recorded for the city or nearby coastal area; swimming suitability is not verified.", source, scope="city_or_coastal_area")
    if city["city"] in MOUNTAINS:
        facts["mountains"] = MOUNTAINS[city["city"]].copy()
    elif re.search(r"\b(?:foothills|mountains|mountain range)\b", geography, re.I):
        facts["mountains"] = {"status": "context_only", "summary": "The geographic introduction mentions mountains or foothills, but a mountain-trip experience has not been reviewed.", "source": source, "checked_at": CHECKED}
    if city["city"] in QUIET:
        facts["quiet"] = QUIET[city["city"]].copy()
        facts["relaxation"] = QUIET[city["city"]].copy()
    # These activity statements are explicitly described by the linked sources.
    hiking = {
        "Guilin": "https://visitguilin.org/things-to-do/yangshuo-attractions/yulong-river/",
        "Santiago": "https://visitsantiago.travel/en/montana-y-naturaleza/",
        "Quito": "https://visitquito.ec/es/rucu-pichincha-la-montana-guardiana-de-quito/",
        "Denver": "https://visitdenver.com/things-to-do/day-trips-around-colorado/",
        "Vancouver": "https://www.destinationvancouver.com/inspirations/hiking",
        "Sydney": "https://www.nationalparks.nsw.gov.au/get-inspired/stories/skip-royal-head-to-stunning-heathcote-national-park",
        "Sapporo": "https://www.sapporo.travel/en/spot/feature/mountain_climbing_in_sapporo/",
    }
    if city["city"] in hiking:
        facts["hiking"] = fact("The source describes walking or hiking excursions in this destination's surrounding area.", hiking[city["city"]], scope="area_or_excursion")
    if city["city"] in {"Santiago", "Denver"}:
        facts["skiing"] = fact("Nearby ski areas are documented; opening dates and snow conditions must be checked.", facts["mountains"]["source"], scope="excursion")
    if city["city"] == "Sapporo":
        facts["skiing"] = fact("Sapporo Moiwayama offers skiing near the city; operation and snow conditions depend on season.", "https://visit.sapporo.travel/discover/snow/sapporo-moiwayama-ski-resort/", scope="area_or_excursion")
    for key, pattern, summary in [
        ("food", r"\bcuisine|\bculinary|\bstreet food|\bgastronom|\brestaurants?\b", "The source specifically describes local cuisine, restaurants or food culture."),
        ("history", r"\bfounded|\bancient|\bhistor(?:y|ic)|\bmedieval", "The source documents historical context; individual attractions still need verification."),
        ("culture", r"\bmuseums?|\bcultur(?:e|al)|\barchitecture|\bheritage|\barts\b", "The source documents cultural or architectural context."),
    ]:
        relevant = topic_context(context, key, description)
        match = re.search(pattern, relevant, re.I)
        if match:
            # Retain a short source excerpt for reproducible evidence, not a
            # generated opinion or a generic country-level feature label.
            excerpt = " ".join(relevant[:match.start()].split()[-10:] + relevant[match.start():].split()[:14])
            facts[key] = fact(summary, source, scope="city_context", evidence_excerpt=excerpt,
                              method="source_text_rule")
    # Stockholm's reviewed archipelago source supports coastal and beach access.
    if city["city"] == "Stockholm":
        for key in ("coast", "beach"):
            facts[key] = fact("Archipelago seaside camping and beach excursions are documented outside central Stockholm.", QUIET["Stockholm"]["source"], scope="excursion")
    return {"version": 1, "place_type": {"value": place_type, "status": "supported", "source": source},
            "setting": {"value": setting, "status": "supported" if setting != "unknown" else "unknown", "source": source},
            "quality": {"status": "excluded" if issues else "usable", "issues": issues},
            "facts": facts, "checked_at": CHECKED}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "docs/catalogue-audit.md")
    parser.add_argument("--source-cache", type=Path)
    args = parser.parse_args()
    path = ROOT / "travel_planner/data/top_500_cities.json"
    cities = json.loads(path.read_text())
    cache = json.loads(args.source_cache.read_text()) if args.source_cache and args.source_cache.exists() else {}
    for city in cities:
        title = unquote(city["description_source"].split("/wiki/")[1]).replace("_", " ")
        city["travel_profile"] = build_profile(city, cache.get(title, ""))
    path.write_text(json.dumps(cities, ensure_ascii=True, indent=2, separators=(",", ":")) + "\n")
    usable = [c for c in cities if c["travel_profile"]["quality"]["status"] == "usable"]
    coverage = Counter(key for c in usable for key, f in c["travel_profile"]["facts"].items() if f["status"] == "supported")
    lines = ["# Destination catalogue audit", "", f"Checked: {CHECKED}", "",
        f"Original records retained: {len(cities)}. Usable unique records: {len(usable)}.", "",
        "## Supported attribute coverage", "", "| Attribute | Usable records |", "| --- | ---: |"]
    lines += [f"| {key} | {coverage[key]} |" for key in cities[0]["travel_profile"]["facts"]]
    lines += ["", "## Excluded entries", ""]
    lines += [f"- {c['city']}, {c['country']}: {', '.join(c['travel_profile']['quality']['issues'])}." for c in cities if c not in usable]
    lines += ["", "## Interpretation", "",
        "Names, countries, coordinates and legacy features are preserved. Legacy features repeat generic labels and are not used for matching. Structured fields come from linked geographic introductions and reviewed tourism or park sources. Mountain mentions alone do not establish a mountain-trip experience. Quiet-area evidence describes a specific area or excursion; no city-wide calm or live crowd score is invented. Missing evidence is not evidence of absence. Descriptions are not a complete attraction inventory. No generation API is used during matching.", "",
        "The 500-record catalogue includes districts, towns and a village. Most records describe urban destinations. Requests requiring nonurban stays may have no supported match; the app must not fill the list with weak alternatives.", ""]
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines))
    print(json.dumps({"records": len(cities), "usable": len(usable), "coverage": coverage}, indent=2))


if __name__ == "__main__":
    main()
