#import streamlit as st
# import pandas as pd
# import time
# import threading
# import queue
# import matplotlib.pyplot as plt
# from logger import log, log_queue
# from langgraph_setup.run_graph import run_trip_planner

# # Set the page configuration for the title and layout
# st.set_page_config(page_title="Nomads Nest", layout="wide")

# # 💜 Lavender-Themed CSS
# st.markdown("""
#     <style>
#         body {
#             background-color: #f8f4ff;
#             font-family: 'Arial', sans-serif;
#         }
#         .block-container {
#             padding-top: 2rem;
#         }
#         .stButton > button {
#             background-color: #b39ddb;
#             color: white;
#             font-weight: bold;
#             border: none;
#             border-radius: 8px;
#             padding: 10px 16px;
#         }
#         .stButton > button:hover {
#             background-color: #9575cd;
#         }
#         .stTextArea > label, .stDataFrame > label {
#             color: #5e35b1;
#         }
#         .log-box {
#             background-color: #f0e6ff;
#             border: 1px solid #d1c4e9;
#             border-radius: 10px;
#             padding: 10px;
#             font-family: monospace;
#             white-space: pre-wrap;
#             height: 200px;
#             overflow-y: auto;
#         }
#         .current-step-box {
#             height: 100px;  /* Reduced height of the current step box */
#         }
#         .left-column {
#             background-color: #d1c4e9;  /* Light Purple for Left Sidebar */
#             padding: 20px;
#             border-radius: 12px;
#             width: 25%;
#         }
#         .middle-column {
#             padding: 20px;
#             width: 40%;
#         }
#         .right-column {
#             background-color: #b39ddb;  /* Purple background for Right Column */
#             padding: 20px;
#             width: 30%;
#             border-radius: 12px;
#         }
#         .headline {
#             color: #5e35b1;
#             font-size: 32px;
#             font-weight: bold;
#             margin-bottom: 10px;
#         }
#         .subheadline {
#             color: #9575cd;
#             font-size: 11px;
#             margin-bottom: 20px;
#         }
#     </style>
# """, unsafe_allow_html=True)

# # 🔠 Title
# st.markdown("""
#     <style>
#         .title {
#             text-align: center;
#             font-size: 20px;
#             font-weight: bold;
#             color: #5e35b1;
#         }
#     </style>
#     <p class="title">NOMADS NEST</p>
# """, unsafe_allow_html=True)


# st.markdown("""
#     <style>
#         .title {
#             text-align: center;
#             font-size: 30px;
#             font-weight: bold;
#             color: #5e35b1;
#         }
#     </style>
#     <p class="title">Let us take you to your destination</p>
# """, unsafe_allow_html=True)

# # Layout: Three Columns: Left for Logs, Middle for User Input, Right for Graph
# left_col, middle_col, right_col = st.columns([1.5, 2, 1.5], gap="large")

# # Left Column: Activity Log and Current Step
# with left_col:
#     # Current Step and Activity Log containers
#     st.markdown("### Current Step")
#     current_step_log = st.empty()

#     st.markdown("### Activity Log")
#     activity_log = st.empty()

# # Middle Column: User Input
# with middle_col:
#     # Headline and subheadline for the user input section

#     # Input and Submit button
#     st.markdown("### Whats your next destination?")
#     user_input = st.text_area("", placeholder="e.g. A cozy mountain escape with hiking and stargazing.")
#     start_button = st.button("Lets plan")

# # Right Column: Display Graph in Purple Container
# with right_col:
#     st.markdown("### Multi AI Agent graph")
#     # Example Graph in a Purple Container
#     fig, ax = plt.subplots(figsize=(5, 4))
#     ax.plot([1, 2, 3, 4], [10, 20, 25, 30], marker='o')
#     ax.set_title("graph", fontsize=14)
#     ax.set_xlabel("X Axis")
#     ax.set_ylabel("Y Axis")
#     st.pyplot(fig)

