# UR Happy Home Enhanced App - Quick Reference Guide

## 🚀 Getting Started

### Launch the App
```bash
streamlit run app.py
```
Opens at: `http://localhost:8501`

### Login Credentials
- **Email:** admin@urhappyhome.com
- **Password:** urh_admin_1

**Other Team Members:**
- team1@urhappyhome.com / urh_team_1
- assessor1@urhappyhome.com / urh_assessor_1
- assessor2@urhappyhome.com / urh_assessor_2
- analyst@urhappyhome.com / urh_analyst_1

---

## 🎯 Main Features

### 1. Site Assessment
1. Enter address (e.g., "123 Smith St, Ringwood VIC 3134")
2. Click "🔍 Assess Site"
3. App auto-fills from VicGIS:
   - Planning zone
   - Lot dimensions
   - Overlay information
4. Complete remaining fields
5. View viability score

### 2. Interactive Map
**Features:**
- 📍 Site marker (color-coded status)
- 🚌 Transit stops (red)
- 🎓 Schools (blue)
- 🌳 Parks (green)
- 🛒 Shops (orange)
- 🏛️ Heritage (purple)
- 📏 800m transport catchment
- 📐 Measurement tool
- 🖥️ Fullscreen mode

**How to Use:**
1. Click "🎛️ Map Layer Controls" to expand options
2. Check/uncheck layers to toggle visibility
3. Use map control (☰ top right) to toggle layers
4. Click markers for details
5. Right-click + drag to rotate map
6. Use 📐 tool to measure distances

### 3. PDF Reports
**Generates 8-Section Report:**
1. Executive Summary
2. Zoning Analysis
3. Physical Assessment
4. Regulatory Compliance
5. Transport & Amenities
6. Risk Assessment
7. Recommendations
8. Professional Footer

**To Generate:**
1. Fill in assessment form
2. Scroll to "Generate Assessment Report"
3. Click "📥 Generate Professional PDF"
4. Download appears below

### 4. Portfolio Dashboard
**Sidebar Shows:**
- Total sites assessed
- Suitable count
- Conditional count
- Unsuitable count
- Average score
- Success rate %

**Quick Filters:**
- Filter by status (Suitable/Conditional/Unsuitable)

**Recent Assessments:**
- List of last 10 assessments
- Click to load previous assessment

---

## 🎨 UI Enhancements

