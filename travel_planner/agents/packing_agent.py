# # agents/packing_agent.py
# from transformers import pipeline

# generator = pipeline("text-generation", model="gpt2")

# def generate_packing_list(destination, preferences):
#     pref_string = ", ".join(preferences)
#     prompt = f"Essential packing list for a {pref_string} vacation in {destination}:"
#     output = generator(prompt, max_length=80, num_return_sequences=1)[0]['generated_text']
#     return output
from dotenv import load_dotenv
import os
load_dotenv()
from huggingface_hub import InferenceClient

# Initialize client with Hugging Face Inference API
client = InferenceClient(
    model="mistralai/Mistral-7B-Instruct-v0.3",
    token= os.getenv("HUGGINGFACEHUB_API_TOKEN") # Replace with your token if needed
)

def generate_packing_list(destination, preferences):
    pref_string = ", ".join(preferences)

    prompt = f"""[INST] You are a helpful and smart travel assistant.
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

Do not include links, explanations, or repeated items. Avoid generic phrases like "you may need". Just clean and organized items.
[/INST]
"""

    try:
        output = client.text_generation(
            prompt,
            max_new_tokens=500,
            temperature=0.7,
            stop_sequences=["</s>"]
        )

        return output.strip()

    except Exception as e:
        return f"Error generating packing list: {e}"
