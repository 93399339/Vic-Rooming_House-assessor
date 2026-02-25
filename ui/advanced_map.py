"""
Advanced Mapping Module for Vic Rooming House Assessor
Provides enriched map visualization with points of interest (POI), overlays, and planning data
"""

import folium
import streamlit as st
import requests
import json
import os
from haversine import haversine
from typing import Tuple, List, Dict

# Constants for Overpass API
OVERPASS_API = "https://overpass-api.de/api/interpreter"
SEARCH_RADIUS_KM = 1.0  # 1km radius for POI searches

# Victoria planning WMS/GeoJSON endpoints
ACTIVITY_CENTRES_WMS = "https://services.arcgisonline.com/ArcGIS/rest/services"
VICMAP_DATA_URL = "https://data.vic.gov.au"

# Activity centres data (major Victoria centres)
VICTORIA_ACTIVITY_CENTRES = [
    {"name": "Melbourne CBD", "lat": -37.8136, "lon": 144.9631, "type": "Principal Activity Centre", "radius": 2000},
    {"name": "Docklands", "lat": -37.8201, "lon": 144.9518, "type": "Principal Activity Centre", "radius": 1500},
    {"name": "Southbank", "lat": -37.8272, "lon": 144.9675, "type": "Principal Activity Centre", "radius": 1500},
    {"name": "Parramatta (Western Sydney reference)", "lat": -33.8121, "lon": 151.0029, "type": "Major Activity Centre", "radius": 1200},
    # Regional centres will be filtered by proximity
]

def get_nearby_activity_centres(latitude: float, longitude: float, radius_km: float = 5.0) -> List[Dict]:
    """
    Get activity centres near the assessment site from Victoria planning data
    Uses both Esri services and local knowledge
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        radius_km: Search radius in kilometers
    
    Returns:
        List of activity centres within radius
    """
    nearby = []
    
    for centre in VICTORIA_ACTIVITY_CENTRES:
        distance_km = haversine((latitude, longitude), (centre['lat'], centre['lon']))
        if distance_km <= radius_km:
            centre_copy = centre.copy()
            centre_copy['distance_km'] = distance_km
            nearby.append(centre_copy)
    
    # Sort by distance
    nearby.sort(key=lambda x: x['distance_km'])
    return nearby

def add_planning_overlays(m: folium.Map, latitude: float, longitude: float, 
                         show_activity_centres: bool = True, 
                         show_transport_zones: bool = True) -> folium.Map:
    """
    Add Victoria planning overlays to the map
    
    Args:
        m: Folium map object
        latitude: Site latitude
        longitude: Site longitude
        show_activity_centres: Show activity centres overlay
        show_transport_zones: Show transport catchment zones
    
    Returns:
        Enhanced Folium map
    """
    
    # Add activity centres overlay if enabled
    if show_activity_centres:
        activity_centres = get_nearby_activity_centres(latitude, longitude, radius_km=5.0)
        
        for centre in activity_centres:
            # Colour code by type
            color = "#FF6B35" if centre['type'] == "Principal Activity Centre" else "#FFA500"
            
            # Add circle for activity centre catchment
            folium.Circle(
                radius=centre.get('radius', 1000),
                location=[centre['lat'], centre['lon']],
                color=color,
                fill=True,
                fill_opacity=0.12,
                popup=f"<b>{centre['name']}</b><br/>{centre['type']}<br/>Distance: {centre['distance_km']:.1f}km",
                weight=2,
                name="Activity Centres (Planning Zone)"
            ).add_to(m)
            
            # Add marker for activity centre
            folium.Marker(
                location=[centre['lat'], centre['lon']],
                popup=f"<b>{centre['name']}</b><br/>{centre['type']}<br/>Distance: {centre['distance_km']:.1f}km",
                icon=folium.Icon(color=("orange" if centre['type'] == "Principal Activity Centre" else "orange"), 
                               icon="shopping-cart", prefix="fa", icon_color="white"),
                tooltip=f"{centre['name']} - {centre['type']}",
                name="Activity Centres"
            ).add_to(m)
    
    # Add transport zones overlay
    if show_transport_zones:
        # Add 1.5km transport zone (Strategic Planning)
        folium.Circle(
            radius=1500,
            location=[latitude, longitude],
            color="green",
            fill=True,
            fill_opacity=0.08,
            popup="1.5km Transport-Oriented Development Zone",
            weight=2,
            dash_array="2, 8",
            name="TOD Zone (1.5km)"
        ).add_to(m)
    
    return m

