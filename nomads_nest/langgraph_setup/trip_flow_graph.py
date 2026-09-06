
# langgraph_setup/trip_flow_graph.py
from langgraph.graph import StateGraph
from langgraph_setup.nodes import (
    analyze_persona, recommend_destinations, check_weather,
    generate_itinerary, provide_cultural_tips, generate_packing_list
)

from langgraph_setup.state import TripState

def build_trip_graph():
    builder = StateGraph(state_schema=TripState)

    builder.add_node("analyze_persona", analyze_persona)
    builder.add_node("recommend_destinations", recommend_destinations)
    builder.add_node("check_weather", check_weather)
    builder.add_node("generate_itinerary", generate_itinerary)
    builder.add_node("provide_cultural_tips", provide_cultural_tips)
    builder.add_node("generate_packing_list", generate_packing_list)
    builder.add_node("fail", lambda state: {
    **state,
    "message": "❌ All destinations had harsh weather. Try again with different preferences.",
    "itinerary": "Could not generate itinerary due to poor weather.",
    "culture_tips": "No tips available.",
    "packing_list": "No packing list generated."
})

    builder.set_entry_point("analyze_persona")
    builder.add_edge("analyze_persona", "recommend_destinations")
    builder.add_edge("recommend_destinations", "check_weather")
    builder.add_conditional_edges("check_weather", route_weather)
    builder.add_edge("generate_itinerary", "provide_cultural_tips")
    builder.add_edge("provide_cultural_tips", "generate_packing_list")
    builder.add_edge("fail", "provide_cultural_tips")  # or end the graph

    return builder.compile()


def route_weather(state: TripState) -> str:
    if state["weather_check_result"] == "ok":
        return "generate_itinerary"
    elif state["current_rec_index"] < len(state["all_recommendations"]):
        return "check_weather"
    else:
        return "fail"

