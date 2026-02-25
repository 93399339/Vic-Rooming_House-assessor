"""
Professional due diligence PDF generator using fpdf2.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple
import math
import os
import tempfile
from io import BytesIO
from urllib.parse import quote_plus

import requests

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:
    Image = None
    ImageDraw = None


DISCLAIMER_TEXT = (
    "Professional Preliminary Assessment: This report is for initial due-diligence screening only and is not a formal valuation, "
    "credit decision, legal opinion, planning permit advice, or surveying certificate. Independent professional verification is required "
    "before acquisition, lending, or development commitment."
)

PROJECT_TYPE_ROOMING = "Standard Rooming House"
PROJECT_TYPE_SDA = "SDA/NDIS Unit"
PROJECT_TYPE_DUAL_OCC = "Standard Dual Occupancy"


def _safe_text(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _safe_number(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _collect_design_reasons(assessment_data: Dict[str, Any]) -> List[str]:
    design_validation = assessment_data.get("urhh_design_validation", {}) or {}
    reasons = design_validation.get("reasons", [])
    if isinstance(reasons, list):
        return [str(reason) for reason in reasons if str(reason).strip()]
    return []


def _risk_flags(assessment_data: Dict[str, Any]) -> List[Tuple[str, bool]]:
    risk_checks = assessment_data.get("planning_risk_checks", {}) or {}
    return [
        (
            "Planning overlays present",
            bool(assessment_data.get("has_overlay", False)),
        ),
        (
            "Aboriginal cultural heritage sensitivity",
            bool(
                risk_checks.get(
                    "aboriginal_cultural_heritage_sensitivity",
                    assessment_data.get("aboriginal_cultural_heritage_sensitivity", False),
                )
            ),
        ),
        (
            "Special building overlay / flood risk",
            bool(
                risk_checks.get(
                    "special_building_overlay_flood_risk",
                    assessment_data.get("special_building_overlay_flood_risk", False),
                )
            ),
        ),
    ]


def _full_width_multicell(pdf, line_height: float, text: str) -> None:
    """Render multiline text using full printable width and reset cursor safely."""
    width = max(20, pdf.w - pdf.l_margin - pdf.r_margin)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(width, line_height, text, new_x="LMARGIN", new_y="NEXT")


def _full_width_cell(pdf, line_height: float, text: str) -> None:
    """Render single-line text across full printable width from left margin."""
    pdf.set_x(pdf.l_margin)
    pdf.cell(0, line_height, text, ln=1)


def _coord_pair(assessment_data: Dict[str, Any]) -> Tuple[float, float] | Tuple[None, None]:
    lat = assessment_data.get("latitude")
    lon = assessment_data.get("longitude")
    try:
        if lat is not None and lon is not None:
            return float(lat), float(lon)
    except (TypeError, ValueError):
        pass
    return None, None


def _latlon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[float, float]:
    n = 2.0**zoom
    x = (lon + 180.0) / 360.0 * n
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return x, y


def _build_map_snapshot(lat: float, lon: float, zoom: int = 16, tile_span: int = 3) -> Tuple[str | None, str]:
    """Build a static map image by stitching OpenStreetMap tiles around the subject point."""
    if Image is None or ImageDraw is None:
        return None, "Map library unavailable"

    tile_size = 256
    tiles = max(1, int(tile_span))
    half = tiles // 2

    center_x, center_y = _latlon_to_tile(lat, lon, zoom)
    center_xtile = int(math.floor(center_x))
    center_ytile = int(math.floor(center_y))
    world_tiles = 2**zoom

    canvas = Image.new("RGB", (tiles * tile_size, tiles * tile_size), color=(240, 240, 240))
    session = requests.Session()
    session.headers.update({"User-Agent": "URHappyHomeSiteAssessor/1.0"})

    fetched_any = False
    for row in range(tiles):
        for col in range(tiles):
            xtile = (center_xtile - half + col) % world_tiles
            ytile = center_ytile - half + row
            if ytile < 0 or ytile >= world_tiles:
                continue

            url = f"https://tile.openstreetmap.org/{zoom}/{xtile}/{ytile}.png"
            try:
                response = session.get(url, timeout=10)
                response.raise_for_status()
                tile = Image.open(BytesIO(response.content)).convert("RGB")
                canvas.paste(tile, (col * tile_size, row * tile_size))
                fetched_any = True
            except Exception:
                continue

    if not fetched_any:
        return None, "OSM tiles unavailable"

    frac_x = center_x - center_xtile
    frac_y = center_y - center_ytile
    px = (half + frac_x) * tile_size
    py = (half + frac_y) * tile_size

    draw = ImageDraw.Draw(canvas)
    outer_r = 11
    inner_r = 5
    draw.ellipse((px - outer_r, py - outer_r, px + outer_r, py + outer_r), fill=(220, 53, 69), outline=(255, 255, 255), width=2)
    draw.ellipse((px - inner_r, py - inner_r, px + inner_r, py + inner_r), fill=(255, 255, 255))

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    canvas.save(temp_file.name, format="PNG")
    temp_file.close()
    return temp_file.name, "Map source: © OpenStreetMap contributors"


def _render_kv_table(pdf, rows: List[Tuple[str, str]], col1: float = 65, row_h: float = 7) -> None:
    """Render a simple 2-column key-value table."""
    total_w = pdf.w - pdf.l_margin - pdf.r_margin
    col2 = max(30, total_w - col1)

    pdf.set_fill_color(245, 247, 250)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(pdf.l_margin)
    pdf.cell(col1, row_h + 1, "Metric", border=1, fill=True)
    pdf.cell(col2, row_h + 1, "Value", border=1, ln=1, fill=True)

    pdf.set_font("Helvetica", "", 10)
    for key, value in rows:
        pdf.set_x(pdf.l_margin)
        pdf.cell(col1, row_h, _safe_text(key), border=1)
        pdf.cell(col2, row_h, _safe_text(value), border=1, ln=1)


def _resolve_reference_links(assessment_data: Dict[str, Any]) -> List[Tuple[str, str]]:
    vpp = assessment_data.get("vpp_links", {}) or {}
    zone_title = _safe_text(vpp.get("title"), "Victorian Planning Provisions")

    lat, lon = _coord_pair(assessment_data)
    if lat is not None and lon is not None:
        vicplan_url = f"https://mapshare.vic.gov.au/vicplan/?x={lon:.6f}&y={lat:.6f}&z=17"
    else:
        vicplan_url = "https://mapshare.vic.gov.au/vicplan/"

    address = _safe_text(assessment_data.get("address"), "")
    encoded_address = quote_plus(address) if address else ""
    realestate_url = (
        f"https://www.realestate.com.au/buy/?q={encoded_address}"
        if encoded_address
        else "https://www.realestate.com.au/"
    )

    return [
        (f"Open Planning Framework ({zone_title})", "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses"),
        ("Open Clause 5.24 (Planning Framework)", "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses"),
        ("Open Clause 5.24 - Department Guidance", "https://www.planning.vic.gov.au/"),
        ("Open VicPlan Interactive Map", vicplan_url),
        ("Open Landata Title Search", "https://www.landata.online/"),
        ("Open Realestate.com.au for this address", realestate_url),
        ("Open BYDA - Before You Dig Australia", "https://www.byda.com.au/?utm_source=g_ads&utm_medium=cpc&utm_format=search&utm_campaign=byda_brand&utm_client=byda_&_lual&gad_source=1&gad_campaignid=21903255529&gbraid=0AAAAAC1_t6EFjRiOz4xUPVFwGq_yvmDTj&gclid=Cj0KCQiAtfXMBhDzARIsAJ0jp3BNP7Bhk3bHY2pGKYvKmGAuZvicgxn502V5DzBaf2nBb4iWsluKsdMaAgxHEALw_wcB"),
        ("Open HousingHub", "https://www.housinghub.org.au/"),
        ("Open OpenAgent Property Reports", "https://www.openagent.com.au/property-reports/?ref=3&utm_source=google&utm_medium=cpc&utm_campaign=PropertyReport&matchtype=p&keyword=property%20evaluator&device=c&adposition=&network=g&creative=694686930659&cg=property-report&aceid=&campaignid=12266581576&adgroupid=160373079019&gad_source=1&gad_campaignid=12266581576&gbraid=0AAAAADtG_gSNM2-bD4I7_s0GFl_HPyjre&gclid=CjwKCAiAkvDMBhBMEiwAnUA9Be_YqCHj2rsRgEPeA1JcrF8jIZrxJ551IPOI4wllRj-M7AmHRIOs1hoCZLwQAvD_BwE"),
        ("Open Consumer VIC Due Diligence Checklist", "https://www.consumer.vic.gov.au/housing/buying-and-selling-property/checklists/due-diligence"),
        ("Open Google Link 1", "https://www.google.com/aclk?sa=L&ai=DChsSEwjHsOC54_CSAxXGpWYCHeyqAZMYACICCAEQARoCc20&co=1&ase=2&gclid=CjwKCAiAkvDMBhBMEiwAnUA9BQ1vcYVBz9Z2jpOc_XJW-_Z4xkoS-V8OaRMhiRUXYp5MTMGJJbPupxoCnJkQAvD_BwE&cid=CAAS0gHkaA2bG9AnXneFD9VgrcBeFU9-47PVWdjSImUzgmRw5DY0j6AbqExdcfdbrgxa92-XtJSY_74ml2g4ALBv0cWgjy7f0okNxDIeKZtSWN0BdC3Q5t37R6rnR5SLBixvkIFI020jjR2GXSPmeF8GAHHSrfHwUI7P3Emnda9gAYbVOP-nb3h2pLWym_C5tE_wR9dVwmsvLFMXeY6NtPteQpJo3FMHGcJ9CN5TTGL-m5ve18mWsfNNZSodAGVt1zPlskkfh-BzPNXDFF5gRbAFSsjUNU0&cce=2&category=acrcp_v1_32&sig=AOD64_3Y88m2_k_pukFq66ZH9iECz6u3nw&q&nis=4&adurl&ved=2ahUKEwiantu54_CSAxVX-DgGHQ5EA68Q0Qx6BAgpEAE"),
        ("Open Google Link 2", "https://www.google.com/aclk?sa=L&ai=DChsSEwjHsOC54_CSAxXGpWYCHeyqAZMYACICCAEQAxoCc20&co=1&ase=2&gclid=CjwKCAiAkvDMBhBMEiwAnUA9BVjSd2_NVW5zBTnzs7uEWIif8jNonZHyh8etfFVhGcqUENDEbV5m2xoC8ikQAvD_BwE&cid=CAAS0gHkaA2bG9AnXneFD9VgrcBeFU9-47PVWdjSImUzgmRw5DY0j6AbqExdcfdbrgxa92-XtJSY_74ml2g4ALBv0cWgjy7f0okNxDIeKZtSWN0BdC3Q5t37R6rnR5SLBixvkIFI020jjR2GXSPmeF8GAHHSrfHwUI7P3Emnda9gAYbVOP-nb3h2pLWym_C5tE_wR9dVwmsvLFMXeY6NtPteQpJo3FMHGcJ9CN5TTGL-m5ve18mWsfNNZSodAGVt1zPlskkfh-BzPNXDFF5gRbAFSsjUNU0&cce=2&category=acrcp_v1_32&sig=AOD64_3j2pDdaJFQxIVNsne1JWvRI1xsUQ&q&nis=4&adurl&ved=2ahUKEwiantu54_CSAxVX-DgGHQ5EA68Q0Qx6BAgrEAQ"),
        ("Open Smart Property Investment Article", "https://www.smartpropertyinvestment.com.au/hotspots/15930-online-tool-makes-due-diligence-easy-for-investors"),
    ]


def _draw_action_button(pdf, text: str, url: str) -> None:
    button_height = 9
    gap_after = 2

    # Ensure we always draw within printable width and avoid right-edge overflow.
    available_width = pdf.w - pdf.l_margin - pdf.r_margin
    width = max(20, available_width)

    # Add a new page if there isn't enough room left for the full button block.
    if pdf.get_y() + button_height + gap_after > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_x(pdf.l_margin)
    x = pdf.get_x()
    y = pdf.get_y()

    pdf.set_fill_color(31, 127, 76)
    pdf.set_draw_color(31, 127, 76)
    pdf.rect(x, y, width, button_height, style="FD")

    pdf.set_xy(x, y + 2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(width, 5, text, align="C", link=url)

    pdf.set_text_color(24, 33, 45)
    pdf.set_xy(pdf.l_margin, y + button_height + gap_after)


class DueDiligencePDF:
    def __init__(self, fpdf_cls):
        class _ReportPDF(fpdf_cls):
            def footer(self):
                self.set_y(-15)
                self.set_x(self.l_margin)
                self.set_font("Helvetica", "", 7)
                self.set_text_color(125, 130, 135)
                self.cell(0, 4, DISCLAIMER_TEXT, 0, 1, "C")
                self.set_x(self.l_margin)
                self.cell(0, 4, f"Page {self.page_no()}", 0, 0, "C")

        self.pdf = _ReportPDF()
        self.pdf.set_auto_page_break(auto=True, margin=20)


def generate_due_diligence_pdf(assessment_data: Dict[str, Any]) -> bytes:
    """
    Build a professional due diligence PDF report with expanded intelligence details.
    """
    try:
        from fpdf import FPDF
    except ModuleNotFoundError:
        from professional_pdf_generator import create_professional_pdf_report

        fallback_pdf = create_professional_pdf_report(assessment_data)
        if hasattr(fallback_pdf, "getvalue"):
            return fallback_pdf.getvalue()
        if hasattr(fallback_pdf, "getbuffer"):
            return bytes(fallback_pdf.getbuffer())
        return bytes(fallback_pdf)

    report = DueDiligencePDF(FPDF)
    pdf = report.pdf
    pdf.add_page()
    temp_artifacts: List[str] = []

    address = _safe_text(assessment_data.get("address"), "Unknown Address")
    project_type = _safe_text(assessment_data.get("project_type"), PROJECT_TYPE_ROOMING)
    title_map = {
        PROJECT_TYPE_ROOMING: "Rooming House Site Assessment Report",
        PROJECT_TYPE_SDA: "SDA/NDIS Site Assessment Report",
        PROJECT_TYPE_DUAL_OCC: "Dual Occupancy Site Assessment Report",
    }
    report_title = title_map.get(project_type, f"{project_type} Site Assessment Report")
    vicplan_zone = _safe_text(
        assessment_data.get("vicplan_zone") or assessment_data.get("zone_type"),
        "Unknown",
    )

    score = _safe_number(assessment_data.get("raw_score"), 0)
    viability_status = _safe_text(assessment_data.get("viability_status"), "Pending")

    design_validation = assessment_data.get("urhh_design_validation", {}) or {}
    design_pass = bool(design_validation.get("pass_fail", False))
    design_reasons = _collect_design_reasons(assessment_data)

    revenue = assessment_data.get("revenue_potential", {}) or {}
    weekly_min = int(_safe_number(revenue.get("weekly_min"), 0))
    weekly_max = int(_safe_number(revenue.get("weekly_max"), 0))
    annual_min = int(_safe_number(revenue.get("annual_min"), 0))
    annual_max = int(_safe_number(revenue.get("annual_max"), 0))
    annual_midpoint = int((annual_min + annual_max) / 2) if annual_max else 0
    weekly_midpoint = int((weekly_min + weekly_max) / 2) if weekly_max else 0

    setback_requirements = (
        assessment_data.get("setback_requirements")
        or design_validation.get("setback_requirements")
        or {}
    )

    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(24, 33, 45)
    _full_width_cell(pdf, 10, f"UR Happy Home - {report_title}")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(92, 96, 104)
    _full_width_cell(pdf, 6, f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
    _full_width_cell(pdf, 6, f"Address: {address}")
    _full_width_cell(pdf, 6, f"Project Type: {project_type}")
    pdf.ln(4)

    pdf.set_draw_color(220, 224, 230)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(7)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(24, 33, 45)
    _full_width_cell(pdf, 7, "Executive Scorecard")
    pdf.ln(1)

    pdf.set_fill_color(245, 247, 250)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(55, 8, "Metric", border=1, fill=True)
    pdf.cell(135, 8, "Value", border=1, ln=1, fill=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(55, 8, "Viability Status", border=1)
    pdf.cell(135, 8, viability_status, border=1, ln=1)

    pdf.cell(55, 8, "Suitability Score", border=1)
    pdf.cell(135, 8, f"{score:.0f}/100", border=1, ln=1)

    pdf.cell(55, 8, "VicPlan Zone", border=1)
    pdf.cell(135, 8, vicplan_zone, border=1, ln=1)

    pdf.cell(55, 8, "URHH Design Suitability", border=1)
    pdf.cell(135, 8, "PASS" if design_pass else "REVIEW REQUIRED", border=1, ln=1)

    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Detailed Site & Parcel Intelligence")

    lot_refs = assessment_data.get("lot_area_references", []) or []
    lot_ref_text = " | ".join(
        [f"{_safe_text(ref.get('source'))}: {_safe_number(ref.get('area_sqm')):.0f} m²" for ref in lot_refs[:3] if isinstance(ref, dict)]
    )
    if not lot_ref_text:
        lot_ref_text = _safe_text(assessment_data.get("lot_area_source"), "Not specified")

    lat, lon = _coord_pair(assessment_data)
    coord_text = f"{lat:.6f}, {lon:.6f}" if lat is not None and lon is not None else "N/A"

    _render_kv_table(
        pdf,
        [
            ("Address", address),
            ("Coordinates", coord_text),
            ("Lot Geometry", f"{_safe_number(assessment_data.get('lot_width')):.1f}m × {_safe_number(assessment_data.get('lot_depth')):.1f}m"),
            ("Lot Area", f"{_safe_number(assessment_data.get('lot_area')):.0f} m²"),
            ("Lot Area Sources", lot_ref_text),
            ("Transport Distance", f"{_safe_number(assessment_data.get('dist_transport')):.0f} m"),
            ("Nearest Activity Centre", _safe_text((assessment_data.get('nearest_activity_centre') or {}).get('name') if isinstance(assessment_data.get('nearest_activity_centre'), dict) else assessment_data.get('nearest_activity_centre'))),
        ],
    )

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Financial Intelligence")

    pdf.set_font("Helvetica", "", 10)
    _full_width_multicell(
        pdf,
        6,
        f"Weekly gross revenue range: ${weekly_min:,} to ${weekly_max:,} | "
        f"Annual gross revenue range: ${annual_min:,} to ${annual_max:,} | "
        f"Annual midpoint estimate: ${annual_midpoint:,}",
    )
    _render_kv_table(
        pdf,
        [
            ("Revenue Estimate (Weekly Midpoint)", f"${weekly_midpoint:,}"),
            ("Annual Gross (Midpoint)", f"${annual_midpoint:,}"),
            ("Revenue Estimate (Weekly Range)", f"${weekly_min:,} - ${weekly_max:,}"),
            ("Annual Gross (Range)", f"${annual_min:,} - ${annual_max:,}"),
        ],
    )
    proximity_band = _safe_text(revenue.get("proximity_band"), "Standard transport-adjusted model")
    pdf.set_text_color(95, 100, 108)
    _full_width_multicell(pdf, 6, f"Method note: {proximity_band}")
    pdf.set_text_color(24, 33, 45)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Site Planning Requirements (Blueprint V1.1)")
    _render_kv_table(
        pdf,
        [
            ("Front Setback Requirement", "6.0 m"),
            ("Rear Setback Requirement", "6.0 m to 8.0 m"),
            ("Blueprint Width Requirement", "Minimum 12.44 m"),
            ("Blueprint Depth Target", "25.6 m to 27.6 m"),
            ("Blueprint Area Target", "316 m² to 346 m²"),
            (
                "Lot Depth vs Setbacks",
                f"Lot depth {_safe_number(setback_requirements.get('lot_depth_m')):.1f} m | "
                f"Minimum with setbacks {_safe_number(setback_requirements.get('required_total_depth_min_m')):.1f} m",
            ),
        ],
    )

    if project_type == PROJECT_TYPE_DUAL_OCC:
        dual_occ_min_area = 650.0
        lot_area = _safe_number(assessment_data.get("lot_area"), 0.0)
        meets_dual_occ_threshold = lot_area >= dual_occ_min_area

        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        _full_width_cell(pdf, 7, "Dual Occupancy Minimum Area Threshold")
        pdf.set_font("Helvetica", "", 10)
        _full_width_multicell(
            pdf,
            6,
            (
                f"Dual occupancy requires a minimum lot area of {dual_occ_min_area:.0f} m². "
                f"This site is assessed at {lot_area:.0f} m² and "
                f"{'meets' if meets_dual_occ_threshold else 'does not meet'} the threshold."
            ),
        )

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Scoring Breakdown")
    _render_kv_table(
        pdf,
        [
            ("Zone", f"{_safe_number(assessment_data.get('zone_score')):.0f}/40"),
            ("Transport", f"{_safe_number(assessment_data.get('transport_score')):.0f}/25"),
            ("Physical", f"{_safe_number(assessment_data.get('physical_score')):.0f}/25"),
            ("Compliance", f"{_safe_number(assessment_data.get('compliance_score')):.0f}/10"),
        ],
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Regulatory Risk Flags")
    pdf.set_font("Helvetica", "", 10)
    for label, flagged in _risk_flags(assessment_data):
        marker = "FLAGGED" if flagged else "CLEAR"
        _full_width_cell(pdf, 6, f"- {label}: {marker}")

    overlays = assessment_data.get("vicplan_overlays") or assessment_data.get("overlays") or []
    if overlays:
        _full_width_cell(pdf, 6, "- Overlay details:")
        for overlay in overlays[:12]:
            _full_width_multicell(pdf, 6, f"  - {_safe_text(overlay)}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Design Suitability Details")
    pdf.set_font("Helvetica", "", 10)
    if design_reasons:
        for reason in design_reasons:
            _full_width_multicell(pdf, 6, f"- {reason}")
    else:
        _full_width_cell(pdf, 6, "No design constraints were returned by the validator.")

    if setback_requirements:
        _full_width_cell(pdf, 6, "- Blueprint setback requirements:")
        _full_width_cell(
            pdf,
            6,
            f"  - Front setback: {_safe_number(setback_requirements.get('front_setback_m')):.1f}m",
        )
        _full_width_cell(
            pdf,
            6,
            f"  - Rear setback: {_safe_number(setback_requirements.get('rear_setback_min_m')):.1f}m to {_safe_number(setback_requirements.get('rear_setback_max_m')):.1f}m",
        )
        _full_width_cell(
            pdf,
            6,
            f"  - Minimum total depth for Blueprint + setbacks: {_safe_number(setback_requirements.get('required_total_depth_min_m')):.1f}m",
        )
        _full_width_cell(
            pdf,
            6,
            f"  - Full-range total depth for Blueprint + setbacks: {_safe_number(setback_requirements.get('required_total_depth_max_m')):.1f}m",
        )

    design_suitability = assessment_data.get("design_suitability", {}) or {}
    if isinstance(design_suitability, dict) and design_suitability and "error" not in design_suitability:
        checks = design_suitability.get("suitability_checks", {}) or {}
        _full_width_cell(pdf, 6, "- Design-specific checks:")
        _full_width_cell(pdf, 6, f"  - Lot area sufficient: {'PASS' if checks.get('lot_area_sufficient') else 'REVIEW'}")
        _full_width_cell(pdf, 6, f"  - Zone suitable: {'PASS' if checks.get('zone_suitable') else 'REVIEW'}")
        _full_width_cell(pdf, 6, f"  - Transport compliant: {'PASS' if checks.get('transport_compliant') else 'REVIEW'}")

    reg = assessment_data.get("regulatory_findings", {}) or {}
    if isinstance(reg, dict) and reg:
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 12)
        _full_width_cell(pdf, 6, "Regulatory Compliance Detail")
        pdf.set_font("Helvetica", "", 10)
        checks = reg.get("checks", {}) or {}
        if checks:
            for key, val in checks.items():
                label = key.replace("_", " ").title()
                _full_width_cell(pdf, 6, f"- {label}: {'PASS' if bool(val) else 'FAIL'}")
        reasons = reg.get("reasons", []) or []
        for reason in reasons[:15]:
            _full_width_multicell(pdf, 6, f"  - {_safe_text(reason)}")

    amenities = assessment_data.get("amenities_summary", {}) or {}
    if amenities:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 13)
        _full_width_cell(pdf, 7, "Proximity & Amenities")
        pdf.set_font("Helvetica", "", 10)
        for category, label in [
            ("transit", "Public Transport"),
            ("schools", "Schools"),
            ("parks", "Parks"),
            ("shops", "Shops"),
            ("heritage", "Heritage"),
        ]:
            items = amenities.get(category, []) or []
            _full_width_cell(pdf, 6, f"- {label}: {len(items)} found")
            for item in items[:5]:
                if isinstance(item, dict):
                    name = _safe_text(item.get("name"), label)
                    dist = _safe_number(item.get("distance_m"), 0)
                    _full_width_multicell(pdf, 6, f"  - {name} ({dist:.0f} m)")

    recommendations = assessment_data.get("recommendations", []) or []
    if recommendations:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        _full_width_cell(pdf, 6, "Recommended Next Actions")
        pdf.set_font("Helvetica", "", 10)
        for item in recommendations[:15]:
            _full_width_multicell(pdf, 6, f"- {str(item)}")

    constraints = assessment_data.get("identified_constraints", []) or []
    if constraints:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        _full_width_cell(pdf, 6, "Identified Constraints")
        pdf.set_font("Helvetica", "", 10)
        for item in constraints[:20]:
            _full_width_multicell(pdf, 6, f"- {str(item)}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Map Snapshot")
    pdf.set_font("Helvetica", "", 10)
    if pdf.get_y() + 82 > pdf.page_break_trigger:
        pdf.add_page()

    snapshot_y = pdf.get_y()
    map_path = None
    map_note = "Map unavailable"
    if lat is not None and lon is not None:
        map_path, map_note = _build_map_snapshot(lat, lon)
        if map_path:
            temp_artifacts.append(map_path)

    if map_path and os.path.exists(map_path):
        pdf.image(map_path, x=pdf.l_margin, y=snapshot_y, w=190, h=70)
        pdf.set_y(snapshot_y + 72)
        pdf.set_text_color(120, 126, 135)
        _full_width_cell(pdf, 5, map_note)
        pdf.set_text_color(24, 33, 45)
    else:
        pdf.set_draw_color(188, 194, 202)
        pdf.set_fill_color(247, 248, 250)
        pdf.rect(pdf.l_margin, snapshot_y, 190, 55, style="DF")
        pdf.set_xy(pdf.l_margin, snapshot_y + 24)
        pdf.set_text_color(120, 126, 135)
        pdf.cell(190, 6, f"Map snapshot unavailable ({map_note})", align="C")
        pdf.set_text_color(24, 33, 45)
        pdf.set_y(snapshot_y + 60)

    pdf.set_font("Helvetica", "B", 13)
    _full_width_cell(pdf, 7, "Regulatory Appendix - Planning Framework")
    pdf.set_font("Helvetica", "", 10)
    _full_width_multicell(pdf, 6, "Use the links below to verify planning controls, including Clause 5.24 references, and operator due diligence requirements.")

    nearest_activity = assessment_data.get("nearest_activity_centre") or {}
    activity_name = _safe_text(nearest_activity.get("name") if isinstance(nearest_activity, dict) else nearest_activity)
    activity_distance_km = _safe_number(
        nearest_activity.get("distance_km") if isinstance(nearest_activity, dict) else None,
        0.0,
    )
    if activity_name == "N/A":
        alignment_summary = (
            "Clause 5.24 (Future Homes) alignment: Pending verified activity-centre dataset linkage for this site. "
            "Use VicPlan controls and transport proximity as interim alignment indicators."
        )
    else:
        alignment_summary = (
            f"Clause 5.24 (Future Homes) alignment summary: nearest activity centre is {activity_name} "
            f"at approximately {activity_distance_km:.2f} km from the site. "
            "This supports an initial strategic-location assessment subject to detailed planning confirmation."
        )
    _full_width_multicell(pdf, 6, alignment_summary)

    for label, url in _resolve_reference_links(assessment_data):
        _draw_action_button(pdf, label, url)

    output = pdf.output(dest="S")
    for artifact in temp_artifacts:
        try:
            if artifact and os.path.exists(artifact):
                os.remove(artifact)
        except Exception:
            pass
    if isinstance(output, str):
        return output.encode("latin-1", errors="ignore")
    if isinstance(output, bytearray):
        return bytes(output)
    return output
