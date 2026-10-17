"""Check catalogue identity, source attribution and namesake protection."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("enrich_catalogue", ROOT / "scripts/enrich_catalogue.py")
enrichment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enrichment)


def test_all_city_descriptions_have_attribution_and_matching_coordinates():
    cities = json.loads((ROOT / "travel_planner/data/top_500_cities.json").read_text())
    assert len(cities) == 500
    active = [c for c in cities if not c.get("duplicate_of") and c.get("catalogue_status") != "needs_review"]
    assert len(active) == 497
    assert len({c["description_source"] for c in active}) == len(active)
    for city in cities:
        assert 5 <= len(city["description"].split()) <= 180, city["city"]
        assert city["description_title"]
        assert city["description_source"].startswith("https://en.wikipedia.org/wiki/")
        assert city["description_license"] == "CC BY-SA 4.0"
        coord = city["description_coordinates"]
        assert enrichment.distance_km((city["lat"], city["lng"]), (coord["lat"], coord["lng"])) <= 35, city["city"]


def test_namesake_distance_check():
    # Baicheng in Guangxi must not get the description of Baicheng in Jilin.
    assert enrichment.distance_km((23.903, 106.619), (45.6196, 122.838)) > 2000
