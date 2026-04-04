import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json

load_dotenv()
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

try:
    conn = psycopg2.connect(
        dbname="causal_guard",
        user="postgres",
        password=DB_PASSWORD,
        host="localhost"
    )
    cur = conn.cursor()
    
    # ✅ CREATE TABLE IF IT DOESN'T EXIST (ADD THIS)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS causal_audit_logs (
            id SERIAL PRIMARY KEY,
            scenario_id VARCHAR(50),
            incident_category VARCHAR(50),
            llm_explanation TEXT,
            check_results JSONB,
            all_passed BOOLEAN,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Now insert test data
    cur.execute("""
        INSERT INTO causal_audit_logs 
        (scenario_id, incident_category, llm_explanation, check_results, all_passed, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        'TEST-001',
        'Test',
        'This is a test entry',
        Json({'test': True}),
        True,
        Json({'test': 'metadata'})
    ))
    
    test_id = cur.fetchone()[0]
    conn.commit()
    print(f"✅ SUCCESS! Test entry saved with ID: {test_id}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection failed: {e}")