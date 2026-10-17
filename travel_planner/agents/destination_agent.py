# agents/destination_agent.py

import json
from pathlib import Path
from utils.preferences import wants_coast

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

data_path = Path(__file__).resolve().parents[1] / "data" / "top_500_cities.json"
with data_path.open() as f:
    destinations = json.load(f)

# Only cities with the fields we need to score and locate them.
_usable = [
    d for d in destinations
    if d.get("features") and "lat" in d and "lng" in d
]

with (data_path.parent / "coastal_destinations.json").open() as f:
    _coastal = json.load(f)

# Encoded once on first use and reused for every later query. The city
# features never change, so re-encoding them per request just burns time.
_city_embeddings = None


def _embeddings():
    global _city_embeddings
    if _city_embeddings is None:
        _city_embeddings = model.encode(
            [f"{d['city']}, {d.get('country', '')}. {d['features']}. {_coastal.get(d['city'], '')}" for d in _usable],
            normalize_embeddings=True,
            batch_size=64,
        )
    return _city_embeddings


def rank(persona, top_n=3, coastal_only=False, query_text=""):
    """Return the top_n cities whose features best match the persona."""
    if not persona:
        return []

    query = f"{query_text.strip()} Travel preferences: {', '.join(persona)}".strip()
    user_embedding = model.encode(query, normalize_embeddings=True)
    scores = util.cos_sim(user_embedding, _embeddings())[0]

    ranked = sorted(
        (
            {
                "name": d["city"],
                "score": float(score),
                "lat": d["lat"],
                "lng": d["lng"],
                "country": d.get("country", "Unknown"),
                "features": _coastal.get(d["city"], d["features"]),
            }
            for d, score in zip(_usable, scores)
            if not coastal_only or d["city"] in _coastal
        ),
        key=lambda x: x["score"],
        reverse=True,
    )

    if not ranked:
        print("⚠️ No destination matches found.")
    return ranked if top_n is None else ranked[:top_n]


def run(state, top_n=3):
    if "persona" not in state:
        return []
    coastal_only = wants_coast(state.get("user_input", ""))
    ranked = rank(state["persona"], top_n=None, coastal_only=coastal_only, query_text=state.get("user_input", ""))
    diverse, countries = [], set()
    for city in ranked:
        if city["country"] in countries:
            continue
        countries.add(city["country"])
        diverse.append(city)
        if len(diverse) >= top_n:
            break
    return diverse
