"""
Map-First Layout Components for UR Happy Home Assessor
Implements Archistar.ai-inspired UI with map background and collapsible panels
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import Tuple, Dict, Optional, Callable, List


# ============================================================================
# ARCHISTAR GLASSMORPHISM THEME
# ============================================================================

ARCHISTAR_GLASSMORPHISM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ================================================================
       CRITICAL: Force Dark Background Everywhere
       ================================================================ */
    
    html, body, main, [role="main"], div[class*="stApp"], div[class*="appViewContainer"] {
        background: #0F1419 !important;
        background-color: #0F1419 !important;
    }
    
    .stApp {
        background: #0F1419 !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background: #0F1419 !important;
    }
    
    /* ================================================================
       CSS VARIABLES
       ================================================================ */
    
    :root {
        --color-primary: #1F7F4C;
        --color-primary-dark: #0E3A20;
        --color-secondary: #2E5C4A;
        --color-accent: #D4A574;
        --color-success: #27AE60;
        --color-warning: #F39C12;
        --color-danger: #E74C3C;
        --color-bg-dark: #0F1419;
        --color-bg-secondary: #1A1F28;
        --color-bg-tertiary: #252D38;
        --color-text-primary: #E8EAED;
        --color-text-secondary: #9AA0A6;
        --color-border: #3F4658;
    }
    
    /* ================================================================
       GLOBAL TEXT COLOR
       ================================================================ */
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        color: #E8EAED !important;
    }
    
    /* ================================================================
       SIDEBAR GLASSMORPHISM - CRITICAL
       ================================================================ */
    
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, rgba(15, 20, 25, 0.95), rgba(26, 31, 40, 0.9)) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 2px solid rgba(31, 127, 76, 0.3) !important;
        box-shadow: inset 0 0 60px rgba(31, 127, 76, 0.1) !important;
    }
    
    /* ================================================================
       ALL CONTAINERS - GLASSMORPHISM
       ================================================================ */
    
    /* Target all block-level containers */
    div[data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"],
    div[class*="element-container"],
    div[class*="stBlock"] {
        background: linear-gradient(135deg, rgba(37, 45, 56, 0.8), rgba(26, 31, 40, 0.7)) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(31, 127, 76, 0.25) !important;
        border-radius: 14px !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    div[data-testid="stVerticalBlock"]:hover,
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        background: linear-gradient(135deg, rgba(37, 45, 56, 1), rgba(26, 31, 40, 0.95)) !important;
        border-color: rgba(31, 127, 76, 0.5) !important;
        box-shadow: 0 15px 60px rgba(31, 127, 76, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Glass card styling */
    .glass-card {
        background: rgba(37, 45, 56, 0.65) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(232, 234, 237, 0.12) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    }
    
    /* ================================================================
       FORM ELEMENTS WITH GLASSMORPHISM
       ================================================================ */
    
    input[type="text"], input[type="email"], input[type="number"], input[type="password"],
    textarea, select, [data-testid="stSelectbox"], [data-testid="stMultiSelect"], [data-testid="stNumberInput"] {
        background: rgba(37, 45, 56, 0.7) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        border: 1px solid rgba(63, 70, 88, 0.5) !important;
        color: #E8EAED !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    input[type="text"]:focus, input[type="email"]:focus, input[type="number"]:focus, input[type="password"]:focus,
    textarea:focus, select:focus {
        background: rgba(37, 45, 56, 0.9) !important;
        border-color: rgba(31, 127, 76, 0.7) !important;
        box-shadow: 0 0 0 3px rgba(31, 127, 76, 0.2) !important;
        outline: none !important;
    }
    
    /* ================================================================
       BUTTONS
       ================================================================ */
    
    .stButton > button {
        background: linear-gradient(135deg, #1F7F4C, #0E3A20) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        box-shadow: 0 4px 15px rgba(31, 127, 76, 0.25);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--color-success), var(--color-primary)) !important;
        box-shadow: 0 8px 25px rgba(31, 127, 76, 0.4);
        transform: translateY(-2px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 10px rgba(31, 127, 76, 0.2);
    }
    
    /* Metric cards */
    [data-testid="stMetricContainer"] {
        background: rgba(37, 45, 56, 0.4) !important;
        backdrop-filter: blur(6px) !important;
        border: 1px solid rgba(63, 70, 88, 0.3) !important;
        border-radius: 10px !important;
        padding: 1.25rem !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetricContainer"]:hover {
        background: rgba(37, 45, 56, 0.6) !important;
        border-color: rgba(31, 127, 76, 0.4) !important;
        transform: translateY(-2px);
    }
    
    /* ================================================================
       CRITICAL: Form Elements and Inputs
       ================================================================ */
    
    /* All input types */
    input {
        background: rgba(37, 45, 56, 0.85) !important;
        color: #E8EAED !important;
        border: 1px solid rgba(31, 127, 76, 0.4) !important;
        border-radius: 8px !important;
    }
    
    input:focus {
        border-color: rgba(31, 127, 76, 0.8) !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(31, 127, 76, 0.2) !important;
    }
    
    /* Selectbox and multiselect */
    [role="listbox"],
    [role="combobox"],
    div[data-testid*="Select"] {
        background: rgba(37, 45, 56, 0.85) !important;
        border: 1px solid rgba(31, 127, 76, 0.4) !important;
    }
    
    /* ================================================================
       METRIC BOXES - Make them visible with glassmorphism
       ================================================================ */
    
    [data-testid="stMetricContainer"],
    div[class*="metric"] {
        background: linear-gradient(135deg, rgba(37, 45, 56, 0.9), rgba(26, 31, 40, 0.8)) !important;
        border: 1px solid rgba(31, 127, 76, 0.3) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(31, 127, 76, 0.2) !important;
    }
    
    /* ================================================================
       DIVIDERS
       ================================================================ */
    
    hr, [role="separator"], [data-testid="stVerticalBlockBorderWrapper"] hr {
        border-color: rgba(31, 127, 76, 0.3) !important;
        opacity: 0.5;
    }
    
    /* ================================================================
       EXPANDERS and TABS
       ================================================================ */
    
    [data-testid="stExpanderDetails"],
    details {
        background: rgba(37, 45, 56, 0.8) !important;
        border: 1px solid rgba(31, 127, 76, 0.25) !important;
        border-radius: 10px !important;
    }
    
    [data-testid="stTabs"] {
        background: transparent !important;
    }
    
    /* ================================================================
       ALERTS and NOTIFICATIONS
       ================================================================ */
    
    [data-testid="stAlert"],
    .alert {
        background: rgba(37, 45, 56, 0.9) !important;
        border: 1px solid rgba(31, 127, 76, 0.3) !important;
        border-left: 4px solid #1F7F4C !important;
        border-radius: 8px !important;
    }
    
    /* ================================================================
       MISC ELEMENTS
       ================================================================ */
    
    /* Image containers */
    img {
        border-radius: 8px;
    }
    
    /* All untyped divs in main content area */
    [data-testid="stAppViewContainer"] > div {
        background: transparent !important;
    }
    
    /* ================================================================
       ANIMATIONS & TRANSITIONS
       ================================================================ */
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(31, 127, 76, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(31, 127, 76, 0); }
        100% { box-shadow: 0 0 0 0 rgba(31, 127, 76, 0); }
    }
    
    .animate-fade-in-up { animation: fadeInUp 0.6s ease-out; }
    .animate-slide-in-right { animation: slideInRight 0.6s ease-out; }
    
    /* ================================================================
       ACCESSIBILITY
       ================================================================ */
    
    button:focus-visible, [role="button"]:focus-visible, a:focus-visible {
        outline: 2px solid #1F7F4C;
        outline-offset: 2px;
    }
    
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
</style>
"""


