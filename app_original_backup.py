import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
import time

# Import custom modules
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
from ui.ui_enhancements import (
    apply_professional_styling, render_header_banner, render_metric_card,
    render_status_badge, render_info_box, render_score_circlegauge, COLORS
)

# ============================================================================
# PAGE CONFIGURATION & STYLING
# ============================================================================
st.set_page_config(
    page_title="UR Happy Home - Site Assessor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply professional styling globally with enhanced CSS from ui_enhancements
apply_professional_styling()

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
# AUTHENTICATION
# ============================================================================
check_authentication()

# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================
init_database()

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================
TRANSPORT_CATCHMENT = 800  # meters
MIN_LOT_WIDTH = 14  # meters (Victoria standard block width)
MIN_LOT_DEPTH = 24  # meters (Victoria standard block depth)
MIN_LOT_AREA = 336  # sqm (14m x 24m = 336 sqm - Victoria standard lot)
VICTORIA_STANDARD_LOT_WIDTH = 14
VICTORIA_STANDARD_LOT_DEPTH = 24

REPORT_ITEMS = {
    "Executive Summary": True,
    "Site Location & Zoning Analysis": True,
    "Physical Suitability Assessment": True,
    "Regulatory Compliance": True,
    "Proximity & Transport": True,
    "Risk Assessment & Constraints": True,
    "Recommendations": True,
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'assessment_complete' not in st.session_state:
    st.session_state.assessment_complete = False
if 'last_address' not in st.session_state:
    st.session_state.last_address = None
if 'last_coords' not in st.session_state:
    st.session_state.last_coords = None
if 'assessment_id' not in st.session_state:
    st.session_state.assessment_id = None
if 'assessor_notes' not in st.session_state:
    st.session_state.assessor_notes = ""
    st.session_state.last_coords = None

# ============================================================================
# SIDEBAR: PORTFOLIO DASHBOARD & RECENT ASSESSMENTS
# ============================================================================
with st.sidebar:
    st.title("📊 Portfolio Dashboard")
    
    # Portfolio stats
    stats = get_portfolio_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Sites", stats.get('total_assessments', 0))
        st.metric("Suitable", stats.get('suitable_count', 0))
    with col2:
        st.metric("Conditional", stats.get('conditional_count', 0))
        st.metric("Unsuitable", stats.get('unsuitable_count', 0))
    
    st.metric("Avg Score", f"{stats.get('avg_score', 0):.1f}")
    st.metric("Success Rate", f"{stats.get('suitable_percentage', 0):.0f}%")
    
    st.divider()
    
    # Quick filters
    st.subheader("Quick Filters")
    filter_status = st.multiselect(
        "Filter by Status",
        ["Suitable 🟢", "Conditional 🟡", "Unsuitable 🔴"],
        default=["Suitable 🟢"]
    )
    
    st.divider()
    
    # Recent assessments
    st.subheader("Recent Assessments")
    recent = get_recent_assessments(limit=10)
    
    if recent:
        for assessment in recent:
            status_color = {'green': '🟢', 'orange': '🟡', 'red': '🔴'}.get(assessment['viability_color'], '⚪')
            if st.button(
                f"{status_color} {assessment['address'][:30]}...",
                key=f"load_{assessment['id']}",
                use_container_width=True
            ):
                st.session_state.assessment_id = assessment['id']
                loaded = get_assessment(assessment['id'])
                if loaded:
                    st.session_state.assessment_complete = True
                    st.session_state.last_address = loaded['address']
                    st.session_state.last_coords = (loaded['latitude'], loaded['longitude'])
                    st.success(f"Loaded: {loaded['address']}")
                    st.rerun()
        
        if st.button("📥 Export All to Excel", use_container_width=True):
            assessments = [dict(a) for a in recent]
            excel_buffer = generate_excel_report(recent[0] if recent else {}, assessments[1:] if len(assessments) > 1 else None)
            st.download_button(
                label="Download Excel",
                data=excel_buffer,
                file_name=f"UR_Happy_Home_Portfolio_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("No assessments yet. Create your first site assessment!")

# ============================================================================
# MAIN APP HEADER
# ============================================================================
render_header_banner(
    "UR Happy Home - Site Assessor",
    "Professional development site analysis for rooming house opportunities",
    icon="🏠"
)

col_logout1, col_logout2 = st.columns([4, 1])
with col_logout2:
    show_logout_button()

st.divider()

# ============================================================================
# ADDRESS INPUT & ASSESSMENT SECTION
# ============================================================================
st.subheader("📍 Step 1: Enter Site Address")

address_input = st.text_input(
    "Site Address (Victoria, Australia)",
    placeholder="e.g., 123 Examples Street, Ringwood VIC 3134",
    help="Enter the full address of the rooming house site"
)

col_assess, col_clear = st.columns([1, 3])
with col_assess:
    assess_button = st.button("🔍 Assess Site", use_container_width=True, type="primary")

# Process assessment when button clicked
if assess_button and address_input:
    with st.spinner("🌍 Geocoding address and analyzing site..."):
        latitude, longitude = geocode_address(address_input)
        
        if latitude is not None and longitude is not None:
            # Auto-populate fields from address
            auto = auto_assess_from_address(address_input)
            st.session_state.assessment_complete = True
            st.session_state.last_address = address_input
            st.session_state.last_coords = (latitude, longitude)

            # Merge auto fields into session state for later use
            st.session_state.auto_fields = auto
        else:
            st.session_state.assessment_complete = False
            st.error("Could not geocode the address. Please check and try again.")

# ============================================================================
# ASSESSMENT FORM & SCORECARD
# ============================================================================
if st.session_state.assessment_complete:
    latitude, longitude = st.session_state.last_coords
    address = st.session_state.last_address
    
    st.success(f"✅ Address geocoded: {address}")
    
    st.divider()
    st.subheader("📋 Step 2: Site Details & Assessment")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Location & Zoning", "Physical Suitability", "Regulatory Compliance"])
    
    # ========== TAB 1: LOCATION & ZONING ==========
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Planning Zone & Overlays**")
            zone_type = st.selectbox(
                "Planning Zone",
                ("General Residential Zone (GRZ)", "Residential Growth Zone (RGZ)", 
                 "Neighbourhood Residential Zone (NRZ)", "Commercial/Other"),
                help="Select the primary planning zone from VicPlan"
            )
            
            has_overlay = st.checkbox(
                "Heritage / Neighbourhood Character Overlay?",
                help="Check VicPlan for HO or NCO overlays"
            )
        
        with col2:
            st.markdown("**Proximity to Transport**")
            dist_transport = st.number_input(
                "Distance to Train/Activity Centre (m)",
                min_value=0,
                value=650,
                step=50,
                help="Distance to nearest PTV station or major activity centre"
            )
    
    # ========== TAB 2: PHYSICAL SUITABILITY ==========
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Lot Dimensions (Victoria Standard Block)**")
            lot_width = st.number_input(
                "Lot Width (m)",
                min_value=5.0,
                value=float(VICTORIA_STANDARD_LOT_WIDTH),
                step=0.5,
                help="Victoria standard: 14m minimum"
            )
            
            lot_depth = st.number_input(
                "Lot Depth (m)",
                min_value=10.0,
                value=float(VICTORIA_STANDARD_LOT_DEPTH),
                step=0.5,
                help="Victoria standard: 24m minimum"
            )
            
            # Calculate area from dimensions
            lot_area = lot_width * lot_depth
            st.metric("Calculated Lot Area", f"{lot_area:.0f} sqm", f"{lot_width:.1f}m × {lot_depth:.1f}m")
        with col2:
            st.markdown("**Site Conditions**")
            slope = st.select_slider(
                "Site Slope",
                options=["Flat", "Moderate", "Steep"],
                value="Flat"
            )
            
            has_covenant = st.checkbox(
                "Single Dwelling Covenant?",
                help="Check title for restrictive covenants that prevent multi-occupancy"
            )
    
    # ========== TAB 3: REGULATORY COMPLIANCE ==========
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Mandatory Standards (Dec 2025)**")
            check_heating = st.checkbox("✓ Fixed heating in all resident rooms")
            check_windows = st.checkbox("✓ Blind cords properly secured")
        
        with col2:
            st.markdown("**Future Proofing (2030)**")
            check_energy = st.checkbox("✓ All-electric / Heat pump ready")
    
    st.divider()
    
    # ============================================================================
    # ASSESSMENT ALGORITHM & WEIGHTED SCORING
    # ============================================================================
    is_preferred_zone = zone_type in ["General Residential Zone (GRZ)", "Residential Growth Zone (RGZ)"]
    is_transport_compliant = dist_transport <= TRANSPORT_CATCHMENT
    is_width_compliant = lot_width >= MIN_LOT_WIDTH
    is_depth_compliant = lot_depth >= MIN_LOT_DEPTH
    is_area_compliant = lot_area >= MIN_LOT_AREA
    
    # Prepare assessment data for scoring
    assessment_data = {
        'address': address,
        'latitude': latitude,
        'longitude': longitude,
        'zone_type': zone_type,
        'has_overlay': has_overlay,
        'dist_transport': dist_transport,
        'lot_width': lot_width,
        'lot_depth': lot_depth,
        'lot_area': lot_area,
        'slope': slope,
        'has_covenant': has_covenant,
        'check_heating': check_heating,
        'check_windows': check_windows,
        'check_energy': check_energy,
        'is_preferred_zone': is_preferred_zone,
        'is_transport_compliant': is_transport_compliant,
        'is_width_compliant': is_width_compliant,
        'is_depth_compliant': is_depth_compliant,
        'is_area_compliant': is_area_compliant,
    }
    
    # Calculate weighted score
    raw_score = calculate_weighted_score(assessment_data)
    
    # Get status from score
    viability_result = get_viability_status_from_score(raw_score)
    viability_status = viability_result['status']
    viability_color = viability_result['color']
    viability_message = viability_result['message']
    
    # Add to assessment data for storage
    assessment_data['viability_status'] = viability_status
    assessment_data['viability_color'] = viability_color
    assessment_data['raw_score'] = raw_score
    assessment_data['summary_message'] = viability_message
    
    # ============================================================================
    # SCORECARD DISPLAY WITH WEIGHTED SCORE
    # ============================================================================
    st.subheader("🎯 Rooming House Scorecard")
    
    # Score breakdown columns
    score_col1, score_col2, score_col3 = st.columns([1, 2, 1])
    
    with score_col1:
        st.markdown("**Viability Score**")
        score_color_class = f"score-{viability_color}"
        st.markdown(f"<div class='score-display score-{viability_color}'>{raw_score:.1f}</div>", unsafe_allow_html=True)
        st.caption(f"Out of 100")
    
    with score_col2:
        st.markdown("**Status & Recommendation**")
        if viability_color == "green":
            st.markdown(f"<div class='status-green'><h3>✅ {viability_status}</h3><p>{viability_message}</p></div>", 
                       unsafe_allow_html=True)
        elif viability_color == "orange":
            st.markdown(f"<div class='status-amber'><h3>⚠️ {viability_status}</h3><p>{viability_message}</p></div>", 
                       unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='status-red'><h3>❌ {viability_status}</h3><p>{viability_message}</p></div>", 
                       unsafe_allow_html=True)
    
    with score_col3:
        st.markdown("**Score Details**")
        breakdown = detailed_score_breakdown(assessment_data)
        st.write(f"**Zone:** {breakdown['zone']['weighted_score']:.1f}")
        st.write(f"**Transport:** {breakdown['transport']['weighted_score']:.1f}")
        st.write(f"**Physical:** {breakdown['physical']['weighted_score']:.1f}")
        st.write(f"**Compliance:** {breakdown['compliance']['weighted_score']:.1f}")
    
    st.divider()
    
    # Detailed score breakdown expander
    with st.expander("📊 View Detailed Score Breakdown", expanded=False):
        breakdown = detailed_score_breakdown(assessment_data)
        
        # Create breakdown table
        breakdown_data = [
            ["Criteria", "Score", "Max", "Weight", "Feedback"],
            ["Zone", f"{breakdown['zone']['score']}", f"{breakdown['zone']['max']}", f"{breakdown['zone']['weight']*100:.0f}%", breakdown['zone']['feedback']],
            ["Transport", f"{breakdown['transport']['score']}", f"{breakdown['transport']['max']}", f"{breakdown['transport']['weight']*100:.0f}%", breakdown['transport']['feedback']],
            ["Physical", f"{breakdown['physical']['score']:.0f}", f"{breakdown['physical']['max']}", f"{breakdown['physical']['weight']*100:.0f}%", breakdown['physical']['feedback']],
            ["Compliance", f"{breakdown['compliance']['score']}", f"{breakdown['compliance']['max']}", f"{breakdown['compliance']['weight']*100:.0f}%", breakdown['compliance']['feedback']],
        ]
        
        breakdown_df = pd.DataFrame(breakdown_data[1:], columns=breakdown_data[0])
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
    
    # Metrics columns
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Lot Width", f"{lot_width}m", "✓ OK" if is_width_compliant else "✗ Below 14m")
    
    with metric_col2:
        st.metric("Lot Depth", f"{lot_depth}m", "✓ OK" if is_depth_compliant else "✗ Below 24m")
    
    with metric_col3:
        st.metric("Transport Distance", f"{dist_transport}m", "✓ OK" if is_transport_compliant else "✗ Outside 800m")
    
    with metric_col4:
        slope_status = "✓ Ideal" if slope == "Flat" else ("⚠️ Check" if slope == "Moderate" else "✗ High cost")
        st.metric("Site Slope", slope, slope_status)
    
    # Risk flags
    risk_col1, risk_col2, risk_col3 = st.columns(3)
    
    with risk_col1:
        st.markdown("**Zone Compliance**")
        if is_preferred_zone:
            st.success("✓ Preferred zone")
        else:
            st.error("✗ Not preferred zone")
    
    with risk_col2:
        st.markdown("**Overlay Status**")
        if not has_overlay:
            st.success("✓ No overlays")
        else:
            st.error("✗ Has overlay restrictions")
    
    with risk_col3:
        st.markdown("**Regulatory Readiness**")
        compliance_score = sum([check_heating, check_windows, check_energy])
        st.progress(compliance_score / 3, text=f"{compliance_score}/3 standards met")
    
    st.divider()
    
    # ============================================================================
    # ADVANCED MAP VISUALIZATION WITH PROFESSIONAL LAYER CONTROLS
    # ============================================================================
    st.subheader(f"🗺️ Interactive Site Analysis Map")
    
    # Professional map controls
    with st.expander("🎛️ Map Layer Controls", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            map_type = st.selectbox(
                "Map Basemap",
                ["OpenStreetMap", "Satellite", "Terrain"],
                help="Choose map visualization style",
                key="map_basemap"
            )
        
        with col2:
            st.markdown("**Points of Interest Layers**")
            show_transit = st.checkbox("🚌 Public Transit Stops", value=True, key="poi_transit")
            show_schools = st.checkbox("🎓 Schools & Education", value=True, key="poi_schools")
        
        with col3:
            st.markdown("**Additional Layers**")
            show_parks = st.checkbox("🌳 Parks & Recreation", value=True, key="poi_parks")
            show_shops = st.checkbox("🛒 Shops & Services", value=True, key="poi_shops")
            show_heritage = st.checkbox("🏛️ Heritage & Cultural", value=False, key="poi_heritage")
    
    # Create professional interactive map with layer controls
    with st.spinner("⏳ Loading interactive map with layers..."):
        try:
            m, poi_data = create_professional_interactive_map(
                latitude=latitude,
                longitude=longitude,
                address=address,
                viability_color=viability_color,
                zone_type=zone_type,
                has_overlay=has_overlay,
                lot_width=lot_width,
                lot_depth=lot_depth,
                show_transit=show_transit,
                show_schools=show_schools,
                show_parks=show_parks,
                show_shops=show_shops,
                show_heritage=show_heritage,
                map_type=map_type,
            )
        except Exception as e:
            st.warning(f"Enhanced map issue, using fallback map: {str(e)[:50]}")
            m, poi_data = create_advanced_map(
                latitude=latitude,
                longitude=longitude,
                address=address,
                viability_color=viability_color,
                show_transit=show_transit,
                show_schools=show_schools,
                show_parks=show_parks,
                show_shops=show_shops,
                show_heritage=show_heritage,
                map_type=map_type,
                zone_type=zone_type,
                has_overlay=has_overlay,
            )
    
    # Add amenities summary to assessment_data immediately for PDF generation
    assessment_data['amenities_summary'] = poi_data
    
    # Display professional interactive map
    map_data = st_folium(m, width="100%", height=600)
    
    # Map information box
    render_info_box(
        "💡 Map Tips",
        "Use the layer control (☰ icon, top right) to toggle different layers on/off. "
        "The 📏 symbol shows the 800m transport catchment. You can measure distances using the 📐 tool. "
        "Click markers for more information.",
        info_type="info"
    )
    
    st.divider()
    
    # ============================================================================
    # NEARBY AMENITIES SUMMARY
    # ============================================================================
    st.subheader("📍 Nearby Amenities & Services (1km radius)")
    
    summary_col1, summary_col2, summary_col3, summary_col4, summary_col5 = st.columns(5)
    
    with summary_col1:
        transit_count = len(poi_data['transit'])
        if transit_count > 0:
            st.metric("🚌 Transit Stops", transit_count, f"Nearest: {poi_data['transit'][0]['distance_m']}m")
        else:
            st.metric("🚌 Transit Stops", 0)
    
    with summary_col2:
        school_count = len(poi_data['schools'])
        if school_count > 0:
            st.metric("🎓 Schools", school_count, f"Nearest: {poi_data['schools'][0]['distance_m']}m")
        else:
            st.metric("🎓 Schools", 0)
    
    with summary_col3:
        park_count = len(poi_data['parks'])
        if park_count > 0:
            st.metric("🌳 Parks", park_count, f"Nearest: {poi_data['parks'][0]['distance_m']}m")
        else:
            st.metric("🌳 Parks", 0)
    
    with summary_col4:
        shop_count = len(poi_data['shops'])
        if shop_count > 0:
            st.metric("🛒 Shops", shop_count, f"Nearest: {poi_data['shops'][0]['distance_m']}m")
        else:
            st.metric("🛒 Shops", 0)
    
    with summary_col5:
        heritage_count = len(poi_data['heritage'])
        if heritage_count > 0:
            st.metric("🏛️ Heritage", heritage_count, f"Nearest: {poi_data['heritage'][0]['distance_m']}m")
        else:
            st.metric("🏛️ Heritage", 0)
    
    # Detailed amenities information
    with st.expander("📋 View Detailed Amenities List", expanded=False):
        
        if poi_data['transit']:
            st.markdown("**🚌 Public Transport**")
            transit_df = pd.DataFrame([
                {
                    'Name': p['name'],
                    'Distance (m)': p['distance_m'],
                    'Type': p['type']
                }
                for p in sorted(poi_data['transit'], key=lambda x: x['distance_m'])[:10]
            ])
            st.dataframe(transit_df, use_container_width=True, hide_index=True)
        
        if poi_data['schools']:
            st.markdown("**🎓 Education**")
            schools_df = pd.DataFrame([
                {
                    'Name': p['name'],
                    'Distance (m)': p['distance_m'],
                    'Type': p['type']
                }
                for p in sorted(poi_data['schools'], key=lambda x: x['distance_m'])[:10]
            ])
            st.dataframe(schools_df, use_container_width=True, hide_index=True)
        
        if poi_data['parks']:
            st.markdown("**🌳 Recreation**")
            parks_df = pd.DataFrame([
                {
                    'Name': p['name'],
                    'Distance (m)': p['distance_m'],
                    'Type': p['type']
                }
                for p in sorted(poi_data['parks'], key=lambda x: x['distance_m'])[:10]
            ])
            st.dataframe(parks_df, use_container_width=True, hide_index=True)
        
        if poi_data['shops']:
            st.markdown("**🛒 Shopping & Services**")
            shops_df = pd.DataFrame([
                {
                    'Name': p['name'],
                    'Distance (m)': p['distance_m'],
                    'Type': p['type']
                }
                for p in sorted(poi_data['shops'], key=lambda x: x['distance_m'])[:10]
            ])
            st.dataframe(shops_df, use_container_width=True, hide_index=True)
        
        if poi_data['heritage']:
            st.markdown("**🏛️ Heritage & Historical**")
            heritage_df = pd.DataFrame([
                {
                    'Name': p['name'],
                    'Distance (m)': p['distance_m'],
                    'Type': p['type']
                }
                for p in sorted(poi_data['heritage'], key=lambda x: x['distance_m'])[:10]
            ])
            st.dataframe(heritage_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # ============================================================================
    # REPORT GENERATION SECTION
    # ============================================================================
    st.subheader("📄 Generate Assessment Report")
    
    st.markdown("**Select sections to include in your report:**")
    
    report_cols = st.columns(2)
    report_selections = {}
    st.divider()
    
    # ============================================================================
    # ASSESSOR NOTES SECTION
    # ============================================================================
    st.subheader("📝 Assessor Notes")
    
    assessor_notes = st.text_area(
        "Add any additional notes or observations about this site",
        value=st.session_state.assessor_notes,
        height=100,
        placeholder="e.g., Site visit notes, contact info, follow-up items, etc."
    )
    
    st.divider()
    
    # ============================================================================
    # SAVE ASSESSMENT
    # ============================================================================
    st.subheader("💾 Save Assessment")
    
    if st.button("💾 Save Assessment", use_container_width=True, type="primary"):
        # Add recommendations based on assessment
        recommendations = []
        if not is_preferred_zone:
            recommendations.append("Investigate zone change prospects with council")
        if not is_transport_compliant:
            recommendations.append("Commission traffic engineering assessment")
        if not is_width_compliant or not is_area_compliant or not is_depth_compliant:
            recommendations.append("Consult with architect on subdivision opportunities")
        if has_overlay or has_covenant:
            recommendations.append("Obtain title clearance from legal counsel")
        compliance_score = sum([check_heating, check_windows, check_energy])
        if compliance_score < 3:
            recommendations.append("Budget for compliance upgrades (heating, windows, electrification)")
            if not recommendations:
                recommendations.append("Site appears suitable for development. Proceed with detailed planning.")
            
            assessment_data['recommendations'] = recommendations
            assessment_data['assessor_notes'] = assessor_notes
            assessment_data['amenities_summary'] = poi_data
            
            # Identify constraints
            constraints = []
            if has_overlay:
                constraints.append("Heritage or Neighbourhood Character Overlay")
            if has_covenant:
                constraints.append("Single Dwelling Covenant on Title")
            if not is_preferred_zone:
                constraints.append("Zone Type Not Optimal (GRZ/RGZ Preferred)")
            if not is_transport_compliant:
                constraints.append("Outside 800m Transport Catchment")
            if not is_width_compliant:
                constraints.append("Lot Width Below Minimum")
            if not is_area_compliant:
                constraints.append("Lot Area Below Minimum")
            if slope == "Steep":
                constraints.append("Steep Site Slope - High SDA Access Costs")
            
            assessment_data['identified_constraints'] = constraints
            
            # Save to database
            assessment_id = save_assessment(assessment_data)
            st.session_state.assessment_id = assessment_id
            st.success(f"✅ Assessment saved! ID: {assessment_id}")
    
    st.divider()
    
    # ============================================================================
    # REPORT GENERATION SECTION - MOVED OUTSIDE OF CONDITIONAL
    # ============================================================================
    st.subheader("📄 Generate Assessment Report")
    
    st.markdown("**Select sections to include in your report:**")
    
    report_cols = st.columns(2)
    report_selections = {}
    
    for i, (item, default) in enumerate(REPORT_ITEMS.items()):
        col = report_cols[i % 2]
        report_selections[item] = col.checkbox(item, value=default)
    
    col_pdf, col_txt = st.columns(2)
    
    with col_pdf:
        gen_pdf = st.button("📥 Generate Professional PDF", use_container_width=True, type="primary")
    
    with col_txt:
        gen_txt = st.button("📋 Generate Text Report", use_container_width=True)
    
    if gen_pdf:
        with st.spinner("✨ Generating professional PDF report with enhanced formatting..."):
            try:
                # Use new professional PDF generator
                pdf_buffer = create_professional_pdf_report(assessment_data, report_selections)
            except Exception as e:
                # Fallback to original PDF generator
                st.warning(f"Using standard PDF format due to rendering issue: {str(e)[:30]}")
                pdf_buffer = generate_pdf_report(assessment_data, report_selections)
            
            st.success("✅ Professional PDF report generated successfully!")
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_buffer,
                file_name=f"UR_Happy_Home_Assessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    elif gen_txt:
        with st.spinner("Generating text report..."):
            time.sleep(0.3)
            
            # Build recommendations list
            compliance_score = sum([check_heating, check_windows, check_energy])
            recommendations = []
            if not is_preferred_zone:
                recommendations.append("1. Investigate zone change prospects with council")
            if not is_transport_compliant:
                recommendations.append("2. Commission traffic engineering assessment")
            if not is_width_compliant or not is_area_compliant or not is_depth_compliant:
                recommendations.append("3. Consult with architect on subdivision opportunities")
            if has_overlay or has_covenant:
                recommendations.append("4. Obtain title clearance from legal counsel")
            if compliance_score < 3:
                recommendations.append("5. Budget for compliance upgrades (heating, windows, electrification)")
            if not recommendations:
                recommendations.append("Site appears suitable for development. Proceed with detailed planning.")
            
            report_text = f"""
VIC ROOMING HOUSE SITE ASSESSOR - ASSESSMENT REPORT
{'=' * 70}
Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}

SITE INFORMATION
{'-' * 70}
Address: {address}
Coordinates: {latitude:.4f}, {longitude:.4f}
Assessment Date: {datetime.now().strftime('%d %B %Y')}
Viability Score: {raw_score:.1f}/100

"""
            
            if report_selections.get("Executive Summary"):
                report_text += f"""
EXECUTIVE SUMMARY
{'-' * 70}
Viability Status: {viability_status}
Score: {raw_score:.1f}/100
Summary: {viability_message}

"""
            
            if report_selections.get("Site Location & Zoning Analysis"):
                report_text += f"""
SITE LOCATION & ZONING
{'-' * 70}
Planning Zone: {zone_type}
Zone Suitability: {'SUITABLE' if is_preferred_zone else 'NOT SUITABLE'}
Heritage/Character Overlay: {'Yes - CONSTRAINT' if has_overlay else 'No'}

"""
            
            if report_selections.get("Physical Suitability Assessment"):
                report_text += f"""
PHYSICAL SUITABILITY
{'-' * 70}
Lot Width: {lot_width}m (Minimum required: {MIN_LOT_WIDTH}m) - {'PASS' if is_width_compliant else 'FAIL'}
Lot Depth: {lot_depth}m (Minimum required: {MIN_LOT_DEPTH}m) - {'PASS' if is_depth_compliant else 'FAIL'}
Lot Area: {lot_area:.0f} sqm (Minimum required: {MIN_LOT_AREA} sqm)
Site Slope: {slope}
Single Dwelling Covenant: {'YES - CONSTRAINT' if has_covenant else 'NO'}

"""
            
            if report_selections.get("Regulatory Compliance"):
                report_text += f"""
REGULATORY COMPLIANCE (Dec 2025 / 2030 Standards)
{'-' * 70}
Fixed Heating in All Rooms: {'✓ CONFIRMED' if check_heating else '✗ NOT CONFIRMED'}
Blind Cord Safety: {'✓ CONFIRMED' if check_windows else '✗ NOT CONFIRMED'}
All-Electric / Heat Pump Ready: {'✓ CONFIRMED' if check_energy else '✗ NOT CONFIRMED'}
Compliance Score: {compliance_score}/3

"""
            
            if report_selections.get("Proximity & Transport"):
                report_text += f"""
PROXIMITY & TRANSPORT ANALYSIS
{'-' * 70}
Distance to Transport/Activity Centre: {dist_transport}m
Transport Catchment (800m): {'WITHIN' if is_transport_compliant else 'OUTSIDE'}
Status: {'COMPLIANT' if is_transport_compliant else 'REQUIRES TRAFFIC ENGINEERING ASSESSMENT'}

"""
            
            if report_selections.get("Risk Assessment & Constraints"):
                constraints = []
                if has_overlay:
                    constraints.append("• Heritage or Neighbourhood Character Overlay")
                if has_covenant:
                    constraints.append("• Single Dwelling Covenant on Title")
                if not is_preferred_zone:
                    constraints.append("• Zone Type Not Optimal (GRZ/RGZ Preferred)")
                if not is_transport_compliant:
                    constraints.append("• Outside 800m Transport Catchment")
                if not is_width_compliant:
                    constraints.append("• Lot Width Below Minimum (14m)")
                if not is_depth_compliant:
                    constraints.append("• Lot Depth Below Minimum (24m)")
                if not is_area_compliant:
                    constraints.append("• Lot Area Below Minimum (336 sqm)")
                if slope == "Steep":
                    constraints.append("• Steep Site Slope - High SDA Access Costs")
                
                report_text += f"""
RISK ASSESSMENT & CONSTRAINTS
{'-' * 70}
Identified Constraints:
{chr(10).join(constraints) if constraints else 'No significant constraints identified.'}

Overall Risk Level: {'LOW' if viability_color == 'green' else ('MODERATE' if viability_color == 'orange' else 'HIGH')}

"""
            
            if report_selections.get("Recommendations"):
                report_text += f"""
RECOMMENDATIONS
{'-' * 70}
{chr(10).join(recommendations)}

Next Steps:
- Engage local architect for detailed site assessment
- Commission geotechnical survey if slope > 5%
- Obtain formal council pre-lodgement advice
- Engage town planning consultant for zoning confirmation

"""
            
            if assessor_notes.strip():
                report_text += f"""
ASSESSOR NOTES
{'-' * 70}
{assessor_notes}

"""
            
            report_text += f"""
{'=' * 70}
Report generated by Vic Rooming House Assessor
Date: {datetime.now().strftime('%d %B %Y at %H:%M')}
"""
            
            st.success("✅ Report generated successfully!")
            
            st.text_area(
                "Report Content",
                value=report_text,
                height=400,
                disabled=True
            )
            
            st.download_button(
                label="📥 Download Report as Text",
                data=report_text,
                file_name=f"RoomingHouseAssessment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
else:
    if not st.session_state.assessment_complete and address_input:
        st.info("👆 Click the 'Assess Site' button to analyze the address")
    else:
        st.info("👆 Enter a site address and click 'Assess Site' to begin the assessment")
