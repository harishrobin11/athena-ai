"""
SQL Execution Tool
Module: app.tools.sql_tool
"""
import sqlite3
import os
from typing import Dict, Any, Optional

def _init_mock_db(db_path: str):
    """Seed the database with mock enterprise data if it doesn't exist."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create mock sales table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            revenue REAL NOT NULL,
            quarter TEXT NOT NULL
        )
    ''')
    
    # Check if empty
    cursor.execute('SELECT COUNT(*) FROM sales')
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('Engineering', 150000.0, 'Q1'),
            ('Sales', 500000.0, 'Q1'),
            ('Marketing', 120000.0, 'Q1'),
            ('Engineering', 200000.0, 'Q2'),
            ('Sales', 600000.0, 'Q2'),
            ('Marketing', 130000.0, 'Q2')
        ]
        cursor.executemany('INSERT INTO sales (department, revenue, quarter) VALUES (?, ?, ?)', sample_data)
        conn.commit()
        
    conn.close()

def execute_sql_query(tool_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Executes a raw SQL query against the internal analytics database.
    
    Parameters:
    - tool_input: The SQL query string.
    - context: Unused for basic execution.
    """
    db_path = os.path.join(os.getcwd(), "storage", "db", "analytics.db")
    _init_mock_db(db_path)
    
    query = tool_input.strip()
    # Basic safety filter (only allow SELECT for this mock env)
    if not query.upper().startswith("SELECT"):
        return "Error: Only SELECT queries are permitted for analytics reading."
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Get column names
        col_names = [description[0] for description in cursor.description]
        
        conn.close()
        
        if not rows:
            return "Query executed successfully. Zero rows returned."
            
        result_str = f"Columns: {', '.join(col_names)}\n"
        for idx, row in enumerate(rows):
            result_str += f"Row {idx+1}: {row}\n"
            
        return result_str
        
    except Exception as e:
        return f"Error executing SQL query: {str(e)}"
