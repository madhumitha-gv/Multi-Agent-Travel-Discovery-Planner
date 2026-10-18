"""Refresh sourced city descriptions; preserve original features and coordinates.

Run explicitly, never during app startup. Wikipedia text is CC BY-SA 4.0.
Coordinate checks reject namesakes and disambiguation pages. Unresolved entries
are reported and left unchanged rather than filled with invented facts.
"""
import argparse
import csv
import json
import math
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://en.wikipedia.org/w/api.php"
# Legacy gazetteer names mapped to articles whose coordinates are checked below.
ARTICLE_ALIASES = {
    ("Tongshan", "China"): "Xuzhou",
    ("Nangandao", "China"): "Xinxiang",
    ("Huanglongsi", "China"): "Kaifeng",
    ("Xinpu", "China"): "Lianyungang",
    ("Jiangguanchi", "China"): "Xuchang",
    ("Xiaoganzhan", "China"): "Xiaogan",
    ("Xiaoxita", "China"): "Yichang",
    ("Baicheng", "China"): "Baise",
    ("Yulinshi", "China"): "Yulin, Shaanxi",
    ("Baojishi", "China"): "Baoji",
    ("Qincheng", "China"): "Tianshui",
    ("Gāzipura", "Bangladesh"): "Gazipur",
    ("Lianshan", "China"): "Lianshan District",
    ("Longba", "China"): "Longnan",
    ("Nāgpur", "India"): "Nagpur",
    ("Bekasi Kota", "Indonesia"): "Bekasi",
    ("Khowrhesht", "Iran"): "Khvorhesht",
    ("Shengli", "China"): "Dongying",
    ("Qinbaling", "China"): "Qingyang, Gansu",
    ("Portland", "United States"): "Portland, Oregon",
    ("Yushan", "China"): "Kunshan",
    ("Qingyang", "China"): "Jinjiang, Fujian",
    ("Shangzhou", "China"): "Shangluo",
    ("Xiping", "China"): "Datong",
    ("Davao", "Philippines"): "Davao City",
    ("Shuyangzha", "China"): "Shuyang County",
    ("Hyderabad City", "Pakistan"): "Hyderabad, Sindh",
    ("Sanzhou", "China"): "Wanzhou District",
    ("Ximeicun", "China"): "Nan'an, Fujian",
    ("Chengtangcun", "China"): "Tengzhou",
    ("Columbus", "United States"): "Columbus, Ohio",
}
# Reviewed geography statements in the fetched city introductions. A keyword
# scan alone would wrongly include inland cities mentioning "Ivory Coast" or
# a coastal mountain range, so this review is explicit and reproducible.
REVIEWED_COASTAL_CITIES = {
    "Tokyo", "Jakarta", "Shenzhen", "Lagos", "Karachi", "Lima", "Nagoya",
    "Luanda", "Dar es Salaam", "Hong Kong", "Zhanjiang", "Melbourne",
    "Alexandria", "Jeddah", "İzmir", "Shantou", "Wenzhou", "Casablanca",
    "San Francisco", "Dubai", "Qinhuangdao", "Athens", "Rizhao", "Incheon",
    "Ningde", "Haikou", "Tampa", "Kaohsiung", "Mogadishu", "Yantai",
    "Zhuhai", "Huludao", "Beirut", "Accra", "Yingkou", "Colombo",
    "Tijuana", "Santos", "Tainan", "Mersin", "Montevideo", "Valencia",
}


