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
import sqlite3
from datetime import datetime
import time

# ============================================================================
# IMPORTS - CUSTOM MODULES
# ============================================================================

from core.database import (
    init_database, save_assessment, get_recent_assessments, 
    get_assessment, delete_assessment, get_statistics
)
from core.scoring import (
    calculate_weighted_score,
    get_viability_status_from_score,
    detailed_score_breakdown,
    validate_urhh_design,
    estimate_revenue_potential,
    get_blueprint_setback_recommendations,
)
from core.pdf_generator import generate_due_diligence_pdf
from ui.advanced_map import create_advanced_map, get_nearby_summary
from ui.interactive_map_enhanced import create_professional_interactive_map
from core.data_fetcher import auto_assess_from_address, geocode_address as fetcher_geocode_address
from simple_auth import check_authentication, show_logout_button
from core.vicgis_wfs_lookup import auto_fill_from_vicgis, get_planning_data
from portfolio_utils import get_portfolio_stats, filter_by_viability
from core.cost_estimator import estimate_project_total
from excel_exporter import generate_excel_report
from ui.ui_enhancements import (
    apply_archistar_aesthetic,
    render_external_research_command_center,
    render_infographic_pod,
    render_infographic_tile,
    render_project_type_selector,
    get_project_type_subtitle,
    render_sda_hospital_proximity_tile,
)
from ui.map_first_layout import render_left_filter_panel, render_right_property_panel, render_card_grid
from config import has_maps_api_key, has_vicplan_api_key, get_secret_status

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="UR Happy Home | Site Assessor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZATION & SETUP
# ============================================================================

# Apply Archistar enterprise aesthetic (Stage 1 Visual Refinement)
# Ensure styling is applied before rendering any pages (including the login page)
apply_archistar_aesthetic()

# Query params (read early for auth bypass + deep-link behavior)
auth_bypass_param = st.query_params.get("auth_bypass", "")
if isinstance(auth_bypass_param, list):
    auth_bypass_param = auth_bypass_param[0] if auth_bypass_param else ""
auth_bypass_enabled = str(auth_bypass_param).strip().lower() == "true"

deep_link_address = st.query_params.get("address", "")
if isinstance(deep_link_address, list):
    deep_link_address = deep_link_address[0] if deep_link_address else ""
deep_link_address = (deep_link_address or "").strip()

# Secrets startup check (production-safe warnings instead of hard failures)
secret_status = get_secret_status()
if not secret_status.get("maps"):
    st.warning("Maps API secret not configured. Running in OpenStreetMap mode.", icon="⚠️")
if not secret_status.get("vicplan"):
    st.warning("VicPlan API secret not configured. Public planning lookups will be used where available.", icon="⚠️")

# Authentication (supports explicit auth bypass for control-centre deep links)
if auth_bypass_enabled:
    st.session_state.authenticated = True
    st.session_state.user = {
        "email": "admin@urhappyhome.com",
        "name": "Administrator",
    }
else:
    check_authentication()

# Database
init_database()

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
if 'assessment_results' not in st.session_state:
    st.session_state.assessment_results = {}
if 'property_data' not in st.session_state:
    st.session_state.property_data = None
if 'search_triggered' not in st.session_state:
    st.session_state.search_triggered = False
if 'map_mode' not in st.session_state:
    st.session_state.map_mode = "search"
if 'report_pdf_bytes' not in st.session_state:
    st.session_state.report_pdf_bytes = None
if 'report_pdf_filename' not in st.session_state:
    st.session_state.report_pdf_filename = None
if 'deep_link_applied_address' not in st.session_state:
    st.session_state.deep_link_applied_address = None
if 'selected_project_type' not in st.session_state:
    st.session_state.selected_project_type = "Standard Rooming House"

# ============================================================================
# GEOCODING SETUP
# ============================================================================
def geocode_address(address):
    """Geocode an address and return lat, lon using production geocoding pipeline."""
    try:
        latitude, longitude = fetcher_geocode_address(address)
        if latitude is not None and longitude is not None:
            return latitude, longitude
        st.info("Initializing high-precision map...")
        return None, None
    except Exception as e:
        st.info("Initializing high-precision map...")
        return None, None


def is_admin_user():
    """Return True only for the configured admin email account."""
    user = st.session_state.get('user', {})
    email = str(user.get('email', '')).strip().lower()
    return email == 'admin@urhappyhome.com'