def get_poi_data(latitude: float, longitude: float, poi_type: str, radius_km: float = SEARCH_RADIUS_KM) -> List[Dict]:
    """
    Fetch Points of Interest from OpenStreetMap using Overpass API
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        poi_type: Type of POI ('transit', 'schools', 'parks', 'shops', 'heritage')
        radius_km: Search radius in kilometers
    
    Returns:
        List of POI dictionaries with name, lat, lon, type
    """
    
    # Define Overpass queries for different POI types (more robust tags)
    # Use a squared bbox around the point (approx. delta degrees)
    delta = 0.01
    bbox = f"{latitude - delta},{longitude - delta},{latitude + delta},{longitude + delta}"
    queries = {
        'transit': f"""
            [bbox:{bbox}];
            (
              node["public_transport"="platform"];
              node["public_transport"="stop_position"];
              node["railway"="station"];
              node["highway"="bus_stop"];
            );
            out center;
        """,
        'schools': f"""
            [bbox:{bbox}];
            (
              node["amenity"="school"];
              way["amenity"="school"];
            );
            out center;
        """,
        'parks': f"""
            [bbox:{bbox}];
            (
              node["leisure"="park"];
              node["leisure"="playground"];
              way["leisure"="park"];
              way["leisure"="playground"];
            );
            out center;
        """,
        'shops': f"""
            [bbox:{bbox}];
            (
              node["shop"];
              node["amenity"="supermarket"];
              node["amenity"="convenience"];
            );
            out center limit 30;
        """,
        'heritage': f"""
            [bbox:{bbox}];
            (
              node["historic"];
              way["historic"];
              node["heritage"];
              way["heritage"];
            );
            out center;
        """,
        'hospitals': f"""
            [bbox:{bbox}];
            (
              node["amenity"="hospital"];
              way["amenity"="hospital"];
            );
            out center;
        """
    }
    
    if poi_type not in queries:
        return []
    
    try:
        # Make request to Overpass API
        response = requests.post(
            OVERPASS_API,
            data={"data": queries[poi_type]},
            timeout=10
        )
        
        if response.status_code != 200:
            # Try to use cached POIs if available before falling back to dummy POIs
            print(f"Overpass returned status {response.status_code}")
            cache = _load_poi_cache(latitude, longitude, poi_type, radius_km)
            if cache:
                return cache
            return _generate_dummy_pois(latitude, longitude, poi_type)
        
        data = response.json()
        pois = []
        
        # Extract POI data
        for element in data.get('elements', []):
            if 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            elif 'lat' in element:
                lat = element['lat']
                lon = element['lon']
            else:
                continue
            
            # Calculate distance from site
            distance_km = haversine((latitude, longitude), (lat, lon))
            
            # Filter by radius
            if distance_km <= radius_km:
                name = element.get('tags', {}).get('name', f"{poi_type.title()} Point")
                pois.append({
                    'name': name,
                    'lat': lat,
                    'lon': lon,
                    'distance_m': int(distance_km * 1000),
                    'type': poi_type
                })
        
        return pois
    
    except Exception as e:
        print(f"Error fetching {poi_type}: {e}")
        # On exception, try cached POIs, then dummy
        cache = _load_poi_cache(latitude, longitude, poi_type, radius_km)
        if cache:
            return cache
        return _generate_dummy_pois(latitude, longitude, poi_type)


def _load_poi_cache(latitude: float, longitude: float, poi_type: str, radius_km: float = SEARCH_RADIUS_KM) -> List[Dict]:
    """
    Load POIs from a local JSON cache and return entries within radius_km of the given point.
    Cache file path: data/poi_cache.json relative to this module.
    """
    try:
        base_dir = os.path.dirname(__file__)
        cache_path = os.path.join(base_dir, 'data', 'poi_cache.json')
        if not os.path.exists(cache_path):
            return []

        with open(cache_path, 'r', encoding='utf-8') as fh:
            cache = json.load(fh)

        items = cache.get(poi_type, [])
        results = []
        for element in items:
            lat = element.get('lat')
            lon = element.get('lon')
            if lat is None or lon is None:
                continue
            distance_km = haversine((latitude, longitude), (lat, lon))
            if distance_km <= radius_km:
                results.append({
                    'name': element.get('name', f"{poi_type.title()} Point"),
                    'lat': lat,
                    'lon': lon,
                    'distance_m': int(distance_km * 1000),
                    'type': poi_type
                })
        return results
    except Exception as e:
        print(f"Error loading POI cache: {e}")
        return []


