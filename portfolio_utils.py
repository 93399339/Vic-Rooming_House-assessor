"""
Portfolio utilities for dashboard statistics and site comparison.
"""

from typing import List, Dict, Any
import sqlite3

def get_portfolio_stats(db_path: str = "assessments.db") -> Dict[str, Any]:
    """Get summary statistics for the portfolio of assessments."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all assessments
        cursor.execute("SELECT * FROM assessments")
        assessments = cursor.fetchall()
        conn.close()
        
        if not assessments:
            return {
                "total_assessments": 0,
                "suitable_count": 0,
                "conditional_count": 0,
                "unsuitable_count": 0,
                "avg_score": 0,
                "suitable_percentage": 0,
                "avg_lot_area": 0,
                "avg_transport_distance": 0
            }
        
        suitable = sum(1 for a in assessments if a["viability_color"] == "green")
        conditional = sum(1 for a in assessments if a["viability_color"] == "orange")
        unsuitable = sum(1 for a in assessments if a["viability_color"] == "red")
        
        scores = [float(a["raw_score"]) for a in assessments if a["raw_score"]]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        areas = [float(a["lot_area"]) for a in assessments if a["lot_area"]]
        avg_area = sum(areas) / len(areas) if areas else 0
        
        dists = [float(a["dist_transport"]) for a in assessments if a["dist_transport"]]
        avg_dist = sum(dists) / len(dists) if dists else 0
        
        return {
            "total_assessments": len(assessments),
            "suitable_count": suitable,
            "conditional_count": conditional,
            "unsuitable_count": unsuitable,
            "avg_score": round(avg_score, 1),
            "suitable_percentage": round(100 * suitable / len(assessments), 1) if assessments else 0,
            "avg_lot_area": round(avg_area, 0),
            "avg_transport_distance": round(avg_dist, 0)
        }
    
    except Exception as e:
        print(f"Error getting portfolio stats: {e}")
        return {}


def get_comparison_data(assessment_ids: List[int], db_path: str = "assessments.db") -> List[Dict[str, Any]]:
    """Retrieve assessment data for comparison."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        placeholders = ",".join("?" * len(assessment_ids))
        cursor.execute(f"SELECT * FROM assessments WHERE id IN ({placeholders})", assessment_ids)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    except Exception as e:
        print(f"Error getting comparison data: {e}")
        return []


def rank_sites_by_score(assessments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank assessments by viability score."""
    return sorted(assessments, key=lambda x: float(x.get("raw_score", 0)), reverse=True)


def filter_by_viability(assessments: List[Dict[str, Any]], status: str) -> List[Dict[str, Any]]:
    """Filter assessments by viability status (green/orange/red)."""
    color_map = {
        "suitable": "green",
        "conditional": "orange",
        "unsuitable": "red"
    }
    color = color_map.get(status.lower(), status)
    return [a for a in assessments if a.get("viability_color") == color]


def filter_by_zone(assessments: List[Dict[str, Any]], zone: str) -> List[Dict[str, Any]]:
    """Filter assessments by planning zone."""
    return [a for a in assessments if zone.lower() in a.get("zone_type", "").lower()]


def filter_by_constraint(assessments: List[Dict[str, Any]], has_constraint: bool) -> List[Dict[str, Any]]:
    """Filter assessments that have/don't have overlays or covenants."""
    if has_constraint:
        return [a for a in assessments if a.get("has_overlay") or a.get("has_covenant")]
    else:
        return [a for a in assessments if not a.get("has_overlay") and not a.get("has_covenant")]


def estimate_cost_per_suitable_site(assessments: List[Dict[str, Any]], total_spend: float) -> float:
    """Estimate cost per suitable site given total acquisition budget."""
    suitable = filter_by_viability(assessments, "suitable")
    if not suitable:
        return 0
    return total_spend / len(suitable)
