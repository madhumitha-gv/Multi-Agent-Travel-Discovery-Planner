# agents/itinerary_agent.py
from utils.mistral import MistralError, generate


def run(state, num_days=2):
    if "top_destination" not in state or not state["top_destination"]:
        return "No destination selected."

    destination = state["top_destination"]
    preferences = ", ".join(state.get("persona", []))
    matched = state.get("final_destination", {})
    evidence = "; ".join(matched.get("match_reasons", []))

    prompt = f"""You are a travel expert. Create a {num_days}-day itinerary for a trip to {destination}.
Preferences: {preferences}
Original request: {state.get('user_input', '')}
Supported match context: {evidence}
Focus area: {matched.get('match_area', '')}
Honor the original request and exclusions. Where a focus area is given, center
the trip on that area and explain travel from the city base. Do not replace a
quiet-area trip with busy city-center sightseeing. Do not claim crowds or
weather are guaranteed. Do not invent transport durations or availability.

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
