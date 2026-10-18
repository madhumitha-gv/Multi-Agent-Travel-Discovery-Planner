"""Run real local models against fixed acceptance cases; no generation API."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "travel_planner"))

CASES = [
    ("I love oceans", {"Delhi"}),
    ("I love mountains", {"Atlanta", "Orlando", "Boankra"}),
    ("calm places", {"Orlando", "Boankra", "Buenos Aires"}),
    ("quiet mountain scenery", {"Atlanta", "Orlando", "Boankra"}),
    ("quiet beaches", {"Orlando", "Boankra", "Buenos Aires"}),
    ("mountains and beaches", {"Atlanta", "Orlando", "Delhi"}),
    ("I don't want mountains but I want beaches", {"Atlanta", "Santiago", "Cape Town"}),
    ("calm places, no cities", set()),
    ("I love local food and historic architecture", {"Boankra"}),
    ("mountains or beaches", {"Boankra"}),
    ("I want beaches but no beaches", set()),
    ("a mountain trip without hiking", {"Atlanta"}),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from agents import destination_agent as destination, persona_agent
    from utils.preferences import extract_requirements
    from utils.hybrid_matching import eligible
    lookup = {(c["city"], c["country"]): c for c in destination.destinations}
    results = []
    for prompt, forbidden in CASES:
        persona = persona_agent.analyze_preferences(prompt)
        matches = destination.run({"user_input": prompt, "persona": persona})
        names = [c["name"] for c in matches]
        assert not (set(names) & forbidden), (prompt, names)
        needs = extract_requirements(prompt)
        for match in matches:
            assert eligible(lookup[(match["name"], match["country"])], needs)
        if prompt in {"calm places, no cities", "I want beaches but no beaches"}:
            assert not matches, (prompt, names)
        else:
            assert matches, prompt
        if prompt == "quiet beaches":
            assert len(matches) == 1  # Do not invent two filler recommendations.
        row = {"prompt": prompt, "persona": persona, "requirements": needs,
               "destinations": [{k: c[k] for k in ("name", "country", "match_area", "match_reasons", "score_components")} for c in matches]}
        results.append(row)
        print(prompt, "→", names, flush=True)
    args.output.write_text(json.dumps({"cases": results, "passed": len(results)}, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
