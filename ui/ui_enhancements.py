"""
UI enhancements for UR Happy Home Site Assessor.
Modern dark glass styling tuned for Streamlit dashboard layouts.
"""

from datetime import datetime
from urllib.parse import quote_plus

import streamlit as st

BASE_BG = "#0a0f13"
PASS_GLOW = "#2ecc71"
GLASS_BG = "rgba(255, 255, 255, 0.03)"
GLASS_BORDER = "rgba(255, 255, 255, 0.08)"
TEXT_PRIMARY = "#E8EAED"
TEXT_MUTED = "#A9B3BE"

PROJECT_TYPES = [
    "Standard Rooming House",
    "SDA/NDIS Unit",
    "Standard Dual Occupancy",
]

PROJECT_TYPE_SUBTITLES = {
    "Standard Rooming House": "Rooming House Requirements",
    "SDA/NDIS Unit": "SDA/NDIS Requirements",
    "Standard Dual Occupancy": "Dual Occupancy Requirements",
}


def apply_archistar_aesthetic():
    """Apply the core dashboard aesthetic across the app."""
    st.markdown(
        f"""
        <style>
        html, body, .stApp, [data-testid="stAppViewContainer"], main {{
            background: {BASE_BG} !important;
            background-color: {BASE_BG} !important;
            color: {TEXT_PRIMARY} !important;
        }}

        p, div, span, h1, h2, h3, h4, h5, h6, label {{
            color: {TEXT_PRIMARY};
        }}

        [data-testid="stSidebar"] {{
            background: {BASE_BG} !important;
            border-right: 1px solid {GLASS_BORDER} !important;
        }}

        [data-testid="stVerticalBlockBorderWrapper"],
        [data-testid="stMetricContainer"],
        [data-testid="stAlert"],
        [data-testid="stExpander"],
        [data-testid="stExpanderDetails"],
        .stTabs [data-baseweb="tab-panel"] {{
            background: {GLASS_BG} !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border: 1px solid {GLASS_BORDER} !important;
            border-radius: 14px !important;
        }}

        .stButton > button,
        .stDownloadButton > button,
        [data-testid="baseButton-secondary"] {{
            background: {GLASS_BG} !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {GLASS_BORDER} !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
        }}

        [data-testid="stLinkButton"] a,
        [data-testid="stLinkButton"] button {{
            width: 100% !important;
            display: inline-flex !important;
            justify-content: center !important;
            align-items: center !important;
            background: linear-gradient(135deg, {PASS_GLOW}, #1f7f4c) !important;
            color: #ffffff !important;
            border: 1px solid rgba(46, 204, 113, 0.65) !important;
            border-radius: 12px !important;
            padding: 0.58rem 0.95rem !important;
            font-weight: 700 !important;
            box-shadow: 0 6px 18px rgba(46, 204, 113, 0.28) !important;
            text-decoration: none !important;
        }}

        [data-testid="stLinkButton"] a:hover,
        [data-testid="stLinkButton"] button:hover {{
            filter: brightness(1.05) !important;
            box-shadow: 0 8px 22px rgba(46, 204, 113, 0.42) !important;
            transform: translateY(-1px);
        }}

        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] > div {{
            background: {GLASS_BG} !important;
            color: {TEXT_PRIMARY} !important;
            border: 1px solid {GLASS_BORDER} !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
        }}

        .pass-glow,
        .status-pass,
        .status-pass * {{
            color: {PASS_GLOW} !important;
            text-shadow: 0 0 10px rgba(46, 204, 113, 0.85), 0 0 20px rgba(46, 204, 113, 0.35) !important;
        }}

        .glass-tile {{
            background: {GLASS_BG};
            border: 1px solid {GLASS_BORDER};
            border-radius: 14px;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 1rem;
            margin-bottom: 0.7rem;
        }}

        .tile-label {{
            font-size: 0.76rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: {TEXT_MUTED};
            margin-bottom: 0.3rem;
            font-weight: 600;
        }}

        .tile-value {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            line-height: 1.3;
        }}

        .tile-subtitle {{
            font-size: 0.8rem;
            color: {TEXT_MUTED};
            margin-top: 0.25rem;
            line-height: 1.3;
        }}

        [data-testid="stMetricLabel"] {{
            color: {TEXT_MUTED} !important;
        }}

        [data-testid="stMetricValue"] {{
            color: {TEXT_PRIMARY} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_professional_styling():
    """Backward-compatible alias used by app modules."""
    apply_archistar_aesthetic()


def render_project_type_selector(default_project_type: str = "Standard Rooming House") -> str:
    """Render project type selector for multi-engine scoring and return selected value."""
    if default_project_type not in PROJECT_TYPES:
        default_project_type = PROJECT_TYPES[0]

    return st.selectbox(
        "Project Type",
        PROJECT_TYPES,
        index=PROJECT_TYPES.index(default_project_type),
        key="project_type_selector",
        help="Select the housing model to apply the correct assessment logic and revenue assumptions.",
    )


def get_project_type_subtitle(project_type: str) -> str:
    """Return a concise subtitle fragment for the selected project type."""
    return PROJECT_TYPE_SUBTITLES.get(project_type, "Assessment Requirements")


def _nearest_hospital_distance_m(assessment_data: dict) -> float | None:
    """Extract nearest hospital distance from amenities summary if available."""
    amenities = (assessment_data or {}).get("amenities_summary", {}) or {}
    hospitals = amenities.get("hospitals", []) or []

    distances = []
    for item in hospitals:
        if not isinstance(item, dict):
            continue
        distance = item.get("distance_m")
        if distance is None:
            continue
        try:
            distances.append(float(distance))
        except (TypeError, ValueError):
            continue

    return min(distances) if distances else None


def render_sda_hospital_proximity_tile(assessment_data: dict):
    """Render SDA-specific hospital proximity tile using <=5km target."""
    nearest_hospital_m = _nearest_hospital_distance_m(assessment_data)
    threshold_m = 5000.0

    if nearest_hospital_m is None:
        render_infographic_pod(
            "Hospital Proximity",
            "Data Unavailable",
            icon="🏥",
            subtitle="SDA target: nearest hospital within 5.0 km",
            status="warning",
        )
        return

    nearest_km = nearest_hospital_m / 1000.0
    is_within_target = nearest_hospital_m <= threshold_m
    render_infographic_pod(
        "Hospital Proximity",
        f"{nearest_km:.1f} km",
        icon="🏥",
        subtitle="SDA target: nearest hospital within 5.0 km",
        status="pass" if is_within_target else "fail",
    )


def apply_dark_theme_styling():
    """Backward-compatible alias used by app modules."""
    apply_archistar_aesthetic()


def render_header_banner(title, subtitle="", icon="🏠"):
    """Render a simple glass-style header banner."""
    st.markdown(
        f"""
        <div class="glass-tile" style="margin-bottom: 1rem;">
            <h1 style="margin:0; font-size:2rem;">{icon} {title}</h1>
            {f'<div class="tile-subtitle" style="font-size:0.95rem; margin-top:0.35rem;">{subtitle}</div>' if subtitle else ''}
            <div class="tile-subtitle" style="margin-top:0.5rem;">Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(value, label, delta="", delta_color="neutral", icon=""):
    """Render a metric card using the shared glass style."""
    delta_palette = {
        "positive": PASS_GLOW,
        "negative": "#e74c3c",
        "neutral": TEXT_MUTED,
    }
    delta_color_value = delta_palette.get(delta_color, TEXT_MUTED)
    delta_html = f"<span style='color:{delta_color_value}; margin-left:0.4rem;'>{delta}</span>" if delta else ""

    st.markdown(
        f"""
        <div class="glass-tile" style="text-align:center;">
            <div style="font-size:1.2rem; margin-bottom:0.35rem;">{icon}</div>
            <div class="tile-value" style="font-size:1.55rem;">{value}</div>
            <div class="tile-subtitle">{label}{delta_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_badge(status, value, icon="", color_type="info"):
    """Render a compact status badge and return HTML for inline use."""
    palette = {
        "success": PASS_GLOW,
        "warning": "#f39c12",
        "danger": "#e74c3c",
        "info": "#6fb7ff",
    }
    color = palette.get(color_type, palette["info"])
    glow = "box-shadow: 0 0 12px rgba(46,204,113,0.45);" if color_type == "success" else ""

    return (
        f"<span style='display:inline-block; padding:0.45rem 0.85rem; border-radius:999px;"
        f" border:1px solid {GLASS_BORDER}; background:{GLASS_BG}; color:{color}; {glow}'>"
        f"{icon} {status}: <strong>{value}</strong></span>"
    )


def render_external_research_command_center(address: str):
    """Render right-sidebar command center with pre-filled external research links."""
    st.markdown("### 🔎 External Research Command Center")

    clean_address = (address or "").strip()
    if not clean_address:
        st.info("Search a site address to enable external research links.")
        return

    encoded = quote_plus(clean_address)
    realestate_url = f"https://www.realestate.com.au/buy/?q={encoded}"
    domain_url = f"https://www.domain.com.au/sale/?q={encoded}"
    landata_url = f"https://www.landata.vic.gov.au/?q={encoded}"

    st.link_button("🏘️ Open on realestate.com.au", realestate_url, use_container_width=True)
    st.link_button("🏡 Open on domain.com.au", domain_url, use_container_width=True)
    st.link_button("📜 Open land.vic.gov.au Title Search", landata_url, use_container_width=True)
    st.link_button(
        "🛠️ Open BYDA (Before You Dig Australia)",
        "https://www.byda.com.au/?utm_source=g_ads&utm_medium=cpc&utm_format=search&utm_campaign=byda_brand&utm_client=byda_&_lual&gad_source=1&gad_campaignid=21903255529&gbraid=0AAAAAC1_t6EFjRiOz4xUPVFwGq_yvmDTj&gclid=Cj0KCQiAtfXMBhDzARIsAJ0jp3BNP7Bhk3bHY2pGKYvKmGAuZvicgxn502V5DzBaf2nBb4iWsluKsdMaAgxHEALw_wcB",
        use_container_width=True,
    )
    st.link_button(
        "🏘️ Open HousingHub",
        "https://www.housinghub.org.au/",
        use_container_width=True,
    )
    st.link_button(
        "📈 OpenAgent Property Reports",
        "https://www.openagent.com.au/property-reports/?ref=3&utm_source=google&utm_medium=cpc&utm_campaign=PropertyReport&matchtype=p&keyword=property%20evaluator&device=c&adposition=&network=g&creative=694686930659&cg=property-report&aceid=&campaignid=12266581576&adgroupid=160373079019&gad_source=1&gad_campaignid=12266581576&gbraid=0AAAAADtG_gSNM2-bD4I7_s0GFl_HPyjre&gclid=CjwKCAiAkvDMBhBMEiwAnUA9Be_YqCHj2rsRgEPeA1JcrF8jIZrxJ551IPOI4wllRj-M7AmHRIOs1hoCZLwQAvD_BwE",
        use_container_width=True,
    )
    st.link_button(
        "📋 Consumer VIC Due Diligence",
        "https://www.consumer.vic.gov.au/housing/buying-and-selling-property/checklists/due-diligence",
        use_container_width=True,
    )
    st.link_button(
        "🔗 Google Link 1",
        "https://www.google.com/aclk?sa=L&ai=DChsSEwjHsOC54_CSAxXGpWYCHeyqAZMYACICCAEQARoCc20&co=1&ase=2&gclid=CjwKCAiAkvDMBhBMEiwAnUA9BQ1vcYVBz9Z2jpOc_XJW-_Z4xkoS-V8OaRMhiRUXYp5MTMGJJbPupxoCnJkQAvD_BwE&cid=CAAS0gHkaA2bG9AnXneFD9VgrcBeFU9-47PVWdjSImUzgmRw5DY0j6AbqExdcfdbrgxa92-XtJSY_74ml2g4ALBv0cWgjy7f0okNxDIeKZtSWN0BdC3Q5t37R6rnR5SLBixvkIFI020jjR2GXSPmeF8GAHHSrfHwUI7P3Emnda9gAYbVOP-nb3h2pLWym_C5tE_wR9dVwmsvLFMXeY6NtPteQpJo3FMHGcJ9CN5TTGL-m5ve18mWsfNNZSodAGVt1zPlskkfh-BzPNXDFF5gRbAFSsjUNU0&cce=2&category=acrcp_v1_32&sig=AOD64_3Y88m2_k_pukFq66ZH9iECz6u3nw&q&nis=4&adurl&ved=2ahUKEwiantu54_CSAxVX-DgGHQ5EA68Q0Qx6BAgpEAE",
        use_container_width=True,
    )
    st.link_button(
        "🔗 Google Link 2",
        "https://www.google.com/aclk?sa=L&ai=DChsSEwjHsOC54_CSAxXGpWYCHeyqAZMYACICCAEQAxoCc20&co=1&ase=2&gclid=CjwKCAiAkvDMBhBMEiwAnUA9BVjSd2_NVW5zBTnzs7uEWIif8jNonZHyh8etfFVhGcqUENDEbV5m2xoC8ikQAvD_BwE&cid=CAAS0gHkaA2bG9AnXneFD9VgrcBeFU9-47PVWdjSImUzgmRw5DY0j6AbqExdcfdbrgxa92-XtJSY_74ml2g4ALBv0cWgjy7f0okNxDIeKZtSWN0BdC3Q5t37R6rnR5SLBixvkIFI020jjR2GXSPmeF8GAHHSrfHwUI7P3Emnda9gAYbVOP-nb3h2pLWym_C5tE_wR9dVwmsvLFMXeY6NtPteQpJo3FMHGcJ9CN5TTGL-m5ve18mWsfNNZSodAGVt1zPlskkfh-BzPNXDFF5gRbAFSsjUNU0&cce=2&category=acrcp_v1_32&sig=AOD64_3j2pDdaJFQxIVNsne1JWvRI1xsUQ&q&nis=4&adurl&ved=2ahUKEwiantu54_CSAxVX-DgGHQ5EA68Q0Qx6BAgrEAQ",
        use_container_width=True,
    )
    st.link_button(
        "📰 Smart Property Investment Article",
        "https://www.smartpropertyinvestment.com.au/hotspots/15930-online-tool-makes-due-diligence-easy-for-investors",
        use_container_width=True,
    )


def render_infographic_pod(
    label: str,
    value: str,
    icon: str = "📊",
    subtitle: str = "",
    status: str = "neutral",
):
    """Render a glass tile pod with status-driven color treatment."""
    status = (status or "neutral").lower().strip()
    status_styles = {
        "pass": {
            "color": PASS_GLOW,
            "border": "rgba(46, 204, 113, 0.55)",
            "shadow": "0 0 14px rgba(46, 204, 113, 0.55), 0 0 28px rgba(46, 204, 113, 0.24)",
            "value_class": "pass-glow",
        },
        "warning": {
            "color": "#f39c12",
            "border": "rgba(243, 156, 18, 0.45)",
            "shadow": "0 0 14px rgba(243, 156, 18, 0.35)",
            "value_class": "",
        },
        "fail": {
            "color": "#e74c3c",
            "border": "rgba(231, 76, 60, 0.45)",
            "shadow": "0 0 14px rgba(231, 76, 60, 0.35)",
            "value_class": "",
        },
        "neutral": {
            "color": TEXT_PRIMARY,
            "border": GLASS_BORDER,
            "shadow": "none",
            "value_class": "",
        },
    }
    style = status_styles.get(status, status_styles["neutral"])

    st.markdown(
        f"""
        <div class="glass-tile {'status-pass' if status == 'pass' else ''}" style="border-color:{style['border']}; box-shadow:{style['shadow']};">
            <div class="tile-label">{icon} {label}</div>
            <div class="tile-value {style['value_class']}">{value}</div>
            {f'<div class="tile-subtitle">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_infographic_tile(
    label: str,
    value: str,
    icon: str = "📊",
    color: str = "neutral",
    high_fidelity: bool = False,
):
    """Render an infographic tile with subtle bottom-border glow.

    Args:
        label: Tile label.
        value: Main tile value.
        icon: Leading icon.
        color: One of neutral|pass|warning|fail.
    """
    color_key = (color or "neutral").lower().strip()

    palette = {
        "neutral": {
            "value": TEXT_PRIMARY,
            "glow": "rgba(255, 255, 255, 0.12)",
            "text_shadow": "none",
        },
        "pass": {
            "value": PASS_GLOW,
            "glow": "rgba(46, 204, 113, 0.45)",
            "text_shadow": "0 0 10px rgba(46, 204, 113, 0.75), 0 0 18px rgba(46, 204, 113, 0.35)",
        },
        "warning": {
            "value": "#f39c12",
            "glow": "rgba(243, 156, 18, 0.35)",
            "text_shadow": "none",
        },
        "fail": {
            "value": "#e74c3c",
            "glow": "rgba(231, 76, 60, 0.35)",
            "text_shadow": "none",
        },
    }
    style = palette.get(color_key, palette["neutral"])

    tile_bg = "rgba(255, 255, 255, 0.05)" if high_fidelity else "rgba(255, 255, 255, 0.03)"
    tile_blur = "20px" if high_fidelity else "16px"
    tile_shadow = (
        f"0 10px 30px rgba(0, 0, 0, 0.28), 0 6px 18px {style['glow']}"
        if high_fidelity
        else f"0 8px 26px rgba(0, 0, 0, 0.25), 0 4px 16px {style['glow']}"
    )

    st.markdown(
        f"""
        <div style="
            background: {tile_bg};
            border: 1px solid {GLASS_BORDER};
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 0.7rem;
            backdrop-filter: blur({tile_blur});
            -webkit-backdrop-filter: blur({tile_blur});
            border-bottom: 2px solid {style['glow']};
            box-shadow: {tile_shadow};
        ">
            <div class="tile-label">{icon} {label}</div>
            <div class="tile-value" style="color:{style['value']}; text-shadow:{style['text_shadow']};">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_donut(score: float, max_score: float = 100, label: str = "Overall", status: str = "conditional"):
    """Render a compact donut score visualization."""
    safe_max = max(max_score, 1)
    pct = max(0.0, min(100.0, (float(score) / safe_max) * 100.0))

    color_map = {
        "suitable": PASS_GLOW,
        "conditional": "#f39c12",
        "unsuitable": "#e74c3c",
    }
    color = color_map.get(status, "#6fb7ff")

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin:0.25rem 0 0.75rem 0;">
            <div style="
                width:120px;
                height:120px;
                border-radius:50%;
                background: conic-gradient({color} {pct:.1f}%, rgba(255,255,255,0.10) {pct:.1f}% 100%);
                display:flex;
                align-items:center;
                justify-content:center;
                box-shadow: 0 0 22px rgba(0,0,0,0.35);
            ">
                <div style="
                    width:82px;
                    height:82px;
                    border-radius:50%;
                    background:{BASE_BG};
                    border:1px solid {GLASS_BORDER};
                    display:flex;
                    flex-direction:column;
                    align-items:center;
                    justify-content:center;
                ">
                    <div style="font-size:1.15rem; font-weight:700; color:{TEXT_PRIMARY};">{float(score):.0f}</div>
                    <div style="font-size:0.7rem; color:{TEXT_MUTED};">{label}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_bar(label: str, value: float, max_value: float, status: str = "success"):
    """Render a styled horizontal progress bar."""
    safe_max = max(max_value, 1)
    pct = max(0.0, min(100.0, (float(value) / safe_max) * 100.0))
    status = (status or "success").lower()

    bar_colors = {
        "success": PASS_GLOW,
        "warning": "#f39c12",
        "danger": "#e74c3c",
    }
    color = bar_colors.get(status, PASS_GLOW)
    glow = "0 0 12px rgba(46, 204, 113, 0.65)" if status == "success" else "none"

    st.markdown(
        f"""
        <div style="margin: 0.45rem 0 0.65rem 0;">
            <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:{TEXT_MUTED}; margin-bottom:0.3rem;">
                <span>{label}</span>
                <span>{float(value):.0f}/{float(max_value):.0f}</span>
            </div>
            <div style="height:8px; border-radius:999px; background:rgba(255,255,255,0.10); overflow:hidden; border:1px solid {GLASS_BORDER};">
                <div style="height:100%; width:{pct:.1f}%; background:{color}; box-shadow:{glow};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
