import json
import importlib.util
from pathlib import Path
from utils.hybrid_matching import eligible
from utils.preferences import extract_requirements

DATA = Path(__file__).resolve().parents[1] / 'travel_planner/data/top_500_cities.json'


def catalogue():
    return json.loads(DATA.read_text())


def test_profiles_have_source_support_for_populated_facts():
    cities = catalogue()
    assert len(cities) == 500
    for city in cities:
        profile = city['travel_profile']
        assert profile['version'] == 1
        assert profile['place_type']['source']
        for fact in profile['facts'].values():
            assert fact['status'] in {'supported', 'unknown', 'context_only'}
            if fact['status'] != 'unknown':
                assert fact['source'].startswith('https://')
                assert fact['summary']
            if fact['status'] == 'unknown':
                assert 'source' not in fact


def test_actual_catalogue_rejects_reported_bad_matches():
    cities = {c['city']: c for c in catalogue()}
    calm = extract_requirements('calm places')
    for name in ['Orlando', 'Boankra', 'Buenos Aires']:
        assert not eligible(cities[name], calm)
    mountains = extract_requirements('I love mountains')
    assert not eligible(cities['Atlanta'], mountains)
    assert eligible(cities['Guilin'], mountains)
    assert eligible(cities['Santiago'], mountains)
    assert cities['Santiago']['travel_profile']['facts']['mountains']['access'] == 'excursion'
    assert cities['Boankra']['travel_profile']['quality']['status'] == 'excluded'


def test_calm_profiles_are_specific_and_never_guarantee_city_crowds():
    for city in catalogue():
        quiet = city['travel_profile']['facts']['quiet']
        if quiet['status'] == 'supported':
            assert quiet['scope'] == 'specific_area'
            assert quiet['area']
            assert quiet['crowd_level'] == 'unknown'


def test_legacy_labels_cannot_create_structured_support():
    for city in catalogue():
        if 'relaxation' in city.get('features','').lower():
            # Calm support, when present, must have its own source and area.
            quiet = city['travel_profile']['facts']['quiet']
            if quiet['status'] == 'supported':
                assert quiet['area'] and quiet['source']


def test_context_enrichment_does_not_confuse_business_with_cuisine():
    path=DATA.parents[2]/'scripts/build_destination_profiles.py'
    spec=importlib.util.spec_from_file_location('profile_builder',path)
    builder=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    base=next(c for c in catalogue() if c['city']=='Atlanta')
    context='A city in a documented location.\n## Economy\nA restaurant corporation has its headquarters here.\n'
    assert builder.build_profile(base,context)['facts']['food']['status']=='unknown'
    context+='## Cuisine\nLocal cuisine includes several regional dishes.\n'
    enriched=builder.build_profile(base,context)
    assert enriched['facts']['food']['status']=='supported'
    assert 'Cuisine' in enriched['facts']['food']['evidence_excerpt']
