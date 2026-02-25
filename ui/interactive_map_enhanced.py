"""
Advanced interactive map with layer controls and professional overlays.
Implements real estate mapping best practices.
"""

import folium
from folium import plugins
import pandas as pd
from ui.advanced_map import get_poi_data, _load_poi_cache, _generate_dummy_pois

def create_professional_interactive_map(
    latitude,
    longitude,
    address,
    viability_color,
    zone_type,
    has_overlay,
    lot_width,
    lot_depth,
    show_transit=True,
    show_schools=True,
    show_parks=True,
    show_shops=True,
    show_heritage=False,
    map_type="Satellite Hybrid"
):
    """
    Create a professional interactive map with multiple layers and controls.
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        address: Site address string
        viability_color: Color code for site viability (green/orange/red)
        zone_type: Planning zone
        has_overlay: Whether site has overlays
        lot_width: Lot width in meters
        lot_depth: Lot depth in meters
        show_transit: Show transit layer
        show_schools: Show schools layer
        show_parks: Show parks layer
        show_shops: Show shops layer
        show_heritage: Show heritage layer
        map_type: Base map type
        
    Returns:
        Folium map object with layers and POI data
    """
    
    # Initialize map with professional styling
    if map_type == "OpenStreetMap":
        m = folium.Map(
            location=[latitude, longitude],
            zoom_start=15,
            tiles="OpenStreetMap",
            prefer_canvas=True,
            max_bounds=True
        )
    elif map_type == "Terrain":
        m = folium.Map(
            location=[latitude, longitude],
            zoom_start=15,
            tiles="OpenTopoMap",
            prefer_canvas=True,
            max_bounds=True
        )
    else:
        # Default professional basemap: Esri imagery + labels (hybrid-style)
        m = folium.Map(
            location=[latitude, longitude],
            zoom_start=15,
            tiles=None,
            prefer_canvas=True,
            max_bounds=True
        )
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles © Esri",
            name="Satellite Imagery",
            overlay=False,
            control=False,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="Labels © Esri",
            name="Satellite Labels",
            overlay=True,
            control=False,
        ).add_to(m)
    
    # Create feature groups for layer control
    site_layer = folium.FeatureGroup(name="📍 Site & Lot Boundaries", show=True)
    transport_layer = folium.FeatureGroup(name="🚌 Public Transport", show=show_transit)
    schools_layer = folium.FeatureGroup(name="🎓 Schools & Education", show=show_schools)
    parks_layer = folium.FeatureGroup(name="🌳 Parks & Recreation", show=show_parks)
    shops_layer = folium.FeatureGroup(name="🛒 Shops & Services", show=show_shops)
    heritage_layer = folium.FeatureGroup(name="🏛️ Heritage Sites", show=show_heritage)
    zone_overlay_layer = folium.FeatureGroup(name="📋 Planning Overlays", show=True)
    transport_catchment_layer = folium.FeatureGroup(name="📏 Transport Catchment (800m)", show=True)
    
    # ========================================
    # SITE MARKER & GEOMETRY
    # ========================================
    
    # Color mapping for viability
    color_map = {
        'green': '#27AE60',
        'orange': '#F39C12',
        'red': '#E74C3C'
    }
    site_color = color_map.get(viability_color, '#1F7F4C')
    icon_color_map = {
        'green': 'green',
        'orange': 'orange',
        'red': 'red'
    }
    
    # Main site marker with custom styling
    folium.Marker(
        location=[latitude, longitude],
        popup=f"""
        <div style="width: 200px; font-family: Arial;">
            <h4 style="color: #1F7F4C; margin: 0 0 10px 0;">📍 Development Site</h4>
            <p style="margin: 5px 0;"><b>Address:</b> {address}</p>
            <p style="margin: 5px 0;"><b>Zone:</b> {zone_type}</p>
            <p style="margin: 5px 0;"><b>Lot Size:</b> {lot_width:.1f}m × {lot_depth:.1f}m</p>
            <p style="margin: 5px 0;"><b>Status:</b> <span style="color: {site_color}; font-weight: bold;">
                {'Suitable' if viability_color == 'green' else 'Conditional' if viability_color == 'orange' else 'Unsuitable'}</span>
            </p>
        </div>
        """,
        tooltip=f"Site: {address}",
        icon=folium.Icon(
            color=icon_color_map.get(viability_color, 'green'),
            icon='home',
            prefix='fa',
            icon_color='white'
        )
    ).add_to(site_layer)
    
    # Lot boundary polygon (estimated from dimensions)
    lot_bounds = calculate_lot_bounds(latitude, longitude, lot_width, lot_depth)
    
    folium.Polygon(
        locations=lot_bounds,
        color=site_color,
        fill=True,
        fillColor=site_color,
        fillOpacity=0.2,
        weight=3,
        popup=f"Lot Boundary ({lot_width:.1f}m × {lot_depth:.1f}m)",
        tooltip="Lot Boundary"
    ).add_to(site_layer)
    
    # ========================================
    # TRANSPORT CATCHMENT RING
    # ========================================
    
    folium.Circle(
        location=[latitude, longitude],
        radius=800,  # 800 meters
        popup="Transport Catchment - 800m radius",
        color='#3498DB',
        fill=True,
        fillColor='#3498DB',
        fillOpacity=0.1,
        weight=2,
        dash_array='10, 5',
        tooltip="800m Transport Catchment"
    ).add_to(transport_catchment_layer)
    
    # ========================================
    # POINTS OF INTEREST
    # ========================================
    
    # Get POI data
    poi_types = ['transit', 'schools', 'parks', 'shops', 'heritage', 'hospitals']
    poi_data = {}
    try:
        for poi_type in poi_types:
            poi_data[poi_type] = get_poi_data(latitude, longitude, poi_type, radius_km=1.0)
    except Exception as e:
        print(f"Error loading POI data for interactive map: {e}")
        for poi_type in poi_types:
            cache_data = _load_poi_cache(latitude, longitude, poi_type, radius_km=1.0)
            poi_data[poi_type] = cache_data if cache_data else _generate_dummy_pois(latitude, longitude, poi_type)
    
    # Transit stops
    if show_transit and 'transit' in poi_data:
        for poi in poi_data['transit'][:15]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=6,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                tooltip=poi['name'],
                color='#E74C3C',
                fill=True,
                fillColor='#E74C3C',
                fillOpacity=0.7,
                weight=2
            ).add_to(transport_layer)
    
    # Schools
    if show_schools and 'schools' in poi_data:
        for poi in poi_data['schools'][:15]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=7,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m<br/>Type: {poi['type']}",
                tooltip=poi['name'],
                color='#3498DB',
                fill=True,
                fillColor='#3498DB',
                fillOpacity=0.7,
                weight=2
            ).add_to(schools_layer)
    
    # Parks
    if show_parks and 'parks' in poi_data:
        for poi in poi_data['parks'][:15]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=7,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                tooltip=poi['name'],
                color='#27AE60',
                fill=True,
                fillColor='#27AE60',
                fillOpacity=0.7,
                weight=2
            ).add_to(parks_layer)
    
    # Shops
    if show_shops and 'shops' in poi_data:
        for poi in poi_data['shops'][:15]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=6,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m",
                tooltip=poi['name'],
                color='#F39C12',
                fill=True,
                fillColor='#F39C12',
                fillOpacity=0.7,
                weight=2
            ).add_to(shops_layer)
    
    # Heritage sites
    if show_heritage and 'heritage' in poi_data:
        for poi in poi_data['heritage'][:15]:
            folium.CircleMarker(
                location=[poi['lat'], poi['lon']],
                radius=7,
                popup=f"<b>{poi['name']}</b><br/>Distance: {poi['distance_m']}m<br/>Heritage",
                tooltip=poi['name'],
                color='#9B59B6',
                fill=True,
                fillColor='#9B59B6',
                fillOpacity=0.7,
                weight=2
            ).add_to(heritage_layer)
    
    # ========================================
    # PLANNING OVERLAYS
    # ========================================
    
    if has_overlay:
        # Activity centres - nearby major centers
        activity_centres = [
            {'name': 'Ringwood Activity Centre', 'lat': -37.8136, 'lon': 144.9631, 'radius': 500},
            {'name': 'Forest Hill Activity Centre', 'lat': -37.8313, 'lon': 145.0986, 'radius': 500},
        ]
        
        for centre in activity_centres:
            folium.Circle(
                location=[centre['lat'], centre['lon']],
                radius=centre['radius'],
                popup=f"{centre['name']} (Activity Centre)",
                color='#8E44AD',
                fill=True,
                fillColor='#8E44AD',
                fillOpacity=0.1,
                weight=2,
                dash_array='5, 5'
            ).add_to(zone_overlay_layer)
            
            folium.Marker(
                location=[centre['lat'], centre['lon']],
                popup=centre['name'],
                icon=folium.Icon(color='purple', icon='star', prefix='fa'),
                tooltip=centre['name']
            ).add_to(zone_overlay_layer)
    
    # ========================================
    # MEASUREMENT & DISTANCE TOOLS
    # ========================================
    
    # Add measure control
    plugins.MeasureControl(primary_length_unit='meters').add_to(m)
    
    # Add fullscreen control
    plugins.Fullscreen().add_to(m)
    
    # Add mini map
    minimap = plugins.MiniMap(toggle_display=True)
    m.add_child(minimap)
    
    # ========================================
    # ADD LAYERS TO MAP
    # ========================================
    
    site_layer.add_to(m)
    transport_catchment_layer.add_to(m)
    transport_layer.add_to(m)
    schools_layer.add_to(m)
    parks_layer.add_to(m)
    shops_layer.add_to(m)
    heritage_layer.add_to(m)
    zone_overlay_layer.add_to(m)
    
    # Add layer control with professional styling
    layer_control = folium.LayerControl(
        position='topright',
        collapsed=False,
        auto_index=False
    )
    m.add_child(layer_control)
    
    # Add custom CSS for layer control styling
    m.get_root().html.add_child(folium.Element("""
    <style>
        .leaflet-control-layers-toggle {
            background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect fill="%231F7F4C" width="32" height="32"/><path fill="white" d="M8 6h16v4H8V6m0 6h16v4H8v-4m0 6h16v4H8v-4"/></svg>') !important;
        }
        
        .leaflet-control-layers {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(31, 127, 76, 0.2);
        }
        
        .leaflet-control-layers-list label {
            font-weight: 500;
            color: #2C3E50;
        }
        
        .leaflet-control-layers-list label:hover {
            background-color: #f8f9fa;
        }
    </style>
    """))
    
    return m, poi_data


