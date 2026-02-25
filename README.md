# Vic-Rooming_House-assessor
Web based Rooming House interactive map assessment
# Vic-Rooming_House-assessor
Web based Rooming House interactive map assessment

## Weekly POI Cache & Automation

This project refreshes nearby Points-of-Interest (POI) weekly and stores a cached copy at `data/poi_cache.json` so the app remains reliable if live Overpass queries fail.

How it works
- `weekly_updater.py` — queries POI layers and writes `data/poi_cache.json`.
- A GitHub Actions workflow `.github/workflows/weekly-update.yml` runs weekly and commits the refreshed cache back to the repo.

Run locally
1. (Optional) create and activate a Python virtualenv
2. Install deps if you have a `requirements.txt`

```bash
python -m pip install -r requirements.txt
python weekly_updater.py --lat -37.8136 --lon 144.9631 --radius 2.0
```

Trigger the GitHub Actions workflow manually
- Via the GitHub Actions UI: open the `Weekly POI Cache Refresh` workflow and click `Run workflow`. You can provide inputs for `lat`, `lon`, and `radius`.
- Via GitHub CLI (example):

```bash
# Install GitHub CLI and authenticate first: https://cli.github.com/
gh workflow run weekly-update.yml --repo YOUR-ORG/Vic-Rooming_House-assessor --ref main \
	-f lat=-37.8136 -f lon=144.9631 -f radius=2.0
```

Notes
- The workflow runs every Monday 03:00 UTC by default. Adjust schedule in `.github/workflows/weekly-update.yml` if needed.
- If you want authoritative parcel/zone extraction, provide WFS/WMS endpoints and credentials; see `DATA_SOURCES.md` for recommended services.