# # 🧳 Start Planning Process if Submit Button is Pressed
# if start_button:
#     if not user_input.strip():
#         st.warning("Please describe your trip preferences before generating a plan.")
#     else:
#         logs = []
#         result_container = {"result": None}

#         with st.spinner("Planning your adventure..."):

#             def run_graph():
#                 result_container["result"] = run_trip_planner(user_input)

#             thread = threading.Thread(target=run_graph)
#             thread.start()

#             last_log_time = time.time()
#             while thread.is_alive() or not log_queue.empty():
#                 try:
#                     msg = log_queue.get(timeout=0.2)
#                     logs.append(msg)
#                     current_step_log.markdown(f'<div class="log-box current-step-box">{msg}</div>', unsafe_allow_html=True)
#                     activity_log.markdown(f'<div class="log-box">{"<br>".join(logs)}</div>', unsafe_allow_html=True)
#                     last_log_time = time.time()
#                 except queue.Empty:
#                     if time.time() - last_log_time > 2 and not thread.is_alive():
#                         break
#                     time.sleep(0.1)

#             thread.join()
#             result = result_container["result"]

#         # ✅ Display Final Results on the Middle Panel
#         if result:
#             st.success("Here’s your personalized trip plan!")

#             st.markdown("### Your Travel Preferences")
#             st.write(result.get("persona", "Not detected."))

#             st.markdown("### Recommended Destination")
#             st.markdown(f"**Final Pick:** {result.get('top_destination', 'No destination')}")

#             st.markdown("### Weather Decisions (Backtracking Log)")
#             weather_log = result.get("weather_log", [])
#             if weather_log:
#                 df = pd.DataFrame(weather_log)
#                 df["Decision"] = df["skipped"].map({True: "Skipped", False: "Selected"})
#                 df = df.rename(columns={
#                     "city": "City",
#                     "temperature": "Temp (°C)",
#                     "condition": "Condition"
#                 })[["City", "Temp (°C)", "Condition", "Decision"]]
#                 st.dataframe(df)
#             else:
#                 st.write("No weather log available.")

#             st.markdown("### Suggested Itinerary")
#             st.text(result.get("itinerary", "No itinerary generated."))

#             st.markdown("### Cultural Tips")
#             st.write(result.get("culture_tips", "No cultural information available."))

#             st.markdown("### Packing List")
#             st.text(result.get("packing_list", "No packing list generated."))
#         else:
#             st.error("Something went wrong — no result returned.")







# import streamlit as st
# import pandas as pd
# import time
# import threading
# import queue
# import matplotlib.pyplot as plt
# import networkx as nx
# from logger import log, log_queue
# from langgraph_setup.run_graph import run_trip_planner

# # Set the page configuration for the title and layout
# st.set_page_config(page_title="Nomads Nest", layout="wide")

# # Pastel Color Scheme (Soft Greens and Purples)
# st.markdown("""
#     <style>
#         body {
#             background-color: #f4f8f6;  /* Light pastel background */
#             font-family: 'Arial', sans-serif;
#         }
#         .block-container {
#             padding-top: 2rem;
#         }
#         .stButton > button {
#             background-color: #a5d6a7;  /* Pastel Green */
#             color: black;
#             font-weight: bold;
#             border: none;
#             border-radius: 8px;
#             padding: 12px 20px;
#         }
#         .stButton > button:hover {
#             background-color: #81c784;  /* Darker Green */
#         }
#         .stTextArea > label, .stDataFrame > label {
#             color: black;
#         }
#         .log-box {
#             background-color: #e8f5e9;  /* Light pastel green for logs */
#             border: 1px solid #c8e6c9;
#             border-radius: 10px;
#             padding: 12px;
#             font-family: monospace;
#             white-space: pre-wrap;
#             height: 200px;
#             overflow-y: auto;
#         }
#         .current-step-box {
#             height: 100px;
#         }
#         .left-column {
#             background-color: #c8e6c9;  /* Pastel Green for Left Sidebar */
#             padding: 20px;
#             border-radius: 12px;
#             width: 25%;
#             height: 100%;
#         }
#         .middle-column {
#             padding: 20px;
#             width: 40%;
#             background-color: #ffffff;  /* White background for user input */
#             border-radius: 12px;
#         }
#         .right-column {
#             background-color: #c5cae9;  /* Soft pastel purple for the graph section */
#             padding: 20px;
#             width: 30%;
#             border-radius: 12px;
#         }
#         .headline {
#             color: black;
#             font-size: 32px;
#             font-weight: bold;
#             margin-bottom: 10px;
#         }
#         .subheadline {
#             color: #388e3c;  /* Pastel Green accent for subheadline */
#             font-size: 16px;
#             margin-bottom: 20px;
#         }
#         .title {
#             text-align: center;
#             font-size: 40px;
#             font-weight: bold;
#             color: #388e3c;  /* Pastel Green for title */
#         }
#         .section-title {
#             font-size: 24px;
#             font-weight: bold;
#             color: #388e3c;
#             margin-top: 20px;
#         }
#     </style>
# """, unsafe_allow_html=True)

