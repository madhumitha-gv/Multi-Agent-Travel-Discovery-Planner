# langgraph_setup/run_graph.py
from langgraph_setup.trip_flow_graph import build_trip_graph
from logger import log, bind_progress, reset_progress

def run_trip_planner(user_input: str, progress=None, require_approval=False):
    token = bind_progress(progress)
    try:
        return _run(user_input, require_approval)
    finally:
        reset_progress(token)


def _run(user_input, require_approval):
    graph = build_trip_graph()
    initial_state = {"user_input": user_input, "require_approval": require_approval}
    final_state = {}

    for step in graph.stream(initial_state):
        if isinstance(step, dict):
            # Each step is {step_name: state_dict}, extract the value
            values = list(step.values())
            if values:
                final_state.update(values[0])  # merge partial node updates
                log(f"🤖 Step output captured: {list(step.keys())[0]}")
            else:
                log("⚠️ No values in step")
        else:
            log(f"⚠️ Unexpected stream output: {step}")

    return final_state