def load_portfolio_analytics_data():
    """Load portfolio analytics from saved assessments for admin dashboard."""
    try:
        conn = sqlite3.connect("assessments.db")
        query = """
            SELECT
                id,
                address,
                viability_status,
                viability_color,
                raw_score,
                lot_area,
                dist_transport,
                zone_type,
                has_overlay,
                project_type,
                created_at
            FROM assessments
            ORDER BY datetime(created_at) DESC
        """
        all_df = pd.read_sql_query(query, conn)
        conn.close()

        if all_df.empty:
            return pd.DataFrame(), 0.0, pd.DataFrame()

        all_df['viability_status'] = all_df['viability_status'].fillna('')
        all_df['created_at'] = pd.to_datetime(all_df['created_at'], errors='coerce')

        highly_suitable_df = all_df[
            all_df['viability_status'].str.upper().eq('HIGHLY SUITABLE')
        ].copy().head(10)

        suitable_mask = (
            all_df['viability_status'].str.upper().str.contains('SUITABLE')
            & ~all_df['viability_status'].str.upper().str.contains('NOT SUITABLE')
        )
        suitable_df = all_df[suitable_mask].copy()

        total_potential_revenue = 0.0
        for _, row in suitable_df.iterrows():
            estimate_input = {
                'project_type': row.get('project_type') or 'Standard Rooming House',
                'lot_area': float(row.get('lot_area') or 0),
                'dist_transport': float(row.get('dist_transport') or 9999),
                'zone_type': row.get('zone_type') or 'Unknown',
                'has_overlay': bool(row.get('has_overlay')),
            }
            revenue_data = estimate_revenue_potential(estimate_input)
            total_potential_revenue += float(revenue_data.get('annual_gross', 0) or 0)

        weekly_df = all_df.dropna(subset=['created_at']).copy()
        if not weekly_df.empty:
            weekly_df['week_start'] = weekly_df['created_at'].dt.to_period('W').dt.start_time
            weekly_df = (
                weekly_df.groupby('week_start')
                .size()
                .reset_index(name='assessments_completed')
                .sort_values('week_start')
            )

        return highly_suitable_df, total_potential_revenue, weekly_df
    except Exception:
        return pd.DataFrame(), 0.0, pd.DataFrame()


# ============================================================================
# MAIN LAYOUT - MAP-FIRST ARCHITECTURE
# ============================================================================

