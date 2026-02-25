"""
Cost estimator for rooming house properties.
Uses Victorian postcode-level land value estimates.
"""

from typing import Optional

# Victorian land value estimates (2025) in AUD per sqm
# Based on public Victorian property market data
# These are approximate indicative values; actual property prices vary widely
POSTCODE_LAND_VALUES = {
    # Melbourne inner/close
    3000: 3500,  # Melbourne CBD
    3002: 3200,  # Southbank/St Kilda Road
    3004: 3000,  # South Melbourne
    3006: 2800,  # St Kilda
    3008: 2500,  # Albert Park
    3011: 2200,  # Docklands
    3015: 1800,  # Footscray
    3031: 1600,  # St Kilda
    3039: 1200,  # Ringwood
    3122: 1400,  # Hawthorn
    3141: 1300,  # Camberwell
    3146: 1100,  # Glen Waverley
    3206: 1500,  # Cremorne
    # Default regional estimate
    0: 800  # Regional/default
}

def estimate_land_cost(postcode: str, lot_area_sqm: float) -> dict:
    """
    Estimate land cost based on Victorian postcode and lot area.
    
    Args:
        postcode: Australian postcode (string)
        lot_area_sqm: Lot area in square meters
    
    Returns:
        dict with estimated costs and assumptions
    """
    try:
        pc = int(postcode)
    except (ValueError, TypeError):
        pc = 0
    
    # Get value per sqm for postcode
    value_per_sqm = POSTCODE_LAND_VALUES.get(pc, POSTCODE_LAND_VALUES[0])
    
    # Estimate total land value
    estimated_land_value = value_per_sqm * lot_area_sqm
    
    # Add contingency/acquisition fees (typically 10-15%)
    acquisition_cost = estimated_land_value * 1.12
    
    return {
        "postcode": pc,
        "value_per_sqm": value_per_sqm,
        "lot_area_sqm": lot_area_sqm,
        "estimated_land_value": round(estimated_land_value, 0),
        "acquisition_total": round(acquisition_cost, 0),
        "contingency_percentage": 12,
        "currency": "AUD",
        "estimate_accuracy": "±30% (market dependent)",
        "note": "Indicative only; obtain professional valuation for actual investment decisions"
    }


def estimate_construction_cost(lot_area_sqm: float, bedrooms: int = 8) -> dict:
    """
    Rough construction cost estimate for rooming house conversion.
    
    Args:
        lot_area_sqm: Lot area in square meters
        bedrooms: Expected number of rooms (default 8)
    
    Returns:
        dict with construction cost estimates
    """
    # Typical Victorian rooming house construction cost: $2,500-3,500 per sqm
    # Assumes renovation/conversion of existing structure or new build
    cost_per_sqm = 3000
    base_build_area = lot_area_sqm * 0.6  # Assume 60% of land is built area
    
    build_cost = base_build_area * cost_per_sqm
    
    # Contingency on build
    total_build_cost = build_cost * 1.15
    
    return {
        "build_area_sqm": round(base_build_area, 0),
        "cost_per_sqm": cost_per_sqm,
        "gross_build_cost": round(build_cost, 0),
        "with_contingency": round(total_build_cost, 0),
        "contingency_percentage": 15,
        "estimated_bedrooms": bedrooms,
        "currency": "AUD",
        "note": "Indicative only; obtain detailed cost estimates from builders"
    }


def estimate_project_total(postcode: str, lot_area_sqm: float, bedrooms: int = 8) -> dict:
    """
    Estimate total project cost (land + construction + holding costs).
    """
    land = estimate_land_cost(postcode, lot_area_sqm)
    construction = estimate_construction_cost(lot_area_sqm, bedrooms)
    
    # Additional costs (planning, legal, finance, holding)
    additional_costs = {
        "planning_legal": 50000,
        "finance_holding": 30000,
        "contingency_total": round((land["acquisition_total"] + construction["with_contingency"]) * 0.10, 0)
    }
    
    total_cost = (
        land["acquisition_total"] +
        construction["with_contingency"] +
        additional_costs["planning_legal"] +
        additional_costs["finance_holding"] +
        additional_costs["contingency_total"]
    )
    
    # Estimate revenue (rough)
    weekly_rent_per_room = 400  # AUD per room per week
    annual_revenue = bedrooms * weekly_rent_per_room * 52
    
    return {
        "land_acquisition": round(land["acquisition_total"], 0),
        "construction": round(construction["with_contingency"], 0),
        "planning_legal": additional_costs["planning_legal"],
        "finance_holding": additional_costs["finance_holding"],
        "project_contingency": additional_costs["contingency_total"],
        "total_project_cost": round(total_cost, 0),
        "estimated_annual_revenue": round(annual_revenue, 0),
        "estimated_roi_percentage": round(100 * annual_revenue / total_cost, 1),
        "payback_years": round(total_cost / annual_revenue, 1),
        "beds": bedrooms,
        "note": "Indicative projections; actual performance depends on many factors"
    }