# # Set the local image as the background
# image_path = "background_image.jpg"  # Replace with your image's file path
# st.markdown(f"""
#     <style>
#         body {{
#             background-image: url('{image_path}');
#             background-size: cover;  /* Ensures the image covers the whole screen */
#             background-position: center;  /* Centers the image */
#             background-attachment: fixed;  /* Keeps the image fixed when scrolling */
#             color: white;  /* Text color to contrast with background */
#         }}
#     </style>
# """, unsafe_allow_html=True)

# # Page Title
# st.markdown("<p class='title'>Nomads Nest</p>", unsafe_allow_html=True)

# # Subtitle with description
# st.markdown("<p class='subheadline'>Let us take you to your next adventure</p>", unsafe_allow_html=True)

# # Layout: Three Columns (Left for Logs, Middle for User Input, Right for Graph)
# left_col, middle_col, right_col = st.columns([1.5, 2, 1.5], gap="large")

# # Left Column: Activity Log and Current Step
# with left_col:
#     st.markdown("<p class='section-title'>Current Step</p>", unsafe_allow_html=True)
#     current_step_log = st.empty()

#     st.markdown("<p class='section-title'>Activity Log</p>", unsafe_allow_html=True)
#     activity_log = st.empty()

# # Middle Column: User Input
# with middle_col:
#     st.markdown("<p class='section-title'>What’s Your Next Destination?</p>", unsafe_allow_html=True)
#     user_input = st.text_area("", placeholder="e.g. A cozy mountain escape with hiking and stargazing.", height=150)
#     start_button = st.button("Let’s Plan")

# # Right Column: Display AI Agent Graph
# with right_col:
#     st.markdown("<p class='section-title'>AI Agent Graph</p>", unsafe_allow_html=True)
    
#     # Build the directed graph for AI agents
#     G = nx.DiGraph()

#     # Add nodes (AI agents)
#     agents = [
#         "analyze_persona", 
#         "recommend_destinations", 
#         "check_weather", 
#         "generate_itinerary", 
#         "provide_cultural_tips", 
#         "generate_packing_list", 
#         "fail"
#     ]
#     G.add_nodes_from(agents)

#     # Add edges (connections between AI agents)
#     G.add_edge("analyze_persona", "recommend_destinations")
#     G.add_edge("recommend_destinations", "check_weather")
#     G.add_edge("check_weather", "generate_itinerary")
#     G.add_edge("generate_itinerary", "provide_cultural_tips")
#     G.add_edge("provide_cultural_tips", "generate_packing_list")
#     G.add_edge("fail", "provide_cultural_tips")  # or end the graph

#     # Visualize the graph
#     plt.figure(figsize=(10, 8))
#     pos = nx.spring_layout(G)  # positions for all nodes
#     nx.draw(G, pos, with_labels=True, node_size=3000, node_color="#a5d6a7", font_size=10, font_weight='bold', edge_color="#388e3c", width=2, arrows=True)
#     plt.title("AI Agent Network")
#     st.pyplot(plt)

