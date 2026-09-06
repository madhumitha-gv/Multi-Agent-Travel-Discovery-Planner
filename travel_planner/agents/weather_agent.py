from utils.weather_utils import get_current_weather
from utils.weather_api import fetch_apparent_temperature

HARSH_CONDITIONS = {"freezing", "very hot"}

def run(state):
    index = state["current_rec_index"]
    recommendations = state["all_recommendations"]
    
    if index >= len(recommendations):
        state["weather_check_result"] = "fail"
        return state

    destination = recommendations[index]
    lat, lng = destination["lat"], destination["lng"]
    temp = fetch_apparent_temperature(lat, lng)
    condition = get_current_weather(temp)

    print(f"Checking weather at {destination['name']}: {condition}")

    if condition in HARSH_CONDITIONS:
        state["current_rec_index"] += 1
        state["weather_check_result"] = "harsh"
    else:
        state["final_destination"] = destination
        state["weather_check_result"] = "ok"

    return state
