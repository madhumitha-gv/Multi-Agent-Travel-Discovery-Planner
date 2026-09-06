# utils/mistral.py
"""Single entry point for Mistral text generation.

Every generative agent goes through here so the model, endpoint and
error handling are defined in exactly one place.

Mistral-7B-Instruct is served through the Hugging Face router rather
than a local pipeline. Note that the plain `hf-inference` provider no
longer serves it, so the request is routed to a provider that does.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
PROVIDER = "featherless-ai"
ENDPOINT = f"https://router.huggingface.co/{PROVIDER}/v1/chat/completions"

TIMEOUT = 120


class MistralError(RuntimeError):
    """Raised when the model could not be reached or returned no text."""


def generate(prompt, max_tokens=500, temperature=0.7):
    """Send a single-turn prompt to Mistral and return the reply text."""
    token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not token:
        raise MistralError(
            "HUGGINGFACEHUB_API_TOKEN is not set. Copy .env.example to .env "
            "and add your Hugging Face token."
        )

    try:
        response = requests.post(
            ENDPOINT,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=TIMEOUT,
        )
    except requests.RequestException as e:
        raise MistralError(f"Could not reach {PROVIDER}: {e}") from e

    if not response.ok:
        raise MistralError(f"{response.status_code} from {PROVIDER}: {response.text[:200]}")

    try:
        return response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError) as e:
        raise MistralError(f"Unexpected response shape: {response.text[:200]}") from e