### Color Scheme
- 🟢 **Green (#1F7F4C)** - Primary / Suitable
- 🟡 **Orange (#F39C12)** - Warning / Conditional
- 🔴 **Red (#E74C3C)** - Danger / Unsuitable
- ⚪ **Gold (#D4A574)** - Accent

### Design Features
- Professional gradient header
- Smooth hover animations
- Color-coded status badges
- Professional tables
- Responsive layout
- Mobile-friendly design

---

## 📊 Scoring System

### Score Ranges
- **75-100:** SUITABLE 🟢
- **60-74:** CONDITIONAL 🟡
- **Below 60:** UNSUITABLE/INVESTIGATE 🔴

### Score Components
- **Zone:** 25 points max (preferred zones score higher)
- **Transport:** 25 points max (closer = better)
- **Physical:** 25 points max (larger lots score better)
- **Compliance:** 25 points max (all standards met = better)

### Lot Standards
- **Width:** 14m minimum
- **Depth:** 24m minimum
- **Area:** 336 sqm minimum
- **Transport:** 800m catchment

---

## 💡 Tips & Tricks

### Assessments
- ✅ Address auto-fill saves time
- ✅ Save assessments to database
- ✅ Load previous assessments from sidebar
- ✅ Add notes for follow-up items

### Maps
- 🗺️ Drag to pan, scroll to zoom
- 🎨 Right-click + drag to rotate
- 📍 Click markers for details
- 📐 Measure tool for distances
- 🖥️ Fullscreen for detailed viewing

### Reports
- 📄 Professional PDFs are client-ready
- 📋 Text reports are edit-friendly
- 📊 Excel exports for comparison
- 💾 All auto-saved to database

### Portfolio
- 📊 Dashboard updates in real-time
- 📈 Track all assessments
- 🔄 Quick filters for analysis
- 📥 Export all to Excel

---

## 🚨 Troubleshooting

### Map Not Loading
- Try refreshing the page
- Check zoom level
- Ensure coordinates are valid
- Falls back to standard map if needed

### PDF Not Generating
- Check all required fields are filled
- Ensure address is valid
- Try standard PDF if professional fails
- Check disk space

### Address Not Found
- Check spelling
- Include suburb/postcode
- Use full address format
- Try similar address

### Performance Issues
- Reduce number of layers shown
- Zoom in for better performance
- Reduce map height
- Clear browser cache

---

## 📈 Best Practices

### Assessment Workflow
1. ✅ Enter complete address
2. ✅ Verify auto-filled zone data
3. ✅ Complete physical details
4. ✅ Check all compliance boxes
5. ✅ Review map and amenities
6. ✅ Add assessor notes
7. ✅ Save to database
8. ✅ Generate PDF report

### Site Evaluation
1. Check zone type (GRZ/RGZ preferred)
2. Verify no overlays or covenants
3. Measure transport distance (< 800m)
4. Assess lot size (minimum 336 sqm)
5. Review compliance requirements
6. Consider site slope
7. Check nearby amenities
8. Make recommendation

### Reporting
1. Generate professional PDF
2. Review all sections
3. Add notes if needed
4. Export to client
5. File in portfolio
6. Track in database

---

## ⌨️ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Full screen map | F in map |
| Toggle layers | Ctrl + L (map) |
| Export to Excel | E (sidebar) |
| New assessment | Ctrl + N (app) |
| Generate PDF | Ctrl + P (form) |

---

## 📞 Support

### Common Issues

**Q: Where's my previous assessment?**
A: Check sidebar "Recent Assessments" list or load from database.

**Q: Why is score so low?**
A: Check zone type, transport distance, lot size, and compliance items.

**Q: How do I change the score components?**
A: Edit scoring.py file and adjust weights (zone, transport, physical, compliance).

**Q: Can I customize the map layers?**
A: Edit interactive_map_enhanced.py to add/remove layers or POI types.

**Q: How do I add team members?**
A: Edit simple_auth.py TEAM_CREDENTIALS dictionary and add new entries.

---

## 🔐 Security Notes

- Login credentials stored locally (demo only)
- For production, integrate with Azure AD or OAuth2
- Don't share demo credentials with external parties
- All assessments stored in local SQLite database
- Backup database.db regularly

---

## 📂 File Structure

```
/workspaces/Vic-Rooming_House-assessor/
├── app.py                           # Main application
├── ui_enhancements.py               # Professional styling
├── professional_pdf_generator.py    # Enhanced PDF reports
├── interactive_map_enhanced.py      # Advanced interactive maps
├── database.py                      # SQLite persistence
├── scoring.py                       # Scoring algorithm
├── simple_auth.py                   # Team authentication
├── portfolio_utils.py               # Dashboard functions
├── cost_estimator.py                # Cost calculations
├── excel_exporter.py                # Excel export
├── vicgis_wfs_lookup.py            # VicGIS integration
└── data/
    └── poi_cache.json               # Cached POI data
```

---

## 🎯 Next Steps

1. **Customize Credentials:** Update team members in simple_auth.py
2. **Add Your Logo:** Replace logo placeholder in ui_enhancements.py
3. **Configure Colors:** Modify COLORS dictionary in ui_enhancements.py
4. **Deploy to Server:** Use Streamlit Cloud or own server
5. **Integrate CRM:** Connect to your property management system
6. **Custom Reports:** Add your own report sections

---

## 📚 Documentation

- **UR_HAPPY_HOME_GUIDE.md** - Complete feature guide
- **ENHANCEMENTS_REPORT.md** - Technical enhancement details
- **DATA_SOURCES.md** - Data source references
- **START_HERE.md** - Getting started guide
- **IMPROVEMENT_RECOMMENDATIONS.md** - Future enhancements

---

**Version:** 2.0 Enhanced
**Last Updated:** February 16, 2026
**Status:** Production Ready ✅
