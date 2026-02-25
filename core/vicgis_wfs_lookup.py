"""
VicGIS WFS lookup for automatic parcel and zone retrieval.
Uses public opendata.maps.vic.gov.au WFS endpoints.
"""

import requests
import json
from typing import Dict, Any, Optional, List, Tuple
import math
from haversine import haversine

VICGIS_WFS_URL = "https://opendata.maps.vic.gov.au/geoserver/ows"

ZONE_LAYER_CANDIDATES = [
    "open-data-platform:plan_zone",
    "datavic:VM_PLAN_ZONE",
]

OVERLAY_LAYER_CANDIDATES = [
    "open-data-platform:plan_overlay",
    "datavic:VM_PLAN_OVERLAY",
]

PARCEL_LAYER_CANDIDATES = [
    "open-data-platform:parcel_view",
    "datavic:VM_PROPERTY_PARCEL_POLYGON",
]

VPP_CLAUSE_URLS = {
    "GRZ": {
        "clause": "32.08",
        "title": "General Residential Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "RGZ": {
        "clause": "32.07",
        "title": "Residential Growth Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "NRZ": {
        "clause": "32.09",
        "title": "Neighbourhood Residential Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "MUZ": {
        "clause": "32.04",
        "title": "Mixed Use Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "C1Z": {
        "clause": "34.01",
        "title": "Commercial 1 Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "C2Z": {
        "clause": "34.02",
        "title": "Commercial 2 Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "IN1Z": {
        "clause": "33.01",
        "title": "Industrial 1 Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "IN2Z": {
        "clause": "33.02",
        "title": "Industrial 2 Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
    "IN3Z": {
        "clause": "33.03",
        "title": "Industrial 3 Zone",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    },
}


def _query_layer_features(layer_names: List[str], bbox: str, timeout: int = 15) -> List[Dict[str, Any]]:
    for layer in layer_names:
        try:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": layer,
                "outputFormat": "application/json",
                "bbox": bbox,
                "srsName": "EPSG:4326",
            }
            response = requests.get(VICGIS_WFS_URL, params=params, timeout=timeout)
            if response.status_code != 200:
                continue
            data = response.json()
            features = data.get("features", [])
            if features:
                return features
        except Exception:
            continue
    return []


def _extract_first(props: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in props and props.get(key) not in (None, ""):
            return props.get(key)
    lower = {str(k).lower(): v for k, v in props.items()}
    for key in keys:
        value = lower.get(key.lower())
        if value not in (None, ""):
            return value
    return None


def _polygon_area_sqm_from_geometry(geometry: Dict[str, Any]) -> Optional[float]:
    try:
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates")
        if not geom_type or not coords:
            return None

        def ring_area(ring: List[List[float]]) -> float:
            if len(ring) < 3:
                return 0.0
            lat0 = sum(pt[1] for pt in ring) / len(ring)
            scale_x = 111320.0 * math.cos(math.radians(lat0))
            scale_y = 110540.0
            area = 0.0
            for i in range(len(ring) - 1):
                x1, y1 = ring[i][0] * scale_x, ring[i][1] * scale_y
                x2, y2 = ring[i + 1][0] * scale_x, ring[i + 1][1] * scale_y
                area += x1 * y2 - x2 * y1
            return abs(area) / 2.0

        def polygon_area(poly: List[List[List[float]]]) -> float:
            if not poly:
                return 0.0
            outer = ring_area(poly[0])
            holes = sum(ring_area(r) for r in poly[1:])
            return max(0.0, outer - holes)

        if geom_type == "Polygon":
            return polygon_area(coords)
        if geom_type == "MultiPolygon":
            return sum(polygon_area(poly) for poly in coords)
        return None
    except Exception:
        return None


def _point_in_ring(lon: float, lat: float, ring: List[List[float]]) -> bool:
    """Ray-casting point-in-polygon for a single ring (lon/lat order)."""
    inside = False
    n = len(ring)
    if n < 3:
        return False

    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]

        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) if (yj - yi) != 0 else 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i

    return inside


def _point_in_polygon(lon: float, lat: float, polygon_coords: List[List[List[float]]]) -> bool:
    if not polygon_coords:
        return False

    outer = polygon_coords[0]
    if not _point_in_ring(lon, lat, outer):
        return False

    # If point is inside any hole, it is not inside polygon.
    for hole in polygon_coords[1:]:
        if _point_in_ring(lon, lat, hole):
            return False

    return True


def _point_in_geometry(lon: float, lat: float, geometry: Dict[str, Any]) -> bool:
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates")
    if not geom_type or not coords:
        return False

    if geom_type == "Polygon":
        return _point_in_polygon(lon, lat, coords)
    if geom_type == "MultiPolygon":
        return any(_point_in_polygon(lon, lat, poly) for poly in coords)
    return False


