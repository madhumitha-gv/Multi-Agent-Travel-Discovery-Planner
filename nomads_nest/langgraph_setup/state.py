from typing import TypedDict, List, Dict, Optional

class TripState(TypedDict, total=False):
    user_input: str
    persona: List[str]
    destination_scores: dict
    destinations: List[str]
    top_destination: str
    all_recommendations: List[dict] 
    current_rec_index: int           
    weather_check_result: str
    weather_log: List[Dict[str, Optional[str]]]
    itinerary: str
    culture_tips: str
    packing_list: str
