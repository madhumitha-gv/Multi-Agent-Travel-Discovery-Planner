# agents/packing_agent.py
from utils.mistral import MistralError, generate


def generate_packing_list(destination, preferences):
    pref_string = ", ".join(preferences)

    prompt = f"""You are a helpful and smart travel assistant.
Generate a clean, duplicate-free, categorized packing list for a trip to {destination}.
The traveler enjoys: {pref_string}.

The list should include only essential and highly relevant items, grouped under the following categories:
Clothing, Gear, Documents & Essentials, Tech & Accessories, Health & Safety.

Respond in this format:
Clothing:
- Item 1
- Item 2

Gear:
- Item 1
...

Do not include links, explanations, or repeated items. Avoid generic phrases like "you may need". Just clean and organized items."""

    try:
        return generate(prompt, max_tokens=500, temperature=0.7)
    except MistralError as e:
        return f"Error generating packing list: {e}"
