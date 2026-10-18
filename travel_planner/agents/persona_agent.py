# agents/persona_agent.py
from transformers import pipeline
from utils.preferences import wants_coast

classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"
)

# DeBERTa supports 512 tokens; the pipeline truncates the input side.
classifier.tokenizer.model_max_length = 512


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
    preferences = [label for label, score in sorted_preferences[:3]]
    if wants_coast(user_text):
        preferences = ["beach"] + [p for p in preferences if p != "beach"]
    return preferences[:3]