# ============================================================================
# LAYOUT FUNCTIONS
# ============================================================================

def apply_dark_theme():
    """Apply Archistar glassmorphism dark theme CSS to the application."""
    st.markdown(ARCHISTAR_GLASSMORPHISM_CSS, unsafe_allow_html=True)


def render_left_filter_panel(
    on_address_submit=None,
    on_filter_change=None
) -> Dict:
    """
    Render the left-side collapsible filter panel.
    
    Args:
        on_address_submit: Callback function when address is submitted
        on_filter_change: Callback function when filters change
        
    Returns:
        Dictionary with filter values
    """
    with st.sidebar:
        # Header with logo/title
        st.markdown("### 🏠 UR Happy Home")
        st.markdown("Site Assessment Platform")
        st.divider()
        
        # Address input section
        st.markdown("#### 📍 Site Search")
        address = st.text_input(
            "Address",
            placeholder="123 Example St, Ringwood VIC 3134",
            label_visibility="collapsed",
            help="Enter the site address to begin assessment"
        )
        
        col_search, col_clear = st.columns([3, 1])
        with col_search:
            submit_btn = st.button("🔍 Search", use_container_width=True)
        with col_clear:
            clear_btn = st.button("✕", use_container_width=True)
        
        st.divider()
        
        # Filter section
        st.markdown("#### 🎯 Filters")
        
        filter_status = st.multiselect(
            "Viability Status",
            ["Suitable 🟢", "Conditional 🟡", "Unsuitable 🔴"],
            default=["Suitable 🟢"],
            label_visibility="collapsed"
        )
        
        score_range = st.slider(
            "Minimum Score",
            min_value=0,
            max_value=100,
            value=50,
            step=5
        )
        
        st.divider()
        
        # Portfolio section
        st.markdown("#### 📊 Portfolio")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", "12")
        with col2:
            st.metric("Suitable", "8")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conditional", "2")
        with col2:
            st.metric("Unsuitable", "2")
        
        st.divider()
        
        # Recent assessments
        st.markdown("#### 📋 Recent Sites")
        
        recent_sites = [
            {"name": "123 High Street, Ringwood", "score": 78},
            {"name": "456 Main Road, Croydon", "score": 52},
            {"name": "789 Park Avenue, Thornton", "score": 35},
        ]
        
        for site in recent_sites:
            color = "🟢" if site['score'] >= 75 else "🟡" if site['score'] >= 50 else "🔴"
            if st.button(
                f"{color} {site['name'][:25]}... ({site['score']})",
                key=f"recent_{site['name']}",
                use_container_width=True
            ):
                st.session_state.selected_site = site
        
        st.divider()
        
        # Settings and help
        st.markdown("#### ⚙️ Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Export", use_container_width=True):
                st.session_state.export_portfolio = True
        with col2:
            if st.button("❓ Help", use_container_width=True):
                st.session_state.show_help = True
        
        col1, col2 = st.columns(2)
        with col1:
            show_logout = st.button("🚪 Logout", use_container_width=True)
        with col2:
            st.empty()
        
        return {
            "address": address,
            "submit": submit_btn,
            "clear": clear_btn,
            "filter_status": filter_status,
            "score_range": score_range
        }


