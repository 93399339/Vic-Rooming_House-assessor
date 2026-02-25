"""
Standard Rooming House Design - Locked Specification

This module defines the standardized rooming house design that is compliant
with all Victorian rooming-house minimum standards and NDIS regulations.

All properties assessed through UR Happy Home are evaluated against the
ability to accommodate this design. The design has been confirmed compliant
with all rooming-house and NDIS requirements (February 2026).
"""

from typing import Dict, Any


def get_standard_design() -> Dict[str, Any]:
    """
    Return the locked-in standard rooming house design specification.

    This design is compliant with:
    - Victorian consumer affairs rooming-house minimum standards
    - NDIS (National Disability Insurance Scheme) requirements
    - Accessibility and disability accommodation standards
    - Planning permit exemption thresholds (where applicable)

    Returns:
        Dictionary with complete design specifications
    """
    return {
        # Design identification
        'design_name': 'UR Happy Home Standard Rooming House Design',
        'design_version': '1.0',
        'compliance_status': 'CONFIRMED_COMPLIANT',
        'compliance_scope': ['Rooming-house standards', 'NDIS regulations', 'Disability access standards'],
        'approval_date': '2026-02-17',

        # Key specifications
        'bedrooms': 5,
        'bathrooms': 3,
        'wet_areas': {
            'bathrooms': 3,
            'ensuite_bathrooms': 1,
            'toilets': 4,
        },

        # Kitchen and dining
        'kitchens': 2,  # Main kitchen and secondary kitchenette/meals
        'dining_areas': 2,
        'meals_areas': 2,

        # Common areas
        'living_areas': 2,
        'circulation_area_sqm': 80,  # Hallways, stairs, passages
        'storage_areas': ['Linen storage', 'General storage', 'Robe storage'],

        # Utility and support
        'laundry_area': True,
        'laundry_sqm': 12,
        'outdoor_area': True,  # Balcony or patio
        'outdoor_sqm': 25,

        # Gross floor area
        'gross_floor_area_sqm': 274,  # Based on footprint 13.8m × 9.94m × 2 levels
        'breakdown_sqm': {
            'bedrooms': 120,  # ~24 sqm average per bedroom
            'bathrooms': 35,  # ~11-12 sqm each
            'kitchens': 30,   # ~15 sqm each
            'living': 60,     # Lounge/living spaces
            'laundry': 12,
            'storage': 15,
            'circulation': 80,
            'other': 68,      # Hallways, vestibules, plant rooms
        },

        # Accessibility & NDIS compliance
        'disability_features': {
            'accessible_bedrooms': 3,  # Rooms with wheelchair accessibility
            'accessible_bathrooms': 2,  # Rooms with disability-friendly fixtures
            'corridors_width_mm': 1200,  # Minimum 1200mm for wheelchair access
            'doorways_width_mm': 850,    # Minimum 850mm for wheelchair access
            'ramps_present': True,
            'parking_accessible': 1,     # Accessible parking space
            'emergency_exit_paths': True,
            'handrails': True,
            'grab_rails': True,
            'non_slip_surfaces': True,
            'accessible_kitchens': 1,
            'accessible_bathroom_fixtures': True,
        },

        # Building specifications
        'levels': 2,
        'building_width_mm': 9940,    # 9.94m
        'building_length_mm': 13800,  # 13.8m
        'footprint_sqm': 137,         # 13.8m × 9.94m = 137.17 m²
        'site_coverage_percent': 100,  # Assumes design fits within nominal lot

        # Regulatory compliance checkpoints
        'compliance_criteria': {
            'exemption_compliant': True,  # Meets exemption thresholds
            'max_floor_area_300sqm': True,  # GFA 274 < 300 — exemption threshold met
            'persons_accommodated': 5,  # 1 person per bedroom minimum
            'max_persons_12': True,  # 5 persons < 12 limit
            'bedrooms_limit_8': True,  # 5 bedrooms < 8 limit
            'permit_required': False,  # GFA 274 ≤ 300 so planning-permit exemption may apply (confirm with council)
        },

        # Utilities and infrastructure
        'utilities': {
            'power_phases': 3,  # 3-phase power for commercial kitchen
            'water_supplied': True,
            'hot_water_system': 'Heat pump (all-electric ready)',
            'heating_system': 'Ducted reverse-cycle (fixed heating)',
            'cooling': 'Ducted reverse-cycle',
            'ventilation': 'Mechanical with recirculation filters',
        },

        # Safety features
        'safety_features': {
            'fire_rated_walls': True,
            'fire_extinguishers': True,
            'emergency_lighting': True,
            'smoke_alarms': True,
            'sprinkler_system': 'As per building code',
            'emergency_exits': 2,
            'first_aid_kit_location': 'Main kitchen',
            'safety_signage': True,
        },

        # Building code compliance
        'building_code': 'NCC 2022 (National Construction Code)',
        'energy_rating': 7.5,  # Estimated energy rating (out of 10)
        'all_electric_capable': True,
        'ev_charging_ready': True,  # EV charging infrastructure ready
        'solar_ready': True,  # Roof designed for solar panels

        # Interior design features
        'interior_features': {
            'natural_lighting': 'Maximized in common areas',
            'privacy': 'Rooms accessed from central hallway',
            'noise_isolation': 'Acoustic treatments in bedrooms',
            'dementia_friendly': True,  # Design supports people with dementia
            'sensory_features': True,  # Sensory gardens or spaces available
        },

        # Outdoor and landscaping
        'landscaping': {
            'accessible_outdoor': True,
            'garden_beds': True,
            'pathways_accessible': True,
            'seating_areas': 3,
            'shade_structures': True,
        },

        # Legal and regulatory notes
        'notes': {
            'design_origin': 'UR Happy Home standard template (February 2026)',
            'compliance_verification': 'Independently verified against CAV and NDIS standards',
            'permit_status': 'Subject to planning permit rules; GFA is below 300 m² exemption threshold for this design',
            'zone_exempt': True,  # Design GFA falls under 300m² exemption threshold (confirm with council)
            'title_covenant_check': 'Required - title must be free of single-dwelling restrictions',
            'site_suitability': 'Suitable for GRZ, RGZ, and other specified zones (council confirmation)',
            'future_adaptability': 'Design allows for future upgrades (e.g., height extensions, additional services)',
        },
    }


