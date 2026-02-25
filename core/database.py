"""
Database module for Vic Rooming House Assessor
Handles SQLite operations for assessment storage and retrieval
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import streamlit as st

DATABASE_PATH = Path("assessments.db")


def _ensure_column_exists(cursor, table_name, column_name, column_sql):
    """Ensure a column exists on a table; add it if missing."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")

def init_database():
    """Initialize the SQLite database with required tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            zone_type TEXT NOT NULL,
            has_overlay INTEGER NOT NULL,
            dist_transport INTEGER NOT NULL,
            lot_width REAL NOT NULL,
            lot_area INTEGER NOT NULL,
            slope TEXT NOT NULL,
            has_covenant INTEGER NOT NULL,
            check_heating INTEGER NOT NULL,
            check_windows INTEGER NOT NULL,
            check_energy INTEGER NOT NULL,
            viability_status TEXT NOT NULL,
            viability_color TEXT NOT NULL,
            raw_score REAL NOT NULL,
            project_type TEXT DEFAULT 'Standard Rooming House',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            assessor_notes TEXT,
            custom_weights TEXT DEFAULT NULL
        )
    """)

    _ensure_column_exists(
        cursor,
        "assessments",
        "project_type",
        "TEXT DEFAULT 'Standard Rooming House'",
    )
    
    conn.commit()
    conn.close()

def save_assessment(assessment_data):
    """Save an assessment to the database"""
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO assessments (
                address, latitude, longitude, zone_type, has_overlay, dist_transport,
                lot_width, lot_area, slope, has_covenant, check_heating, check_windows,
                check_energy, viability_status, viability_color, raw_score, project_type, assessor_notes, custom_weights
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_data['address'],
            assessment_data['latitude'],
            assessment_data['longitude'],
            assessment_data['zone_type'],
            assessment_data['has_overlay'],
            assessment_data['dist_transport'],
            assessment_data['lot_width'],
            assessment_data['lot_area'],
            assessment_data['slope'],
            assessment_data['has_covenant'],
            assessment_data['check_heating'],
            assessment_data['check_windows'],
            assessment_data['check_energy'],
            assessment_data['viability_status'],
            assessment_data['viability_color'],
            assessment_data['raw_score'],
            assessment_data.get('project_type', 'Standard Rooming House'),
            assessment_data.get('assessor_notes', ''),
            assessment_data.get('custom_weights', None)
        ))
        
        conn.commit()
        assessment_id = cursor.lastrowid
        conn.close()
        return assessment_id
    except Exception as e:
        conn.close()
        raise e

def get_recent_assessments(limit=10):
    """Get recent assessments from the database"""
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, address, viability_status, viability_color, created_at
        FROM assessments
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return assessments

def get_assessment(assessment_id):
    """Retrieve a specific assessment by ID"""
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM assessments WHERE id = ?
    """, (assessment_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def delete_assessment(assessment_id):
    """Delete an assessment from the database"""
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM assessments WHERE id = ?", (assessment_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e

def update_assessment_notes(assessment_id, notes):
    """Update assessor notes for an assessment"""
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE assessments
            SET assessor_notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (notes, assessment_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        raise e

def get_statistics():
    """Get statistics about all assessments"""
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_assessments,
            SUM(CASE WHEN viability_color = 'green' THEN 1 ELSE 0 END) as suitable_count,
            SUM(CASE WHEN viability_color = 'orange' THEN 1 ELSE 0 END) as conditional_count,
            SUM(CASE WHEN viability_color = 'red' THEN 1 ELSE 0 END) as unsuitable_count,
            AVG(raw_score) as average_score
        FROM assessments
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    return {
        'total_assessments': result[0] or 0,
        'suitable_count': result[1] or 0,
        'conditional_count': result[2] or 0,
        'unsuitable_count': result[3] or 0,
        'average_score': result[4] or 0
    }

def export_to_csv():
    """Export all assessments to CSV format"""
    import csv
    from io import StringIO
    
    init_database()
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM assessments ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return None
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=dict(rows[0]).keys())
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))
    
    return output.getvalue()
