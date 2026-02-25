"""
Scoring System for Vic Rooming House Assessor
Implements weighted scoring for professional recommendations
"""

BLUEPRINT_MIN_WIDTH = 12.44
BLUEPRINT_MIN_DEPTH = 25.6
BLUEPRINT_MAX_DEPTH = 27.6
BLUEPRINT_MIN_AREA = 316.0
BLUEPRINT_MAX_AREA = 346.0

FRONT_SETBACK_REQUIRED = 6.0
REAR_SETBACK_MIN = 6.0
REAR_SETBACK_MAX = 8.0

PROJECT_TYPE_ROOMING = "Standard Rooming House"
PROJECT_TYPE_SDA = "SDA/NDIS Unit"
PROJECT_TYPE_DUAL_OCC = "Standard Dual Occupancy"


def _normalize_project_type(project_type):
    val = str(project_type or "").strip()
    if val in {PROJECT_TYPE_ROOMING, PROJECT_TYPE_SDA, PROJECT_TYPE_DUAL_OCC}:
        return val
    return PROJECT_TYPE_ROOMING


def get_logic_thresholds(project_type):
    """Return project-specific thresholds for logic and design checks."""
    project_type = _normalize_project_type(project_type)

    if project_type == PROJECT_TYPE_SDA:
        return {
            "project_type": PROJECT_TYPE_SDA,
            "min_width": 12.44,
            "min_depth": 25.6,
            "max_depth": 30.0,
            "target_area_min": 340.0,
            "target_area_max": 420.0,
            "front_setback": 7.0,
            "rear_setback_min": 8.0,
            "rear_setback_max": 10.0,
            "min_lot_area": 340.0,
            "requires_hospital_proximity": True,
            "max_hospital_distance_m": 5000,
            "revenue_units": 4,
            "weekly_rate_min": 650,
            "weekly_rate_max": 900,
        }

    if project_type == PROJECT_TYPE_DUAL_OCC:
        return {
            "project_type": PROJECT_TYPE_DUAL_OCC,
            "min_width": 14.0,
            "min_depth": 28.0,
            "max_depth": 40.0,
            "target_area_min": 650.0,
            "target_area_max": 900.0,
            "front_setback": 6.0,
            "rear_setback_min": 6.0,
            "rear_setback_max": 8.0,
            "min_lot_area": 650.0,
            "requires_hospital_proximity": False,
            "max_hospital_distance_m": None,
            "revenue_units": 2,
            "weekly_rate_min": 520,
            "weekly_rate_max": 680,
        }

    return {
        "project_type": PROJECT_TYPE_ROOMING,
        "min_width": BLUEPRINT_MIN_WIDTH,
        "min_depth": BLUEPRINT_MIN_DEPTH,
        "max_depth": BLUEPRINT_MAX_DEPTH,
        "target_area_min": BLUEPRINT_MIN_AREA,
        "target_area_max": BLUEPRINT_MAX_AREA,
        "front_setback": FRONT_SETBACK_REQUIRED,
        "rear_setback_min": REAR_SETBACK_MIN,
        "rear_setback_max": REAR_SETBACK_MAX,
        "min_lot_area": BLUEPRINT_MIN_AREA,
        "requires_hospital_proximity": False,
        "max_hospital_distance_m": None,
        "revenue_units": 5,
        "weekly_rate_min": 250,
        "weekly_rate_max": 300,
    }


def _nearest_hospital_distance_m(assessment_data):
    amenities = assessment_data.get("amenities_summary", {}) or {}
    hospitals = amenities.get("hospitals", []) or []
    dists = []
    for item in hospitals:
        if isinstance(item, dict) and item.get("distance_m") is not None:
            try:
                dists.append(float(item.get("distance_m")))
            except (TypeError, ValueError):
                continue
    if dists:
        return min(dists)
    return None


def evaluate_setback_requirements(lot_depth, project_type=PROJECT_TYPE_ROOMING):
    """Evaluate whether lot depth can accommodate project depth + setbacks."""
    thresholds = get_logic_thresholds(project_type)
    depth = float(lot_depth or 0)
    required_depth_min = thresholds["min_depth"] + thresholds["front_setback"] + thresholds["rear_setback_min"]
    required_depth_max = thresholds["max_depth"] + thresholds["front_setback"] + thresholds["rear_setback_max"]

    return {
        "front_setback_m": thresholds["front_setback"],
        "rear_setback_min_m": thresholds["rear_setback_min"],
        "rear_setback_max_m": thresholds["rear_setback_max"],
        "required_total_depth_min_m": round(required_depth_min, 2),
        "required_total_depth_max_m": round(required_depth_max, 2),
        "lot_depth_m": round(depth, 2),
        "supports_minimum_blueprint_with_setbacks": depth >= required_depth_min,
        "supports_full_blueprint_range_with_setbacks": depth >= required_depth_max,
    }