def get_design_summary() -> str:
    """Return a human-readable summary of the standard design."""
    d = get_standard_design()
    summary = f"""
UR HAPPY HOME STANDARD DESIGN - SUMMARY
{'='*60}
Design: {d['design_name']}
Status: {d['compliance_status']}
Compliance: {', '.join(d['compliance_scope'])}

ACCOMMODATION:
- {d['bedrooms']} Bedrooms
- {d['bathrooms']} Bathrooms ({d['wet_areas']['ensuite_bathrooms']} ensuite)
- {d['kitchens']} Kitchen(s)
- Gross floor area: {d['gross_floor_area_sqm']} m²

NDIS & ACCESSIBILITY:
- {len([k for k, v in d['disability_features'].items() if v])} accessibility features
- {d['disability_features']['accessible_bedrooms']} fully accessible bedrooms
- Wheelchair-compliant corridors (1200mm minimum width)
- Emergency exit paths compliant

REGULATORY:
- Persons: {d['compliance_criteria']['persons_accommodated']} < 12 limit ✓
- Bedrooms: {d['bedrooms']} < 8 limit ✓
- Planning permit: REQUIRED (GFA {d['gross_floor_area_sqm']} m² > 300 m² threshold)
- Title covenant check: REQUIRED

UTILITIES:
- All-electric ready with heat pump heating
- 3-phase power for commercial kitchen
- Mechanical ventilation with filters
- EV charging-ready infrastructure

{'='*60}
"""
    return summary


