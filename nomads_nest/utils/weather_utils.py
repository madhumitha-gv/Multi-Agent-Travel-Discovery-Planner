# utils/weather_utils.py

def get_current_weather(temp_celsius):
    temp_ranges = {
        (float('-inf'), 5): "freezing",
        (5, 15): "cold",
        (15, 22): "chilly",
        (22, 28): "warm",
        (28, 35): "hot",
        (35, float('inf')): "very hot"
    }

    for (low, high), description in temp_ranges.items():
        if low <= temp_celsius < high:
            return description
