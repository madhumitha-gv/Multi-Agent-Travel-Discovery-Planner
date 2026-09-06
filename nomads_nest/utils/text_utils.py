from transformers import AutoTokenizer

def truncate_prompt(prompt: str, model_id: str, max_input_tokens: int = 1900):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokens = tokenizer(prompt, truncation=True, max_length=max_input_tokens)
    return tokenizer.decode(tokens["input_ids"], skip_special_tokens=True)