# # 🧳 Start Planning Process if Submit Button is Pressed
# if start_button:
#     if not user_input.strip():
#         st.warning("Please describe your trip preferences before generating a plan.")
#     else:
#         logs = []
#         result_container = {"result": None}

#         with st.spinner("Planning your adventure..."):

#             def run_graph():
#                 result_container["result"] = run_trip_planner(user_input)

#             thread = threading.Thread(target=run_graph)
#             thread.start()

#             last_log_time = time.time()
#             while thread.is_alive() or not log_queue.empty():
#                 try:
#                     msg = log_queue.get(timeout=0.2)
#                     logs.append(msg)
#                     current_step_log.markdown(f'<div class="log-box current-step-box">{msg}</div>', unsafe_allow_html=True)
#                     activity_log.markdown(f'<div class="log-box">{"<br>".join(logs)}</div>', unsafe_allow_html=True)
#                     last_log_time = time.time()
#                 except queue.Empty:
#                     if time.time() - last_log_time > 2 and not thread.is_alive():
#                         break
#                     time.sleep(0.1)

#             thread.join()
#             result = result_container["result"]

#         # ✅ Display Final Results on the Middle Panel
#         if result:
#             st.success("Here’s your personalized trip plan!")

#             st.markdown("<p class='section-title'>Your Travel Preferences</p>", unsafe_allow_html=True)
#             st.write(result.get("persona", "Not detected."))

#             st.markdown("<p class='section-title'>Recommended Destination</p>", unsafe_allow_html=True)
#             st.markdown(f"**Final Pick:** {result.get('top_destination', 'No destination')}")

#             st.markdown("<p class='section-title'>Weather Decisions (Backtracking Log)</p>", unsafe_allow_html=True)
#             weather_log = result.get("weather_log", [])
#             if weather_log:
#                 df = pd.DataFrame(weather_log)
#                 df["Decision"] = df["skipped"].map({True: "Skipped", False: "Selected"})
#                 df = df.rename(columns={
#                     "city": "City",
#                     "temperature": "Temp (°C)",
#                     "condition": "Condition"
#                 })[["City", "Temp (°C)", "Condition", "Decision"]]
#                 st.dataframe(df)
#             else:
#                 st.write("No weather log available.")

#             st.markdown("<p class='section-title'>Suggested Itinerary</p>", unsafe_allow_html=True)
#             st.text(result.get("itinerary", "No itinerary generated."))

#             st.markdown("<p class='section-title'>Cultural Tips</p>", unsafe_allow_html=True)
#             st.write(result.get("culture_tips", "No cultural information available."))

#             st.markdown("<p class='section-title'>Packing List</p>", unsafe_allow_html=True)
#             st.text(result.get("packing_list", "No packing list generated."))
#         else:
#             st.error("Something went wrong — no result returned.")

import torch
if not hasattr(torch, "__path__"):
    torch.__path__ = []
import streamlit as st
import pandas as pd
import time
import threading
import queue
import matplotlib.pyplot as plt
import networkx as nx
import plotly.graph_objects as go
from logger import log, log_queue
from langgraph_setup.run_graph import run_trip_planner

# Page setup
st.set_page_config(page_title="Nomads Nest", layout="wide")

