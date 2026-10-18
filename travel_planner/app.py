"""Public travel discovery demo with isolated progress and partial results."""
import logging
import os
import queue
import threading
import time

import pandas as pd
import streamlit as st
from utils.limits import admit, release, LimitError

st.set_page_config(page_title="Nomad's Nest · Travel Discovery", page_icon="🌍", layout="wide")
try:
    for key in ("HUGGINGFACEHUB_API_TOKEN", "GEMINI_API_KEY"):
        if not os.getenv(key) and key in st.secrets:
            os.environ[key] = str(st.secrets[key])
except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
    pass

st.markdown("""<style>
.block-container {max-width:1200px; padding-top:2.5rem; padding-bottom:3rem;}
h1 {letter-spacing:-.04em;}
[data-testid="stMetric"] {background:#f0f5f2; border:1px solid #dce8df; border-radius:12px; padding:16px;}
.stButton>button[kind="primary"] {background:#246249; border-color:#246249;}
</style>""", unsafe_allow_html=True)
st.caption("NOMAD'S NEST  /  MULTI-AGENT TRAVEL DISCOVERY")
st.title("Start with a feeling. Find your next trip.")
st.write("Describe what you love. Six specialized agents discover a destination, check its weather, and create your two-day travel guide.")

EXAMPLES = {
    "Choose an example…": "",
    "Food & history": "I love local food, historic neighborhoods and architecture. I'd like a relaxed two-day city break with time to explore on foot.",
    "Nature & adventure": "I want a two-day escape with hiking, mountain scenery and nature. I enjoy adventure and prefer a modest budget.",
    "Family beach break": "A relaxing two-day beach break with family-friendly activities, local food and a little shopping.",
}
example = st.selectbox("Need inspiration?", list(EXAMPLES))
if st.session_state.get("last_example") != example:
    if EXAMPLES[example]:
        st.session_state["trip_input"] = EXAMPLES[example]
    st.session_state["last_example"] = example

with st.form("trip_form"):
    user_input = st.text_area(
        "What would make this trip feel like you?", key="trip_input", height=120,
        max_chars=1500,
        placeholder="I love local food, historic streets and a relaxed pace. Help me discover a two-day escape.",
    )
    submitted = st.form_submit_button("Discover my trip", type="primary")
st.caption("Plans cover two days. Weather is current apparent temperature, not a forecast for future travel dates. Please avoid entering personal or sensitive details.")


def execute(job, consumes_quota=True):
    """All expensive paths share the same session and process admission gate."""
    try:
        st.session_state["starts"] = admit(st.session_state.get("starts", []), consumes_quota=consumes_quota)
    except LimitError as exc:
        st.warning(str(exc))
        return None
    events = queue.Queue()
    outcome = {}
    trace = []
    started = time.monotonic()

    def record(event):
        trace.append({"Operation": "Guide generation" if consumes_quota else "Discovery", "Elapsed (s)": round(time.monotonic() - started, 2), "Event": str(event)})

    def worker():
        from logger import bind_progress, reset_progress
        token = bind_progress(events.put)
        try:
            outcome["result"] = job(events.put)
        except Exception:
            logging.getLogger(__name__).exception("Trip planning failed")
            outcome["failed"] = True
        finally:
            reset_progress(token)
            release()

    with st.status("Finding your next adventure…", expanded=True) as status:
        progress = st.empty()
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        while thread.is_alive():
            try:
                event = events.get(timeout=0.25)
                record(event)
                progress.write(event)
            except queue.Empty:
                pass
        thread.join()
        while not events.empty():
            record(events.get_nowait())
        st.session_state["trace_events"] = st.session_state.get("trace_events", []) + trace
        if outcome.get("failed"):
            status.update(label="We couldn't finish this request", state="error", expanded=False)
            st.error("The planner is temporarily unavailable. Please try again shortly. Your previous result is still available below.")
            return None
        status.update(label="Your results are ready", state="complete", expanded=False)
    return outcome.get("result")


def discover(text, progress):
    progress("Loading the travel agents…")
    from langgraph_setup.run_graph import run_trip_planner
    return run_trip_planner(text, progress=progress, require_approval=True)


if submitted:
    if len(user_input.strip()) < 10:
        st.warning("Describe your trip in at least 10 characters so we can find a useful match.")
    else:
        st.session_state["trace_events"] = []
        updated = execute(lambda progress: discover(user_input.strip(), progress), consumes_quota=False)
        if updated:
            st.session_state["result"] = updated
            st.session_state.pop("alternatives", None)