def _normalize_zone_code(zone_value: str) -> str:
    text = (zone_value or "").upper()
    if "(" in text and ")" in text:
        possible = text.split("(")[-1].split(")")[0].strip()
        if possible:
            return possible

    for key in VPP_CLAUSE_URLS:
        if key in text:
            return key

    if text.startswith("GRZ"):
        return "GRZ"
    if text.startswith("RGZ"):
        return "RGZ"
    if text.startswith("NRZ"):
        return "NRZ"
    if text.startswith("MUZ") or text.startswith("MUA"):
        return "MUZ"
    if text.startswith("C1Z"):
        return "C1Z"
    if text.startswith("C2Z"):
        return "C2Z"
    if text.startswith("IN1Z"):
        return "IN1Z"
    if text.startswith("IN2Z"):
        return "IN2Z"
    if text.startswith("IN3Z"):
        return "IN3Z"
    return "UNKNOWN"


def get_vpp_links(zone_code: str) -> Dict[str, str]:
    """
    Return official Victorian Planning Provisions URL for a zone code.

    Example:
        GRZ -> Clause 32.08
    """
    normalized = _normalize_zone_code(zone_code)
    link = VPP_CLAUSE_URLS.get(normalized)
    if link:
        return {
            "zone_code": normalized,
            "clause": link["clause"],
            "title": link["title"],
            "url": link["url"],
        }

    return {
        "zone_code": normalized,
        "clause": "VPP",
        "title": "Victorian Planning Provisions",
        "url": "https://planning-schemes.app.planning.vic.gov.au/VPPS/clauses",
    }


def _query_aboriginal_cultural_sensitivity(lat: float, lon: float, buffer_m: float = 30) -> bool:
    """Best-effort WFS check for Aboriginal Cultural Heritage Sensitivity."""
    delta = buffer_m / 111320.0
    bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta},EPSG:4326"

    candidate_layers = [
        "datavic:VM_ABORIGINAL_CULTURAL_HERITAGE_SENSITIVITY",
        "datavic:ABORIGINAL_CULTURAL_HERITAGE_SENSITIVITY",
        "datavic:VICMAP_ABORIGINAL_CULTURAL_HERITAGE_SENSITIVITY",
    ]

    for layer in candidate_layers:
        try:
            params = {
                "service": "WFS",
                "version": "2.0.0",
                "request": "GetFeature",
                "typeNames": layer,
                "outputFormat": "application/json",
                "bbox": bbox,
                "srsName": "EPSG:4326",
            }
            resp = requests.get(VICGIS_WFS_URL, params=params, timeout=8)
            if resp.status_code != 200:
                continue
            features = resp.json().get("features", [])
            if features:
                return True
        except Exception:
            continue

    return False


def _extract_risk_checks(overlays: list[str]) -> Dict[str, bool]:
    text = " | ".join([str(v).upper() for v in overlays])
    flood_overlay = (
        "SBO" in text
        or "SPECIAL BUILDING" in text
        or "FLOOD" in text
        or "LSIO" in text
        or "FO" in text
    )
    aboriginal = (
        "ABORIGINAL" in text
        or "CULTURAL HERITAGE" in text
        or "CHMP" in text
    )
    return {
        "aboriginal_cultural_heritage_sensitivity": aboriginal,
        "special_building_overlay_flood_risk": flood_overlay,
    }


