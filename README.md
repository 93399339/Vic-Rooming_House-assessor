# 🏗️ Vic Rooming House Assessor

A web-based interactive tool to assess the suitability of a Victorian site for a compliant Rooming House under the **Future Homes** planning framework and **2025–2030 regulatory standards**.

![App Screenshot](https://github.com/user-attachments/assets/820a33f3-d7be-408c-b58a-3721c243cbe0)

## Features

- **Traffic-light viability score** — GREEN / AMBER / RED based on zone, transport access, lot size and overlays
- **Interactive Folium map** — 800 m transport catchment visualised around the site
- **Compliance checklist** — Dec 2025 (heating, blind cords) and 2030 (all-electric) requirements
- **Physical metrics** — lot width and area checked against minimum thresholds

## Quickstart

### Option 1 – GitHub Codespaces (recommended, zero setup)

Click **Code → Codespaces → Create codespace on main**.  
The dev container installs all dependencies and launches the app automatically on port **8501**, which Codespaces forwards and opens as a browser preview.

### Option 2 – Run locally

```bash
# 1. Clone the repo
git clone https://github.com/93399339/Vic-Rooming_House-assessor.git
cd Vic-Rooming_House-assessor

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
streamlit run app.py
```

Open <http://localhost:8501> in your browser.

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | UI framework |
| `folium` | Interactive map |
| `streamlit-folium` | Embed Folium maps in Streamlit |
| `pandas` | Data handling |
