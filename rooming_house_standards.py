"""Rooming house minimum standards (Victoria) and compliance checks.

This module codifies the key minimum standards from Consumer Affairs Victoria
for rooming houses (see: consumer.vic.gov.au 'rooming-house-minimum-standards').

Functions:
- get_standards(): returns the numeric and textual standards used
- evaluate_rooming_house_compliance(assessment_data): returns dict with
  boolean pass/fail flags and human-readable reasons for the app and PDF.
"""
from typing import Dict, Any
from standard_rooming_house_design import get_standard_design, get_design_summary


def get_standards() -> Dict[str, Any]:
    """Return the canonical rooming-house minimum standards used for checks.

    These reflect the key rules used to determine whether a site meets the
    rooming-house requirements referenced on the Victorian government page.
    """
    return {
        'max_gross_floor_area_sqm': 300.0,  # maximum gross floor area for exemption
        'max_persons_accommodated': 12,     # maximum persons accommodated
        'max_bedrooms': 8,                  # maximum bedrooms developed on the land
        'notes': (
            "Exemption applies where: gross floor area ≤ 300 sqm, ≤12 persons "
            "accommodated, and ≤8 bedrooms. Other planning permit rules may still apply "
            "depending on zone and overlays. Always confirm with council and title searches."
        )
    }


def evaluate_rooming_house_compliance(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate assessment_data against rooming-house minimum standards.

    Returns a dict with boolean checks and a `reasons` list explaining each outcome.
    Fields expected in `assessment_data` (if available):
      - gross_floor_area (sqm) or lot_area as fallback
      - persons_accommodated (int) -- if not present, assumed unknown
      - bedrooms (int) -- if not present, assumed unknown
      - zone_type and overlays may affect permit requirements
    """
    standards = get_standards()
    r = {
        'standards': standards,
        'checks': {},
        'overall_compliant': True,
        'reasons': [],
        'design_reference': 'UR Happy Home Standard Rooming House Design v1.0',
        'design_required_specs': {
            'bedrooms': 5,
            'bathrooms': 3,
            'gross_floor_area_sqm': 274,
        }
    }

    # Gross floor area check: prefer explicit 'gross_floor_area', fallback to 'lot_area'
    gfa = None
    if 'gross_floor_area' in assessment_data and assessment_data.get('gross_floor_area'):
        try:
            gfa = float(assessment_data.get('gross_floor_area'))
        except Exception:
            gfa = None
    if gfa is None:
        # fallback: use dwelling footprint estimate derived from lot_area heuristics
        # If lot_area is present, we cannot assume building footprint; but use conservative check
        if 'lot_area' in assessment_data and assessment_data.get('lot_area'):
            try:
                lot_area = float(assessment_data.get('lot_area'))
                # conservative estimate: assume up to 50% of lot could be gross floor area
                gfa = lot_area * 0.5
                r['reasons'].append(
                    "Gross floor area not supplied — using conservative estimate of 50% of lot area."
                )
            except Exception:
                gfa = None

    if gfa is None:
        r['checks']['gross_floor_area_ok'] = False
        r['overall_compliant'] = False
        r['reasons'].append("Gross floor area unknown — cannot confirm compliance with size limits.")
    else:
        ok = gfa <= standards['max_gross_floor_area_sqm']
        r['checks']['gross_floor_area_ok'] = ok
        if not ok:
            r['overall_compliant'] = False
            r['reasons'].append(
                f"Gross floor area estimated {gfa:.0f} m² exceeds allowed {standards['max_gross_floor_area_sqm']:.0f} m²."
            )
        else:
            r['reasons'].append(f"Gross floor area {gfa:.0f} m² within allowed limit.")

    # Persons accommodated check
    persons = assessment_data.get('persons_accommodated')
    if persons is None:
        r['checks']['persons_ok'] = False
        r['overall_compliant'] = False
        r['reasons'].append("Persons accommodated not provided — cannot confirm maximum occupants (≤12).")
    else:
        try:
            p = int(persons)
            ok = p <= standards['max_persons_accommodated']
            r['checks']['persons_ok'] = ok
            if not ok:
                r['overall_compliant'] = False
                r['reasons'].append(
                    f"Persons accommodated ({p}) exceeds allowed maximum of {standards['max_persons_accommodated']}."
                )
            else:
                r['reasons'].append(f"Persons accommodated ({p}) within allowed maximum.")
        except Exception:
            r['checks']['persons_ok'] = False
            r['overall_compliant'] = False
            r['reasons'].append("Persons accommodated value invalid — cannot confirm occupancy limit.")

    # Bedroom count check
    bedrooms = assessment_data.get('bedrooms') or assessment_data.get('num_bedrooms')
    if bedrooms is None:
        r['checks']['bedrooms_ok'] = False
        r['overall_compliant'] = False
        r['reasons'].append("Number of bedrooms not provided — cannot confirm bedroom limit (≤8).")
    else:
        try:
            b = int(bedrooms)
            ok = b <= standards['max_bedrooms']
            r['checks']['bedrooms_ok'] = ok
            if not ok:
                r['overall_compliant'] = False
                r['reasons'].append(f"Bedrooms ({b}) exceeds allowed maximum of {standards['max_bedrooms']}.")
            else:
                r['reasons'].append(f"Bedrooms ({b}) within allowed maximum.")
        except Exception:
            r['checks']['bedrooms_ok'] = False
            r['overall_compliant'] = False
            r['reasons'].append("Bedrooms value invalid — cannot confirm bedroom limit.")

    # Zone/permit note: some zones are explicitly exempt from permit requirements under certain conditions.
    zone = assessment_data.get('zone_type') or assessment_data.get('zone')
    overlays = assessment_data.get('overlays') or []
    permit_note = ""
    if zone:
        # If in certain zones, permit requirements differ — we provide guidance rather than legal advice
        permit_note = (
            f"Site located in zone: {zone}. Refer to planning scheme for permit requirements. "
            "Exemptions may apply depending on exact planning scheme clauses and overlays."
        )
        r['reasons'].append(permit_note)
    else:
        r['reasons'].append("Zone information not available — permit requirement cannot be determined.")

    r['permit_note'] = permit_note
    r['note'] = (
        "All assessment results assume implementation of the UR Happy Home "
        "Standard Design (5BR, 274m² GFA, NDIS-compliant, verified Feb 2026). "
        "Site must accommodate this design. Specific permits and conditions apply by zone."
    )
    return r
