"""
Enhanced PDF report generator with professional formatting.
Implements best practices from real estate industry reports.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
    Image, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime

# Colors matching UR Happy Home branding
PRIMARY_COLOR = colors.HexColor('#1F7F4C')
SECONDARY_COLOR = colors.HexColor('#2E5C4A')
ACCENT_COLOR = colors.HexColor('#D4A574')
WARNING_COLOR = colors.HexColor('#F39C12')
SUCCESS_COLOR = colors.HexColor('#27AE60')
DANGER_COLOR = colors.HexColor('#E74C3C')
TEXT_COLOR = colors.HexColor('#2C3E50')
LIGHT_GRAY = colors.HexColor('#F8F9FA')


def create_professional_pdf_report(assessment_data, report_selections=None):
    """
    Generate professional-grade PDF report with modern formatting.
    
    Args:
        assessment_data: Dictionary with assessment information
        report_selections: Dictionary of selected sections to include
    
    Returns:
        BytesIO buffer containing PDF
    """
    
    if report_selections is None:
        report_selections = {
            "Executive Summary": True,
            "Site Location & Zoning Analysis": True,
            "Physical Suitability Assessment": True,
            "Regulatory Compliance": True,
            "Proximity & Transport": True,
            "Risk Assessment & Constraints": True,
            "Recommendations": True,
        }
    
    # Create PDF buffer
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        title="UR Happy Home - Site Assessment Report"
    )
    
    # Container for PDF content
    story = []
    
    # Define custom styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        backColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=12,
        alignment=TA_LEFT,
        leftIndent=10,
        rightIndent=10,
        fontName='Helvetica-Bold'
    )
    
    # Normal text style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=10,
        leading=12
    )
    
    # ========================================
    # COVER PAGE / HEADER
    # ========================================
    
    # Company header
    header_data = [
        [
            Paragraph(
                f"<font color='{PRIMARY_COLOR.hexval()}'><b>UR HAPPY HOME</b></font><br/>"
                "<font size='8'>Site Assessment Report</font>",
                ParagraphStyle('Header', parent=styles['Normal'], fontSize=16, alignment=TA_LEFT)
            ),
            Paragraph(
                f"<font size='10'><b>Report Date:</b><br/>{datetime.now().strftime('%d %B %Y')}</font>",
                ParagraphStyle('Header', parent=styles['Normal'], fontSize=9, alignment=TA_RIGHT)
            )
        ]
    ]
    
    header_table = Table(header_data, colWidths=[4*inch, 2*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Main title
    story.append(Paragraph("DEVELOPMENT SITE ASSESSMENT REPORT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Address highlight box
    address = assessment_data.get('address', 'Unknown Address')
    score = assessment_data.get('raw_score', 0)
    status = assessment_data.get('viability_status', 'UNKNOWN')
    
    address_table = Table([
        [
            Paragraph(f"<b>Site Address:</b><br/><font size='12'>{address}</font>", body_style),
            Paragraph(
                f"<b>Assessment Score:</b><br/><font size='14' color='{PRIMARY_COLOR.hexval()}'><b>{score:.1f}/100</b></font><br/>"
                f"<font size='9'>Status: <b>{status}</b></font>",
                ParagraphStyle('Score', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
            )
        ]
    ], colWidths=[3.5*inch, 2.5*inch])
    
    address_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GRAY),
        ('BORDER', (0, 0), (-1, -1), 2, PRIMARY_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(address_table)
    story.append(Spacer(1, 0.3*inch))
    
    # ========================================
    # EXECUTIVE SUMMARY
    # ========================================
    if report_selections.get("Executive Summary"):
        story.append(Paragraph("EXECUTIVE SUMMARY", section_style))
        
        summary_text = f"""
        This site assessment evaluates the suitability of the property at <b>{address}</b> for rooming house development 
        in accordance with Victorian planning requirements. The assessment considers zoning compliance, physical characteristics, 
        regulatory standards, and proximity to essential services.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Overall Viability Score: <font color='{PRIMARY_COLOR.hexval()}'><b>{score:.1f}/100</b></font><br/>
        • Assessment Status: <b>{status}</b><br/>
        • Planning Zone: <b>{assessment_data.get('zone_type', 'N/A')}</b><br/>
        • Lot Area: <b>{assessment_data.get('lot_area', 0):.0f} sqm</b> ({assessment_data.get('lot_width', 0):.1f}m × {assessment_data.get('lot_depth', 0):.1f}m)<br/>
        • Transport Distance: <b>{assessment_data.get('dist_transport', 0):.0f}m</b><br/>
        """
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 0.2*inch))

    # ========================================
    # DESIGN SPECIFICATION (NEW)
    # ========================================
    design_locked = assessment_data.get('design_locked')
    if design_locked:
        story.append(Paragraph("STANDARD DESIGN SPECIFICATION", section_style))
        
        design_text = f"""
        <b>All properties are assessed for their suitability to accommodate the UR Happy Home 
        Standard Rooming House Design (approved February 2026).</b><br/><br/>
        <b>Design Details:</b><br/>
        • Design Name: UR Happy Home Standard Rooming House Design v1.0<br/>
        • Bedrooms: 5<br/>
        • Bathrooms: 3 (including 1 ensuite)<br/>
        • Gross Floor Area: 274 m²<br/>
        • Levels: 2<br/>
        • NDIS Compliant: Yes<br/>
        • Accessibility Features: Full wheelchair access, accessible kitchens, grab rails, emergency exits<br/>
        • All-Electric Ready: Yes (heat pump heating, EV charging infrastructure)<br/>
        <br/>
        <b>Compliance Status:</b><br/>
        This design has been independently verified to be compliant with:<br/>
        • Victorian rooming-house minimum standards (CAV)<br/>
        • NDIS (National Disability Insurance Scheme) requirements<br/>
        • Disability access and accommodation standards<br/>
        • NCC 2022 Building Code requirements<br/>
        <br/>
        <b>Site Assessment Context:</b><br/>
        This property has been evaluated for its suitability to construct and operate this standard design.
        Site-specific limitations, zoning constraints, or other factors may impact feasibility.
        """
        story.append(Paragraph(design_text, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # ========================================
    # ZONING ANALYSIS
    # ========================================
    if report_selections.get("Site Location & Zoning Analysis"):
        story.append(Paragraph("SITE LOCATION & ZONING ANALYSIS", section_style))
        
        zone = assessment_data.get('zone_type', 'Unknown')
        overlay = "Yes" if assessment_data.get('has_overlay') else "No"
        
        zoning_text = f"""
        <b>Planning Zone:</b> {zone}<br/>
        <b>Heritage/Neighbourhood Character Overlay:</b> {overlay}<br/>
        <br/>
        The planning zone has been verified through VicPlan. The site's zoning compliance is critical for rooming house 
        development, as only certain zones permit this land use. General Residential Zones (GRZ) and Residential Growth 
        Zones (RGZ) are typically preferred for this use.
        <br/><br/>
        <b>Zoning Compatibility:</b> {'✓ SUITABLE' if assessment_data.get('is_preferred_zone') else '✗ REQUIRES FURTHER INVESTIGATION'}<br/>
        {'Zone overlay restrictions apply and should be verified with the local council.' if overlay == 'Yes' else 'No zone overlays identified.'}
        """
        story.append(Paragraph(zoning_text, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # ========================================
    # PHYSICAL SUITABILITY
    # ========================================
    if report_selections.get("Physical Suitability Assessment"):
        story.append(Paragraph("PHYSICAL SUITABILITY ASSESSMENT", section_style))
        
        lot_width = assessment_data.get('lot_width', 0)
        lot_depth = assessment_data.get('lot_depth', 0)
        lot_area = assessment_data.get('lot_area', 0)
        slope = assessment_data.get('slope', 'Unknown')
        covenant = "Yes" if assessment_data.get('has_covenant') else "No"
        
        physical_data = [
            ['Criteria', 'Value', 'Standard', 'Status'],
            ['Lot Width', f"{lot_width:.1f}m", '14m', '✓ OK' if lot_width >= 14 else '✗ Below'],
            ['Lot Depth', f"{lot_depth:.1f}m", '24m', '✓ OK' if lot_depth >= 24 else '✗ Below'],
            ['Lot Area', f"{lot_area:.0f} sqm", '336 sqm', '✓ OK' if lot_area >= 336 else '✗ Below'],
            ['Site Slope', slope, 'Flat preferred', 'See notes'],
            ['Single Dwelling Covenant', covenant, 'None', '✓ Clear' if covenant == 'No' else '✗ Present'],
        ]
        
        physical_table = Table(physical_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
        physical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(physical_table)
        story.append(Spacer(1, 0.2*inch))
    
    # ========================================
    # REGULATORY COMPLIANCE
    # ========================================
    if report_selections.get("Regulatory Compliance"):
        story.append(Paragraph("REGULATORY COMPLIANCE (Rooming-house Minimum Standards)", section_style))

        heating = "✓ Confirmed" if assessment_data.get('check_heating') else "✗ Not Confirmed"
        windows = "✓ Confirmed" if assessment_data.get('check_windows') else "✗ Not Confirmed"
        energy = "✓ Confirmed" if assessment_data.get('check_energy') else "✗ Not Confirmed"

        # Build compliance summary including rooming-house-specific findings
        compliance_parts = []
        compliance_parts.append("<b>Mandatory Building Items:</b><br/>")
        compliance_parts.append(f"• Fixed Heating: {heating}<br/>")
        compliance_parts.append(f"• Blind Cord Safety: {windows}<br/>")
        compliance_parts.append(f"• All-Electric / Heat Pump Ready: {energy}<br/><br/>")

        reg = assessment_data.get('regulatory_findings') or {}
        if reg:
            checks = reg.get('checks', {})
            overall = reg.get('overall_compliant', False)
            compliance_parts.append("<b>Rooming-house Minimum Standards Check:</b><br/>")
            # Present each check with a short pass/fail and the reason text
            if 'gross_floor_area_ok' in checks:
                compliance_parts.append(f"• Gross floor area test: {'PASS' if checks['gross_floor_area_ok'] else 'FAIL'}<br/>")
            if 'bedrooms_ok' in checks:
                compliance_parts.append(f"• Bedrooms test: {'PASS' if checks['bedrooms_ok'] else 'FAIL'}<br/>")
            if 'persons_ok' in checks:
                compliance_parts.append(f"• Occupancy test: {'PASS' if checks['persons_ok'] else 'FAIL'}<br/>")

            # Add detailed reasons
            compliance_parts.append("<br/><b>Details:</b><br/>")
            for reason in reg.get('reasons', []):
                # Use plain bullet for reportlab
                compliance_parts.append(f"• {reason}<br/>")

            compliance_parts.append(f"<br/><b>Overall rooming-house compliance:</b> {'Compliant' if overall else 'Not compliant'}<br/>")
        else:
            compliance_parts.append("Rooming-house minimum standards: Not evaluated.<br/>")

        compliance_text = "".join(compliance_parts)
        story.append(Paragraph(compliance_text, body_style))
        story.append(Spacer(1, 0.2*inch))

    # ========================================
    # DESIGN SUITABILITY (NEW)
    # ========================================
    design_suit = assessment_data.get('design_suitability') or {}
    if design_suit and 'error' not in design_suit:
        story.append(Paragraph("UR HAPPY HOME DESIGN - SITE SUITABILITY", section_style))
        
        design_parts = []
        design_parts.append(f"<b>Design:</b> {design_suit.get('design_name', 'Standard Design')}<br/><br/>")
        
        # Suitability checks
        checks = design_suit.get('suitability_checks', {})
        all_pass = design_suit.get('all_checks_pass', False)
        
        design_parts.append("<b>Site Fit Assessment:</b><br/>")
        design_parts.append(f"• Lot area sufficient: {'PASS' if checks.get('lot_area_sufficient') else 'REVIEW'}<br/>")
        design_parts.append(f"• Zone suitable: {'PASS' if checks.get('zone_suitable') else 'CONFIRM'}<br/>")
        design_parts.append(f"• Transport access: {'PASS' if checks.get('transport_compliant') else 'NOTE'}<br/>")
        design_parts.append(f"• Title check required: YES<br/>")
        
        # Detailed reasons
        design_parts.append("<br/><b>Suitability Assessment:</b><br/>")
        for reason in design_suit.get('reasons', []):
            design_parts.append(f"• {reason}<br/>")
        
        # Permit info
        permit = design_suit.get('permit_requirement', {})
        if permit:
            design_parts.append(f"<br/><b>Planning Permit:</b><br/>")
            design_parts.append(f"• Required: {'Yes' if permit.get('required') else 'No'}<br/>")
            design_parts.append(f"• Reason: {permit.get('reason', 'N/A')}<br/>")
        
        design_parts.append(f"<br/><b>Overall suitability:</b> {'Site suitable for design ✓' if all_pass else 'Site requires further assessment'}<br/>")
        
        design_text = "".join(design_parts)
        story.append(Paragraph(design_text, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # ========================================
    # TRANSPORT & AMENITIES
    # ========================================
    if report_selections.get("Proximity & Transport"):
        story.append(Paragraph("PROXIMITY & TRANSPORT ANALYSIS", section_style))
        
        transport_dist = assessment_data.get('dist_transport', 0)
        amenities = assessment_data.get('amenities_summary', {})
        
        transit_count = len(amenities.get('transit', []))
        school_count = len(amenities.get('schools', []))
        park_count = len(amenities.get('parks', []))
        shop_count = len(amenities.get('shops', []))

        def nearest_distance(category_list):
            try:
                distances = [p.get('distance_m', 99999) for p in category_list]
                min_d = int(min(distances))
                # find corresponding name if available
                for p in category_list:
                    if int(p.get('distance_m', 99999)) == min_d:
                        name = p.get('name') or p.get('title') or None
                        return f"{min_d}m" + (f" ({name})" if name else "")
                return f"{min_d}m"
            except Exception:
                return 'N/A'

        amenities_data = [
            ['Amenity Type', 'Count', 'Nearest Distance'],
            ['🚌 Public Transport Stops', transit_count, nearest_distance(amenities.get('transit', [])) if transit_count > 0 else 'N/A'],
            ['🎓 Schools', school_count, nearest_distance(amenities.get('schools', [])) if school_count > 0 else 'N/A'],
            ['🌳 Parks & Recreation', park_count, nearest_distance(amenities.get('parks', [])) if park_count > 0 else 'N/A'],
            ['🛒 Shops & Services', shop_count, nearest_distance(amenities.get('shops', [])) if shop_count > 0 else 'N/A'],
        ]
        
        amenities_table = Table(amenities_data, colWidths=[2.2*inch, 1.2*inch, 2.1*inch])
        amenities_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GRAY),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ]))
        story.append(amenities_table)
        story.append(Spacer(1, 0.2*inch))
        
        transport_text = f"""
        Distance to nearest transport/activity centre: <b>{transport_dist:.0f}m</b>
        <br/>
        Transport Compliance (800m catchment): <b>{'✓ COMPLIANT' if transport_dist <= 800 else '✗ OUTSIDE CATCHMENT'}</b>
        """
        story.append(Paragraph(transport_text, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # ========================================
    # RECOMMENDATIONS
    # ========================================
    if report_selections.get("Recommendations"):
        story.append(Paragraph("RECOMMENDATIONS & NEXT STEPS", section_style))
        
        recommendations = assessment_data.get('recommendations', [])
        constraints = assessment_data.get('identified_constraints', [])
        
        if recommendations:
            recommendations_text = "<b>Recommended Actions:</b><br/>"
            for i, rec in enumerate(recommendations, 1):
                # Fix: Use plain bullet character instead of invalid <bullet> tag
                recommendations_text += f"• {rec}<br/>"
        else:
            recommendations_text = "No specific recommendations at this time."
        
        if constraints:
            recommendations_text += "<br/><b>Identified Constraints:</b><br/>"
            for constraint in constraints:
                # Fix: Use plain bullet character instead of invalid <bullet> tag
                recommendations_text += f"• {constraint}<br/>"
        
        story.append(Paragraph(recommendations_text, body_style))
        story.append(Spacer(1, 0.2*inch))
    
    # ========================================
    # FOOTER
    # ========================================
    story.append(Spacer(1, 0.3*inch))
    footer_text = """
    <font size='8'>
    <b>Disclaimer:</b> This report is prepared for assessment purposes only. It is based on information available at the time of assessment.
    Site conditions, planning requirements, and regulations may change. Professional advice should be obtained before making investment decisions.
    All estimates are indicative and subject to verification.<br/><br/>
    UR Happy Home - Site Assessment Report | Generated {date}
    </font>
    """.format(date=datetime.now().strftime('%d %B %Y at %H:%M'))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#999999'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer
