"""
Simple authentication for UR Happy Home team.
Supports 5 team member logins with session management.
"""

import streamlit as st
from typing import Optional, Dict

# Hard­coded team credentials (in production, use a proper auth system)
TEAM_CREDENTIALS = {
    "team1@urhappyhome.com": {"password": "urh_team_1", "name": "Team Lead"},
    "assessor1@urhappyhome.com": {"password": "urh_assessor_1", "name": "Assessor 1"},
    "assessor2@urhappyhome.com": {"password": "urh_assessor_2", "name": "Assessor 2"},
    "analyst@urhappyhome.com": {"password": "urh_analyst_1", "name": "Data Analyst"},
    "admin@urhappyhome.com": {"password": "urh_admin_1", "name": "Administrator"},
}

def verify_credentials(email: str, password: str) -> Optional[Dict]:
    """Verify team member credentials."""
    user = TEAM_CREDENTIALS.get(email)
    if user and user["password"] == password:
        return {"email": email, "name": user["name"]}
    return None


def init_auth_session():
    """Initialize session state for authentication."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None


def show_login_page():
    """Display login interface."""
    st.set_page_config(page_title="UR Happy Home - Login", page_icon="🏠", layout="centered")
    
    # Logo and branding
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("assets/ur_happy_home_logo.png", width=200) if False else st.markdown(
            "<h1 style='text-align: center; color: #1F7F4C;'>🏠 UR Happy Home</h1>",
            unsafe_allow_html=True
        )
    
    st.markdown("<h2 style='text-align: center;'>Site Assessment Tool</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Identify suitable rooming house development sites</p>", unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@urhappyhome.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            
            if submit:
                if not email or not password:
                    st.error("Please enter both email and password")
                else:
                    user = verify_credentials(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success(f"Welcome, {user['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
    
    st.markdown("---")
    st.markdown("""
    <p style='text-align: center; font-size: 0.8em; color: #999;'>
    <strong>Demo Credentials:</strong><br>
    admin@urhappyhome.com / urh_admin_1
    </p>
    """, unsafe_allow_html=True)


def check_authentication():
    """Check if user is authenticated; redirect to login if not."""
    init_auth_session()
    if not st.session_state.authenticated:
        show_login_page()
        st.stop()


def show_logout_button():
    """Display logout button in sidebar."""
    if st.session_state.get("authenticated"):
        user = st.session_state.get("user", {})
        with st.sidebar:
            st.markdown(f"**User:** {user.get('name', 'Unknown')}")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.rerun()
