"""
Data fetcher and auto-assessment helper.
Provides best-effort automatic population of assessment fields from an address.

Integrates with multiple Victorian property data sources:
- Victorian Land Registry WFS (cadastral data, lot sizes)
- Planning Victoria (zoning, overlays)
- OpenStreetMap/Overpass (POIs, amenities)
- Intelligent caching and fallback strategies

Behavior:
- Geocodes the address
- Fetches actual lot dimensions from cadastral data when available
- Fetches zoning from planning schemes
- Uses cached POIs for amenities and transport
- Uses `advanced_map.get_nearby_activity_centres` to find nearby activity centres
- Returns a dict of auto-filled assessment fields that `app.py` can merge into its form
"""

from typing import Dict, Any, Tuple, Optional
import time
import json
import os
import requests
import streamlit as st
from urllib.parse import urlencode

from ui.advanced_map import get_nearby_summary, get_nearby_activity_centres
from rooming_house_standards import evaluate_rooming_house_compliance
from standard_rooming_house_design import evaluate_site_suitability_for_design
from haversine import haversine
from core.vicgis_wfs_lookup import query_parcel_at_point

# ============================================================================
# PROPERTY DATA CACHING
# ============================================================================

PROPERTY_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'data', 'property_data_cache.json')

def _load_property_cache() -> Dict[str, Any]:
    """Load property data cache from file."""
    if os.path.exists(PROPERTY_CACHE_FILE):
        try:
            with open(PROPERTY_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_property_cache(cache: Dict[str, Any]):
    """Save property data cache to file."""
    try:
        os.makedirs(os.path.dirname(PROPERTY_CACHE_FILE), exist_ok=True)
        with open(PROPERTY_CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass  # Silently fail if cache write fails

def _get_cached_property_data(address: str, lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Get cached property data for an address."""
    cache = _load_property_cache()
    cache_key = f"{lat:.4f},{lon:.4f}"
    
    if cache_key in cache:
        cached = cache[cache_key]
        # Check if cache is recent (within 7 days)
        try:
            import time as time_module
            if time_module.time() - cached.get('timestamp', 0) < 7 * 24 * 3600:
                return cached.get('data', {})
        except Exception:
            pass
    
    return None

def _cache_property_data(lat: float, lon: float, data: Dict[str, Any]):
    """Cache property data for future lookup."""
    cache = _load_property_cache()
    cache_key = f"{lat:.4f},{lon:.4f}"
    
    try:
        import time as time_module
        cache[cache_key] = {
            'timestamp': time_module.time(),
            'data': data
        }
        _save_property_cache(cache)
    except Exception:
        pass  # Silently fail


def _has_numeric_alpha_address_suffix(address: str) -> bool:
    compact_address = (address or "").replace(' ', '').upper()
    return any(
        compact_address[i].isdigit() and i + 1 < len(compact_address) and compact_address[i + 1].isalpha()
        for i in range(len(compact_address) - 1)
    )

# ============================================================================
# VICTORIAN CADASTRAL & ZONING DATA SOURCES
# ============================================================================

def fetch_victorian_lot_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch Victorian cadastral lot data from available sources.
    
    This attempts to retrieve:
    - Lot width and depth
    - Lot area
    - Zone type
    - Overlays
    
    Uses multiple data sources with fallback strategies.
    """
    result = {}
    area_sources = []
    
    # Strategy 1: Try Victoria Land Registry WFS service
    try:
        lot_data = _try_vic_land_wfs(lat, lon)
        if lot_data:
            result.update(lot_data)
            if lot_data.get('lot_area'):
                area_sources.append({
                    'source': 'vic_land_wfs',
                    'lot_area': float(lot_data['lot_area'])
                })
    except Exception:
        pass

    # Strategy 1B: VicGIS parcel endpoint (second independent reference)
    try:
        vicgis_parcel = query_parcel_at_point(lat, lon, buffer_m=60)
        if vicgis_parcel and vicgis_parcel.get('area_sqm'):
            vicgis_area = float(vicgis_parcel['area_sqm'])
            area_sources.append({
                'source': 'vicgis_parcel_wfs',
                'lot_area': vicgis_area
            })
            if not result.get('lot_area'):
                result['lot_area'] = vicgis_area
            if not result.get('lot_width') and vicgis_parcel.get('estimated_width'):
                result['lot_width'] = float(vicgis_parcel['estimated_width'])
            if not result.get('lot_depth') and vicgis_parcel.get('estimated_depth'):
                result['lot_depth'] = float(vicgis_parcel['estimated_depth'])
    except Exception:
        pass
    
    # Strategy 2: Try to infer zone from coordinates + known patterns
    try:
        zone_data = _infer_zone_from_location(lat, lon)
        if zone_data and 'zone_type' not in result:
            result['zone_type'] = zone_data.get('zone_type')
            result['overlays'] = zone_data.get('overlays', [])
    except Exception:
        pass
    
    # Reconcile lot area from all available authoritative references
    authoritative_areas = [s['lot_area'] for s in area_sources if s.get('lot_area')]
    if authoritative_areas:
        # Conservative default: choose smallest authoritative area to avoid overestimating split lots
        # (e.g. addresses like 146A where parent parcel may be larger)
        selected_area = min(authoritative_areas)
        result['lot_area'] = round(selected_area, 1)
        result['lot_area_references'] = area_sources
        result['lot_area_source'] = 'reconciled_authoritative'

    return result

def _try_vic_land_wfs(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Attempt to fetch cadastral data from Victoria Land Registry WFS.
    
    Endpoint: https://services.land.vic.gov.au/catalogue/publicproxy/wfs
    Feature: Cadastral_Parcel
    """
    try:
        wfs_params = {
            'service': 'WFS',
            'version': '2.0.0',
            'request': 'GetFeature',
            'typeNames': 'Cadastral_Parcel',
            'outputFormat': 'application/json',
            'cql_filter': f'INTERSECTS(Shape, Point({lon} {lat}))',
            'srsName': 'EPSG:4326'
        }
        
        url = 'https://services.land.vic.gov.au/catalogue/publicproxy/wfs'
        response = requests.get(url, params=wfs_params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                props = feature.get('properties', {})
                
                result = {}
                
                # Extract lot dimensions if available
                if 'area' in props:
                    area_m2 = float(props['area'])
                    result['lot_area'] = area_m2
                    # Estimate dimensions assuming roughly square or common ratios
                    # For typical residential: estimate width/depth from area
                    if area_m2 > 0:
                        # Estimate as roughly 3:4 ratio (common in Victoria)
                        result['lot_width'] = (area_m2 * 0.75) ** 0.5 if area_m2 else 0
                        result['lot_depth'] = (area_m2 / 0.75) ** 0.5 if area_m2 else 0
                
                if 'address' in props:
                    result['cadastral_address'] = props['address']
                
                if 'lfn' in props:
                    result['lot_number'] = props['lfn']
                
                return result if result else None
    except Exception:
        pass
    
    return None

def _infer_zone_from_location(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Infer zoning and overlays from location coordinates.
    Uses known Victoria zoning patterns.
    """
    try:
        # Try ArcGIS rest service for zone lookup
        # This service provides planning scheme zones
        wfs_params = {
            'f': 'json',
            'geometry': json.dumps({'x': lon, 'y': lat}),
            'geometryType': 'esriGeometryPoint',
            'spatialRel': 'esriSpatialRelIntersects',
            'inSR': '4326',
            'outSR': '4326'
        }
        
        # Try planning.vic.gov.au service
        url = 'https://services.land.vic.gov.au/catalogue/publicproxy/arcgis/rest/services/Planning/VIC_PLANNING_SCHEME_ZONES/FeatureServer/0/query'
        
        response = requests.get(url, params=wfs_params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('features') and len(data['features']) > 0:
                feature = data['features'][0]
                props = feature.get('attributes', {})
                
                result = {}
                if 'ZONE_NAME' in props:
                    result['zone_type'] = props['ZONE_NAME']
                if 'ZONE_CODE' in props:
                    result['zone_code'] = props['ZONE_CODE']
                
                return result if result else None
    except Exception:
        pass
    
    # Fallback: Use area-based heuristics for common Victorian zones
    return _estimate_zone_by_coordinate(lat, lon)

def _estimate_zone_by_coordinate(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Estimate zone type based on location coordinates using known patterns.
    This is a fallback when official data isn't available.
    """
    # Victoria CBD and inner areas typically have Mixed Use
    if -37.82 < lat < -37.80 and 144.95 < lon < 144.98:
        return {
            'zone_type': 'Mixed Use',
            'overlays': ['Central City Zone'],
            'confidence': 'pattern-based'
        }
    
    # Suburban areas - use statistical patterns
    if -37.9 < lat < -37.7:  # Greater Melbourne
        # Closer to CBD = more likely urban/mixed
        distance_to_cbd = ((lat + 37.8136)**2 + (lon - 144.9631)**2) ** 0.5
        
        if distance_to_cbd < 0.05:  # ~5km
            return {
                'zone_type': 'Residential Growth Zone',
                'overlays': [],
                'confidence': 'estimate'
            }
        elif distance_to_cbd < 0.1:  # ~10km
            return {
                'zone_type': 'General Residential Zone',
                'overlays': [],
                'confidence': 'estimate'
            }
        else:
            return {
                'zone_type': 'Neighbourhood Residential Zone',
                'overlays': [],
                'confidence': 'estimate'
            }
    
    # Default for other areas
    return {
        'zone_type': 'General Residential Zone',
        'overlays': [],
        'confidence': 'default'
    }

# ============================================================================
# LOT SIZE ESTIMATION
# ============================================================================

def estimate_lot_dimensions(address: str, lat: float, lon: float) -> Dict[str, float]:
    """
    Estimate lot dimensions based on address patterns and location.
    
    Uses Victoria-specific patterns for common lot sizes:
    - Inner suburbs: typically 400-600 m²
    - Middle suburbs: typically 600-900 m²  
    - Outer suburbs: typically 800-1200 m²
    - Rural areas: 1000+ m²
    """
    result = {}
    
    # Strategy 1: Parse address for explicit lot/block size hints
    address_lower = address.lower()
    if 'lot' in address_lower and any(char.isdigit() for char in address_lower):
        # Address contains "lot" reference - might be subdivision lot
        result = _estimate_from_subdivision_pattern(address, lat, lon)
        if result:
            return result
    
    # Strategy 2: Use location-based heuristics
    result = _estimate_by_location_tier(lat, lon)

    # Adjust down for likely subdivided lots (e.g., 146A, 146B)
    has_alpha_suffix = _has_numeric_alpha_address_suffix(address)
    if has_alpha_suffix and result.get('lot_area', 0) > 650:
        target_area = 500.0
        ratio = 1.7
        width = (target_area / ratio) ** 0.5
        depth = width * ratio
        result['lot_width'] = round(width, 1)
        result['lot_depth'] = round(depth, 1)
        result['lot_area'] = round(width * depth, 1)
        result['land_estimate_method'] = 'subdivision-adjusted'
    
    return result

def _estimate_from_subdivision_pattern(address: str, lat: float, lon: float) -> Optional[Dict[str, float]]:
    """Try to extract lot details from address patterns like 'Lot 45 Smyth Street'."""
    try:
        # This is a placeholder - in reality, would need cadastral lookups
        # For now, use location-based defaults
        return None
    except Exception:
        return None

def _estimate_by_location_tier(lat: float, lon: float) -> Dict[str, float]:
    """
    Estimate lot dimensions based on Melbourne area tier.
    Uses distance from CBD as primary metric.
    """
    # Calculate distance from Melbourne CBD
    cbd_lat, cbd_lon = -37.8136, 144.9631
    distance_km = ((lat - cbd_lat)**2 + (lon - cbd_lon)**2) ** 0.5 * 111  # Rough km conversion
    
    # Define tier-based lot sizes (width x depth estimates)
    if distance_km < 5:  # Inner CBD/suburbs
        # Typically smaller, more uniform lots: 400-550m²
        typical_area = 520
        ratio = 1.6  # width:depth ratio
        width = (typical_area / ratio) ** 0.5
        depth = width * ratio
    elif distance_km < 15:  # Middle suburbs
        # Common residential: 600-800m²
        typical_area = 700
        ratio = 1.7
        width = (typical_area / ratio) ** 0.5
        depth = width * ratio
    else:  # Outer suburbs
        # Larger lots: 800-1200m²
        typical_area = 950
        ratio = 1.8
        width = (typical_area / ratio) ** 0.5
        depth = width * ratio
    
    return {
        'lot_width': round(width, 1),
        'lot_depth': round(depth, 1),
        'lot_area': round(width * depth, 1),
        'land_estimate_method': 'location-based'
    }



# ============================================================================
# GEOCODING
# ============================================================================

def geocode_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    def _wait_for_maps_api_key(max_attempts: int = 5, delay_seconds: float = 0.2) -> str:
        for _ in range(max_attempts):
            try:
                api_key = str(st.secrets["MAPS_API_KEY"]).strip()
                if api_key:
                    return api_key
            except Exception:
                pass
            time.sleep(delay_seconds)
        return ""

    def _geocode_with_google_maps(query: str) -> Tuple[Optional[float], Optional[float]]:
        api_key = _wait_for_maps_api_key()
        if not api_key:
            return None, None

        try:
            response = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": query,
                    "components": "country:AU",
                    "region": "au",
                    "language": "en-AU",
                    "key": api_key,
                },
                timeout=10,
            )
            if response.status_code != 200:
                return None, None

            payload = response.json()
            if payload.get("status") != "OK" or not payload.get("results"):
                return None, None

            location = payload["results"][0].get("geometry", {}).get("location", {})
            lat = location.get("lat")
            lon = location.get("lng")
            if lat is None or lon is None:
                return None, None

            return float(lat), float(lon)
        except Exception:
            return None, None

    def _street_suburb_fallback_query(full_address: str) -> str:
        parts = [p.strip() for p in (full_address or "").split(",") if p.strip()]
        if len(parts) >= 2:
            return f"{parts[0]}, {parts[1]}, VIC, Australia"
        return full_address

    try:
        lat, lon = _geocode_with_google_maps(address)
        if lat is not None and lon is not None:
            return lat, lon

        fallback_query = _street_suburb_fallback_query(address)
        if fallback_query and fallback_query != address:
            lat, lon = _geocode_with_google_maps(fallback_query)
            if lat is not None and lon is not None:
                return lat, lon
    except Exception:
        return None, None

    return None, None

# ============================================================================
# MAIN AUTO-ASSESSMENT FUNCTION
# ============================================================================

def auto_assess_from_address(address: str, lat: float = None, lon: float = None) -> Dict[str, Any]:
    """Auto-populate assessment fields from an address with comprehensive data sourcing.

    Returns a dict with keys that match `assessment_data` used by `app.py`.
    
    Args:
        address: The property address
        lat: Optional latitude (if already geocoded)
        lon: Optional longitude (if already geocoded)
    """
    time.sleep(0.5)

    # Use provided coordinates or geocode the address
    if lat is None or lon is None:
        lat, lon = geocode_address(address)
    if lat is None or lon is None:
        return {}

    # Check cache first
    cached_data = _get_cached_property_data(address, lat, lon)
    if cached_data:
        # Refresh potentially stale/overestimated lot areas in cache (common for split lots like 146A)
        cached_lot_area = float(cached_data.get('lot_area') or 0)
        needs_lot_refresh = (
            not cached_data.get('lot_area_source')
            or not cached_data.get('lot_area_references')
            or (_has_numeric_alpha_address_suffix(address) and cached_lot_area > 700)
        )
        if needs_lot_refresh:
            refreshed = fetch_victorian_lot_data(lat, lon)
            if refreshed.get('lot_area'):
                cached_data['lot_area'] = refreshed.get('lot_area')
                if refreshed.get('lot_width'):
                    cached_data['lot_width'] = refreshed.get('lot_width')
                if refreshed.get('lot_depth'):
                    cached_data['lot_depth'] = refreshed.get('lot_depth')
                cached_data['lot_area_source'] = refreshed.get('lot_area_source')
                cached_data['lot_area_references'] = refreshed.get('lot_area_references')

            # Final guard if authoritative references are unavailable
            if _has_numeric_alpha_address_suffix(address) and float(cached_data.get('lot_area') or 0) > 700:
                cached_data['lot_area'] = 500.0
                cached_data['lot_width'] = 17.1
                cached_data['lot_depth'] = 29.2
                cached_data['lot_area_source'] = 'subdivision_sanity_fallback'
                cached_data['lot_area_references'] = []

            _cache_property_data(lat, lon, cached_data)

        # Lock in design values first (before regulatory check)
        if 'bedrooms' not in cached_data or cached_data.get('bedrooms') != 5:
            cached_data['bedrooms'] = 5
            cached_data['gross_floor_area'] = 274
            cached_data['persons_accommodated'] = 5
            cached_data['design_locked'] = 'UR Happy Home Standard Rooming House Design v1.0'
        # Ensure cached data includes regulatory findings (evaluate if missing)
        if 'regulatory_findings' not in cached_data:
            try:
                cached_data['regulatory_findings'] = evaluate_rooming_house_compliance(cached_data)
            except Exception:
                cached_data['regulatory_findings'] = {'error': 'Regulatory evaluation failed'}
        # Ensure cached data includes design suitability (evaluate if missing)
        if 'design_suitability' not in cached_data:
            try:
                cached_data['design_suitability'] = evaluate_site_suitability_for_design(cached_data)
            except Exception:
                cached_data['design_suitability'] = {'error': 'Design evaluation failed'}
        return cached_data

    # Get nearby cached/remote POIs
    poi_summary = get_nearby_summary(lat, lon)

    # Determine nearest transit distance
    nearest_transit_m = None
    if poi_summary.get('transit'):
        nearest_transit_m = min([p['distance_m'] for p in poi_summary['transit']])

    # Determine nearest activity centre
    centres = get_nearby_activity_centres(lat, lon, radius_km=10.0)
    nearest_centre = centres[0] if centres else None

    # Construct auto fields with POI data
    auto = {
        'address': address,
        'latitude': lat,
        'longitude': lon,
        'amenities_summary': poi_summary,
        'dist_transport': nearest_transit_m if nearest_transit_m is not None else 9999,
        'nearest_activity_centre': nearest_centre,
    }

    # **NEW: Fetch actual lot and zoning data from Victorian sources**
    victorian_property_data = fetch_victorian_lot_data(lat, lon)
    auto.update(victorian_property_data)

    # **NEW: If lot dimensions still not populated, use intelligent estimation**
    if 'lot_width' not in auto or not auto.get('lot_width'):
        lot_estimates = estimate_lot_dimensions(address, lat, lon)
        auto.update(lot_estimates)

    # If only area is authoritative, infer dimensions to keep geometry internally consistent
    if auto.get('lot_area') and (not auto.get('lot_width') or not auto.get('lot_depth')):
        try:
            area = float(auto['lot_area'])
            ratio = 1.7
            inferred_width = (area / ratio) ** 0.5
            inferred_depth = inferred_width * ratio
            if not auto.get('lot_width'):
                auto['lot_width'] = round(inferred_width, 1)
            if not auto.get('lot_depth'):
                auto['lot_depth'] = round(inferred_depth, 1)
        except Exception:
            pass

    # Final sanity check: avoid implausibly large fallback for likely unit/subdivided addresses
    has_alpha_suffix = _has_numeric_alpha_address_suffix(address)
    if has_alpha_suffix and auto.get('lot_area', 0) > 700 and not auto.get('lot_area_references'):
        auto['lot_area'] = 500.0
        auto['lot_width'] = 17.1
        auto['lot_depth'] = 29.2
        auto['lot_area_source'] = 'subdivision_sanity_fallback'

    # **LOCK IN DESIGN VALUES BEFORE REGULATORY CHECK**
    # This ensures compliance evaluation sees the correct bedrooms, GFA, and occupancy
    auto['design_locked'] = 'UR Happy Home Standard Rooming House Design v1.0'
    auto['bedrooms'] = 5
    auto['gross_floor_area'] = 274
    auto['persons_accommodated'] = 5

    # Evaluate rooming-house regulatory compliance and include findings
    try:
        regulatory_findings = evaluate_rooming_house_compliance(auto)
        auto['regulatory_findings'] = regulatory_findings
    except Exception:
        auto['regulatory_findings'] = {'error': 'Regulatory evaluation failed'}

    # **NEW: Evaluate site suitability for standard UR Happy Home design**
    try:
        design_suitability = evaluate_site_suitability_for_design(auto)
        auto['design_suitability'] = design_suitability
    except Exception:
        auto['design_suitability'] = {'error': 'Design evaluation failed'}

    # Estimate transport compliance
    TRANSPORT_CATCHMENT = 800
    auto['is_transport_compliant'] = auto['dist_transport'] <= TRANSPORT_CATCHMENT

    # **NEW: Populate scoring fields for compliance calculations**
    # Zone assessment - recognize compliant residential zones
    zone = auto.get('zone_type', '')
    compliant_zones = ['General Residential', 'Residential Growth Zone', 'Neighbourhood Residential', 'Mixed Use']
    auto['is_preferred_zone'] = any(cz.lower() in zone.lower() for cz in compliant_zones)
    
    # Width compliance - minimum 12m recommended, 15m excellent
    lot_width = auto.get('lot_width', 0)
    auto['is_width_compliant'] = lot_width >= 12
    
    # Area compliance - minimum 300m² recommended for rooming house, 800m² scores excellent
    lot_area = auto.get('lot_area', 0)
    auto['is_area_compliant'] = lot_area >= 300
    
    # Compliance with building standards (locked design is fully compliant)
    auto['check_heating'] = 1  # Design has fixed ducted heating
    auto['check_windows'] = 1  # Design meets modern window standards
    auto['check_energy'] = 1   # Design has 7.5 energy rating

    # Cache the result for future lookups
    _cache_property_data(lat, lon, auto)

    return auto
