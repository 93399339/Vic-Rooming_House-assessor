import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Vic Rooming House Assessor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# MOCK GEOCODING & CONSTANTS
# -----------------------------------------------------------------------------
# In a real app, you would use: from geopy.geocoders import GoogleV3
# For this prototype, we mock a location (e.g., a site in Ringwood, Victoria)
MOCK_LAT = -37.815
MOCK_LON = 145.23
Future_Homes_Radius_Meters = 800

# -----------------------------------------------------------------------------
# SIDEBAR: SITE INPUTS
# -----------------------------------------------------------------------------
st.sidebar.header("📍 Site Details")

# 1. Location & Zoning
st.sidebar.subheader("1. Location & Zoning")
address = st.sidebar.text_input("Site Address", "123 Example St, Victoria")
zone_type = st.sidebar.selectbox(
    "Planning Zone",
    ("General Residential Zone (GRZ)", "Residential Growth Zone (RGZ)", "Neighbourhood Residential Zone (NRZ)", "Commercial/Other")
)
dist_transport = st.sidebar.number_input(
    "Distance to Train/Activity Centre (m)", 
    min_value=0, 
    value=650, 
    step=50,
    help="Distance to nearest PPTV station or Major Activity Centre."
)
has_overlay = st.sidebar.checkbox(
    "Heritage / Neighbourhood Character Overlay?", 
    value=False,
    help="Check this if the VicPlan report shows HO or NCO overlays."
)

# 2. Physical Suitability
st.sidebar.subheader("2. Physical Suitability")
lot_width = st.sidebar.number_input("Lot Width (m)", min_value=5.0, value=15.0, step=0.5)
lot_area = st.sidebar.number_input("Lot Area (sqm)", min_value=100, value=750, step=10)
slope = st.sidebar.select_slider(
    "Site Slope", 
    options=["Flat", "Moderate", "Steep"],
    value="Flat"
)
has_covenant = st.sidebar.checkbox(
    "Single Dwelling Covenant?", 
    value=False,
    help="Check title for restrictive covenants."
)

# 3. Regulatory Compliance (2025-2030)
st.sidebar.subheader("3. Compliance Checklist")
check_heating = st.sidebar.checkbox("Dec 2025: Fixed Heating in ALL rooms")
check_windows = st.sidebar.checkbox("Dec 2025: Blind cords secured")
check_energy = st.sidebar.checkbox("2030: All-electric / Heat pump ready")

# -----------------------------------------------------------------------------
# ASSESSMENT ALGORITHM
# -----------------------------------------------------------------------------

# Derived Variables
is_preferred_zone = zone_type in ["General Residential Zone (GRZ)", "Residential Growth Zone (RGZ)"]
is_transport_compliant = dist_transport <= 800
is_width_compliant = lot_width >= 12
is_area_compliant = lot_area >= 600

# Traffic Light Logic
viability_color = "RED"
viability_status = "NOT SUITABLE"
viability_message = "Critical constraints detected."

# Logic Tree
if has_overlay or has_covenant:
    # HARD FAIL conditions
    viability_color = "red"
    viability_status = "NOT SUITABLE (RED)"
    if has_overlay:
        viability_message = "FAIL: Site has Heritage or Character Overlay."
    else:
        viability_message = "FAIL: Title contains Single Dwelling Covenant."

elif not is_preferred_zone:
    # Wrong Zone (NRZ or Commercial usually hard for Rooming Houses under Future Homes)
    viability_color = "red"
    viability_status = "HIGH RISK (RED)"
    viability_message = "Zone is not GRZ or RGZ. Unlikely to support density."

elif is_preferred_zone and not is_transport_compliant:
    # AMBER: Good zone, but bad location
    viability_color = "orange"
    viability_status = "CONDITIONAL (AMBER)"
    viability_message = "Meets zoning, but outside 800m transport catchment. Traffic Engineering report required."

