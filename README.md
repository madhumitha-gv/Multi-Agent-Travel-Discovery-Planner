# Multi-Agent Travel Discovery Planner

Discover a destination from the kind of trip you want, then build a two-day guide.

**[Try the hosted planner](https://travel-planner.gentlemushroom-48179c71.centralus.azurecontainerapps.io/)**

Example: *I love local food, historic neighborhoods and architecture. I'd like a relaxed two-day city break with time to explore on foot.*

## How it works

1. **Understand the request:** local DeBERTa identifies travel interests. An English requirement parser separately extracts explicit coast/beach, mountain, quiet-area, hiking and skiing requirements, geographic exclusions, simple “mountains or beaches” alternatives, and nonurban stays.
2. **Hybrid discovery:** supported structured facts filter the catalogue before MiniLM ranks candidates. Ranking combines semantic relevance (55%), supported preference fit (35%) and relevant evidence quality (10%); these are ranking weights, not calibrated probabilities. Original generic feature labels are retained for reference but are not scored. The shortlist contains at most one city per country. Missing evidence cannot satisfy a positive requirement, and fewer than three results are returned rather than adding weak fillers. Alternatives preserve the same requirements.
3. **Weather:** LangGraph checks the shortlisted cities’ current apparent temperatures separately from preference fit. A comfortable temperature does not make a city calm or mountainous. City weather is not mountain weather or a future forecast.
4. **Your decision:** the UI explains each match with source links, distinguishes an area or excursion from the city itself, and pauses before writing. Approve a destination, override the weather preference, or search eligible alternatives. Requests with no supported matches explain the gap instead of offering an invalid approval.
5. **Writing:** itinerary, culture and packing agents run independently in parallel behind the unchanged `generate(prompt, max_tokens, temperature)` interface in `utils/mistral.py`, trying Gemini then Hugging Face. The itinerary receives the original request, exclusions, match evidence and focus area. A full guide uses three primary generation requests, plus retries/fallbacks. Discovery does not consume generation quota.

The unified catalogue retains all 500 original records, with 496 currently eligible after filtering two duplicate aliases, an unverified city identity and Boankra’s sparse travel evidence. Structured profiles include sourced settlement type, setting, geography, activities, specific-area context and quality flags. Read [the data audit](docs/catalogue-audit.md) for exact coverage. Reviewed mountain-trip and quieter-area coverage is deliberately limited; the catalogue mostly describes cities. A mountain mention or a low population does not prove a mountain retreat or a calm destination. No permanent crowd score is invented.

Source text comes from Wikipedia contributors under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), with article links, licenses, source coordinates and short evidence excerpts in each record. Reviewed experience facts also cite tourism and park sources. Basic article locations were checked within 35 km of the original coordinates. Source-text rules fill documented food, history and culture context; this is not an independent verification of every travel claim or current availability.

Offline refresh steps: `python scripts/enrich_catalogue.py --cache /path/to/city-cache.json`, then `python scripts/fetch_catalogue_context.py --cache /path/to/context-cache.json`, then `python scripts/build_destination_profiles.py --source-cache /path/to/context-cache.json`. Keep caches outside the repository. No source fetch or generation call runs during matching. Rule-based interpretation supports common English requests; complex negation and unsupported experience types remain limitations. Run `python scripts/evaluate_matching.py --output /path/to/evaluation.json` to exercise the actual local models against the acceptance prompts.

```mermaid
flowchart LR
  Input[Trip preferences] --> Persona[Persona classifier]
  Persona --> Rank[Destination ranking]
  Rank --> Weather{Current weather}
  Weather -->|Outside range or unavailable| Next{More candidates?}
  Next -->|Yes| Weather
  Next -->|No| Choice[Traveller chooses]
  Weather -->|Within range| Choice
  Choice --> Guide
  Guide --> Download[Downloadable guide]
```

The app uses Streamlit and LangGraph. It does not expose a FastAPI service.

## Reliability and public-demo controls

- Progress messages belong to the current request; visitors do not share an activity queue. A persistent activity trace shows persona labels, shortlist, weather, approval, individual writing-agent activity and provider/fallback outcomes. An always-visible workflow diagram shows the approval gate.
- Failed writing preserves preferences, destination matches and weather observations.
- Missing writing sections can be retried without replacing successful sections.
- Weather failures are shown as unavailable, never accepted as comfortable weather.
- Model credentials and provider response bodies are not displayed to visitors.
- The container runs as a non-root user. Streamlit's XSRF protection stays enabled.
- A process-wide gate allows one expensive operation at a time.
- Default caps: one guide-generation operation per minute, five per browser session per hour, five globally per hour and five globally per rolling day. Writing retries also count; discovery and alternative searches share the concurrency gate without consuming model-generation quota.
- Gemini HTTP 429 responses immediately fall through to Hugging Face and cool only the failed candidate.
- Both providers use the same ordered-candidate policy, bounded retries and per-candidate cooldowns. The retry budget reserves time for the fallback. Provider-specific request encoding lives in the same client file.
- A missing, rejected or exhausted credential does not disable candidates using the other provider. The Hugging Face token still needs available credits for the fallback to succeed.

