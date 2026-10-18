# agents/destination_agent.py

import json
import numpy as np
from collections import OrderedDict
from pathlib import Path
from utils.preferences import extract_requirements
from utils.hybrid_matching import eligible, rank_candidates, semantic_text
from logger import log

from sentence_transformers import SentenceTransformer, util

model = None

data_path = Path(__file__).resolve().parents[1] / "data" / "top_500_cities.json"
with data_path.open() as f:
    destinations = json.load(f)

# Only cities with the fields we need to score and locate them.
_usable = [
    d for d in destinations
    if d.get("features") and "lat" in d and "lng" in d
    and not d.get("duplicate_of") and d.get("catalogue_status") != "needs_review"
    and d.get("travel_profile", {}).get("quality", {}).get("status") == "usable"
]

# Encoded once on first use and reused for every later query. The city
# features never change, so re-encoding them per request just burns time.
_city_embeddings = OrderedDict()


def _embeddings(cities, needs):
    topics = tuple(sorted(set(needs['required'] + needs['preferred'] + needs['either'])))
    def key(d):
        return (d['city'], d['country'], topics)
    for city in cities:
        if key(city) in _city_embeddings:
            _city_embeddings.move_to_end(key(city))
    missing = [d for d in cities if key(d) not in _city_embeddings]
    if missing:
        vectors = model.encode(
            [semantic_text(d, needs) for d in missing],
            normalize_embeddings=True,
            batch_size=16,
        )
        _city_embeddings.update({key(d): vector for d, vector in zip(missing, vectors)})
        while len(_city_embeddings) > 4096:
            _city_embeddings.popitem(last=False)
    return np.stack([_city_embeddings[key(d)] for d in cities])


def rank(persona, top_n=3, coastal_only=False, query_text=""):
    """Filter supported requirements first, then rank eligible candidates."""
    global model
    if not persona and not query_text.strip():
        return []
    needs = extract_requirements(query_text)
    if coastal_only and "coast" not in needs["required"]:
        needs["required"].append("coast")
    candidates = [d for d in _usable if eligible(d, needs)]
    log("Matching requirements: " + (", ".join(needs["required"]) or "open discovery") +
        "; eligible catalogue entries: " + str(len(candidates)))
    if not candidates:
        return []
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    query = f"{query_text.strip()} Travel preferences: {', '.join(persona)}".strip()
    user_embedding = model.encode(query, normalize_embeddings=True)
    scores = util.cos_sim(user_embedding, _embeddings(candidates, needs))[0]
    ranked = rank_candidates(candidates, needs, scores)
    return ranked if top_n is None else ranked[:top_n]


def run(state, top_n=3):
    if "persona" not in state:
        return []
    ranked = rank(state["persona"], top_n=None, query_text=state.get("user_input", ""))
    diverse, countries = [], set()
    for city in ranked:
        if city["country"] in countries:
            continue
        countries.add(city["country"])
        diverse.append(city)
        if len(diverse) >= top_n:
            break
    return diverse