def get_blueprint_setback_recommendations(lot_depth, project_type=PROJECT_TYPE_ROOMING, assessment_data=None):
    """Return recommendation text that includes project-specific setback requirements."""
    thresholds = get_logic_thresholds(project_type)
    setback = evaluate_setback_requirements(lot_depth, project_type)
    recs = [
        f"Apply {thresholds['project_type']} setbacks: Front {thresholds['front_setback']:.0f}m and Rear {thresholds['rear_setback_min']:.0f}-{thresholds['rear_setback_max']:.0f}m.",
    ]

    if not setback["supports_minimum_blueprint_with_setbacks"]:
        recs.append(
            f"Current lot depth ({setback['lot_depth_m']:.1f}m) is below minimum depth needed for Blueprint + setbacks ({setback['required_total_depth_min_m']:.1f}m)."
        )
    elif not setback["supports_full_blueprint_range_with_setbacks"]:
        recs.append(
            f"Lot depth supports minimum Blueprint depth but not full target range with setbacks ({setback['required_total_depth_max_m']:.1f}m)."
        )
    else:
        recs.append(
            f"PASS: Front setback {thresholds['front_setback']:.0f}m and rear setback {thresholds['rear_setback_min']:.0f}-{thresholds['rear_setback_max']:.0f}m criteria are satisfied for this lot depth."
        )

    if thresholds["requires_hospital_proximity"] and assessment_data:
        nearest_hospital_m = _nearest_hospital_distance_m(assessment_data)
        if nearest_hospital_m is None:
            recs.append("SDA/NDIS requirement: nearest hospital distance could not be confirmed (target ≤5km).")
        elif nearest_hospital_m > thresholds["max_hospital_distance_m"]:
            recs.append(
                f"SDA/NDIS requirement not met: nearest hospital is {nearest_hospital_m/1000:.1f}km away (target ≤5.0km)."
            )
        else:
            recs.append(
                f"SDA/NDIS hospital proximity check passed: nearest hospital is {nearest_hospital_m/1000:.1f}km away."
            )

    return recs


def _calculate_project_physical_score(lot_width, lot_depth, lot_area, slope, project_type=PROJECT_TYPE_ROOMING):
    """Calculate physical score using project-specific thresholds."""
    thresholds = get_logic_thresholds(project_type)
    width = float(lot_width or 0)
    depth = float(lot_depth or 0)
    area = float(lot_area or 0)

    # Width component (max 8)
    if width >= thresholds["min_width"]:
        width_score = 8
    elif width >= max(12.0, thresholds["min_width"] - 0.5):
        width_score = 5
    elif width >= max(11.5, thresholds["min_width"] - 1.0):
        width_score = 2
    else:
        width_score = 0

    # Depth component (max 8)
    if thresholds["min_depth"] <= depth <= thresholds["max_depth"]:
        depth_score = 8
    elif (thresholds["min_depth"] - 1.6) <= depth <= (thresholds["max_depth"] + 2.4):
        depth_score = 5
    elif depth >= (thresholds["min_depth"] - 3.6):
        depth_score = 2
    else:
        depth_score = 0

    # Area component (max 6)
    if thresholds["target_area_min"] <= area <= thresholds["target_area_max"]:
        area_score = 6
    elif max(280.0, thresholds["target_area_min"] - 40.0) <= area <= (thresholds["target_area_max"] + 80.0):
        area_score = 4
    elif area >= max(240.0, thresholds["target_area_min"] - 90.0):
        area_score = 1
    else:
        area_score = 0

    # Slope component (max 3)
    slope_score = 3 if slope == "Flat" else 2 if slope == "Moderate" else 0

    total = width_score + depth_score + area_score + slope_score
    return min(25, total), width_score, depth_score, area_score, slope_score