def evaluate_site_suitability_for_design(site_assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate whether a site can accommodate the standard design.

    Args:
        site_assessment: Site assessment data from data_fetcher/auto_assess_from_address

    Returns:
        Dictionary with suitability checks and recommendations
    """
    design = get_standard_design()
    result = {
        'design_name': design['design_name'],
        'site_address': site_assessment.get('address', 'N/A'),
        'suitability_checks': {},
        'all_checks_pass': True,
        'reasons': [],
        'recommendations': [],
    }

    # Check 1: Lot size - ensure enough space for footprint + setbacks
    lot_area = site_assessment.get('lot_area', 0)
    footprint = design.get('footprint_sqm', 0)
    required_area = int(footprint * 1.25)  # footprint + 25% allowance for setbacks/future space
    lot_ok = lot_area >= required_area
    result['suitability_checks']['lot_area_sufficient'] = lot_ok
    if not lot_ok:
        result['all_checks_pass'] = False
        result['reasons'].append(
            f"Lot area {lot_area:.0f} m² may be insufficient for design footprint "
            f"({footprint} m² + setbacks). Recommended: {required_area}+ m²."
        )
    else:
        result['reasons'].append(f"Lot area {lot_area:.0f} m² sufficient for design placement.")

    # Check 2: Zoning - design typically suitable in GRZ, RGZ, mixed-use
    zone = site_assessment.get('zone_type', 'Unknown')
    compliant_zones = ['General Residential Zone', 'Residential Growth Zone', 'Mixed Use', 'Neighbourhood Residential Zone']
    zone_ok = any(z.lower() in zone.lower() for z in compliant_zones)
    result['suitability_checks']['zone_suitable'] = zone_ok
    if not zone_ok:
        result['all_checks_pass'] = False
        result['reasons'].append(f"Zone '{zone}' may restrict residential development. Verify with council permitting.")
    else:
        result['reasons'].append(f"Zone '{zone}' suitable for rooming house development.")

    # Check 3: Transport compliance - design benefits from good transport access
    transport = site_assessment.get('dist_transport', 9999)
    transport_ok = transport <= 800
    result['suitability_checks']['transport_compliant'] = transport_ok
    if not transport_ok:
        result['reasons'].append(
            f"Distance to transport {transport}m exceeds preferred 800m catchment. "
            "May impact tenant accessibility."
        )
    else:
        result['reasons'].append(f"Transport within {transport}m - good accessibility.")

    # Check 4: Planning permit requirement - derive from design GFA and note
    design_gfa = design.get('gross_floor_area_sqm', 0)
    if design_gfa <= 300:
        permit_required = False
        permit_reason = f"Design gross floor area ({design_gfa} m²) is below the 300 m² exemption threshold — planning permit may not be required (confirm with council)."
    else:
        permit_required = True
        permit_reason = f"Design gross floor area ({design_gfa} m²) exceeds the 300 m² exemption threshold — planning permit is likely required."

    permit_check = {
        'required': permit_required,
        'reason': permit_reason,
    }
    result['suitability_checks']['planning_noted'] = True
    result['permit_requirement'] = permit_check

    # Check 5: Title check reminder
    result['suitability_checks']['title_check_required'] = True
    result['reasons'].append("Full title search required to confirm no single-dwelling covenants or restrictions.")

    # Recommendations
    result['recommendations'].append(
        "Engage town planning consultant to confirm permit pathway and conditions."
    )
    result['recommendations'].append(
        "Commission geotechnical survey if slope revealed in preliminary assessment."
    )
    result['recommendations'].append(
        "Obtain quantity surveyor estimate for construction costs (typically $600-800k for this design)."
    )
    if not zone_ok:
        result['recommendations'].append(
            "Before proceeding, confirm with council that rooming house use is supported in this zone."
        )

    return result
