# agents/culture_agent.py
# from transformers import pipeline

# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# def cultural_tips(destination):
#     text = f"Travelers visiting {destination} should be aware of cultural norms including respect, attire, etiquette, and local customs."
#     summary = summarizer(text, max_length=1200, min_length=300)[0]['summary_text']
#     return summary


from transformers import pipeline

# Load GPT-Neo model (open access, no token)
generator = pipeline("text-generation", model="EleutherAI/gpt-neo-1.3B")

def cultural_tips(destination):
    prompt = (
        f"You're a travel writer. Write a paragraph about the culture, architecture, dress code, and etiquette of {destination}. "
        f"Make it friendly, informative, and suitable for tourists."
    )

    output = generator(
        prompt,
        max_length=512,
        temperature=0.8,
        top_p=0.95,
        repetition_penalty=1.1
    )[0]['generated_text']

    return output[len(prompt):].strip()