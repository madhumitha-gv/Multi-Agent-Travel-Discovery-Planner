# agents/destination_agent.py

import json
from pathlib import Path

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

# Encoded once on first use and reused for every later query. The city
# features never change, so re-encoding them per request just burns time.
_city_embeddings = None


def _embeddings():
    global _city_embeddings
    if _city_embeddings is None:
        _city_embeddings = model.encode(
            [d["features"] for d in _usable],
            normalize_embeddings=True,
            batch_size=64,
        )
    return _city_embeddings


def rank(persona, top_n=3):
    """Return the top_n cities whose features best match the persona."""
    if not persona:
        return []

    user_embedding = model.encode(", ".join(persona), normalize_embeddings=True)
    scores = util.cos_sim(user_embedding, _embeddings())[0]

    ranked = sorted(
        (
            {
                "name": d["city"],
                "score": float(score),
                "lat": d["lat"],
                "lng": d["lng"],
                "country": d.get("country", "Unknown"),
                "features": d["features"],
            }
            for d, score in zip(_usable, scores)
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
    return rank(state["persona"], top_n=top_n)