def distance_km(a, b):
    lat1, lat2 = map(math.radians, (a[0], b[0]))
    dl = math.radians(b[0] - a[0])
    dn = math.radians(b[1] - a[1])
    h = math.sin(dl / 2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dn / 2)**2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def fetch(session, **params):
    for attempt in range(3):
        try:
            response = session.get(API, params={"action": "query", "format": "json", **params}, timeout=30)
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise ValueError(str(result["error"]))
            return result.get("query", {})
        except (requests.RequestException, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    catalogue = ROOT / "travel_planner/data/top_500_cities.json"
    cities = json.loads(catalogue.read_text())
    with (catalogue.parent / "worldcities.csv").open() as f:
        source = {(r["city"], r["country"]): r for r in csv.DictReader(f)}
    cache = json.loads(args.cache.read_text()) if args.cache.exists() else {}
    session = requests.Session()
    session.headers["User-Agent"] = "TravelPlannerCatalogueEnrichment/1.0 (educational project; source attribution stored per city)"
    unresolved = []
    for index, city in enumerate(cities):
        key = city["city"] + "|" + city["country"]
        page = cache.get(key)
        if not page:
            row = source.get((city["city"], city["country"]), {})
            names = list(dict.fromkeys(filter(None, [ARTICLE_ALIASES.get((city["city"], city["country"])), city["city"], row.get("city_ascii"),
                f"{city['city']}, {row.get('admin_name', city['country'])}",
                f"{city['city']}, {city['country']}"])))
            result = fetch(session, titles="|".join(names), redirects=1,
                prop="extracts|coordinates|pageprops", exintro=1, explaintext=1,
                exlimit="max", exchars=1400)
            candidates = list(result.get("pages", {}).values())
            valid = [p for p in candidates if p.get("extract") and p.get("coordinates")
                and "disambiguation" not in p.get("pageprops", {})
                and distance_km((city["lat"],city["lng"]),
                    (p["coordinates"][0]["lat"],p["coordinates"][0]["lon"])) <= 35]
            if not valid:
                # Some articles expose their location only through Wikidata.
                for candidate in candidates:
                    item = candidate.get("pageprops", {}).get("wikibase_item")
                    if not item or candidate.get("coordinates") or "disambiguation" in candidate.get("pageprops", {}):
                        continue
                    response = session.get(f"https://www.wikidata.org/wiki/Special:EntityData/{item}.json", timeout=30)
                    response.raise_for_status()
                    claims = response.json().get("entities", {}).get(item, {}).get("claims", {}).get("P625", [])
                    for claim in claims:
                        coord = claim.get("mainsnak", {}).get("datavalue", {}).get("value", {})
                        if "latitude" in coord and distance_km((city["lat"], city["lng"]), (coord["latitude"], coord["longitude"])) <= 35:
                            candidate["coordinates"] = [{"lat": coord["latitude"], "lon": coord["longitude"]}]
                            candidate["coordinate_source"] = f"https://www.wikidata.org/wiki/{item}"
                            if candidate.get("extract"):
                                valid.append(candidate)
                            break
            if not valid:
                nearby = fetch(session, generator="geosearch", ggscoord=f"{city['lat']}|{city['lng']}",
                    ggsradius=10000, ggslimit=10, prop="extracts|coordinates|pageprops",
                    exintro=1, explaintext=1, exlimit="max", exchars=1400)
                # Nearby landmarks are not substitutes for city descriptions.
                aliases = [n.casefold() for n in (city["city"], row.get("city_ascii", "")) if n]
                valid = [p for p in nearby.get("pages", {}).values()
                    if p.get("extract") and p.get("coordinates")
                    and "disambiguation" not in p.get("pageprops", {})
                    and any(p.get("title", "").casefold() == n or p.get("title", "").casefold().startswith(n + ",") for n in aliases)]
            if valid:
                page = min(valid, key=lambda p: distance_km((city["lat"],city["lng"]),
                    (p["coordinates"][0]["lat"],p["coordinates"][0]["lon"])))
                cache[key] = page
                args.cache.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
            time.sleep(.15)
        if page:
            text = " ".join(page["extract"].split())
            # Stay below 200 source words and end at a sentence boundary.
            text = " ".join(text.split()[:180])
            if not text.endswith("."):
                text = text.rsplit(".", 1)[0] + "."
            city["description"] = text
            city["description_source"] = "https://en.wikipedia.org/wiki/" + quote(page["title"].replace(" ", "_"))
            city["description_title"] = page["title"]
            city["place_type_description"] = page.get("pageprops", {}).get("wikibase-shortdesc", "")
            city["description_coordinates"] = {
                "lat": page["coordinates"][0]["lat"],
                "lng": page["coordinates"][0]["lon"],
            }
            city["description_coordinate_source"] = page.get("coordinate_source", city["description_source"])
            city["description_license"] = "CC BY-SA 4.0"
            if city["city"] in REVIEWED_COASTAL_CITIES and re.search(r"\b(?:coast\w*|beach\w*)\b", text, re.I):
                city["coastal"] = True
                city["coastal_source"] = city["description_source"]
        else:
            unresolved.append(key)
        if (index + 1) % 25 == 0:
            print(f"Checked {index+1}/500; sourced {index+1-len(unresolved)}", flush=True)
        catalogue.write_text(json.dumps(cities, indent=2, ensure_ascii=True, separators=(",", ":")) + "\n")
    seen = {}
    for city in cities:
        identity = (city["country"], city.get("description_source"))
        if identity in seen:
            city["duplicate_of"] = seen[identity]
        else:
            city.pop("duplicate_of", None)
            seen[identity] = city["city"]
        if city["city"] == "Kotla Qasim Khan":
            city["catalogue_status"] = "needs_review"
            city["description"] = "This catalogue entry redirects to Gujrat District in Punjab, Pakistan. Its identity as a distinct city is unverified, so it is excluded from destination matching."
    catalogue.write_text(json.dumps(cities, indent=2, ensure_ascii=True, separators=(",", ":")) + "\n")
    print("Unresolved:", json.dumps(unresolved), flush=True)
    return bool(unresolved)


if __name__ == "__main__":
    raise SystemExit(main())
