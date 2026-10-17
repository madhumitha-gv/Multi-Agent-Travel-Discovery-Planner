from langgraph.graph import StateGraph, END
from langgraph_setup.nodes import analyze_persona, recommend_destinations, check_weather
from langgraph_setup.state import TripState
from utils.plan_generation import generate_sections


def build_trip_graph():
    builder = StateGraph(state_schema=TripState)
    builder.add_node("analyze_persona", analyze_persona)
    builder.add_node("recommend_destinations", recommend_destinations)
    builder.add_node("check_weather", check_weather)
    builder.add_node("generate_plan", generate_sections)
    builder.add_node("choose_destination", lambda state: {
        "weather_check_result": "fail",
        "message": "Choose a destination to continue; none passed the current weather check.",
        "itinerary": "", "culture_tips": "", "packing_list": "",
    })
    builder.set_entry_point("analyze_persona")
    builder.add_edge("analyze_persona", "recommend_destinations")
    builder.add_edge("recommend_destinations", "check_weather")
    builder.add_conditional_edges("check_weather", route_weather)
    builder.add_edge("generate_plan", END)
    builder.add_edge("choose_destination", END)
    return builder.compile()


def route_weather(state: TripState) -> str:
    if state.get("weather_check_result") == "ok":
        return "generate_plan"
    if state.get("current_rec_index", 0) < len(state.get("all_recommendations", [])):
        return "check_weather"
    return "choose_destination"
