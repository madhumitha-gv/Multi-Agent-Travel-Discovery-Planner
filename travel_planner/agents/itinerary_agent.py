# agents/itinerary_agent.py
from utils.mistral import MistralError, generate


def run(state, num_days=2):
    if "top_destination" not in state or not state["top_destination"]:
        return "No destination selected."

    destination = state["top_destination"]
    preferences = ", ".join(state.get("persona", []))

    prompt = f"""You are a travel expert. Create a {num_days}-day itinerary for a trip to {destination}.
Preferences: {preferences}

Format:
Day 1:
- Morning:
- Afternoon:
- Evening:
...

No links, just cultural and food recommendations."""

    try:
        return generate(prompt, max_tokens=500, temperature=0.7)
    except MistralError as e:
        return f"Error generating itinerary: {e}"