def validate_urhh_design(lot_width, lot_depth, lot_area, project_type=PROJECT_TYPE_ROOMING, assessment_data=None):
    """
    Validate lot dimensions for UR Happy Home standard design fit.

    Criteria are project-type specific from get_logic_thresholds().
    """
    thresholds = get_logic_thresholds(project_type)
    reasons = []
    recommendations = []

    width = float(lot_width or 0)
    depth = float(lot_depth or 0)
    area = float(lot_area or 0)

    if width < thresholds["min_width"]:
        reasons.append(f"Lot width {width:.2f}m is less than required minimum {thresholds['min_width']:.2f}m for {thresholds['project_type']}")
    if depth < thresholds["min_depth"]:
        reasons.append(
            f"Lot depth {depth:.2f}m is less than required minimum {thresholds['min_depth']:.1f}m"
        )
    if area < thresholds["min_lot_area"]:
        reasons.append(
            f"Lot area {area:.1f}m² is less than required minimum {thresholds['min_lot_area']:.0f}m²"
        )

    if project_type == PROJECT_TYPE_DUAL_OCC and area < 650.0:
        reasons.append("Dual Occupancy requires minimum lot area of 650m²")

    if thresholds["requires_hospital_proximity"] and assessment_data:
        nearest_hospital_m = _nearest_hospital_distance_m(assessment_data)
        if nearest_hospital_m is None:
            reasons.append("SDA/NDIS requires nearest hospital check (≤5km), but no hospital data was found")
        elif nearest_hospital_m > thresholds["max_hospital_distance_m"]:
            reasons.append(
                f"SDA/NDIS hospital proximity not met: nearest hospital is {nearest_hospital_m/1000:.1f}km away (required ≤5.0km)"
            )

    recommendations.extend(get_blueprint_setback_recommendations(depth, project_type, assessment_data=assessment_data))
    setback_requirements = evaluate_setback_requirements(depth, project_type)

    return {
        'pass_fail': len(reasons) == 0,
        'reasons': reasons,
        'recommendations': recommendations,
        'setback_requirements': setback_requirements,
        'project_type': thresholds['project_type'],
    }


def estimate_revenue_potential(assessment_data):
    """
    Estimate weekly and annual gross revenue based on selected project type.

    Transport proximity adjustment:
    - <=400m: +10%
    - <=800m: 0%
    - <=1200m: -8%
    - >1200m: -15%
    """
    thresholds = get_logic_thresholds(assessment_data.get('project_type'))
    units = thresholds['revenue_units']
    min_per_unit = thresholds['weekly_rate_min']
    max_per_unit = thresholds['weekly_rate_max']

    base_weekly_min = units * min_per_unit
    base_weekly_max = units * max_per_unit

    dist_transport = float(assessment_data.get('dist_transport', 9999) or 9999)
    if dist_transport <= 400:
        transport_multiplier = 1.10
        proximity_band = 'Premium access (<=400m)'
    elif dist_transport <= 800:
        transport_multiplier = 1.00
        proximity_band = 'Strong access (<=800m)'
    elif dist_transport <= 1200:
        transport_multiplier = 0.92
        proximity_band = 'Moderate access (<=1200m)'
    else:
        transport_multiplier = 0.85
        proximity_band = 'Limited access (>1200m)'

    weekly_min = round(base_weekly_min * transport_multiplier)
    weekly_max = round(base_weekly_max * transport_multiplier)

    annual_min = round(weekly_min * 52)
    annual_max = round(weekly_max * 52)

    midpoint_weekly = round((weekly_min + weekly_max) / 2)
    midpoint_annual = round((annual_min + annual_max) / 2)

    return {
        'project_type': thresholds['project_type'],
        'units_assumed': units,
        'rooms_assumed': units,
        'weekly_min': weekly_min,
        'weekly_max': weekly_max,
        'weekly_midpoint': midpoint_weekly,
        'annual_min': annual_min,
        'annual_max': annual_max,
        'annual_midpoint': midpoint_annual,
        'transport_multiplier': transport_multiplier,
        'proximity_band': proximity_band,
    }

