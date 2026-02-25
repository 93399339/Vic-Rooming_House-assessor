"""Generate map HTML and PDF report preview for inspection.
Creates `outputs/map_preview.html` and `outputs/report_preview.pdf`.
"""
import os
from ui.advanced_map import create_advanced_map
from pdf_generator import generate_pdf_report

# Use Melbourne CBD as test site
latitude = -37.8136
longitude = 144.9631
address = "Melbourne CBD, VIC"

os.makedirs('outputs', exist_ok=True)

# Create map
map_obj, poi_data = create_advanced_map(
    latitude=latitude,
    longitude=longitude,
    address=address,
    viability_color='green',
    show_transit=True,
    show_schools=True,
    show_parks=True,
    show_shops=True,
    show_heritage=False,
    map_type='OpenStreetMap',
    zone_type='General Residential Zone (GRZ)',
    has_overlay=False
)

map_path = os.path.join('outputs', 'map_preview.html')
map_obj.save(map_path)
print(f"Wrote map to {map_path}")

# Build a sample assessment_data for PDF
assessment_data = {
    'address': address,
    'latitude': latitude,
    'longitude': longitude,
    'zone_type': 'General Residential Zone (GRZ)',
    'has_overlay': False,
    'dist_transport': 350,
    'lot_width': 15.0,
    'lot_depth': 24.0,
    'lot_area': 360.0,
    'slope': 'Flat',
    'has_covenant': False,
    'check_heating': True,
    'check_windows': True,
    'check_energy': True,
    'is_preferred_zone': True,
    'is_transport_compliant': True,
    'is_width_compliant': True,
    'is_depth_compliant': True,
    'is_area_compliant': True,
    'viability_status': 'Suitable',
    'viability_color': 'green',
    'raw_score': 92.5,
    'summary_message': 'Site is well-located and meets key criteria',
    'recommendations': ['Proceed with detailed design'],
    'assessor_notes': 'Generated preview',
    'amenities_summary': poi_data,
    'identified_constraints': []
}

report_selections = {
    "Executive Summary": True,
    "Site Location & Zoning Analysis": True,
    "Physical Suitability Assessment": True,
    "Regulatory Compliance": True,
    "Proximity & Transport": True,
    "Risk Assessment & Constraints": True,
    "Recommendations": True,
}

pdf_buffer = generate_pdf_report(assessment_data, report_selections)
pdf_path = os.path.join('outputs', 'report_preview.pdf')
with open(pdf_path, 'wb') as fh:
    fh.write(pdf_buffer.getbuffer())

print(f"Wrote PDF to {pdf_path}")