def needs_choice(result):
    return (result.get("awaiting_approval") or result.get("weather_check_result") != "ok") and not result.get("human_override")


def plan_for_city(result, candidate, passed_check=False):
    from utils.plan_generation import generate_sections
    from logger import log
    log(f"Human approval: {candidate['city']}; building the guide")
    updated = dict(result)
    updated.update(top_destination=candidate["city"], final_destination=candidate,
                   human_override=candidate["city"], override_passed=passed_check, awaiting_approval=False)
    updated.update(generate_sections(updated))
    return updated


def find_alternatives(result):
    from agents.destination_agent import rank
    from utils.weather_api import fetch_apparent_temperatures
    from utils.weather_utils import get_current_weather
    ranked = rank(result.get("persona", []), top_n=None, query_text=result.get("user_input", ""))
    already = {entry["city"] for entry in result.get("weather_log", [])}
    ranked = [c for c in ranked if c["name"] not in already]
    temperatures = fetch_apparent_temperatures((c["lat"], c["lng"]) for c in ranked)
    passing, countries = [], set()
    for city, temp in zip(ranked, temperatures):
        condition = get_current_weather(temp)
        if condition not in {"chilly", "warm"} or city["country"] in countries:
            continue
        countries.add(city["country"])
        passing.append({**city, "city": city["name"], "temperature": temp, "condition": condition})
        if len(passing) == 5:
            break
    return {"cities": passing}


def export_plan(result):
    parts = ["# Your two-day travel guide", f"Destination: {result.get('top_destination', 'Not selected')}",
             "Preferences: " + ", ".join(result.get("persona", []))]
    for title, key in [("Itinerary", "itinerary"), ("Culture & etiquette", "culture_tips"), ("Packing list", "packing_list")]:
        parts.extend([f"## {title}", result.get(key) or "Not generated."])
    parts.append("AI-generated suggestions. Verify opening hours, reservations, entry requirements and local conditions before traveling. Weather shown in the app is current, not a future forecast.")
    return "\n\n".join(parts)


st.subheader("Agent workflow")
st.graphviz_chart("""digraph {
    rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#eef5f0", fontname="Arial"];
    P [label="1. Persona"]; D [label="2. Destinations"]; W [label="3. Live weather"];
    H [label="Your approval", fillcolor="#dceaff"];
    I [label="4. Itinerary"]; C [label="5. Culture"]; K [label="6. Packing"]; O [label="Travel guide"];
    P -> D -> W -> H; W -> W [label="next city"];
    H -> I [label="approve"]; H -> C; H -> K; I -> O; C -> O; K -> O;
}""", use_container_width=True)
traces = st.session_state.get("trace_events", [])
if traces:
    st.subheader("Agent activity trace")
    st.dataframe(pd.DataFrame(traces), hide_index=True, use_container_width=True)
    st.caption("Execution events and provider outcomes. No credentials or private model reasoning are shown.")

result = st.session_state.get("result")
if result and result.get("matching_message"):
    st.info(result["matching_message"])
if result and not result.get("all_recommendations") and result.get("matching_message"):
    result = None
