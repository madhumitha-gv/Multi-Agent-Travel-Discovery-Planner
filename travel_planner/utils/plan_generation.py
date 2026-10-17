"""Generate writing sections and preserve partial successes."""
from concurrent.futures import ThreadPoolExecutor
import logging
from agents import itinerary_agent, culture_agent, packing_agent
from logger import log

KEYS = ("itinerary", "culture_tips", "packing_list")


def generate_sections(state, only=None):
    city = state.get("top_destination")
    wanted = [key for key in KEYS if only is None or key in only]
    if not city or city == "Unknown":
        return {**{key: "" for key in wanted}, "generation_errors": []}
    jobs = {
        "itinerary": lambda: itinerary_agent.run(state, num_days=2),
        "culture_tips": lambda: culture_agent.cultural_tips(city),
        "packing_list": lambda: packing_agent.generate_packing_list(city, state.get("persona", [])),
    }
    jobs = {key: job for key, job in jobs.items() if key in wanted}
    log("Writing your itinerary, cultural guide and packing list...")
    outputs, errors = {}, []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {key: pool.submit(job) for key, job in jobs.items()}
        for key, future in futures.items():
            try:
                text = future.result()
            except Exception:
                logging.getLogger(__name__).exception("Writing agent %s failed", key)
                text = ""
            if not text or text.startswith("Error generating"):
                errors.append(key)
                text = ""
            outputs[key] = text
    outputs.update(generation_errors=errors, generation_message="")
    return outputs