def calculate_weighted_score(assessment_data):
    """
    Calculate a weighted viability score (0-100) based on assessment criteria.
    
    Weights:
    - Zone: 40%
    - Transport: 25%
    - Physical: 25%
    - Compliance: 10%
    """
    
    ZONE_WEIGHT = 0.40
    TRANSPORT_WEIGHT = 0.25
    PHYSICAL_WEIGHT = 0.25
    COMPLIANCE_WEIGHT = 0.10
    project_type = _normalize_project_type(assessment_data.get('project_type'))
    thresholds = get_logic_thresholds(project_type)
    
    # Zone Score (0-25)
    zone_score = 0
    if assessment_data.get('has_overlay') or assessment_data.get('has_covenant'):
        zone_score = 0  # Hard fail
    elif assessment_data.get('is_preferred_zone'):
        zone_score = 25  # Perfect score for preferred zones
    else:
        zone_score = 10  # Low score for non-preferred zones
    
    # Transport Score (0-25)
    transport_score = 0
    dist = assessment_data.get('dist_transport', 1000)
    
    if dist <= 400:
        transport_score = 25  # Excellent
    elif dist <= 600:
        transport_score = 22  # Very good
    elif dist <= 800:
        transport_score = 18  # Good
    elif dist <= 1000:
        transport_score = 10  # Acceptable
    else:
        transport_score = 0  # Poor

    if thresholds['requires_hospital_proximity']:
        nearest_hospital_m = _nearest_hospital_distance_m(assessment_data)
        if nearest_hospital_m is None:
            transport_score = min(transport_score, 8)
        elif nearest_hospital_m > thresholds['max_hospital_distance_m']:
            transport_score = min(transport_score, 8)
    
    # Physical Suitability Score (0-25) - Blueprint V1.1
    slope = assessment_data.get('slope', 'Moderate')
    lot_width = assessment_data.get('lot_width', 0)
    lot_depth = assessment_data.get('lot_depth', 0)
    lot_area = assessment_data.get('lot_area', 0)

    physical_score, _, _, _, _ = _calculate_project_physical_score(
        lot_width,
        lot_depth,
        lot_area,
        slope,
        project_type,
    )
    
    # Compliance Score (0-10)
    compliance_score = 0
    compliance_checks = sum([
        assessment_data.get('check_heating', 0),
        assessment_data.get('check_windows', 0),
        assessment_data.get('check_energy', 0)
    ])
    
    # Map compliance checks to score
    compliance_map = {
        0: 0,
        1: 3,
        2: 6,
        3: 10
    }
    compliance_score = compliance_map.get(compliance_checks, 0)
    
    # Calculate weighted total (0-100)
    total_score = (
        (zone_score / 25 * ZONE_WEIGHT * 100) +
        (transport_score / 25 * TRANSPORT_WEIGHT * 100) +
        (physical_score / 25 * PHYSICAL_WEIGHT * 100) +
        (compliance_score / 10 * COMPLIANCE_WEIGHT * 100)
    )
    
    return round(total_score, 1)

def get_viability_status_from_score(score):
    """
    Determine viability status based on weighted score.
    """
    if score >= 75:
        return {
            'status': 'HIGHLY SUITABLE',
            'color': 'green',
            'message': 'Site meets key criteria for rooming house development.'
        }
    elif score >= 50:
        return {
            'status': 'CONDITIONAL',
            'color': 'orange',
            'message': 'Site has potential but requires addressing identified constraints.'
        }
    else:
        return {
            'status': 'NOT SUITABLE',
            'color': 'red',
            'message': 'Site has significant constraints that limit viability.'
        }