def render_right_property_panel(
    property_data: Optional[Dict] = None
) -> None:
    """
    Render the right-side Property Intelligence panel with enhanced visualizations.
    Includes donut charts, progress bars, and micro-interactions.
    
    Args:
        property_data: Dictionary containing property assessment data
    """
    
    if property_data is None:
        property_data = {}
    
    # Panel header
    st.markdown("### 💡 Property Intelligence")
    st.markdown('<div style="height: 1px; background: rgba(63, 70, 88, 0.3); margin: 1rem 0;"></div>', unsafe_allow_html=True)
    
    if not property_data:
        st.info("📍 Select a site on the map or search an address to view property intelligence")
        return
    
    # Address display
    address = property_data.get("address", "N/A")
    display_address = address[:35] + "..." if len(address) > 35 else address
    st.markdown(f"<div style='font-size: 0.9rem; color: #9AA0A6; margin-bottom: 0.5rem;'>ASSESSED PROPERTY</div><div style='font-size: 1.1rem; font-weight: 600;'>{display_address}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Viability score with donut chart
    status = property_data.get("viability_status", "PENDING")
    score = property_data.get("raw_score", 0)
    
    # Status mapping
    status_map = {"HIGHLY SUITABLE": "suitable", "CONDITIONAL": "conditional", "NOT SUITABLE": "unsuitable"}
    status_type = status_map.get(status, "conditional")
    color_icon_map = {"HIGHLY SUITABLE": "🟢", "CONDITIONAL": "🟡", "NOT SUITABLE": "🔴"}
    status_icon = color_icon_map.get(status, "⚪")
    
    # Viability score display
    st.markdown(f"<div style='text-align: center; margin: 1.5rem 0;'><div style='font-size: 0.75rem; font-weight: 600; color: #9AA0A6; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.5rem;'>Viability Score</div></div>", unsafe_allow_html=True)
    
    # Import visualization functions
    from ui.ui_enhancements import render_metric_donut
    render_metric_donut(
        score=score,
        max_score=100,
        label="Overall",
        status=status_type
    )
    
    st.markdown(f"<div style='text-align: center; margin: 1rem 0;'><span style='display: inline-block; padding: 0.75rem 1.25rem; border-radius: 8px; background: rgba(31, 127, 76, 0.15); color: var(--color-success); border: 1px solid rgba(31, 127, 76, 0.4); font-weight: 600; font-size: 0.95rem;'>{status_icon} {status}</span></div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Key metrics with glassmorphism cards
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #9AA0A6; text-transform: uppercase; letter-spacing: 1px; margin: 1rem 0 0.5rem 0;'>Key Metrics</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        zone_score = property_data.get('zone_score', 0)
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1rem;">
            <div class="metric-label">Zone Score</div>
            <div class="metric-value" style="color: #1F7F4C; margin-top: 0.5rem;">{zone_score:.0f}</div>
            <div class="text-muted" style="margin-top: 0.25rem; font-size: 0.75rem;">/ 40</div>
        </div>
        """, unsafe_allow_html=True)
        
        lot_width = property_data.get('lot_width', 0)
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1rem; margin-top: 0.75rem;">
            <div class="metric-label">Lot Width</div>
            <div class="metric-value" style="color: #1F7F4C; margin-top: 0.5rem;">{lot_width:.1f}m</div>
            <div class="text-muted" style="margin-top: 0.25rem; font-size: 0.75rem;">Width</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        transport_score = property_data.get('transport_score', 0)
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1rem;">
            <div class="metric-label">Transport</div>
            <div class="metric-value" style="color: #1F7F4C; margin-top: 0.5rem;">{transport_score:.0f}</div>
            <div class="text-muted" style="margin-top: 0.25rem; font-size: 0.75rem;">/ 25</div>
        </div>
        """, unsafe_allow_html=True)
        
        lot_depth = property_data.get('lot_depth', 0)
        st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 1rem; margin-top: 0.75rem;">
            <div class="metric-label">Lot Depth</div>
            <div class="metric-value" style="color: #1F7F4C; margin-top: 0.5rem;">{lot_depth:.1f}m</div>
            <div class="text-muted" style="margin-top: 0.25rem; font-size: 0.75rem;">Depth</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Score breakdown with progress bars
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #9AA0A6; text-transform: uppercase; letter-spacing: 1px; margin: 1rem 0 0.5rem 0;'>Score Breakdown</div>", unsafe_allow_html=True)
    
    from ui.ui_enhancements import render_progress_bar
    
    render_progress_bar(
        label="Zone Suitability",
        value=property_data.get('zone_score', 0),
        max_value=40,
        status="success"
    )
    
    transport = property_data.get('transport_score', 0)
    transport_status = "success" if transport >= 15 else "warning" if transport >= 10 else "danger"
    render_progress_bar(
        label="Transport Access",
        value=transport,
        max_value=25,
        status=transport_status
    )
    
    physical = property_data.get('physical_score', 0)
    physical_status = "success" if physical >= 15 else "warning" if physical >= 10 else "danger"
    render_progress_bar(
        label="Physical Suitability",
        value=physical,
        max_value=25,
        status=physical_status
    )
    
    compliance = property_data.get('compliance_score', 0)
    compliance_status = "success" if compliance >= 7 else "warning" if compliance >= 5 else "danger"
    render_progress_bar(
        label="Regulatory Compliance",
        value=compliance,
        max_value=10,
        status=compliance_status
    )
    
    st.divider()
    
    # Zone information
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #9AA0A6; text-transform: uppercase; letter-spacing: 1px; margin: 1rem 0 0.5rem 0;'>Zone & Planning</div>", unsafe_allow_html=True)
    
    zone_type = property_data.get('zone_type', 'N/A')
    has_overlay = property_data.get('has_overlay', False)
    
    overlay_badge = '<span style="color: #E74C3C; font-weight: 600;">⚠️ Yes</span>' if has_overlay else '<span style="color: #27AE60; font-weight: 600;">✓ No</span>'
    
    st.markdown(f"""
    <div class="glass-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span class="text-secondary">Zone Type</span>
            <span style="font-weight: 600;">{zone_type}</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="text-secondary">Planning Overlays</span>
            {overlay_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Action buttons with enhanced styling
    st.markdown("<div style='font-size: 0.75rem; font-weight: 600; color: #9AA0A6; text-transform: uppercase; letter-spacing: 1px; margin: 1rem 0 0.75rem 0;'>Actions</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Generate Report", use_container_width=True, key="gen_report"):
            st.session_state.generate_report = True
    with col2:
        if st.button("💾 Save", use_container_width=True, key="save_prop"):
            st.session_state.save_assessment = True
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Compare", use_container_width=True, key="compare_prop"):
            st.session_state.compare_mode = True
    with col2:
        if st.button("🗺️ Location", use_container_width=True, key="open_location"):
            st.session_state.open_location = True


def create_map_first_layout():
    """
    Create the complete map-first layout with all panels.
    """
    
    # Create a container for the main layout
    # Left panel will be the traditional sidebar
    # Center will be the map
    # Right panel will be created via columns
    
    apply_dark_theme()
    
    # Left filter panel
    filter_panel = render_left_filter_panel()
    
    # Main content area - map + right panel
    main_col1, main_col2 = st.columns([4, 1], gap="small")
    
    with main_col1:
        st.markdown("### Interactive Site Map")
        # Map will be rendered here by parent component
        map_placeholder = st.empty()
    
    with main_col2:
        # Right property intelligence panel
        property_data = st.session_state.get('property_data', None)
        render_right_property_panel(property_data)
    
    return {
        "filter_panel": filter_panel,
        "map_placeholder": map_placeholder,
        "layout": "map-first"
    }


def render_card_grid(card_renderers: List[Callable[[], None]], cards_per_row: int = 3) -> None:
    """
    Render content cards in a clean row grid.

    Args:
        card_renderers: List of no-arg callables that render each card.
        cards_per_row: Number of cards to render per row.
    """
    if not card_renderers:
        return

    cards_per_row = max(1, int(cards_per_row or 3))

    for idx in range(0, len(card_renderers), cards_per_row):
        row_cards = card_renderers[idx: idx + cards_per_row]
        cols = st.columns(cards_per_row, gap="small")
        for col_index, renderer in enumerate(row_cards):
            with cols[col_index]:
                renderer()
        if idx + cards_per_row < len(card_renderers):
            st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)


def render_map_with_context(
    latitude: float,
    longitude: float,
    address: str,
    viability_color: str = "gray",
    zone_type: str = "",
    has_overlay: bool = False,
    lot_width: float = 0,
    lot_depth: float = 0
) -> folium.Map:
    """
    Create and render an interactive map with proper styling.
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        address: Site address
        viability_color: Color indicating viability (green/orange/red)
        zone_type: Planning zone type
        has_overlay: Whether site has planning overlays
        lot_width: Lot width in meters
        lot_depth: Lot depth in meters
        
    Returns:
        Folium map object
    """
    
    # Import advanced_map functions
    from ui.advanced_map import create_advanced_map
    
    # Create the advanced map
    m, poi_data = create_advanced_map(
        latitude=latitude,
        longitude=longitude,
        address=address,
        viability_color=viability_color,
        map_type="OpenStreetMap",
        zone_type=zone_type,
        has_overlay=has_overlay
    )
    
    return m, poi_data
