# agents/persona_agent.py
from transformers import pipeline

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
)

def run(state, user_input):
    preferences = analyze_preferences(user_input)
    state["persona"] = preferences
    return preferences

def analyze_preferences(user_text):
    labels = ["beach", "adventure", "relaxation", "history", "culture",
              "food", "budget", "luxury", "nature", "nightlife",
              "shopping", "family-friendly"]

    results = classifier(user_text, labels, multi_label=True)
    sorted_preferences = sorted(
        zip(results["labels"], results["scores"]),
        key=lambda x: x[1],
        reverse=True
    )
    return [label for label, score in sorted_preferences[:3]]