def get_planning_data(lat: float, lon: float, buffer_m: float = 30) -> Dict[str, Any]:
    """
    Fetch planning zone and overlays for a coordinate from Victorian WFS.

    Returns:
        {
            "Planning Zone": str,
            "Planning Zone Code": str,
            "Overlays": List[str],
            "planning_zone": str,
            "planning_zone_code": str,
            "overlays": List[str],
            "vpp_links": Dict[str, str],
            "risk_checks": Dict[str, bool],
        }
    """
    planning_zone = "Unknown"
    planning_zone_code = "UNKNOWN"
    overlays: list[str] = []

    try:
        delta = buffer_m / 111320.0
        bbox = f"{lon - delta},{lat - delta},{lon + delta},{lat + delta},EPSG:4326"

        zone_features = _query_layer_features(ZONE_LAYER_CANDIDATES, bbox, timeout=15)
        if zone_features:
            containing_zone_features = [
                feature
                for feature in zone_features
                if _point_in_geometry(lon, lat, feature.get("geometry", {}))
            ]
            zone_feature = containing_zone_features[0] if containing_zone_features else zone_features[0]
            zone_props = zone_feature.get("properties", {})
            planning_zone = (
                _extract_first(zone_props, ["zone_description", "ZONE_NAME", "ZONE_DESC"])
                or _extract_first(zone_props, ["zone_code", "ZONE_CODE", "ZONE"])
                or "Unknown"
            )
            planning_zone_code = _normalize_zone_code(
                _extract_first(zone_props, ["zone_code", "ZONE_CODE", "ZONE"]) or planning_zone
            )

        overlay_features = _query_layer_features(OVERLAY_LAYER_CANDIDATES, bbox, timeout=15)
        site_overlay_features = [
            feature
            for feature in overlay_features
            if _point_in_geometry(lon, lat, feature.get("geometry", {}))
        ]
        seen = set()
        for feature in site_overlay_features:
            props = feature.get("properties", {})
            overlay_name = (
                _extract_first(props, ["zone_description", "OVERLAY_NAME", "OVERLAY_DESC"])
                or _extract_first(props, ["zone_code", "OVERLAY_CODE", "OVERLAY"])
            )
            if overlay_name and overlay_name not in seen:
                overlays.append(str(overlay_name))
                seen.add(overlay_name)

    except Exception as e:
        print(f"Error getting planning data: {e}")

    vpp_link = get_vpp_links(planning_zone_code or planning_zone)
    risk_checks = _extract_risk_checks(overlays)
    if not risk_checks["aboriginal_cultural_heritage_sensitivity"]:
        risk_checks["aboriginal_cultural_heritage_sensitivity"] = _query_aboriginal_cultural_sensitivity(
            lat,
            lon,
            buffer_m=buffer_m,
        )

    return {
        "Planning Zone": planning_zone,
        "Planning Zone Code": planning_zone_code,
        "Overlays": overlays,
        "planning_zone": planning_zone,
        "planning_zone_code": planning_zone_code,
        "overlays": overlays,
        "vpp_links": vpp_link,
        "risk_checks": risk_checks,
        "aboriginal_cultural_heritage_sensitivity": risk_checks[
            "aboriginal_cultural_heritage_sensitivity"
        ],
        "special_building_overlay_flood_risk": risk_checks[
            "special_building_overlay_flood_risk"
        ],
    }

def list_available_layers() -> list:
    """Query GetCapabilities to list available WFS layers."""
    try:
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetCapabilities"
        }
        resp = requests.get(VICGIS_WFS_URL, params=params, timeout=10)
        resp.raise_for_status()
        # Parse XML and extract layer names
        # For simplicity, return common known layers
        return [
            "open-data-platform:parcel_view",
            "open-data-platform:plan_zone",
            "open-data-platform:plan_overlay",
        ]
    except Exception as e:
        print(f"Error getting capabilities: {e}")
        return []

def query_parcel_at_point(latitude: float, longitude: float, buffer_m: float = 50) -> Optional[Dict[str, Any]]:
    """Query VicGIS WFS for parcel properties at a point."""
    try:
        delta = buffer_m / 111320.0
        bbox = f"{longitude - delta},{latitude - delta},{longitude + delta},{latitude + delta},EPSG:4326"
        features = _query_layer_features(PARCEL_LAYER_CANDIDATES, bbox, timeout=15)
        if not features:
            return None

        def _extract_area(props: Dict[str, Any]) -> Optional[float]:
            area_keys = [
                "AREA",
                "shape_area",
                "SHAPE_Area",
                "AREA_SQM",
                "PARCEL_AREA",
                "LOT_AREA",
                "shape_starea",
            ]
            for key in area_keys:
                value = props.get(key)
                try:
                    if value is not None:
                        numeric = float(value)
                        if numeric > 0:
                            return numeric
                except (TypeError, ValueError):
                    continue
            return None

        # Rank parcel candidates with heuristics that avoid tiny sliver polygons.
        enriched: List[Tuple[float, float, Dict[str, Any]]] = []
        for feature in features:
            props = feature.get("properties", {})
            area = _extract_area(props)
            if area is None:
                area = _polygon_area_sqm_from_geometry(feature.get("geometry", {}))
            sort_area = area if area is not None else 1e12
            enriched.append((sort_area, area or 0.0, feature))

        plausible_for_split = [item for item in enriched if 300.0 <= item[1] <= 700.0]
        if plausible_for_split:
            plausible_for_split.sort(key=lambda item: abs(item[1] - 500.0))
            feat = plausible_for_split[0][2]
        else:
            enriched.sort(key=lambda item: item[0])
            feat = enriched[0][2]
        props = feat.get("properties", {})
        geometry = feat.get("geometry", {})
        area_sqm = _extract_area(props)
        if area_sqm is None:
            area_sqm = _polygon_area_sqm_from_geometry(geometry)
        
        # Extract relevant parcel properties
        result = {
            "parcel_id": props.get("PARCEL_ID", props.get("id")),
            "address": props.get("ADDRESS", ""),
            "area_sqm": area_sqm,
            "geometry": geometry,
            "raw_properties": props
        }
        
        # Estimate lot width/depth from area if available
        if result["area_sqm"]:
            # Rough approximation: assume rectangular lot
            approx_width = (result["area_sqm"] / 336) ** 0.5 * 14  # Scale from 336 sqm standard
            approx_depth = result["area_sqm"] / approx_width if approx_width > 0 else 24
            result["estimated_width"] = round(approx_width, 1)
            result["estimated_depth"] = round(approx_depth, 1)
        
        return result
    
    except Exception as e:
        print(f"Error querying parcel: {e}")
        return None