def detailed_score_breakdown(assessment_data):
    """
    Return detailed breakdown of score components.
    """
    
    # Zone component
    zone_score = 0
    zone_feedback = ""
    if assessment_data.get('has_overlay'):
        zone_feedback = "Heritage/Character overlay restricts density (HARD FAIL)"
        zone_score = 0
    elif assessment_data.get('has_covenant'):
        zone_feedback = "Single dwelling covenant restricts multi-occupancy (HARD FAIL)"
        zone_score = 0
    elif assessment_data.get('is_preferred_zone'):
        zone_feedback = "Preferred zone (GRZ/RGZ) suitable for rooming houses"
        zone_score = 25
    else:
        zone_feedback = "Non-preferred zone - limited density allowances"
        zone_score = 10
    
    # Transport component
    project_type = _normalize_project_type(assessment_data.get('project_type'))
    thresholds = get_logic_thresholds(project_type)
    dist = assessment_data.get('dist_transport', 1000)
    transport_score = 0
    if dist <= 400:
        transport_feedback = f"Excellent: {dist}m is within highly preferred catchment"
        transport_score = 25
    elif dist <= 600:
        transport_feedback = f"Good: {dist}m within preferred transport catchment"
        transport_score = 22
    elif dist <= 800:
        transport_feedback = f"Acceptable: {dist}m at edge of recommended catchment"
        transport_score = 18
    elif dist <= 1000:
        transport_feedback = f"Limited: {dist}m requires traffic engineering assessment"
        transport_score = 10
    else:
        transport_feedback = f"Poor: {dist}m significantly outside recommended catchment"
        transport_score = 0

    if thresholds['requires_hospital_proximity']:
        nearest_hospital_m = _nearest_hospital_distance_m(assessment_data)
        if nearest_hospital_m is None:
            transport_feedback += " | SDA/NDIS hospital proximity: unknown (target ≤5km)"
            transport_score = min(transport_score, 8)
        elif nearest_hospital_m > thresholds['max_hospital_distance_m']:
            transport_feedback += f" | SDA/NDIS hospital proximity not met ({nearest_hospital_m/1000:.1f}km > 5.0km)"
            transport_score = min(transport_score, 8)
        else:
            transport_feedback += f" | SDA/NDIS hospital proximity met ({nearest_hospital_m/1000:.1f}km)"
    
    # Physical component
    lot_width = assessment_data.get('lot_width', 0)
    lot_depth = assessment_data.get('lot_depth', 0)
    lot_area = assessment_data.get('lot_area', 0)
    slope = assessment_data.get('slope', 'Moderate')

    physical_feedback = []
    if lot_width >= thresholds['min_width']:
        physical_feedback.append(f"Width {lot_width:.2f}m: Meets minimum (≥{thresholds['min_width']:.2f}m)")
    elif lot_width >= 12.0:
        physical_feedback.append(f"Width {lot_width:.2f}m: Near minimum (target ≥{thresholds['min_width']:.2f}m)")
    else:
        physical_feedback.append(f"Width {lot_width:.2f}m: Below minimum")

    if thresholds['min_depth'] <= lot_depth <= thresholds['max_depth']:
        physical_feedback.append(f"Depth {lot_depth:.2f}m: In target ({thresholds['min_depth']:.1f}-{thresholds['max_depth']:.1f}m)")
    else:
        physical_feedback.append(f"Depth {lot_depth:.2f}m: Outside target ({thresholds['min_depth']:.1f}-{thresholds['max_depth']:.1f}m)")

    if thresholds['target_area_min'] <= lot_area <= thresholds['target_area_max']:
        physical_feedback.append(f"Area {lot_area:.1f}m²: In target ({thresholds['target_area_min']:.0f}-{thresholds['target_area_max']:.0f}m²)")
    else:
        physical_feedback.append(f"Area {lot_area:.1f}m²: Outside target ({thresholds['target_area_min']:.0f}-{thresholds['target_area_max']:.0f}m²)")

    if project_type == PROJECT_TYPE_DUAL_OCC:
        if lot_area >= 650:
            physical_feedback.append("Dual Occupancy lot area check: PASS (≥650m²)")
        else:
            physical_feedback.append("Dual Occupancy lot area check: FAIL (<650m²)")

    if slope == "Flat":
        physical_feedback.append("Slope: Ideal for development")
    elif slope == "Moderate":
        physical_feedback.append("Slope: Moderate - requires geotechnical assessment")
    else:
        physical_feedback.append("Slope: Steep - high SDA access costs")

    setback_requirements = evaluate_setback_requirements(lot_depth, project_type)
    physical_feedback.append(
        f"Setbacks required: Front {setback_requirements['front_setback_m']:.0f}m, Rear {setback_requirements['rear_setback_min_m']:.0f}-{setback_requirements['rear_setback_max_m']:.0f}m"
    )
    if not setback_requirements['supports_minimum_blueprint_with_setbacks']:
        physical_feedback.append(
            f"Lot depth may not support Blueprint + setbacks (minimum total depth {setback_requirements['required_total_depth_min_m']:.1f}m)"
        )

    physical_score, _, _, _, _ = _calculate_project_physical_score(
        lot_width,
        lot_depth,
        lot_area,
        slope,
        project_type,
    )
    
    # Compliance component
    compliance_checks = sum([
        assessment_data.get('check_heating', 0),
        assessment_data.get('check_windows', 0),
        assessment_data.get('check_energy', 0)
    ])
    
    compliance_feedback = f"{compliance_checks}/3 standards confirmed"
    if compliance_checks == 3:
        compliance_feedback += " - Fully compliant"
        compliance_score = 10
    elif compliance_checks == 2:
        compliance_feedback += " - Minor upgrades needed"
        compliance_score = 6
    elif compliance_checks == 1:
        compliance_feedback += " - Significant upgrades required"
        compliance_score = 3
    else:
        compliance_feedback += " - Major upgrades required"
        compliance_score = 0
    
    return {
        'zone': {
            'score': zone_score,
            'max': 25,
            'weight': 0.40,
            'feedback': zone_feedback,
            'weighted_score': (zone_score / 25) * 0.40 * 100
        },
        'transport': {
            'score': transport_score,
            'max': 25,
            'weight': 0.25,
            'feedback': transport_feedback,
            'weighted_score': (transport_score / 25) * 0.25 * 100
        },
        'physical': {
            'score': physical_score,
            'max': 25,
            'weight': 0.25,
            'feedback': "; ".join(physical_feedback),
            'weighted_score': (physical_score / 25) * 0.25 * 100
        },
        'compliance': {
            'score': compliance_score,
            'max': 10,
            'weight': 0.10,
            'feedback': compliance_feedback,
            'weighted_score': (compliance_score / 10) * 0.10 * 100
        }
    }
