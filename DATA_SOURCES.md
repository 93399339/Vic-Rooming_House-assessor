# Data Sources & Integration Notes

This document lists recommended authoritative data sources to fully automate assessments from an address. Some data sources require credentials, licensing, or paid access.

- Planning zones / overlays
  - Source: VicPlan / Department of Transport and Planning (Victoria) WMS/WFS or GeoJSON
  - Purpose: Determine Planning Zone (GRZ/RGZ/NRZ/etc) and overlays (HO, NCO)
  - Notes: VicPlan offers APIs and spatial services; licensing and URL endpoints may change. Consider contacting Planning.vic.gov.au for WMS/WFS endpoints or using `data.vic.gov.au` datasets.

- Cadastral parcels & lot dimensions
  - Source: Vicmap Property / Landata / State Government cadastral services (WFS)
  - Purpose: Derive lot boundary, calculate lot width/depth/area exactly
  - Notes: Title/parcel data access may require credentials or fees. If unavailable, approximate lot size via cadastral datasets published on `data.vic.gov.au` or use local council property APIs if available.

- Title covenants (Single Dwelling Covenant)
  - Source: Landata / Titles Office (LPI Victoria)
  - Purpose: Identify covenant restrictions on title (private legal instrument)
  - Notes: Frequently requires paid access and is not openly accessible via a free API. For robust legal checks include a step to order a title search.

- Public transport (stops / stations)
  - Source: Public Transport Victoria (PTV) API or OpenStreetMap (Overpass)
  - Purpose: Accurate stop/station locations and modes (train/tram/bus)
  - Notes: PTV API may require API key; Overpass is free but rate-limited. We recommend caching PTV or Overpass data weekly.

- Schools, hospitals, shops, parks (amenities)
  - Source: OpenStreetMap (Overpass API) and/or state datasets (data.vic.gov.au)
  - Purpose: Populate nearby amenities and compute distances
  - Notes: Use Overpass for convenience and weekly caching; for authoritative data use state datasets where available.

- Activity centres / planning designations
  - Source: State planning datasets (activity centres layers), local council GIS
  - Purpose: Identify nearest Principal/Major/Regional Activity Centre
  - Notes: We maintain a small built-in list for major centres and supplement with state WMS if available.

Recommendations for implementation
- Use a scheduled job (cron or GitHub Actions) to refresh POI caches weekly using `weekly_updater.py`.
- For authoritative planning zone and cadastral parcel data, configure WFS/WMS endpoints (credentials as needed) and implement a `fetch_parcel_and_zone(lat, lon)` function that queries those services and returns structured properties for the report.
- If title/covenant data is required in the report, add a step to procure official title searches (manual or integrated with Landata where licensing permits).

Contact/Access
- Planning Victoria: https://www.planning.vic.gov.au/
- Data.Vic: https://www.data.vic.gov.au/
- Overpass API / OpenStreetMap: https://overpass-api.de/
- Public Transport Victoria (PTV): https://www.ptv.vic.gov.au/ (developer APIs may require key)
- Landata / Titles: https://www.landata.vic.gov.au/ (may require subscription)
