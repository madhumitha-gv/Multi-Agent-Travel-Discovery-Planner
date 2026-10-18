"""Fetch attributed article context for an explicit offline catalogue refresh."""
import argparse
import json
import time
import re
import html
from pathlib import Path
from urllib.parse import unquote
import requests

ROOT = Path(__file__).resolve().parents[1]


def plain_context(text):
    """Remove references and markup; never interpret or execute source text."""
    text = re.split(r"(?im)^==\s*(?:references|notes|external links|bibliography|further reading)\s*==", text)[0]
    text = re.sub(r"(?m)^={2,}\s*(.*?)\s*={2,}\s*$", r"\n## \1\n", text)
    text = re.sub(r"<!--.*?-->|<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", "", text, flags=re.S | re.I)
    text = re.sub(r"\{\|.*?\|\}", "", text, flags=re.S)
    for _ in range(50):
        stripped = re.sub(r"\{\{[^{}]*\}\}", "", text)
        if stripped == text:
            break
        text = stripped
    text = re.sub(r"\[\[(?:File|Image|Category):[^\n]*", "", text, flags=re.I)
    text = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[https?://\S+(?:\s+([^\]]*))?\]", lambda m: m[1] or "", text)
    text = re.sub(r"<[^>]+>|'{2,}|={2,}", "", text)
    return html.unescape(text).strip()


def fetch(titles):
    for attempt in range(5):
        try:
            response = requests.get("https://en.wikipedia.org/w/api.php", params={
                "action": "query", "format": "json", "titles": "|".join(titles),
                "prop": "revisions", "rvprop": "content", "rvslots": "main", "redirects": 1,
            }, headers={"User-Agent": "TravelPlannerCatalogueEnrichment/1.0 (educational project; per-record attribution)"}, timeout=90)
            if response.status_code == 429:
                time.sleep(max(10, min(60, int(response.headers.get("Retry-After", "30")))))
                continue
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise ValueError(str(data["error"]))
            result = {}
            for page in data.get("query", {}).get("pages", {}).values():
                revisions = page.get("revisions", [])
                raw = revisions[0].get("slots", {}).get("main", {}).get("*", "") if revisions else ""
                if raw:
                    result[page["title"]] = plain_context(raw)
            return result
        except (requests.RequestException, ValueError):
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Source service is rate limited; try the refresh later.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True, type=Path)
    args = parser.parse_args()
    cities = json.loads((ROOT / "travel_planner/data/top_500_cities.json").read_text())
    cache = json.loads(args.cache.read_text()) if args.cache.exists() else {}
    titles = list(dict.fromkeys(unquote(c["description_source"].split("/wiki/")[1]).replace("_", " ") for c in cities))
    missing = [title for title in titles if not cache.get(title)]
    batches = [missing[i:i+10] for i in range(0, len(missing), 10)]
    for batch in batches:
        result = fetch(batch)
        cache.update(result)
        args.cache.write_text(json.dumps(cache, ensure_ascii=False))
        print(f"Cached {len(cache)}/{len(titles)} source articles", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    main()
