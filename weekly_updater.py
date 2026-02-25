"""
Weekly updater script to refresh POI cache for the app.

Usage:
  python weekly_updater.py --lat -37.8136 --lon 144.9631 --radius 5

This will call `advanced_map.get_poi_data` for each POI type and save to `data/poi_cache.json`.
"""

import argparse
import json
import os
from ui.advanced_map import get_poi_data


def refresh_cache(lat: float, lon: float, radius_km: float = 1.0, out_path: str = None):
    base = os.path.dirname(__file__)
    data_dir = os.path.join(base, 'data')
    os.makedirs(data_dir, exist_ok=True)
    out_file = out_path or os.path.join(data_dir, 'poi_cache.json')

    types = ['transit', 'schools', 'parks', 'shops', 'heritage', 'hospitals']
    cache = {}
    for t in types:
        try:
            items = get_poi_data(lat, lon, t, radius_km)
            # store minimal fields
            cache[t] = [{'name': i['name'], 'lat': i['lat'], 'lon': i['lon']} for i in items]
            print(f"Fetched {len(items)} items for {t}")
        except Exception as e:
            print(f"Failed to fetch {t}: {e}")
            cache[t] = []

    with open(out_file, 'w', encoding='utf-8') as fh:
        json.dump(cache, fh, indent=2)

    print(f"Wrote POI cache to {out_file}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--lat', type=float, required=True)
    parser.add_argument('--lon', type=float, required=True)
    parser.add_argument('--radius', type=float, default=1.0)
    parser.add_argument('--out', type=str, default=None)
    args = parser.parse_args()
    refresh_cache(args.lat, args.lon, args.radius, args.out)