def query_zone_at_point(latitude: float, longitude: float, buffer_m: float = 50) -> Optional[Dict[str, Any]]:
    """Query VicGIS WFS for planning zone at a point."""
    try:
        delta = buffer_m / 111320.0
        bbox = f"{longitude - delta},{latitude - delta},{longitude + delta},{latitude + delta},EPSG:4326"
        features = _query_layer_features(ZONE_LAYER_CANDIDATES, bbox, timeout=15)
        if not features:
            return None

        containing = [
            feature
            for feature in features
            if _point_in_geometry(longitude, latitude, feature.get("geometry", {}))
        ]
        feat = containing[0] if containing else features[0]
        props = feat.get("properties", {})
        
        # Map zone codes to readable names
        zone_code = _extract_first(props, ["zone_code", "ZONE_CODE", "ZONE", "zone_description"]) or ""
        zone_map = {
            "GRZ": "General Residential Zone (GRZ)",
            "RGZ": "Residential Growth Zone (RGZ)",
            "NRZ": "Neighbourhood Residential Zone (NRZ)",
            "MUA": "Mixed Use Area (MUA)",
            "MUZ": "Mixed Use Zone (MUZ)",
            "C1Z": "Commercial 1 Zone (C1Z)",
            "C2Z": "Commercial 2 Zone (C2Z)",
            "IZ": "Industrial Zone (IZ)"
        }
        
        result = {
            "zone_code": zone_code,
            "zone_name": zone_map.get(zone_code, zone_code),
            "lga": _extract_first(props, ["lga", "LGA_NAME", "LGA"]),
            "raw_properties": props
        }
        
        return result
    
    except Exception as e:
        print(f"Error querying zone: {e}")
        return None


def query_overlays_at_point(latitude: float, longitude: float, buffer_m: float = 50) -> Dict[str, bool]:
    """Query VicGIS WFS for planning overlays (Heritage, NCO, etc.) at a point."""
    try:
        delta = buffer_m / 111320.0
        bbox = f"{longitude - delta},{latitude - delta},{longitude + delta},{latitude + delta},EPSG:4326"
        features = _query_layer_features(OVERLAY_LAYER_CANDIDATES, bbox, timeout=15)
        site_features = [
            feature
            for feature in features
            if _point_in_geometry(longitude, latitude, feature.get("geometry", {}))
        ]
        
        overlays = {
            "heritage": False,
            "neighbourhood_character": False,
            "development_plan": False
        }
        
        for feat in site_features:
            props = feat.get("properties", {})
            overlay_code = str(
                _extract_first(props, ["zone_code", "OVERLAY_CODE", "OVERLAY", "zone_description"]) or ""
            ).upper()
            
            if "HO" in overlay_code or "HERITAGE" in overlay_code:
                overlays["heritage"] = True
            if "NCO" in overlay_code or "NEIGHBOURHOOD" in overlay_code:
                overlays["neighbourhood_character"] = True
            if "DPO" in overlay_code or "DEVELOPMENT" in overlay_code:
                overlays["development_plan"] = True
        
        return overlays
    
    except Exception as e:
        print(f"Error querying overlays: {e}")
        return {}


def auto_fill_from_vicgis(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Auto-populate assessment fields using VicGIS WFS data.
    Returns a dict with parcel, zone, and overlay information.
    """
    result = {
        "parcel": None,
        "zone": None,
        "overlays": {},
        "success": False,
        "message": ""
    }
    
    try:
        # Query parcel data
        parcel = query_parcel_at_point(latitude, longitude)
        if parcel:
            result["parcel"] = parcel
        
        # Query zone data
        zone = query_zone_at_point(latitude, longitude)
        if zone:
            result["zone"] = zone
        
        # Query overlays
        overlays = query_overlays_at_point(latitude, longitude)
        result["overlays"] = overlays
        
        if parcel or zone:
            result["success"] = True
            result["message"] = "Successfully retrieved authoritative data from VicGIS"
        else:
            result["message"] = "No VicGIS data found; using manual entry or defaults"
        
    except Exception as e:
        result["message"] = f"VicGIS lookup error: {str(e)}"
    
    return result
