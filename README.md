# ✈️ Nomads Nest - Agentic Travel Buddy

Nomads Nest is a **multi-agent travel assistant** that intelligently understands user preferences and suggests top destinations tailored to their tastes. It evaluates weather conditions, plans detailed itineraries, provides cultural insights, and even generates a personalized packing list — all automatically. 🌍✈️

### 🎬 Video Demo 
https://www.youtube.com/watch?v=7fO3230ZSuw 
## 👥 Team members
- **Anmol Munnolli** 👨‍💻
- **Vishwajyothi Reshmi** 👩‍💻
- **Madhumitha Gannavaram** 👩‍💻

## 💡 Architecture

The architecture consists of:

### UI/UX Design 🎨
- **Streamlit** (Python-based web app) to interact with users.

### Backend Design🔧
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
```bash
.\\env\Scripts\activate
```
### **3. Install Dependencies**
- Install the required packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```
### **4. Set Up Environment Variables**
- Copy `.env.example` to `.env` and add your own [Hugging Face token](https://huggingface.co/settings/tokens):
```bash
cp .env.example .env
```
- `.env` is gitignored — never commit your token.

### **5. Run the Backend**
- After setting up the virtual environment and installing the dependencies, run the `agent_controller.py` file.

### **6. Run the Frontend**
- To start the frontend using Streamlit, run the `app.py` file:
```bash
streamlit run app.py
```