elif not is_width_compliant or not is_area_compliant:
    # AMBER/RED: Physical constraints
    viability_color = "orange"
    viability_status = "PHYSICAL CONSTRAINTS (AMBER)"
    msg = []
    if not is_width_compliant: msg.append("Too narrow (<12m).")
    if not is_area_compliant: msg.append("Lot too small (<600sqm).")
    viability_message = " ".join(msg)

else:
    # GREEN: The Gold Standard
    viability_color = "green"
    viability_status = "HIGHLY SUITABLE (GREEN)"
    viability_message = "Site meets all key Future Homes & Rooming House criteria."

# -----------------------------------------------------------------------------
# MAIN DASHBOARD
# -----------------------------------------------------------------------------

st.title("🏗️ Victorian Rooming House Site Assessor")
st.markdown(f"**Site:** {address}")

# --- SCORECARD SECTION ---
st.divider()
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("### Viability Score")
    if viability_color == "green":
        st.success(f"## {viability_status}")
    elif viability_color == "orange":
        st.warning(f"## {viability_status}")
    else:
        st.error(f"## {viability_status}")
    st.info(f"**Reason:** {viability_message}")

with c2:
    st.markdown("### Physical Metrics")
    # Lot Width
    w_delta = "OK" if is_width_compliant else "-NARROW"
    st.metric("Lot Width", f"{lot_width}m", delta=w_delta, delta_color="normal" if is_width_compliant else "inverse")
    
    # Lot Area
    a_delta = "OK" if is_area_compliant else "-SMALL"
    st.metric("Lot Area", f"{lot_area} sqm", delta=a_delta, delta_color="normal" if is_area_compliant else "inverse")

with c3:
    st.markdown("### Risk Flags")
    if slope == "Steep":
        st.error("⚠️ Steep Slope: SDA Access Costs High")
    elif slope == "Moderate":
        st.warning("⚠️ Moderate Slope: Check Cut/Fill")
    else:
        st.success("✅ Flat Site: Ideal for Class 1b")
        
    compliance_score = sum([check_heating, check_windows, check_energy])
    st.progress(compliance_score / 3, text=f"Regulatory Readiness: {compliance_score}/3")

# --- MAP SECTION ---
st.divider()
st.subheader(f"📍 Proximity Visualization (800m Buffer)")

m = folium.Map(location=[MOCK_LAT, MOCK_LON], zoom_start=14)

# Draw the 800m "Future Homes" catchment circle
folium.Circle(
    radius=800,
    location=[MOCK_LAT, MOCK_LON],
    color="blue",
    fill=True,
    fill_opacity=0.1,
    popup="800m Transport Catchment"
).add_to(m)

# Draw the Site Marker
icon_color = "green" if viability_color == "green" else ("orange" if viability_color == "orange" else "red")
folium.Marker(
    [MOCK_LAT, MOCK_LON],
    popup=address,
    icon=folium.Icon(color=icon_color, icon="home")
).add_to(m)

# Render map in Streamlit
st_data = st_folium(m, width="100%", height=400)

st.caption("ℹ️ Map centered on mock coordinates for prototype. In production, this connects to Google Geocoding API.")

# --- COMPLIANCE DETAIL SECTION ---
st.divider()
with st.expander("📋 Regulatory Compliance Detail (2025/2030 Standards)", expanded=True):
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**Mandatory Checks (Dec 2025)**")
        if check_heating:
            st.success("✅ Heating capacity confirmed for all resident rooms.")
        else:
            st.error("❌ MISSING: Must budget for fixed electrical heating in 5 bedrooms.")
            
        if check_windows:
            st.success("✅ Window coverings compliant.")
        else:
            st.error("❌ MISSING: Blind cord safety budget required.")

    with col_b:
        st.markdown("**Future Proofing (2030)**")
        if check_energy:
            st.success("✅ All-electric design confirmed.")
        else:
            st.warning("⚠️ RISK: Gas connections may become obsolete/costly by 2030.")