**Limits are process-local and reset on restart.** Keep one replica. These controls are demo safeguards, not authentication, a durable quota system or a billing guarantee. A shared limiter and persistence are required before broader public traffic or multiple replicas.

## Local setup

Use Python 3.12:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `GEMINI_API_KEY` and `HUGGINGFACEHUB_API_TOKEN` in `.env`. The default candidate order is Gemini followed by Hugging Face. Then:

```bash
cd travel_planner
streamlit run app.py
```

The first local run downloads the DeBERTa and MiniLM models. Production images bake them in at build time. The landing page renders before the local models are imported.

### Model configuration

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Gemini credential; never commit it |
| `GEN_TIMEOUT` | Socket inactivity timeout per request in seconds |
| `HUGGINGFACEHUB_API_TOKEN` | Credential for the Hugging Face fallback; requires available credits |
| `GEN_CANDIDATES` | Ordered `provider\|model` pairs; default `gemini\|gemini-2.5-flash,auto\|meta-llama/Llama-3.1-8B-Instruct` |
| `GEN_TOTAL_TIMEOUT` | Shared retry scheduling budget; active network requests may overrun it |
| `SESSION_PLANS_PER_HOUR` | Per-browser-session hourly cap |
| `GLOBAL_PLANS_PER_MINUTE` | Per-process per-minute cap |
| `GLOBAL_PLANS_PER_HOUR` | Per-process rolling hourly cap |
| `GLOBAL_PLANS_PER_DAY` | Per-process rolling 24-hour cap |

The configured Gemini model was verified by a real API call with this project’s credential. AI Studio quota values require an authenticated Google session; they have not been independently read here. Gemini quotas vary by model, project and account. Check the project's actual limits in [AI Studio](https://ai.google.dev/gemini-api/docs/rate-limits). A free-tier key is not unlimited. Google may use free-tier inputs and outputs to improve its products; do not submit sensitive information. See [Gemini pricing and data use](https://ai.google.dev/gemini-api/docs/pricing).

## Validation

```bash
pip install pytest==9.1.1
python -m pytest -q
```

Tests exercise real LangGraph routing with deterministic model boundaries, provider fallback and authentication errors, both response formats and quota cooldowns, partial generation, weather failure handling, request-local logging and usage admission. UI tests use Streamlit's AppTest. Live smoke checks are separate and require working model credentials.

### Live fallback smoke test

With credentials loaded from environment variables or a gitignored `.env`:

```bash
GEN_CANDIDATES='bogus|fake/model,gemini|gemini-2.5-flash' \
  python -c 'import sys; sys.path.insert(0, "travel_planner"); from utils.mistral import generate; assert generate("Say hello in one sentence.", max_tokens=32); print("Fallback passed")'
```

Then run a full plan with the default candidates. An exhausted Hugging Face account cannot serve fallback traffic even when the routing logic is correct.

## Azure deployment

The existing app uses Azure Container Apps in `travel-planner-rg` and ACR `tpacr10229`, with 1 vCPU and 2 GiB memory. Credentials are injected from Container Apps secrets.

A clean build uses `Dockerfile`:

```bash
az acr build --registry tpacr10229 --image travel-planner:<unique-tag> --file Dockerfile --platform linux/amd64 .
```

`Dockerfile.release` offers a faster source-only release on top of the exact deployed v1 runtime digest, reusing its dependencies and baked-in model weights. It requires access to this project's private registry. Use the normal Dockerfile for an independent clean build or dependency updates.

After setting the `gemini-api-key` Container Apps secret through a secure channel:

```bash
az containerapp update -n travel-planner -g travel-planner-rg \
  --image tpacr10229.azurecr.io/travel-planner:<unique-tag> \
  --min-replicas 1 --max-replicas 1 \
  --set-env-vars GEMINI_API_KEY=secretref:gemini-api-key \
    'GEN_CANDIDATES=gemini|gemini-2.5-flash,auto|meta-llama/Llama-3.1-8B-Instruct' \
    GEN_TIMEOUT=20 GEN_TOTAL_TIMEOUT=75 \
    GLOBAL_PLANS_PER_MINUTE=1 GLOBAL_PLANS_PER_HOUR=5 GLOBAL_PLANS_PER_DAY=5
```

One warm replica reduces cold starts but consumes Azure resources while idle. Set `--min-replicas 0` when the review window ends if scale-to-zero is preferred. That reintroduces cold starts.

Before sharing, verify the revision is ready, `/_stcore/health` returns 200, and a complete query works without login. Keep the previous image and revision available for rollback; changing the image alone does not roll back configuration.

## Practical limits

- Weather is current apparent temperature, cached for up to an hour, not a future trip forecast or a safety assessment.
- The city catalogue uses broad feature descriptions; destination scores are approximate and ties are common. Enriching city-specific data is the most valuable ranking improvement.
- Travel dates, flight prices, bookings, opening hours and live availability are not verified.
- AI output can be inaccurate; verify local requirements and details before traveling.
- Results are browser-session state and disappear on restart. There is no shared persistence or authentication.
- Full dependency vulnerability review, load testing, durable quotas, monitoring and content evaluation remain necessary for a general production service.
