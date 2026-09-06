# ✈️ Multi-Agent Travel Planner

A **multi-agent travel assistant** that intelligently understands user preferences and suggests top destinations tailored to their tastes. It evaluates weather conditions, plans detailed itineraries, provides cultural insights, and even generates a personalized packing list — all automatically. 🌍✈️

### 🎬 Video Demo
https://www.youtube.com/watch?v=7fO3230ZSuw

## 💡 Architecture

The architecture consists of:

### UI/UX Design 🎨
- **Streamlit** (Python-based web app) to interact with users.

### Backend Design 🔧
- **Agents** powered by **Hugging Face**, **LangGraph** for agent communication and logic flow.

### Agents:
- **Persona Agent** 👤: Handles user preferences, budget, interests.
- **Destination Agent** 🌍: Recommends travel destinations based on persona.
- **Itinerary Agent** 🗓️: Suggests travel itineraries based on destination.
- **Culture Agent** 🍲: Provides insights into local culture, food, etc.
- **Packing Agent** 🧳: Helps users decide what to pack.
- **Weather Agent** 🌦️: Checks weather conditions and provides feedback on destinations.

## 🛠️ How to Run the Project

### **1. Create a Virtual Environment**
```bash
python -m venv venv
```

### **2. Activate the Virtual Environment**
macOS / Linux:
```bash
source venv/bin/activate
```
Windows:
```bash
venv\Scripts\activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Set Up Environment Variables**
Copy `.env.example` to `.env` and add your own [Hugging Face token](https://huggingface.co/settings/tokens):
```bash
cp .env.example .env
```
`.env` is gitignored — never commit your token.

### **5. Run the Backend**
The modules import each other by top-level name, so run from inside `nomads_nest/`:
```bash
cd nomads_nest
python -m langchain_agents.agent_controller
```

### **6. Run the Frontend**
From the same `nomads_nest/` directory:
```bash
streamlit run app.py
```