# Left sidebar filter panel
with st.sidebar:
    st.sidebar.markdown(
        '<a href="https://peppy-churros-175700.netlify.app/" target="_self" style="text-decoration: none;"><button style="width: 100%; cursor: pointer;">⬅️ Return to Control Centre</button></a>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown("### 🏠 UR Happy Home")
    st.caption(f"Analyzing: {get_project_type_subtitle(st.session_state.selected_project_type)}")
    st.markdown("**Site Assessment Platform**")
    st.divider()
    
    # Configuration status
    if has_maps_api_key():
        st.success("✅ Maps API configured")
    else:
        st.info("ℹ️ Using OpenStreetMap (free tiles)")

    if has_vicplan_api_key():
        st.success("✅ VicPlan API configured")
    else:
        st.info("ℹ️ Using public VicPlan/WFS endpoints")
    
    st.divider()
    
    # Address search section
    st.markdown("#### 📍 Site Search")
    st.markdown("#### 🏗️ Project Type")
    selected_project_type = render_project_type_selector(st.session_state.selected_project_type)
    st.session_state.selected_project_type = selected_project_type

    default_search_address = deep_link_address or st.session_state.last_address or ""
    search_address = st.text_input(
        "Address",
        value=default_search_address,
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
        st.session_state.assessment_results = {}
        st.session_state.property_data = None
        st.session_state.search_triggered = False
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
                    st.session_state.assessment_results = loaded
                    st.session_state.property_data = loaded
                    st.session_state.search_triggered = True
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
# MAIN CONTENT AREA - FULL-WIDTH MAP + STACKED INTELLIGENCE CARDS
# ============================================================================

st.markdown("### 🗺️ Interactive Site Map")

# Address search handling
auto_trigger_search = bool(
    deep_link_address
    and deep_link_address != st.session_state.deep_link_applied_address
)

address_to_assess = (deep_link_address if auto_trigger_search else search_address or "").strip()

if (search_btn and search_address) or auto_trigger_search:
    st.session_state.deep_link_applied_address = address_to_assess
    st.session_state.last_address = address_to_assess
    prefetched_assessment = None
    lat, lon = None, None

    if auto_trigger_search and auth_bypass_enabled and deep_link_address:
        prefetched_assessment = auto_assess_from_address(address_to_assess)
        lat = prefetched_assessment.get('latitude') if prefetched_assessment else None
        lon = prefetched_assessment.get('longitude') if prefetched_assessment else None

    if lat is None or lon is None:
        lat, lon = geocode_address(address_to_assess)

    if lat and lon:
        st.session_state.last_coords = (lat, lon)

        # Auto-assess the location
        with st.spinner("🔍 Analyzing site..."):
            try:
                assessment_data = prefetched_assessment or auto_assess_from_address(address_to_assess, lat, lon)
                assessment_data['project_type'] = st.session_state.selected_project_type

                if auto_trigger_search:
                    assessment_data['lot_width'] = 12.44
                    assessment_data['lot_depth'] = 25.6
                    assessment_data['lot_area'] = 316.0

                # Automated planning due diligence from VicPlan (WFS)
                planning_data = get_planning_data(lat, lon)
                assessment_data['vicplan_zone'] = planning_data.get('Planning Zone', 'Unknown')
                assessment_data['vicplan_overlays'] = planning_data.get('Overlays', [])
                assessment_data['vpp_links'] = planning_data.get('vpp_links', {})
                assessment_data['planning_risk_checks'] = planning_data.get('risk_checks', {})
                assessment_data['aboriginal_cultural_heritage_sensitivity'] = planning_data.get(
                    'aboriginal_cultural_heritage_sensitivity',
                    False,
                )
                assessment_data['special_building_overlay_flood_risk'] = planning_data.get(
                    'special_building_overlay_flood_risk',
                    False,
                )

                if assessment_data.get('vicplan_zone') and assessment_data['vicplan_zone'] != 'Unknown':
                    assessment_data['zone_type'] = assessment_data['vicplan_zone']
                if assessment_data.get('vicplan_overlays'):
                    assessment_data['has_overlay'] = True

                st.session_state.assessment_data = assessment_data

                # Calculate score
                score = calculate_weighted_score(assessment_data)
                viability = get_viability_status_from_score(score)

                # Get detailed score breakdown
                breakdown = detailed_score_breakdown(assessment_data)

                # Populate all assessment fields for export
                assessment_data['raw_score'] = score
                assessment_data['viability_status'] = viability['status']
                assessment_data['viability_color'] = viability['color']

                # Add score components from breakdown
                assessment_data['zone_score'] = breakdown.get('zone', {}).get('weighted_score', 0)
                assessment_data['transport_score'] = breakdown.get('transport', {}).get('weighted_score', 0)
                assessment_data['physical_score'] = breakdown.get('physical', {}).get('weighted_score', 0)
                assessment_data['compliance_score'] = breakdown.get('compliance', {}).get('weighted_score', 0)

                # Add default values for fields not auto-populated
                if 'zone_type' not in assessment_data or not assessment_data['zone_type']:
                    assessment_data['zone_type'] = 'General Residential Zone'
                if 'lot_width' not in assessment_data or assessment_data['lot_width'] == 0:
                    assessment_data['lot_width'] = 12.44
                if 'lot_depth' not in assessment_data or assessment_data['lot_depth'] == 0:
                    assessment_data['lot_depth'] = 25.6
                if 'lot_area' not in assessment_data or assessment_data['lot_area'] == 0:
                    assessment_data['lot_area'] = max(
                        316.0,
                        assessment_data.get('lot_width', 12.44) * assessment_data.get('lot_depth', 25.6)
                    )
                if 'has_overlay' not in assessment_data:
                    assessment_data['has_overlay'] = False
                if 'slope' not in assessment_data:
                    assessment_data['slope'] = 'Moderate'
                if 'check_heating' not in assessment_data:
                    assessment_data['check_heating'] = True
                if 'check_windows' not in assessment_data:
                    assessment_data['check_windows'] = True
                if 'check_energy' not in assessment_data:
                    assessment_data['check_energy'] = True
                if 'amenities_summary' not in assessment_data:
                    assessment_data['amenities_summary'] = {
                        'transit': [],
                        'schools': [],
                        'parks': [],
                        'shops': [],
                        'heritage': []
                    }

                # Automated URHH design fit validation
                urhh_design_validation = validate_urhh_design(
                    assessment_data.get('lot_width', 0),
                    assessment_data.get('lot_depth', 0),
                    assessment_data.get('lot_area', 0),
                    project_type=assessment_data.get('project_type'),
                    assessment_data=assessment_data,
                )
                assessment_data['urhh_design_validation'] = urhh_design_validation
                assessment_data['setback_requirements'] = urhh_design_validation.get('setback_requirements', {})

                # Revenue intelligence
                assessment_data['revenue_potential'] = estimate_revenue_potential(assessment_data)

                # Add placeholder recommendations and constraints for export
                if 'identified_constraints' not in assessment_data:
                    constraints = []
                    if assessment_data.get('has_overlay'):
                        constraints.append("Planning overlay present - requires additional approval")
                    if assessment_data.get('dist_transport', 0) > 800:
                        constraints.append("Distance to nearest transport exceeds catchment")
                    if assessment_data.get('lot_area', 0) < 316:
                        constraints.append("Lot area below minimum 316sqm requirement")

                    reg = assessment_data.get('regulatory_findings')
                    if reg:
                        if not reg.get('overall_compliant', True):
                            constraints.append('Does NOT meet rooming-house minimum standards:')
                            for reason in reg.get('reasons', []):
                                constraints.append(f"- {reason}")
                        else:
                            constraints.append('Meets rooming-house minimum standards (preliminary check).')

                    assessment_data['identified_constraints'] = constraints if constraints else ["No significant constraints identified"]

                if 'recommendations' not in assessment_data:
                    recommendations = [
                        "Conduct legal due diligence including title search",
                        "Obtain builder quotes for estimated construction costs",
                        "Engage town planning consultant for design review",
                        "Confirm council development approval pathway"
                    ]
                    recommendations.extend(
                        get_blueprint_setback_recommendations(
                            assessment_data.get('lot_depth', 0),
                            project_type=assessment_data.get('project_type')
                        )
                    )
                    reg = assessment_data.get('regulatory_findings')
                    if reg and not reg.get('overall_compliant', True):
                        recommendations.insert(0, "Review rooming-house minimum standards and confirm gross floor area, bedrooms and intended occupancy with a qualified planner or building surveyor.")
                    assessment_data['recommendations'] = recommendations

                st.session_state.property_data = assessment_data
                st.session_state.assessment_results = assessment_data
                st.session_state.assessment_complete = True
                st.session_state.search_triggered = True

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

    try:
        zoom_start = 18 if st.session_state.deep_link_applied_address else 16
        m, poi_data = create_advanced_map(
            latitude=lat,
            longitude=lon,
            address=address_display,
            viability_color=viability_color,
            zone_type=zone_type,
            has_overlay=has_overlay,
            map_type="Satellite",
            zoom_start=zoom_start,
        )
        map_data = st_folium(m, height=720, use_container_width=True)
    except Exception as e:
        st.error(f"Map rendering error: {str(e)[:100]}")
else:
    placeholder_map = folium.Map(
        location=[-37.8136, 144.9631],
        zoom_start=12,
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    )

    folium.Marker(
        location=[-37.8136, 144.9631],
        popup="Search for a site address to begin",
        tooltip="Enter an address in the left panel"
    ).add_to(placeholder_map)

    map_data = st_folium(placeholder_map, height=720, use_container_width=True)
    st.info("👈 Enter a site address in the left panel to begin")

st.markdown("### 💡 Property Intelligence")

property_data = st.session_state.get('assessment_results') or st.session_state.property_data
if property_data:
    score = property_data.get('raw_score', 0)
    status = property_data.get('viability_status', 'PENDING')
    color = property_data.get('viability_color', 'gray')
    color_map = {'green': '🟢', 'orange': '🟡', 'red': '🔴', 'gray': '⚪'}
    status_icon = color_map.get(color, '⚪')
    status_pod = 'pass' if color == 'green' else 'warning' if color == 'orange' else 'fail' if color == 'red' else 'neutral'

    revenue_potential = property_data.get('revenue_potential', {})
    project_type = property_data.get('project_type', st.session_state.get('selected_project_type', 'Standard Rooming House'))
    weekly_min = revenue_potential.get('weekly_min', 0)
    weekly_max = revenue_potential.get('weekly_max', 0)
    annual_min = revenue_potential.get('annual_min', 0)
    annual_max = revenue_potential.get('annual_max', 0)

    risk_checks = property_data.get('planning_risk_checks', {})
    ach_flag = risk_checks.get('aboriginal_cultural_heritage_sensitivity', False)
    flood_flag = risk_checks.get('special_building_overlay_flood_risk', False)
    design_validation = property_data.get('urhh_design_validation', {})
    blueprint_pass = bool(design_validation.get('pass_fail'))

    def render_snapshot_card():
        with st.container(border=True):
            st.markdown("#### 🧭 Site Snapshot")
            address = property_data.get('address', 'N/A')
            st.caption(address)
            render_infographic_tile(
                "Suitability",
                f"{status_icon} {status}",
                icon="🏁",
                color="pass" if blueprint_pass else status_pod,
                high_fidelity=True,
            )
            render_infographic_tile("Suitability Score", f"{score:.0f}/100", icon="📈", color="pass" if blueprint_pass else status_pod)
            render_infographic_pod("VicPlan Zone", str(property_data.get('vicplan_zone') or property_data.get('zone_type', 'N/A'))[:32], icon="🧱", subtitle="Primary planning control", status="neutral")

    def render_yield_card():
        with st.container(border=True):
            st.markdown("#### 💰 Revenue & Yield")
            weekly_midpoint = int((weekly_min + weekly_max) / 2) if (weekly_min or weekly_max) else 0
            render_infographic_tile(
                "Revenue Estimate",
                f"${weekly_min:,} - ${weekly_max:,} /wk",
                icon="📅",
                color="pass" if weekly_min else "neutral",
                high_fidelity=True,
            )
            render_infographic_tile(
                "Yield (Midpoint)",
                f"${weekly_midpoint:,} /wk" if weekly_midpoint else "N/A",
                icon="📊",
                color="pass" if weekly_midpoint else "neutral",
            )
            render_infographic_tile("Annual Gross", f"${annual_min:,} - ${annual_max:,}", icon="🗓️", color="pass" if annual_min else "neutral")
            render_infographic_pod("Project Type", project_type, icon="🏗️", subtitle="Enterprise Intelligence Active", status="pass")
            render_infographic_pod("Intelligence Status", "Enterprise Intelligence Active", icon="🧠", subtitle="Revenue and score intelligence enabled", status="pass")
            render_infographic_pod("Lot Geometry", f"{property_data.get('lot_width', 0):.1f}m × {property_data.get('lot_depth', 0):.1f}m", icon="📐", subtitle=f"Total area {property_data.get('lot_area', 0):.0f} m²", status="neutral")

    def render_planning_card():
        with st.container(border=True):
            st.markdown("#### ⚖️ Planning & Risk")
            overlay_label = "Overlay Present" if property_data.get('has_overlay') else "No Overlay"
            render_infographic_pod("Overlay Status", overlay_label, icon="🗺️", subtitle="Planning overlays and controls", status="warning" if property_data.get('has_overlay') else "pass")
            render_infographic_pod("Cultural Heritage", "Flagged" if ach_flag else "Clear", icon="🏛️", subtitle="Aboriginal heritage sensitivity", status="warning" if ach_flag else "pass")
            render_infographic_pod("Flood / SBO", "Flagged" if flood_flag else "Clear", icon="🌧️", subtitle="Special building overlay / flood", status="fail" if flood_flag else "pass")
            if project_type == "SDA/NDIS Unit":
                render_sda_hospital_proximity_tile(property_data)
            vpp_link = property_data.get('vpp_links', {})
            if vpp_link:
                st.link_button(
                    f"📘 Clause {vpp_link.get('clause', 'VPP')} — {vpp_link.get('title', 'Victorian Planning Provisions')}",
                    vpp_link.get('url', 'https://planning-schemes.app.planning.vic.gov.au/schemes/vpps'),
                    use_container_width=True,
                )

    def render_design_card():
        with st.container(border=True):
            st.markdown("#### 🏗️ Design Suitability")
            design_pass = bool(design_validation.get('pass_fail'))
            render_infographic_tile(
                "Design Suitability",
                "PASS" if design_pass else "REVIEW REQUIRED",
                icon="✅" if design_pass else "⚠️",
                color="pass" if design_pass else "warning",
                high_fidelity=True,
            )
            render_infographic_pod(
                "URHH Standard Fit",
                "PASS" if design_pass else "REVIEW REQUIRED",
                icon="✅" if design_pass else "⚠️",
                subtitle="Preliminary design fit check",
                status="pass" if design_pass else "fail",
            )
            reasons = design_validation.get('reasons', [])
            if reasons:
                st.markdown("**Detailed reasons**")
                for reason in reasons:
                    st.write(f"• {reason}")

    def render_scores_card():
        with st.container(border=True):
            st.markdown("#### 📊 Score Breakdown")
            breakdown = detailed_score_breakdown(property_data)
            render_infographic_pod("Zone", f"{breakdown['zone']['weighted_score']:.0f}/40", icon="🧭", subtitle="Zoning and planning suitability", status="neutral")
            render_infographic_pod("Transport", f"{breakdown['transport']['weighted_score']:.0f}/25", icon="🚉", subtitle="PT accessibility score", status="neutral")
            render_infographic_pod("Physical", f"{breakdown['physical']['weighted_score']:.0f}/25", icon="📏", subtitle="Lot and site attributes", status="neutral")
            render_infographic_pod("Compliance", f"{breakdown['compliance']['weighted_score']:.0f}/10", icon="📋", subtitle="Standards and policy fit", status="neutral")

    def render_actions_card():
        with st.container(border=True):
            st.markdown("#### 🚀 Actions & Research")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📄 Generate Report", use_container_width=True, key="report_card_btn"):
                    assessment_data = st.session_state.assessment_data
                    if assessment_data:
                        with st.spinner("Generating due diligence PDF..."):
                            try:
                                pdf_bytes = generate_due_diligence_pdf(assessment_data)
                                safe_address = assessment_data.get('address', 'site').replace(' ', '_')
                                st.session_state.report_pdf_bytes = pdf_bytes
                                st.session_state.report_pdf_filename = f"Due_Diligence_{safe_address}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                st.success("✅ Report ready for download")
                            except Exception as e:
                                st.error(f"Report generation failed: {str(e)[:100]}")
            with col2:
                if st.button("💾 Save Assessment", use_container_width=True, key="save_card_btn"):
                    assessment_data = st.session_state.assessment_data
                    assessment_data['timestamp'] = datetime.now().isoformat()
                    save_assessment(assessment_data)
                    st.success("✅ Assessment saved!")

            if st.session_state.get('report_pdf_bytes') and st.session_state.get('report_pdf_filename'):
                st.download_button(
                    label="📥 Download Due Diligence PDF",
                    data=st.session_state.report_pdf_bytes,
                    file_name=st.session_state.report_pdf_filename,
                    mime="application/pdf",
                    use_container_width=True,
                    key="download_report_card_btn",
                )
            with st.expander("Open Research Links & Actions", expanded=False):
                render_external_research_command_center(property_data.get('address', st.session_state.last_address))

    st.markdown("#### Financial Potential")
    render_card_grid(
        [
            render_snapshot_card,
            render_yield_card,
        ],
        cards_per_row=3,
    )

    st.markdown("#### Site Constraints")
    render_card_grid(
        [
            render_planning_card,
            render_design_card,
            render_scores_card,
        ],
        cards_per_row=3,
    )

    st.markdown("#### Compliance")
    with st.expander("Open Compliance Links & Actions", expanded=False):
        render_card_grid(
            [
                render_actions_card,
            ],
            cards_per_row=3,
        )

else:
    st.info("Select a site to view intelligence panels.")
    with st.expander("Open Research Links & Actions", expanded=False):
        render_external_research_command_center(st.session_state.last_address)

st.caption("Powered by UR Happy Home Intelligence")

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
            st.write(f"**Lot Area:** {assessment_data.get('lot_area', 0):.0f}m²")
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
        # Regulatory findings from rooming-house standards
        reg = assessment_data.get('regulatory_findings')
        if reg:
            st.markdown("**Rooming-house Minimum Standards:**")
            overall = reg.get('overall_compliant', False)
            st.write(f"**Overall:** {'Meets standards ✓' if overall else 'Does NOT meet standards ⚠️'}")
            with st.expander("Show detailed regulatory findings"):
                for reason in reg.get('reasons', []):
                    st.write(f"• {reason}")

        # **NEW: Design suitability for UR Happy Home Standard Design**
        design_suit = assessment_data.get('design_suitability')
        if design_suit:
            st.markdown("**Design Suitability (UR Happy Home Standard):**")
            all_pass = design_suit.get('all_checks_pass', False)
            st.write(f"**Overall:** {'Suitable ✓' if all_pass else 'Issues noted ⚠️'}")
            with st.expander("Show design suitability details"):
                for reason in design_suit.get('reasons', []):
                    st.write(f"• {reason}")
                if design_suit.get('recommendations'):
                    st.markdown("**Recommendations:**")
                    for rec in design_suit.get('recommendations', []):
                        st.write(f"• {rec}")

# ============================================================================
# ADMIN-ONLY PORTFOLIO ANALYTICS TAB
# ============================================================================

if is_admin_user():
    st.divider()
    analytics_tab, = st.tabs(["📈 Portfolio Analytics"])

    with analytics_tab:
        st.markdown("#### Portfolio Analytics")
        highly_suitable_df, total_revenue, weekly_df = load_portfolio_analytics_data()

        st.metric("Total Potential Revenue (Suitable Sites)", f"${total_revenue:,.0f}")

        st.markdown("##### Last 10 HIGHLY SUITABLE Sites")
        if highly_suitable_df.empty:
            st.info("No HIGHLY SUITABLE assessments found yet.")
        else:
            display_df = highly_suitable_df[[
                'address',
                'project_type',
                'raw_score',
                'created_at'
            ]].copy()
            display_df.columns = ['Address', 'Project Type', 'Score', 'Assessed At']
            display_df['Assessed At'] = pd.to_datetime(display_df['Assessed At'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            csv_export_df = highly_suitable_df[[
                'address',
                'raw_score',
                'project_type',
            ]].copy()
            csv_export_df.columns = ['Address', 'Yield Score', 'Project Type']
            csv_data = csv_export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"highly_suitable_sites_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_highly_suitable_csv",
            )

        st.markdown("##### Weekly Assessments Completed")
        if weekly_df.empty:
            st.info("No assessment activity data available yet.")
        else:
            chart_df = weekly_df.set_index('week_start')[['assessments_completed']]
            st.bar_chart(chart_df, use_container_width=True)

# ============================================================================
# REPORT GENERATION & EXPORT SECTION
# ============================================================================

# Handle export portfolio button
if st.session_state.get('export_portfolio'):
    st.divider()
    st.markdown("## 📊 Export Options")
    
    with st.expander("Export Report", expanded=True):
        export_type = st.radio(
            "Choose export format:",
            ["PDF Report", "Excel Spreadsheet"],
            horizontal=True
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate PDF", use_container_width=True):
                assessment_data = st.session_state.assessment_data
                if assessment_data:
                    with st.spinner("Generating PDF report..."):
                        try:
                            pdf_buffer = generate_due_diligence_pdf(assessment_data)
                            
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_buffer,
                                file_name=f"Assessment_{assessment_data.get('address', 'site').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"PDF generation failed: {str(e)[:100]}")
                else:
                    st.warning("No assessment data available to generate report")
        
        with col2:
            if st.button("Generate Excel", use_container_width=True):
                assessment_data = st.session_state.assessment_data
                if assessment_data:
                    with st.spinner("Generating Excel report..."):
                        try:
                            # Fetch all assessments for comparison
                            try:
                                all_assessments = get_recent_assessments(limit=10)
                            except:
                                all_assessments = []
                            
                            excel_buffer = generate_excel_report(
                                assessment_data,
                                comparison_data=all_assessments[1:] if len(all_assessments) > 1 else None
                            )
                            
                            st.download_button(
                                label="📊 Download Excel",
                                data=excel_buffer,
                                file_name=f"Assessment_{assessment_data.get('address', 'site').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        except Exception as e:
                            st.error(f"Excel generation failed: {str(e)[:100]}")
                else:
                    st.warning("No assessment data available to generate report")
    
    st.session_state.export_portfolio = False

# Handle generate report button
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
                    pdf_buffer = generate_due_diligence_pdf(assessment_data)
                    
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
