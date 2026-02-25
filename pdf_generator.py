"""
PDF Report Generator for Vic Rooming House Assessor
Generates professional PDF reports with assessment data
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from io import BytesIO
import os

def generate_pdf_report(assessment_data, report_selections, logo_path=None):
    """
    Generate a professional PDF report for an assessment.
    
    Args:
        assessment_data: Dictionary containing all assessment information
        report_selections: Dictionary of selected report sections
        logo_path: Optional path to company logo
    
    Returns:
        BytesIO object containing the PDF
    """
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    custom_styles = {
        'title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ),
        'heading': ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ),
        'subheading': ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=11,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ),
        'normal': ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=colors.HexColor('#333333')
        ),
        'status_text': ParagraphStyle(
            'StatusText',
            parent=styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold'
        )
    }
    
    story = []
    
    # Header with optional logo
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=1.5*inch, height=0.75*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))
        except:
            pass
    
    # Title
    title = Paragraph("ROOMING HOUSE SITE ASSESSMENT REPORT", custom_styles['title'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Report metadata
    generated_date = datetime.now().strftime('%d %B %Y at %H:%M')
    meta_text = f"<b>Generated:</b> {generated_date} | <b>Address:</b> {assessment_data['address']}"
    story.append(Paragraph(meta_text, custom_styles['normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Status banner
    status_color = {
        'green': '#d4edda',
        'orange': '#fff3cd',
        'red': '#f8d7da'
    }.get(assessment_data['viability_color'], '#f8f9fa')
    
    status_text_color = {
        'green': '#155724',
        'orange': '#856404',
        'red': '#721c24'
    }.get(assessment_data['viability_color'], '#383d41')
    
    status_symbols = {
        'green': '✓',
        'orange': '⚠',
        'red': '✗'
    }
    
    status_symbol = status_symbols.get(assessment_data['viability_color'], '?')
    
    # Create status box
    status_style = ParagraphStyle(
        'StatusBox',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(status_text_color),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    status_para = Paragraph(
        f"{status_symbol} <b>{assessment_data['viability_status']}</b><br/>"
        f"<font size=10>{assessment_data.get('summary_message', '')}</font>",
        status_style
    )
    
    status_table = Table(
        [[status_para]],
        colWidths=[6*inch],
        rowHeights=[1*inch]
    )
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(status_color)),
        ('BORDER', (0, 0), (-1, -1), 1, colors.HexColor(status_text_color)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Executive Summary
    if report_selections.get("Executive Summary"):
        story.append(Paragraph("EXECUTIVE SUMMARY", custom_styles['heading']))
        summary_items = [
            ("Viability Status", assessment_data['viability_status']),
            ("Overall Score", f"{assessment_data.get('raw_score', 0):.1f}/100"),
            ("Risk Level", {
                'green': 'LOW',
                'orange': 'MODERATE',
                'red': 'HIGH'
            }.get(assessment_data['viability_color'], 'UNKNOWN')),
            ("Assessment Date", datetime.now().strftime('%d %B %Y'))
        ]
        
        summary_data = [["Metric", "Value"]]
        for metric, value in summary_items:
            summary_data.append([metric, value])
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')])
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Site Information
    if report_selections.get("Site Location & Zoning Analysis"):
        story.append(Paragraph("SITE LOCATION & ZONING", custom_styles['heading']))
        
        zoning_data = [
            ["Planning Zone", assessment_data.get('zone_type', 'N/A')],
            ["Zone Suitability", "SUITABLE" if assessment_data.get('is_preferred_zone') else "NOT SUITABLE"],
            ["Heritage/Character Overlay", "YES - CONSTRAINT" if assessment_data.get('has_overlay') else "NO"],
            ["Coordinates", f"{assessment_data.get('latitude', 0):.4f}, {assessment_data.get('longitude', 0):.4f}"]
        ]
        
        zoning_table = Table(zoning_data, colWidths=[2*inch, 4*inch])
        zoning_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(zoning_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Physical Suitability
    if report_selections.get("Physical Suitability Assessment"):
        story.append(Paragraph("PHYSICAL SUITABILITY", custom_styles['heading']))
        
        physical_data = [
            ["Metric", "Value", "Requirement", "Status"],
            ["Lot Width", f"{assessment_data.get('lot_width', 0)}m", "≥14m", 
             "✓ PASS" if assessment_data.get('is_width_compliant') else "✗ FAIL"],
            ["Lot Depth", f"{assessment_data.get('lot_depth', 0)}m", "≥24m", 
             "✓ PASS" if assessment_data.get('is_depth_compliant') else "✗ FAIL"],
            ["Lot Area", f"{assessment_data.get('lot_area', 0):.0f} sqm", "≥336 sqm", 
             "✓ PASS" if assessment_data.get('is_area_compliant') else "✗ FAIL"],
            ["Site Slope", assessment_data.get('slope', 'Unknown'), "Flat preferred", 
             "✓ Ideal" if assessment_data.get('slope') == 'Flat' else "⚠ Check"],
            ["Single Dwelling Covenant", "YES - CONSTRAINT" if assessment_data.get('has_covenant') else "NO", "-", 
             "✗" if assessment_data.get('has_covenant') else "✓"]
        ]
        
        physical_table = Table(physical_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        physical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(physical_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Regulatory Compliance
    if report_selections.get("Regulatory Compliance"):
        story.append(Paragraph("REGULATORY COMPLIANCE (Dec 2025 / 2030 Standards)", custom_styles['heading']))
        
        compliance_score = sum([
            assessment_data.get('check_heating', 0),
            assessment_data.get('check_windows', 0),
            assessment_data.get('check_energy', 0)
        ])
        
        compliance_data = [
            ["Standard", "Status"],
            ["Fixed Heating in All Rooms", "✓ CONFIRMED" if assessment_data.get('check_heating') else "✗ NOT CONFIRMED"],
            ["Blind Cord Safety", "✓ CONFIRMED" if assessment_data.get('check_windows') else "✗ NOT CONFIRMED"],
            ["All-Electric / Heat Pump Ready", "✓ CONFIRMED" if assessment_data.get('check_energy') else "✗ NOT CONFIRMED"],
            ["Compliance Score", f"{compliance_score}/3"]
        ]
        
        compliance_table = Table(compliance_data, colWidths=[3.5*inch, 2.5*inch])
        compliance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(compliance_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Proximity & Transport
    if report_selections.get("Proximity & Transport"):
        story.append(Paragraph("PROXIMITY & TRANSPORT ANALYSIS", custom_styles['heading']))
        
        is_transport_compliant = assessment_data.get('dist_transport', 0) <= 800
        transport_data = [
            ["Metric", "Value", "Standard"],
            ["Distance to Transport/Activity Centre", f"{assessment_data.get('dist_transport', 0)}m", "≤800m"],
            ["Status", "COMPLIANT" if is_transport_compliant else "OUTSIDE CATCHMENT", "-"]
        ]
        
        transport_table = Table(transport_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        transport_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')])
        ]))
        story.append(transport_table)
        story.append(Spacer(1, 0.3*inch))
    
    # Risk Assessment
    if report_selections.get("Risk Assessment & Constraints"):
        story.append(Paragraph("RISK ASSESSMENT & CONSTRAINTS", custom_styles['heading']))
        
        constraints = assessment_data.get('identified_constraints', [])
        if constraints:
            for constraint in constraints:
                story.append(Paragraph(f"• {constraint}", custom_styles['normal']))
        else:
            story.append(Paragraph("No significant constraints identified.", custom_styles['normal']))
        
        story.append(Spacer(1, 0.2*inch))
        risk_level_text = {
            'green': 'LOW - Site appears suitable for development',
            'orange': 'MODERATE - Conditional constraints require mitigation',
            'red': 'HIGH - Significant constraints present'
        }.get(assessment_data['viability_color'], 'UNKNOWN')
        
        story.append(Paragraph(f"<b>Overall Risk Level:</b> {risk_level_text}", custom_styles['normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    if report_selections.get("Recommendations"):
        story.append(Paragraph("RECOMMENDATIONS", custom_styles['heading']))
        
        recommendations = assessment_data.get('recommendations', [])
        if recommendations:
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", custom_styles['normal']))
        else:
            story.append(Paragraph("Site appears suitable for development. Proceed with detailed planning.", 
                                  custom_styles['normal']))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("<b>Next Steps:</b>", custom_styles['subheading']))
        story.append(Paragraph("• Engage local architect for detailed site assessment", custom_styles['normal']))
        story.append(Paragraph("• Commission geotechnical survey if slope > 5%", custom_styles['normal']))
        story.append(Paragraph("• Obtain formal council pre-lodgement advice", custom_styles['normal']))
        story.append(Paragraph("• Engage town planning consultant for zoning confirmation", custom_styles['normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # Nearby Amenities (New Section)
    story.append(PageBreak())
    story.append(Paragraph("NEARBY AMENITIES & SERVICES (1km Radius)", custom_styles['heading']))
    
    amenities_summary = assessment_data.get('amenities_summary', {})
    
    if amenities_summary.get('transit'):
        story.append(Paragraph("<b>Public Transport Stops</b>", custom_styles['subheading']))
        transit_list = amenities_summary['transit'][:5]
        for item in transit_list:
            story.append(Paragraph(f"• {item.get('name', 'Transit Stop')} ({item.get('distance_m', 0)}m)", custom_styles['normal']))
        story.append(Spacer(1, 0.2*inch))
    
    if amenities_summary.get('schools'):
        story.append(Paragraph("<b>Educational Facilities</b>", custom_styles['subheading']))
        schools_list = amenities_summary['schools'][:5]
        for item in schools_list:
            story.append(Paragraph(f"• {item.get('name', 'School')} ({item.get('distance_m', 0)}m)", custom_styles['normal']))
        story.append(Spacer(1, 0.2*inch))
    
    if amenities_summary.get('parks'):
        story.append(Paragraph("<b>Parks & Recreation</b>", custom_styles['subheading']))
        parks_list = amenities_summary['parks'][:5]
        for item in parks_list:
            story.append(Paragraph(f"• {item.get('name', 'Park')} ({item.get('distance_m', 0)}m)", custom_styles['normal']))
        story.append(Spacer(1, 0.2*inch))
    
    if amenities_summary.get('shops'):
        story.append(Paragraph("<b>Shopping & Services</b>", custom_styles['subheading']))
        shops_list = amenities_summary['shops'][:5]
        for item in shops_list:
            story.append(Paragraph(f"• {item.get('name', 'Shop')} ({item.get('distance_m', 0)}m)", custom_styles['normal']))
        story.append(Spacer(1, 0.2*inch))
    
    if amenities_summary.get('heritage'):
        story.append(Paragraph("<b>Heritage & Historical Sites</b>", custom_styles['subheading']))
        heritage_list = amenities_summary['heritage'][:5]
        for item in heritage_list:
            story.append(Paragraph(f"• {item.get('name', 'Heritage Site')} ({item.get('distance_m', 0)}m)", custom_styles['normal']))
        story.append(Spacer(1, 0.3*inch))
    
    # Footer
    story.append(Spacer(1, 0.2*inch))
    footer_text = (
        f"<br/><br/><font size=8>"
        f"Report generated by Vic Rooming House Assessor on {datetime.now().strftime('%d %B %Y at %H:%M')}<br/>"
        f"This report is for assessment purposes only and should be reviewed by a qualified planning consultant.<br/>"
        f"©2026 Vic Rooming House Assessor. All rights reserved."
        f"</font>"
    )
    story.append(Paragraph(footer_text, custom_styles['normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
