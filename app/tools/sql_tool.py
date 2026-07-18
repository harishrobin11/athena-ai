"""
SQL Execution Tool
Module: app.tools.sql_tool
"""
from sqlalchemy import text
from app.db.database import engine
from typing import Dict, Any, Optional

def _init_mock_db():
    """Seed the database with mock enterprise data if it doesn't exist."""
    with engine.begin() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                department VARCHAR(255) NOT NULL,
                revenue FLOAT NOT NULL,
                quarter VARCHAR(50) NOT NULL
            )
        '''))
        
        # Check if empty
        result = conn.execute(text('SELECT COUNT(*) FROM sales'))
        count = result.scalar()
        if count == 0:
            sample_data = [
                {'department': 'Engineering', 'revenue': 150000.0, 'quarter': 'Q1'},
                {'department': 'Sales', 'revenue': 500000.0, 'quarter': 'Q1'},
                {'department': 'Marketing', 'revenue': 120000.0, 'quarter': 'Q1'},
                {'department': 'Engineering', 'revenue': 200000.0, 'quarter': 'Q2'},
                {'department': 'Sales', 'revenue': 600000.0, 'quarter': 'Q2'},
                {'department': 'Marketing', 'revenue': 130000.0, 'quarter': 'Q2'}
            ]
            conn.execute(text('INSERT INTO sales (department, revenue, quarter) VALUES (:department, :revenue, :quarter)'), sample_data)

def execute_sql_query(tool_input: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Executes a raw SQL query against the internal analytics database.
    
    Parameters:
    - tool_input: The SQL query string.
    - context: Unused for basic execution.
    """
    _init_mock_db()
    
    query = tool_input.strip()
    # Basic safety filter (only allow SELECT for this mock env)
    if not query.upper().startswith("SELECT"):
        return "Error: Only SELECT queries are permitted for analytics reading."
        
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            col_names = list(result.keys())
            
            if not rows:
                return "Query executed successfully. Zero rows returned."
                
            result_str = f"Columns: {', '.join(col_names)}\n"
            for idx, row in enumerate(rows):
                result_str += f"Row {idx+1}: {row}\n"
                
            return result_str
            
    except Exception as e:
        return f"Error executing SQL query: {str(e)}"
