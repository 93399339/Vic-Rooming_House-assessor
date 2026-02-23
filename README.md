# Vic-Rooming_House-assessor

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/93399339/Vic-Rooming_House-assessor)

Web based Rooming House interactive map assessment

## Accessing the App

### GitHub Codespaces (Recommended — no local install needed)

1. Click the **Open in GitHub Codespaces** badge above, or click the green **Code** button → **Codespaces** tab → **Create codespace on main**.
2. Wait for the dev container to build and install packages (this takes a minute or two).
3. The app starts automatically and the browser opens to the forwarded port URL.

**Finding the port link manually:**

If the browser doesn't open automatically, locate the live URL in the **Ports** tab:

- In VS Code (Codespaces): click the **Ports** tab in the bottom panel. Find the row labelled **Application** (port `8501`) and click the 🌐 globe icon or the URL under **Forwarded Address**.
- The URL has the form:
  ```
  https://<your-codespace-name>-8501.app.github.dev
  ```
  Copy and paste it into any browser to access the app.

> **Tip:** Make sure the port visibility is set to **Public** (right-click the port row → *Port Visibility → Public*) if you want to share the link with others.

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```
3. Open **<http://localhost:8501>** in your browser.