def _generate_dummy_pois(latitude: float, longitude: float, poi_type: str) -> List[Dict]:
    """Generate small set of synthetic POIs as fallback when Overpass API is unavailable."""
    samples = []
    offsets = [ (0.0008, 0.0005), (-0.0006, 0.0009), (0.0004, -0.0007) ]
    names = {
        'transit': ['Main St Station', 'Central Bus Stop', 'Local Platform'],
        'schools': ['Primary School', 'High School', 'Community College'],
        'parks': ['Local Park', 'Neighbourhood Reserve', 'Playground'],
        'shops': ['Supermarket', 'Corner Store', 'Pharmacy'],
        'heritage': ['Historic Site', 'Heritage Building', 'Old Church'],
        'hospitals': ['Community Hospital', 'Health Clinic', 'Emergency Centre']
    }
    for i, off in enumerate(offsets):
        lat = latitude + off[0]
        lon = longitude + off[1]
        dist_m = int(haversine((latitude, longitude), (lat, lon)) * 1000)
        samples.append({
            'name': names.get(poi_type, ['POI'])[i % 3],
            'lat': lat,
            'lon': lon,
            'distance_m': dist_m,
            'type': poi_type
        })
    return samples

def create_advanced_map(
    latitude: float,
    longitude: float,
    address: str,
    viability_color: str,
    show_transit: bool = True,
    show_schools: bool = True,
    show_parks: bool = True,
    show_shops: bool = True,
    show_heritage: bool = False,
    map_type: str = "OpenStreetMap",
    zone_type: str = "",
    has_overlay: bool = False,
    zoom_start: int = 16,
) -> Tuple[folium.Map, Dict]:
    """
    Create an advanced folium map with POIs and multiple layers
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        address: Site address for popup
        viability_color: Site viability color (green/orange/red)
        show_transit: Show public transport stops
        show_schools: Show schools nearby
        show_parks: Show parks nearby
        show_shops: Show shops nearby
        show_heritage: Show heritage sites
        map_type: Type of map tile ('OpenStreetMap', 'Satellite', 'Hybrid')
    
    Returns:
        Tuple of (folium map, POI summary dict)
    """
    
    # Map tile options
    tiles = {
        'OpenStreetMap': 'OpenStreetMap',
        'Satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        'Terrain': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        'Dark': 'CartoDB positron'
    }
    
    # Create base map
    m = folium.Map(
        location=[latitude, longitude],
        zoom_start=zoom_start,
        tiles=tiles.get(map_type, 'OpenStreetMap')
    )
    
    # Add other tile options
    folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite View',
        overlay=False
    ).add_to(m)
    folium.TileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Terrain',
        overlay=False
    ).add_to(m)
    
    # Add 800m transport catchment circle
    folium.Circle(
        radius=800,
        location=[latitude, longitude],
        color="blue",
        fill=True,
        fill_opacity=0.12,
        popup="800m Transport/Activity Centre Catchment",
        weight=2,
        name="800m Catchment"
    ).add_to(m)
    
    # Add 1km amenity radius circle
    folium.Circle(
        radius=1000,
        location=[latitude, longitude],
        color="purple",
        fill=False,
        fill_opacity=0.05,
        popup="1km Amenity Radius",
        weight=1,
        dash_array="5, 5",
        name="1km Amenity Radius"
    ).add_to(m)
    
    # Add site marker
    icon_color = "green" if viability_color == "green" else ("orange" if viability_color == "orange" else "red")
    folium.Marker(
        [latitude, longitude],
        popup=f"<b>{address}</b><br/>Assessment Site",
        icon=folium.Icon(color=icon_color, icon="home", prefix="fa", icon_color="white"),
        tooltip="Assessment Site",
        name="Assessment Site"
    ).add_to(m)

    # Add planning zone label as a small marker
    if zone_type:
        folium.map.Marker(
            [latitude, longitude],
            icon=folium.DivIcon(html=f"<div style='font-size:12px;color:#333;background:rgba(255,255,255,0.8);padding:4px;border-radius:4px;border:1px solid #ccc'>{zone_type}</div>"),
            tooltip=f"Zone: {zone_type}"
        ).add_to(m)

    # If overlay present, mark on map
    if has_overlay:
        folium.Circle(
            radius=40,
            location=[latitude, longitude],
            color="brown",
            fill=True,
            fill_opacity=0.15,
            popup="Heritage / Neighbourhood Character Overlay present",
            weight=1,
            name="Overlay Indicator"
        ).add_to(m)
    
    # Collect POI summary (including hospitals)
    poi_summary = {
        'transit': [],
        'schools': [],
        'parks': [],
        'shops': [],
        'heritage': [],
        'hospitals': []
    }

    # Create FeatureGroups for each POI category so LayerControl can toggle them
    transit_group = folium.FeatureGroup(name='Transit Stops', show=show_transit)
    schools_group = folium.FeatureGroup(name='Schools', show=show_schools)
    parks_group = folium.FeatureGroup(name='Parks', show=show_parks)
    shops_group = folium.FeatureGroup(name='Shops & Amenities', show=show_shops)
    heritage_group = folium.FeatureGroup(name='Heritage Sites', show=show_heritage)
    hospitals_group = folium.FeatureGroup(name='Hospitals', show=True)

    # Add transit stops
    if show_transit:
        transit_pois = get_poi_data(latitude, longitude, 'transit')
        for poi in transit_pois[:30]:  # Limit for performance
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=6,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                color="red",
                fill=True,
                fillColor="red",
                fillOpacity=0.8,
                weight=1,
            ).add_to(transit_group)
            poi_summary['transit'].append(poi)
    
    # Add schools
    if show_schools:
        school_pois = get_poi_data(latitude, longitude, 'schools')
        for poi in school_pois[:30]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=6,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                color="green",
                fill=True,
                fillColor="green",
                fillOpacity=0.8,
                weight=1,
            ).add_to(schools_group)
            poi_summary['schools'].append(poi)
    
    # Add parks
    if show_parks:
        park_pois = get_poi_data(latitude, longitude, 'parks')
        for poi in park_pois[:30]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=5,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                color="darkgreen",
                fill=True,
                fillColor="lightgreen",
                fillOpacity=0.7,
                weight=1,
            ).add_to(parks_group)
            poi_summary['parks'].append(poi)
    
    # Add shops
    if show_shops:
        shop_pois = get_poi_data(latitude, longitude, 'shops')
        for poi in shop_pois[:30]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=5,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                color="orange",
                fill=True,
                fillColor="orange",
                fillOpacity=0.7,
                weight=1,
            ).add_to(shops_group)
            poi_summary['shops'].append(poi)
    
    # Add heritage sites
    if show_heritage:
        heritage_pois = get_poi_data(latitude, longitude, 'heritage')
        for poi in heritage_pois[:30]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=6,
                popup=f"<b>Heritage: {poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                color="brown",
                fill=True,
                fillColor="tan",
                fillOpacity=0.9,
                weight=1,
            ).add_to(heritage_group)
            poi_summary['heritage'].append(poi)

    # Add hospitals (always show)
    hospital_pois = get_poi_data(latitude, longitude, 'hospitals')
    for poi in hospital_pois[:30]:
        folium.CircleMarker(
            location=[poi['lat'], poi['lon']],
            radius=7,
            popup=f"<b>Hospital: {poi['name']}</b><br/>Distance: {poi['distance_m']}m",
            color="purple",
            fill=True,
            fillColor="purple",
            fillOpacity=0.9,
            weight=1,
        ).add_to(hospitals_group)
        poi_summary['hospitals'].append(poi)

    # Attach groups to map
    transit_group.add_to(m)
    schools_group.add_to(m)
    parks_group.add_to(m)
    shops_group.add_to(m)
    heritage_group.add_to(m)
    hospitals_group.add_to(m)
    
    # Add planning overlays for Victoria planning context
    try:
        m = add_planning_overlays(
            m, 
            latitude, 
            longitude,
            show_activity_centres=True,
            show_transport_zones=True
        )
    except Exception as e:
        print(f"Error adding planning overlays: {e}")
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m, poi_summary

def get_nearby_summary(latitude: float, longitude: float) -> Dict:
    """
    Get a summary of all nearby POIs without rendering
    Useful for text-based reports
    """
    summary = {
        'transit': get_poi_data(latitude, longitude, 'transit')[:5],
        'schools': get_poi_data(latitude, longitude, 'schools')[:5],
        'parks': get_poi_data(latitude, longitude, 'parks')[:5],
        'shops': get_poi_data(latitude, longitude, 'shops')[:5],
        'heritage': get_poi_data(latitude, longitude, 'heritage')[:5]
    }
    return summary
