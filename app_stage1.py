"""
UR Happy Home - Site Assessor
Map-First Layout Architecture (Stage 1)
Implements Archistar.ai-inspired UI with full-screen interactive map

This is the refactored main application entry point.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
import time

# ============================================================================
# IMPORTS - CUSTOM MODULES
# ============================================================================

from core.database import (
    init_database, save_assessment, get_recent_assessments, 
    get_assessment, delete_assessment, get_statistics
)
from core.scoring import calculate_weighted_score, get_viability_status_from_score, detailed_score_breakdown
from pdf_generator import generate_pdf_report
from professional_pdf_generator import create_professional_pdf_report
from ui.advanced_map import create_advanced_map, get_nearby_summary
from ui.interactive_map_enhanced import create_professional_interactive_map
from core.data_fetcher import auto_assess_from_address
from simple_auth import check_authentication, show_logout_button
from core.vicgis_wfs_lookup import auto_fill_from_vicgis
from portfolio_utils import get_portfolio_stats, filter_by_viability
from core.cost_estimator import estimate_project_total
from excel_exporter import generate_excel_report
from ui.ui_enhancements import apply_professional_styling, apply_dark_theme_styling
from ui.map_first_layout import render_left_filter_panel, render_right_property_panel
from config import get_maps_api_key, has_maps_api_key, log_config_status

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="UR Happy Home - Site Assessor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZATION & SETUP
# ============================================================================

# Authentication
check_authentication()

# Database
init_database()

# Apply dark theme (Stage 1 UI)
apply_dark_theme_styling()

# ============================================================================
# SESSION STATE
# ============================================================================

if 'assessment_complete' not in st.session_state:
    st.session_state.assessment_complete = False
if 'last_address' not in st.session_state:
    st.session_state.last_address = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None
if 'assessment_id' not in st.session_state:
    st.session_state.assessment_id = None
if 'assessment_data' not in st.session_state:
    st.session_state.assessment_data = {}
if 'property_data' not in st.session_state:
    st.session_state.property_data = None
if 'map_mode' not in st.session_state:
    st.session_state.map_mode = "search"

# ============================================================================
# GEOCODING SETUP
# ============================================================================

@st.cache_resource
def get_geocoder():
    """Initialize geocoder with caching"""
    return Nominatim(user_agent="vic_rooming_house_assessor")


def geocode_address(address):
    """Geocode an address and return lat, lon"""
    try:
        geocoder = get_geocoder()
        location = geocoder.geocode(address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            st.error(f"Could not find coordinates for: {address}")
            return None, None
    except Exception as e:
        st.error(f"Geocoding error: {e}")
        return None, None


# ============================================================================
# MAIN LAYOUT - MAP-FIRST ARCHITECTURE
# ============================================================================

# Left sidebar filter panel
with st.sidebar:
    st.markdown("### 🏠 UR Happy Home")
    st.markdown("**Site Assessment Platform**")
    st.divider()
    
    # Configuration status
    if has_maps_api_key():
        st.success("✅ Maps API configured")
    else:
        st.info("ℹ️ Using OpenStreetMap (free tiles)")
    
    st.divider()
    
    # Address search section
    st.markdown("#### 📍 Site Search")
    search_address = st.text_input(
        "Address",
        placeholder="123 Example St, Ringwood VIC 3134",
        label_visibility="collapsed",
    )
    
    col_search, col_clear = st.columns([3, 1])
    with col_search:
        search_btn = st.button("🔍 Search", use_container_width=True)
    with col_clear:
        clear_btn = st.button("✕ Clear", use_container_width=True)
    
    if clear_btn:
        st.session_state.last_address = None
        st.session_state.last_coords = None
        st.session_state.assessment_data = {}
        st.session_state.property_data = None
        st.rerun()
    
    st.divider()
    
    # Quick filter section
    st.markdown("#### 🎯 Filters")
    
    filter_status = st.multiselect(
        "Viability",
        ["Suitable 🟢", "Conditional 🟡", "Unsuitable 🔴"],
        default=["Suitable 🟢"],
        label_visibility="collapsed"
    )
    
    min_score = st.slider(
        "Min Score",
        min_value=0,
        max_value=100,
        value=50,
        step=5,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    # Portfolio stats
    st.markdown("#### 📊 Portfolio")
    stats = get_portfolio_stats()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", stats.get('total_assessments', 0))
        st.metric("Conditional", stats.get('conditional_count', 0))
    with col2:
        st.metric("Suitable", stats.get('suitable_count', 0))
        st.metric("Unsuitable", stats.get('unsuitable_count', 0))
    
    st.divider()
    
    # Recent assessments
    st.markdown("#### 📋 Recent Sites")
    recent = get_recent_assessments(limit=5)
    
    if recent:
        for assessment in recent:
            color_map = {'green': '🟢', 'orange': '🟡', 'red': '🔴'}
            status_icon = color_map.get(assessment['viability_color'], '⚪')
            
            if st.button(
                f"{status_icon} {assessment['address'][:22]}... ({assessment['raw_score']:.0f})",
                key=f"load_{assessment['id']}",
                use_container_width=True,
                help=assessment['address']
            ):
                st.session_state.assessment_id = assessment['id']
                loaded = get_assessment(assessment['id'])
                if loaded:
                    st.session_state.last_address = loaded['address']
                    st.session_state.last_coords = (loaded['latitude'], loaded['longitude'])
                    st.session_state.assessment_data = loaded
                    st.session_state.property_data = loaded
                    st.rerun()
    else:
        st.info("No assessments yet")
    
    st.divider()
    
    # Export and settings
    st.markdown("#### ⚙️ Options")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 Export", use_container_width=True):
            st.session_state.export_portfolio = True
    with col2:
        if st.button("❓ Help", use_container_width=True):
            st.session_state.show_help = True


# ============================================================================
# MAIN CONTENT AREA - MAP + RIGHT PANEL
# ============================================================================

# Create main layout: map (4 cols) + right panel (1 col) + spacing
main_cols = st.columns([4, 0.05, 1], gap="small")

with main_cols[0]:  # Map area
    st.markdown("### 🗺️ Interactive Site Map")
    
    # Address search handling
    if search_btn and search_address:
        st.session_state.last_address = search_address
        lat, lon = geocode_address(search_address)
        if lat and lon:
            st.session_state.last_coords = (lat, lon)
            
            # Auto-assess the location
            with st.spinner("🔍 Analyzing site..."):
                try:
                    assessment_data = auto_assess_from_address(search_address, lat, lon)
                    st.session_state.assessment_data = assessment_data
                    
                    # Calculate score
                    score = calculate_weighted_score(assessment_data)
                    viability = get_viability_status_from_score(score)
                    
                    assessment_data['raw_score'] = score
                    assessment_data['viability_status'] = viability['status']
                    assessment_data['viability_color'] = viability['color']
                    
                    st.session_state.property_data = assessment_data
                    st.session_state.assessment_complete = True
                    
                except Exception as e:
                    st.error(f"Assessment error: {str(e)[:100]}")
            
            st.rerun()
    
    # Render map
    if st.session_state.last_coords:
        lat, lon = st.session_state.last_coords
        address_display = st.session_state.last_address or "Site"
        
        assessment_data = st.session_state.assessment_data or {}
        viability_color = assessment_data.get('viability_color', 'gray')
        zone_type = assessment_data.get('zone_type', '')
        has_overlay = assessment_data.get('has_overlay', False)
        
        # Create map
        try:
            m, poi_data = create_advanced_map(
                latitude=lat,
                longitude=lon,
                address=address_display,
                viability_color=viability_color,
                zone_type=zone_type,
                has_overlay=has_overlay
            )
            
            # Display map with Streamlit
            map_data = st_folium(m, width=1400, height=700)
            
        except Exception as e:
            st.error(f"Map rendering error: {str(e)[:100]}")
    else:
        # Show placeholder map
        placeholder_map = folium.Map(
            location=[-37.8136, 144.9631],
            zoom_start=12,
            tiles="OpenStreetMap"
        )
        
        # Add instruction marker
        folium.Marker(
            location=[-37.8136, 144.9631],
            popup="Search for a site address to begin",
            tooltip="Enter an address in the left panel"
        ).add_to(placeholder_map)
        
        map_data = st_folium(placeholder_map, width=1400, height=700)
        
        st.info("👈 Enter a site address in the left panel to begin")

with main_cols[1]:  # Spacer
    st.empty()

with main_cols[2]:  # Right panel - Property Intelligence
    st.markdown("### 💡 Property Intel")
    
    if st.session_state.property_data:
        property_data = st.session_state.property_data
        
        # Address
        address = property_data.get('address', 'N/A')
        st.markdown(f"📍 **{address[:30]}**" if len(address) > 30 else f"📍 **{address}**")
        
        st.divider()
        
        # Score and status
        score = property_data.get('raw_score', 0)
        status = property_data.get('viability_status', 'PENDING')
        color = property_data.get('viability_color', 'gray')
        
        color_map = {'green': '🟢', 'orange': '🟡', 'red': '🔴', 'gray': '⚪'}
        status_icon = color_map.get(color, '⚪')
        
        st.markdown(f"### {status_icon} {status}")
        st.metric("Score", f"{score:.0f}/100")
        
        st.divider()
        
        # Key metrics
        st.markdown("**Key Metrics**")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Zone", property_data.get('zone_type', 'N/A')[:10])
            st.metric("Width", f"{property_data.get('lot_width', 0):.1f}m")
        with col2:
            overlay_text = "Yes ⚠️" if property_data.get('has_overlay') else "No ✓"
            st.metric("Overlay", overlay_text)
            st.metric("Depth", f"{property_data.get('lot_depth', 0):.1f}m")
        
        st.divider()
        
        # Score breakdown
        if st.session_state.assessment_complete:
            breakdown = detailed_score_breakdown(property_data)
            
            st.markdown("**Scores**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Zone", f"{breakdown['zone']['weighted_score']:.0f}")
                st.metric("Physical", f"{breakdown['physical']['weighted_score']:.0f}")
            with col2:
                st.metric("Transport", f"{breakdown['transport']['weighted_score']:.0f}")
                st.metric("Compliance", f"{breakdown['compliance']['weighted_score']:.0f}")
        
        st.divider()
        
        # Action buttons
        st.markdown("**Actions**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Report", use_container_width=True):
                st.session_state.generate_report = True
        with col2:
            if st.button("💾 Save", use_container_width=True):
                # Save assessment
                assessment_data = st.session_state.assessment_data
                assessment_data['timestamp'] = datetime.now().isoformat()
                save_assessment(assessment_data)
                st.success("✅ Assessment saved!")
    else:
        st.info("Select a site to view details")

# ============================================================================
# LOWER TABS - DETAILED ANALYSIS (Conditionally shown)
# ============================================================================

if st.session_state.assessment_complete and st.session_state.assessment_data:
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📍 Location & Zoning", "📐 Physical", "📋 Compliance"])
    
    assessment_data = st.session_state.assessment_data
    
    with tab1:
        st.markdown("#### Location & Zoning Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Zone Type:** {assessment_data.get('zone_type', 'N/A')}")
            st.write(f"**Activity Centre:** {assessment_data.get('activity_centre', 'N/A')}")
        with col2:
            overlay = "Yes ⚠️" if assessment_data.get('has_overlay') else "No ✓"
            st.write(f"**Overlays:** {overlay}")
            st.write(f"**Transport Score:** {assessment_data.get('transport_score', 0):.0f}/25")
    
    with tab2:
        st.markdown("#### Physical Suitability")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Lot Width:** {assessment_data.get('lot_width', 0):.1f}m")
            st.write(f"**Lot Depth:** {assessment_data.get('lot_depth', 0):.1f}m")
        with col2:
            area = assessment_data.get('lot_width', 0) * assessment_data.get('lot_depth', 0)
            st.write(f"**Lot Area:** {area:.0f}m²")
            st.write(f"**Physical Score:** {assessment_data.get('physical_score', 0):.0f}/25")
    
    with tab3:
        st.markdown("#### Compliance Assessment")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Compliance Score:** {assessment_data.get('compliance_score', 0):.0f}/10")
            st.write(f"**Meets Standards:** {'Yes ✓' if assessment_data.get('compliance_score', 0) >= 7 else 'No ⚠️'}")
        with col2:
            st.write(f"**Zone Compliance:** {'Compliant ✓' if assessment_data.get('zone_compliant', True) else 'Non-compliant ⚠️'}")
            if assessment_data.get('has_overlay'):
                st.write("**⚠️ Planning overlays present**")

# ============================================================================
# REPORT GENERATION (Modal-like via expander)
# ============================================================================

if st.session_state.get('generate_report'):
    st.divider()
    st.markdown("## 📄 Generate Report")
    
    with st.expander("Report Options", expanded=True):
        report_sections = st.multiselect(
            "Select report sections",
            ["Executive Summary", "Location & Zoning", "Physical Assessment", 
             "Compliance", "Transport Analysis", "Recommendations"],
            default=["Executive Summary", "Location & Zoning", "Physical Assessment"]
        )
        
        if st.button("Generate PDF"):
            assessment_data = st.session_state.assessment_data
            with st.spinner("Generating report..."):
                try:
                    pdf_buffer = create_professional_pdf_report(
                        assessment_data,
                        include_sections=report_sections
                    )
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    st.session_state.generate_report = False
                except Exception as e:
                    st.error(f"Report generation failed: {str(e)[:100]}")

# ============================================================================
# FOOTER - DEBUG INFO (Collapsible in development)
# ============================================================================

with st.expander("⚙️ Debug Info"):
    if has_maps_api_key():
        st.success("✅ MAPS_API_KEY: Configured")
    else:
        st.info("ℹ️ MAPS_API_KEY: Not configured (using free OpenStreetMap tiles)")
    
    st.write(f"**Session State:** {dict(st.session_state) if st.session_state else 'Empty'}")