def calculate_lot_bounds(lat, lon, width_m, depth_m):
    """
    Calculate approximate lot boundary coordinates from center point and dimensions.
    
    Args:
        lat: Latitude of center
        lon: Longitude of center
        width_m: Width in meters (East-West)
        depth_m: Depth in meters (North-South)
    
    Returns:
        List of [lat, lon] coordinates for polygon
    """
    
    # Approximate meters per degree at Victoria's latitude
    meters_per_lat = 111000
    meters_per_lon = 111000 * 0.784  # cos(37.8°) for Victoria
    
    half_width_deg = (width_m / 2) / meters_per_lon
    half_depth_deg = (depth_m / 2) / meters_per_lat
    
    bounds = [
        [lat + half_depth_deg, lon - half_width_deg],  # NW
        [lat + half_depth_deg, lon + half_width_deg],  # NE
        [lat - half_depth_deg, lon + half_width_deg],  # SE
        [lat - half_depth_deg, lon - half_width_deg],  # SW
        [lat + half_depth_deg, lon - half_width_deg],  # Close polygon
    ]
    
    return bounds


def add_scale_and_tools(m):
    """Add scale, coordinates display, and other useful tools."""
    
    # Add scale
    plugins.MiniMap(
        toggle_display=True,
        width=150,
        height=150,
    ).add_to(m)
    
    # Add coordinates display via custom HTML
    m.get_root().html.add_child(folium.Element("""
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 200px;
        background: white;
        padding: 10px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-family: Arial, sans-serif;
        font-size: 11px;
        z-index: 9999;
    " id="coords-display">
        <div style="color: #1F7F4C; font-weight: bold; margin-bottom: 5px;">
            Map Information
        </div>
        <div id="coords-text" style="color: #666;">Hover over map for coordinates</div>
    </div>
    
    <script>
        var map = window.map || document.querySelector('.leaflet-container').mapObject;
        if (map) {
            map.on('mousemove', function(e) {
                document.getElementById('coords-text').innerHTML = 
                    'Lat: ' + e.latlng.lat.toFixed(4) + '<br/>' +
                    'Lon: ' + e.latlng.lng.toFixed(4) + '<br/>' +
                    'Zoom: ' + map.getZoom();
            });
        }
    </script>
    """))
