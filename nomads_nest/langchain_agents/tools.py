from langchain.agents import Tool
from agents import (
    persona_agent,
    destination_agent,
    itinerary_agent,
    culture_agent,
    packing_agent
)

from shared_state import SharedState

# Create a reusable state instance (can be passed if needed)
state = SharedState()

tools = [
    Tool(
        name="AnalyzePersona",
        func=lambda x: persona_agent.run(state, x),
        description="Analyze the user's travel preferences and return a list of interests."
    ),
    Tool(
        name="RecommendDestination",
        func=lambda _: destination_agent.run(state),
        description="Recommend top travel destinations based on the persona."
    ),
    Tool(
        name="GenerateItinerary",
        func=lambda _: itinerary_agent.run(state, num_days=2),  # you can parameterize days if needed
        description="Generate a 2-day itinerary for the top destination and preferences."
    ),
    Tool(
        name="ProvideCulturalTips",
        func=lambda x: culture_agent.cultural_tips(x),
        description="Provide cultural etiquette and tips for the destination."
    ),
    Tool(
        name="GeneratePackingList",
        func=lambda x: packing_agent.generate_packing_list(x, state["persona"] or []),
        description="Generate a packing list based on the destination and preferences."
    )
]