# ---- CSS for Pastel Theme ----
st.markdown("""
    <style>
        .pill {
            display: inline-block;
            padding: 0.4em 0.9em;
            border-radius: 30px;
            margin: 4px 6px;
            font-size: 0.9em;
            font-weight: 500;
            color: white;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }
        .log-box {
            background-color: #e8f5e9;
            border: 1px solid #c8e6c9;
            border-radius: 10px;
            padding: 12px;
            font-family: monospace;
            white-space: pre-wrap;
            height: 200px;
            overflow-y: auto;
        }
        .current-step-box {
            height: 100px;
        }
        .title {
            text-align: center;
            font-size: 40px;
            font-weight: bold;
            color: #388e3c;
        }
        .section-title {
            font-size: 24px;
            font-weight: bold;
            color: #388e3c;
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# ---- Category Definitions ----
CATEGORY_COLORS = {
    "Experience": "#FF7F50", "Nature": "#2ECC71", "Luxury & Budget": "#FFD700",
    "Interests": "#6A5ACD", "Audience": "#FF69B4"
}
CATEGORY_GROUPS = {
    "Experience": ["relaxation", "adventure", "cultural immersion", "spiritual retreat", "learning", "road trip"],
    "Nature": ["mountains", "beach", "jungle", "desert", "wildlife", "national parks"],
    "Luxury & Budget": ["luxury", "budget", "all-inclusive", "backpacking"],
    "Interests": ["food", "history", "architecture", "nightlife", "shopping", "festivals", "art"],
    "Audience": ["solo travel", "family-friendly", "romantic", "group travel"]
}
def get_category(label):
    for category, items in CATEGORY_GROUPS.items():
        if label in items:
            return category
    return "Interests"

def display_colored_preferences(preferences):
    st.markdown("<p class='section-title'>Your Travel Preferences</p>", unsafe_allow_html=True)
    html_pills = ""
    for pref in preferences:
        category = get_category(pref)
        color = CATEGORY_COLORS.get(category, "#888888")
        html_pills += f"<span class='pill' style='background-color:{color}'>{pref}</span>"
    st.markdown(html_pills, unsafe_allow_html=True)

def render_weather_table(weather_log):
    if not weather_log:
        st.info("No weather data available.")
        return

    df = pd.DataFrame(weather_log)
    df["Decision"] = df["skipped"].map({True: "Skipped", False: "Selected"})
    df = df.rename(columns={"city": "City", "temperature": "Temp (°C)", "condition": "Condition"})[
        ["City", "Temp (°C)", "Condition", "Decision"]
    ]

    fig = go.Figure(data=[go.Table(
        columnwidth=[80, 80, 120, 80],
        header=dict(values=list(df.columns),
                    fill_color='#a5d6a7',
                    align='center',
                    font=dict(color='black', size=14)),
        cells=dict(values=[df[col] for col in df.columns],
                   fill_color=[['#ffffff' if i % 2 == 0 else '#f0f4f7'] * len(df) for i in range(len(df.columns))],
                   align='center',
                   font=dict(color='black', size=12))
    )])
    fig.update_layout(margin=dict(l=5, r=5, t=5, b=0))
    st.markdown("<p class='section-title'>Weather Insights</p>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("<div style='margin-top: -15px;'></div>", unsafe_allow_html=True)

# ---- Header ----
st.markdown("<p class='title'>Nomads Nest</p>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 18px;'>Let us take you to your next adventure</div>", unsafe_allow_html=True)

# ---- Layout ----
left_col, middle_col, right_col = st.columns([1.5, 2, 1.5], gap="large")

with left_col:
    st.markdown("<p class='section-title'>Current Step</p>", unsafe_allow_html=True)
    current_step_log = st.empty()
    st.markdown("<p class='section-title'>Activity Log</p>", unsafe_allow_html=True)
    activity_log = st.empty()

with middle_col:
    st.markdown("<p class='section-title'>What’s Your Next Destination?</p>", unsafe_allow_html=True)
    user_input = st.text_area("Trip preferences", placeholder="....", height=150, label_visibility="collapsed")
    start_button = st.button("Let’s Plan")

with right_col:
    st.markdown("<p class='section-title'>AI Agent Graph</p>", unsafe_allow_html=True)
    G = nx.DiGraph()
    agents = ["analyze_persona", "recommend_destinations", "check_weather", "generate_itinerary", "provide_cultural_tips", "generate_packing_list", "fail"]
    G.add_nodes_from(agents)
    G.add_edge("analyze_persona", "recommend_destinations")
    G.add_edge("recommend_destinations", "check_weather")
    G.add_edge("check_weather", "generate_itinerary")
    G.add_edge("generate_itinerary", "provide_cultural_tips")
    G.add_edge("provide_cultural_tips", "generate_packing_list")
    G.add_edge("fail", "provide_cultural_tips")

    fig, ax = plt.subplots(figsize=(10, 8))  # Corrected here
    pos = nx.spring_layout(G, seed=42)
    nx.draw(
        G, pos, ax=ax, with_labels=True,
        node_size=3000, node_color="#a5d6a7",
        font_size=10, font_weight='bold',
        edge_color="#388e3c", width=2, arrows=True
    )
    st.pyplot(fig)


# ---- Process on Button ----
if start_button:
    if not user_input.strip():
        st.warning("Please describe your trip preferences before generating a plan.")
    else:
        logs = []
        result_container = {"result": None}

        with st.spinner("Planning your adventure..."):
            def run_graph():
                result_container["result"] = run_trip_planner(user_input)

            thread = threading.Thread(target=run_graph)
            thread.start()

            last_log_time = time.time()
            while thread.is_alive() or not log_queue.empty():
                try:
                    msg = log_queue.get(timeout=0.2)
                    logs.append(msg)
                    current_step_log.markdown(f'<div class="log-box current-step-box">{msg}</div>', unsafe_allow_html=True)
                    activity_log.markdown(f'<div class="log-box">{"<br>".join(logs)}</div>', unsafe_allow_html=True)
                    last_log_time = time.time()
                except queue.Empty:
                    if time.time() - last_log_time > 2 and not thread.is_alive():
                        break
                    time.sleep(0.1)
            thread.join()
            result = result_container["result"]

        # ---- Display Result ----
        if result:
            st.success("Here’s your personalized trip plan!")
            display_colored_preferences(result.get("persona", []))

            st.markdown(f"<p class='section-title'>Final Pick: {result.get('top_destination', 'No destination')}</p>", unsafe_allow_html=True)
            render_weather_table(result.get("weather_log", []))

            st.markdown("<p class='section-title'>Suggested Itinerary</p>", unsafe_allow_html=True)
            itinerary = result.get("itinerary", "")
            if itinerary:
                itinerary_lines = [line.strip("-• ") for line in itinerary.strip().split("\n") if line.strip()]
                for item in itinerary_lines:
                    st.markdown(f"- {item}")
            else:
                st.info("No itinerary generated.")

            st.markdown("<p class='section-title'>Cultural Tips</p>", unsafe_allow_html=True)
            culture_tips = result.get("culture_tips", "")
            if culture_tips:
                culture_lines = [line.strip("-• ") for line in culture_tips.strip().split("\n") if line.strip()]
                for tip in culture_lines:
                    st.markdown(f"- {tip}")
            else:
                st.info("No cultural information available.")

            st.markdown("<p class='section-title'>Packing List</p>", unsafe_allow_html=True)
            packing_list = result.get("packing_list", "")
            if packing_list:
                lines = [line.strip() for line in packing_list.split("\n") if line.strip()]
                has_colon = any(":" in line for line in lines)

                if has_colon:
                    for line in lines:
                        try:
                            category, items = line.split(":", 1)
                            category = category.strip()
                            items = [item.strip() for item in items.split(",") if item.strip()]
                            with st.container():
                                st.markdown(f"""
                                    <div style="background-color:#f1f8e9; border: 1px solid #c5e1a5; border-radius: 10px; padding: 15px; margin: 10px 0;">
                                        <strong>{category}</strong><br>
                                        {"<br>".join(f"• {item}" for item in items)}
                                    </div>
                                """, unsafe_allow_html=True)
                        except ValueError:
                            st.warning(f"Skipping malformed line: {line}")
                else:
                    with st.container():
                        st.markdown(f"""
                            <div style="background-color:#f1f8e9; border: 1px solid #c5e1a5; border-radius: 10px; padding: 15px; margin: 10px 0;">
                                <strong>Items to Pack</strong><br>
                                {"<br>".join(f"• {item}" for item in lines)}
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No packing list generated.")
        else:
            st.error("Something went wrong — no result returned.")