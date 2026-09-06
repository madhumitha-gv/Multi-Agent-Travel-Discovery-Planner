from dotenv import load_dotenv
load_dotenv()

from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_community.llms import HuggingFaceHub
from langchain.memory import ConversationBufferMemory
from langchain_agents.tools import tools
from utils.text_utils import truncate_prompt  # 👈 make sure this import works

# Define your model

from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.5
)


# Shared memory for conversational agent
memory = ConversationBufferMemory(memory_key="chat_history")

# Build the LangChain agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    max_iterations=10,              # ⬅️ Increase from default (4)
    max_execution_time=60,          # ⬅️ Optional: increase to 60+ seconds
    early_stopping_method="generate"  # ⬅️ Allow LLM to give up gracefully
)

def run_agent_chain(user_input: str, state):
    # Step 1: Persona
    preferences = persona_agent.run(state, user_input)

    # Step 2: Destination
    destinations = destination_agent.run(state)
    top_dest = destinations[0][0] if destinations else "Bali"

    # Step 3: Itinerary
    itinerary = itinerary_agent.run(state)

    # Step 4: Culture
    culture = culture_agent.cultural_tips(top_dest)

    # Step 5: Packing
    packing = packing_agent.generate_packing_list(top_dest, preferences)

    # Final Output
    return f"""
🧠 Preferences: {preferences}

📍 Top Destination: {top_dest}

🗓 Itinerary:
{itinerary}

🌍 Cultural Tips:
{culture}

🎒 Packing List:
{packing}
"""
