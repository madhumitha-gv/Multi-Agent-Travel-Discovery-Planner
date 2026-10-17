import json
from pathlib import Path
import pytest
from utils.preferences import wants_coast

@pytest.mark.parametrize('text', ['oceans', 'I love the ocean', 'family beach trip', 'I want beaches', 'coastal walks', 'the sea', 'snorkeling and food'])
def test_explicit_coast_requirement(text):
    assert wants_coast(text)

@pytest.mark.parametrize('text', ['seafood and history', 'avoid beaches', 'no ocean', 'a mountain escape'])
def test_no_unintended_coast_constraint(text):
    assert not wants_coast(text)


def test_coastal_allowlist_excludes_delhi_and_only_contains_catalogue_cities():
    data=Path(__file__).resolve().parents[1]/'travel_planner'/'data'
    coast=json.loads((data/'coastal_destinations.json').read_text())
    cities={c['city'] for c in json.loads((data/'top_500_cities.json').read_text())}
    assert 'Delhi' not in coast
    assert set(coast) <= cities
