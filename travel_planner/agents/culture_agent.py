# agents/culture_agent.py
from utils.mistral import MistralError, generate


def cultural_tips(destination):
    prompt = (
        f"You're a travel writer. Write a paragraph about the culture, architecture, "
        f"dress code, and etiquette of {destination}. "
        f"Make it friendly, informative, and suitable for tourists."
    )

    try:
        return generate(prompt, max_tokens=400, temperature=0.8)
    except MistralError as e:
        return f"Error generating cultural tips: {e}"
