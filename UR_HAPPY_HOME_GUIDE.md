# UR Happy Home - Site Assessor Implementation Summary

## What's Been Delivered

### ✅ Phase 1: Core Fixes (Completed Previously)
- ✅ PDF report generation with amenities
- ✅ Lot metrics updated to Victoria standard (14m × 24m = 336 sqm)
- ✅ Zone overlay labeling on maps
- ✅ Activity centre visibility and planning overlays
- ✅ Cached POI fallback (data/poi_cache.json) with weekly GitHub Actions refresh

### ✅ Phase 2: UR Happy Home Rollout Features (Completed Now)

#### 1. **Rebranding** ✅
   - Updated color scheme to UR Happy Home green (#1F7F4C)
   - New page title: "UR Happy Home - Site Assessor"
   - Professional styling aligned with company logo

#### 2. **Authentication System** ✅
   - 5-team member login system (simple_auth.py)
   - Pre-configured credentials for team:
     - team1@urhappyhome.com
     - assessor1@urhappyhome.com
     - assessor2@urhappyhome.com
     - analyst@urhappyhome.com
     - admin@urhappyhome.com
   - Secure session management in Streamlit

#### 3. **VicGIS WFS Auto-Fill** ✅
   - Integration with public opendata.maps.vic.gov.au WFS endpoints
   - Automatic retrieval of:
     - Cadastral parcel boundaries & area
     - Planning zone classification (GRZ, RGZ, NRZ, etc.)
     - Heritage & Neighbourhood Character overlays
   - Falls back to manual entry if WFS unavailable
   - No credentials required (fully public APIs)

#### 4. **Portfolio Dashboard** ✅
   - Real-time statistics:
     - Total sites assessed
     - Suitable / Conditional / Unsuitable breakdown
     - Average viability score
     - Success rate percentage
     - Average lot area & transport distance
   - Quick filter toggles (by status, zone type, constraints)
   - Portfolio comparison view (side-by-side site metrics)

#### 5. **Cost Estimator** ✅
   - Land value estimates by Victorian postcode (data/cost_estimator.py)
   - Construction cost projections (AUD $2,500–3,500/sqm)
   - Total project cost breakdown:
     - Land acquisition (with contingency)
     - Construction (with contingency)
     - Planning & legal fees
     - Finance & holding costs
   - Estimated ROI & payback period
   - Sample outpu: for a site in Ringwood with 8 rooms → ~$850k total → ~$350k annual revenue → ~2.4 year payback

#### 6. **Excel Multi-Sheet Export** ✅
   - Comprehensive workbooks with 5 professional sheets:
     1. **Assessment Summary** — site details, viability score, status
     2. **Physical & Cost** — lot dimensions, regulatory compliance, cost estimates
     3. **Amenities** — nearby transit, schools, parks, shops, heritage (top 5 each)
     4. **Comparison** — side-by-side comparison of multiple sites (if selected)
     5. **Recommendations** — constraints, next steps, action items
   - Color-coded headers matching UR Happy Home branding
   - Export button in portfolio sidebar

#### 7. **Weekly POI Cache Updater** ✅
   - GitHub Actions workflow (.github/workflows/weekly-update.yml)
   - Automatically runs every Monday at 03:00 UTC
   - Can be manually triggered with custom coordinates
   - Keeps data/poi_cache.json fresh

### 📦 New Files Created

```
vicgis_wfs_lookup.py         # VicGIS WFS integration (auto-fill parcel/zone/overlays)
portfolio_utils.py            # Dashboard stats, filtering, comparison logic
cost_estimator.py             # Land value & construction cost estimates
excel_exporter.py             # Multi-sheet Excel report generator
simple_auth.py                # Team authentication (5 users)
.github/workflows/weekly-update.yml  # Auto-cache refresh workflow
generate_preview.py           # Script to generate HTML map & PDF previews
assets/                       # Directory for logos/images
```

## Quick Start Guide

### 1. Run the App Locally

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Start the app
streamlit run app.py

# Open browser at http://localhost:8501
```

### 2. Login
Use demo credentials:
- **Email:** admin@urhappyhome.com
- **Password:** urh_admin_1

(See simple_auth.py for other team member credentials)

### 3. Assess a Site
1. Enter an address (e.g., "123 Smith Street, Ringwood, VIC 3134")
2. Click "Assess Site"
3. App auto-fills from VicGIS:
   - Planning zone
   - Lot dimensions (estimated from parcel area)
   - Overlay flags (Heritage, NCO)
4. Complete remaining fields (optional):
   - Site slope
   - Regulatory compliance checkboxes
5. App calculates viability score + recommendations
6. Generate PDF or Excel report

### 4. Portfolio Management
- **Dashboard** (left sidebar):
  - View aggregate stats (total sites, % suitable, avg score)
  - See list of recent assessments
  - Quick filter by status or zone
  - Export entire portfolio to Excel
- **Comparison View**: Select multiple sites to compare side-by-side
- **Cost Estimator**: View land value + construction + ROI for any site

### 5. Export Reports

**PDF Report:**
- "Generate PDF" button → Download professional PDF with all assessment sections

**Excel Workbook:**
- "Export All to Excel" button (sidebar) → Multi-sheet workbook with summary, costs, amenities, comparison, recommendations

## Data Sources & APIs

### Public Data Accessed (No Credentials Needed)
| Source | Purpose | API |
|--------|---------|-----|
| VicGIS (opendata.maps.vic.gov.au) | Parcel boundaries, zones, overlays | WFS (public) |
| OpenStreetMap/Overpass | Amenities (schools, parks, transit, shops) | Overpass API (public, rate-limited) |
| Data.Vic | Planning datasets, activity centres | WFS/WMS (public) |

### Cost Data
- Land values by postcode: Based on 2025 Victorian market estimates (conservative)
- Construction rates: $2,500–$3,500/sqm (Victoria average for residential)

**Note:** Estimates are indicative; actual costs vary by market, site conditions, and market timing.

## Team Authentication

**5 Pre-configured Users** (in simple_auth.py):

| Email | Password | Role |
|-------|----------|------|
| team1@urhappyhome.com | urh_team_1 | Team Lead |
| assessor1@urhappyhome.com | urh_assessor_1 | Assessor |
| assessor2@urhappyhome.com | urh_assessor_2 | Assessor |
| analyst@urhappyhome.com | urh_analyst_1 | Data Analyst |
| admin@urhappyhome.com | urh_admin_1 | Administrator |

**Upgrade Path:** Replace simple_auth.py with OAuth2 / SAML / Azure AD integration for production.

## Future Enhancements (Optional)

1. **Parcel Geometry Analysis** — Extract exact lot width/depth from parcel polygon (currently estimate from area)
2. **Title Search Integration** — Connect to Landata/LPI for covenant & title status (requires credentials)
3. **PTV Live API** — Real-time transit accuracy (requires PTV API key)
4. **Multi-LGA Support** — Pre-cache data for multiple LGAs, refresh independently
5. **Advanced Filters** — Search by LGA, proximity to specific amenities, price range
6. **Team Roles & Permissions** — Role-based data access (assessor vs. approver vs. admin)
7. **Audit Trail** — Log all assessments, changes, and decisions for compliance

## Troubleshooting

**VicGIS WFS timeout:**
- Falls back to manual entry automatically
- Try again or check VicGIS status at opendata.maps.vic.gov.au

**Overpass POI failures:**
- Cached POIs (data/poi_cache.json) are used as fallback
- Synthetic dummy POIs generated if both live and cache fail

**Excel export error:**
- Ensure openpyxl is installed: `pip install openpyxl`

## Support & Maintenance

### Weekly Cache Refresh
- Automatic: GitHub Actions runs every Monday 03:00 UTC
- Manual: `python weekly_updater.py --lat -37.8136 --lon 144.9631 --radius 2.0`
- Custom coords: Set LAT, LON, RADIUS env vars or CLI args

### Logs & Diagnostics
- Run: `python test_diagnostics.py` (validates all modules)
- Check Streamlit logs in terminal when running the app

---

**Generated:** February 16, 2026 | **For:** UR Happy Home Real Estate Team