if result:
    st.divider()
    preferences = result.get("persona", [])
    st.caption("YOUR TRAVEL STYLE · " + " · ".join(preferences).upper())
    if needs_choice(result):
        if result.get("awaiting_approval"):
            st.subheader(f"Recommended: {result.get('top_destination', 'Choose a destination')}")
            st.info("You decide. Review the shortlist and weather below, then approve a destination before the writing agents start.")
        else:
            st.subheader("A few possibilities, with a weather tradeoff")
            st.info("None of the shortlisted cities could be confirmed within our 15–28 °C comfort range. Choose one anyway, or search the catalogue for alternatives.")
    else:
        city = result.get("top_destination", "Your destination")
        country = result.get("final_destination", {}).get("country", "")
        st.subheader(f"Your next stop: {city}" + (f", {country}" if country else ""))
        if result.get("human_override"):
            st.caption("Selected by you from weather-checked alternatives." if result.get("override_passed") else "Selected by you with a weather override. Check local conditions before traveling.")

    weather = result.get("weather_log", [])
    with st.expander("See how the destination was chosen", expanded=needs_choice(result)):
        if weather:
            frame = pd.DataFrame(weather)
            frame["decision"] = frame.apply(lambda row: "Weather unavailable" if row["condition"] == "unavailable" else ("Outside comfort range" if row["skipped"] else "Within comfort range"), axis=1)
            st.dataframe(frame[["city", "temperature", "condition", "decision"]].rename(columns={"city":"City", "temperature":"Feels like (°C)", "condition":"Conditions", "decision":"Weather check"}), hide_index=True, use_container_width=True)
        else:
            st.info("No weather observations are available.")
        st.caption("Current apparent temperature from Open-Meteo; cached for up to one hour. This is a temperature preference check, not a travel safety assessment.")
        for candidate in result.get("all_recommendations", []):
            if candidate.get("match_reasons"):
                st.markdown("**" + candidate["name"] + "**")
                for reason in candidate["match_reasons"]:
                    st.write(reason)
                for source in candidate.get("match_sources", []):
                    st.markdown(f"[{source['label']} evidence]({source['url']})")
                for note in candidate.get("match_limits", []):
                    st.caption(note)

    if needs_choice(result):
        mode = st.radio("How would you like to continue?", ["Choose a shortlisted city", "Find comfortable alternatives"], horizontal=True)
        if mode == "Choose a shortlisted city":
            options = weather
        else:
            if st.button("Check alternatives across the catalogue"):
                alternatives = execute(lambda progress: find_alternatives(result), consumes_quota=False)
                if alternatives is not None:
                    st.session_state["alternatives"] = alternatives["cities"]
            options = st.session_state.get("alternatives", [])
            if "alternatives" in st.session_state and not options:
                st.warning("No alternatives could be confirmed in the comfort range. You can choose an original match or try different preferences.")
        if options:
            def label(i):
                c = options[i]
                temp = c.get("temperature")
                return c["city"] + (f" · {temp:.1f} °C" if temp is not None else " · weather unavailable")
            default = next((i for i, c in enumerate(options) if c["city"] == result.get("top_destination")), 0)
            choice = st.selectbox("Destination", range(len(options)), index=default, format_func=label)
            if st.button("Approve destination & build guide", type="primary"):
                selected = options[choice]
                updated = execute(lambda progress: plan_for_city(result, selected, passed_check=selected.get("condition") in {"chilly", "warm"}))
                if updated:
                    st.session_state["result"] = updated
                    st.rerun()
    else:
        if result.get("human_override"):
            selected = result.get("final_destination", {})
            temp = selected.get("temperature")
            if temp is not None:
                st.caption(f"Selected city's current apparent temperature: {temp:.1f} °C ({selected.get('condition', '')}).")
        errors = result.get("generation_errors", [])
        if errors:
            st.warning(result.get("generation_message") or "Some writing agents are temporarily unavailable. Your destination and weather results are saved; you can retry the missing sections below.")
        itinerary, culture, packing = st.tabs(["Two-day itinerary", "Culture & etiquette", "Packing list"])
        for container, key in [(itinerary,"itinerary"), (culture,"culture_tips"), (packing,"packing_list")]:
            with container:
                if result.get(key):
                    st.markdown(result[key])
                else:
                    st.info("This section couldn't be generated. Please retry in a minute.")
        if errors and st.button("Retry missing sections"):
            def retry_missing(progress):
                from utils.plan_generation import generate_sections
                update = dict(result)
                # Retain successful sections if the retry has a partial failure.
                fresh = generate_sections(result, only=errors)
                for key in ("itinerary", "culture_tips", "packing_list"):
                    update[key] = result.get(key) or fresh.get(key, "")
                update["generation_message"] = fresh.get("generation_message", "")
                update["generation_errors"] = [key for key in ("itinerary", "culture_tips", "packing_list") if not update[key]]
                return update
            updated = execute(retry_missing)
            if updated:
                st.session_state["result"] = updated
                st.rerun()
        st.download_button("Download travel guide", export_plan(result), file_name="travel-guide.md", mime="text/markdown")
        st.caption("AI-generated suggestions: verify opening hours, reservations, entry requirements and local conditions before traveling.")

with st.expander("How the agents work"):
    st.markdown("**1. Understand your style** → **2. Rank destinations** → **3. Check current weather** → **4–6. Write itinerary, cultural tips and packing list**")
    st.write("Persona classification and destination matching run locally with DeBERTa and MiniLM. LangGraph coordinates the weather decision loop; three independent writing agents call one shared generation client, trying Gemini first and Hugging Face when Gemini cannot respond. Every discovery pauses for your approval. If no city passes the weather preference check, you can override it or search alternatives.")
    st.caption("Discovery filters a sourced catalogue by explicit requirements, then ranks supported matches using semantic similarity and evidence. Quieter-area recommendations refer to specific locations, not entire cities. It does not search flights, verify availability or make bookings.")
    st.link_button("Explore the source on GitHub", "https://github.com/madhumitha-gv/Multi-Agent-Travel-Discovery-Planner")
