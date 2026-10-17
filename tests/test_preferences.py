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


def test_merged_catalogue_preserves_cities_and_coastal_features():
    data=Path(__file__).resolve().parents[1]/'travel_planner'/'data'
    cities=json.loads((data/'top_500_cities.json').read_text())
    assert len(cities)==500
    assert len({(c['city'],c['country']) for c in cities})==500
    coast={c['city']:c for c in cities if c.get('coastal') is True}
    assert len(coast)==61
    assert 'Delhi' not in coast
    assert 'Kumasi' not in coast  # Mentioning Ivory Coast does not imply coastline.
    assert 'Pittsburgh' not in coast
    assert 'Valencia' in coast
    assert 'Pacific Ocean' in coast['Sydney']['features']
    assert 'Urban Energy, Local Hospitality, Photogenic Charm' in coast['Sydney']['features']
    assert all('lat' in c and 'lng' in c and c['features'] for c in cities)
    assert not (data/'coastal_destinations.json').exists()
