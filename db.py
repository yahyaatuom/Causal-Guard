# db.py
import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Database:
    """Database abstraction that defaults to SQLite, optionally uses PostgreSQL."""
    
    def __init__(self):
        self.connection = None
        self.use_postgres = self._check_postgres()
        self.db_path = Path(__file__).parent / "causal_guard.db"
        
        if self.use_postgres:
            self._init_postgres()
        else:
            self._init_sqlite()
    
    def _check_postgres(self) -> bool:
        """Check if PostgreSQL is configured and available"""
        DB_NAME = os.getenv("DB_NAME")
        DB_USER = os.getenv("DB_USER")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        
        if not all([DB_NAME, DB_USER, DB_PASSWORD]):
            return False
        
        try:
            import psycopg2
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=os.getenv("DB_HOST", "localhost"),
                connect_timeout=5
            )
            conn.close()
            return True
        except Exception:
            return False
    
    def _init_sqlite(self):
        """Initialize SQLite database (no setup required)"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS causal_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT,
                incident_category TEXT,
                llm_explanation TEXT,
                check_results TEXT,
                all_passed INTEGER,
                metadata TEXT,
                run_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
        print(f"📁 Using SQLite database at {self.db_path}")
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        import psycopg2
        from psycopg2.extras import Json
        
        self.psycopg2 = psycopg2
        self.Json = Json
        
        self.connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost")
        )
        
        cur = self.connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS causal_audit_logs (
                id SERIAL PRIMARY KEY,
                scenario_id VARCHAR(50),
                incident_category VARCHAR(50),
                llm_explanation TEXT,
                check_results JSONB,
                all_passed BOOLEAN,
                metadata JSONB,
                run_id VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.connection.commit()
        cur.close()
        print("🐘 Using PostgreSQL database")
    
    def save_result(self, scenario_id: str, category: str, explanation: str, 
                    checks: dict, all_passed: bool, metadata: dict, run_id: str):
        """Save a validation result"""
        if self.use_postgres:
            cur = self.connection.cursor()
            cur.execute("""
                INSERT INTO causal_audit_logs 
                (scenario_id, incident_category, llm_explanation, check_results, all_passed, metadata, run_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                scenario_id, category, explanation,
                self.Json(checks), all_passed, self.Json(metadata), run_id
            ))
            self.connection.commit()
            cur.close()
        else:
            cur = self.connection.cursor()
            cur.execute("""
                INSERT INTO causal_audit_logs 
                (scenario_id, incident_category, llm_explanation, check_results, all_passed, metadata, run_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scenario_id, category, explanation,
                json.dumps(checks), 1 if all_passed else 0, 
                json.dumps(metadata), run_id
            ))
            self.connection.commit()
            cur.close()
        print("   💾 Saved to database")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


# Singleton instance
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance