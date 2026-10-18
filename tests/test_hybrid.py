import pytest
from utils.preferences import extract_requirements
from utils.hybrid_matching import eligible, rank_candidates


def city(name, **facts):
    return {"city": name, "country": name, "lat": 0, "lng": 0, "features": "legacy",
        "travel_profile": {"setting": {"value": "urban"}, "quality": {"status": "usable"}, "facts": facts}}


def fact(**extra):
    return {"status": "supported", "source": "https://example.org/evidence", "summary": "Evidence", **extra}


@pytest.mark.parametrize("text,required,excluded", [
    ("I love mountains", {"mountains"}, set()),
    ("I love oceans", {"coast"}, set()),
    ("calm places", {"quiet"}, set()),
    ("mountains and beaches", {"mountains", "coast", "beach"}, set()),
    ("I don't want mountains but I want beaches", {"coast", "beach"}, {"mountains"}),
    ("quiet places without beaches", {"quiet"}, {"coast", "beach"}),
    ("avoid crowds", {"quiet"}, set()),
    ("a relaxing city break with food", set(), set()),
])
def test_explicit_requirements(text, required, excluded):
    parsed = extract_requirements(text)
    assert set(parsed["required"]) == required
    assert set(parsed["excluded"]) == excluded


def test_either_is_not_interpreted_as_both():
    needs = extract_requirements("mountains or beaches")
    assert eligible(city("Mountains", mountains=fact()), needs)
    assert eligible(city("Coast", coast=fact()), needs)
    assert not eligible(city("Neither"), needs)


def test_semantic_score_cannot_override_required_evidence():
    needs = extract_requirements("calm places")
    rows = [city("Orlando"), city("Boankra"), city("Buenos Aires"),
            city("Supported area", quiet=fact(area="Specific retreat", compatible=[]))]
    matches = rank_candidates(rows, needs, [1, 1, 1, -.2])
    assert [c["name"] for c in matches] == ["Supported area"]
    assert matches[0]["match_area"] == "Specific retreat"
    assert matches[0]["match_limits"]


def test_mountain_mentions_are_not_mountain_experience_evidence():
    needs = extract_requirements("I love mountains")
    assert not eligible(city("Atlanta", mountains={"status": "context_only", "source": "https://example.org"}), needs)
    assert eligible(city("Guilin", mountains=fact(access="in_area")), needs)


def test_features_must_apply_to_same_quiet_area():
    needs = extract_requirements("quiet beaches")
    assert not eligible(city("Separate park", quiet=fact(compatible=["hiking"]), coast=fact(), beach=fact()), needs)
    assert eligible(city("Quiet coast", quiet=fact(compatible=["coast", "beach"]), coast=fact(), beach=fact()), needs)


def test_conflicts_return_no_match():
    assert not eligible(city("Beach", coast=fact(), beach=fact()), extract_requirements("beaches but no beaches"))


def test_nonurban_requirement_does_not_pass_a_quiet_city_park():
    assert not eligible(city("City with park", quiet=fact()), extract_requirements("calm places, no cities"))


def test_missing_and_unattributed_facts_do_not_count_as_supported():
    needs = extract_requirements("I love mountains")
    assert not eligible(city("Unknown", mountains={"status": "unknown"}), needs)
    assert not eligible(city("No source", mountains={"status": "supported"}), needs)
