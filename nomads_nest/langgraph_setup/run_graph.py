# langgraph_setup/run_graph.py
from langgraph_setup.trip_flow_graph import build_trip_graph
from logger import log

def run_trip_planner(user_input: str):
    graph = build_trip_graph()
    initial_state = {"user_input": user_input}
    final_state = {}

    for step in graph.stream(initial_state):
        if isinstance(step, dict):
            # Each step is {step_name: state_dict}, extract the value
            values = list(step.values())
            if values:
                final_state = values[0]  # extract just the state
                log(f"🤖 Step output captured: {list(step.keys())[0]}")
            else:
                log("⚠️ No values in step")
        else:
            log(f"⚠️ Unexpected stream output: {step}")

    return final_state
