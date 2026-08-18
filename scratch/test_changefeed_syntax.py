import os
import sys

sys.path.insert(0, os.path.abspath("apps/api"))
sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import text
from app.db.session import SessionLocal

def main():
    print("Testing CockroachDB Changefeed Execution Syntax...")
    db = SessionLocal()
    try:
        # Let's test EXPERIMENTAL-CHANGEFEED or CHANGEFEED with cursor
        raw_conn = db.connection().connection.driver_connection
        cursor = raw_conn.cursor()
        print("Executing: EXPERIMENTAL CHANGEFEED FOR remediation_outcomes WITH updated;")
        cursor.execute("EXPERIMENTAL CHANGEFEED FOR remediation_outcomes WITH updated;")
        print("EXPERIMENTAL CHANGEFEED started successfully!")
        # We don't block forever, close cursor
        cursor.close()
    except Exception as e:
        print(f"EXPERIMENTAL-CHANGEFEED error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
